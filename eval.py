import os, argparse, json
from collections.abc import Callable
import pandas as pd
from jsonschema import validate
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pos_tagger import POSTagger, Language, TAGMethod
from parsers import parse_italian_analysis, parse_english_analysis
from langchain_community.callbacks.manager import get_openai_callback

# load keys from local settings file
if(os.getenv("PY_ENV") == "DEVELOPMENT"):
    load_dotenv()

# set up parser
parser = argparse.ArgumentParser(
    prog='eval',
    description='Performs a series of analysis and evaluation tasks on input texts using an OAI LLM'
)

parser.add_argument("input", help="a TSV file containing the texts to evaluate")
parser.add_argument("-t", "--tasks", help="a JSON file containing analysis tasks to perform", required=True)
parser.add_argument("-p", "--postagger", help="the language to validate constraints against, used to initialize the postagger", required=True)
parser.add_argument("-l", "--label", help="(optional) the label of the column that contains input data", default="completions")
parser.add_argument('-a', '--analysis', help="(optional) perform analysis only", action='store_true')
parser.add_argument('-s', "--syntax", help="(optional) perform syntax analysis", action='store_true')
parser.add_argument('-d', '--debug', action='store_true', help="(optional) log additional information")
parser.add_argument('-o', '--output', help="(optional) output file")

def validate_args(args):
    """Validate command line arguments"""
    if (not (os.path.isfile(args.input) and (os.path.splitext(args.input)[-1].lower() == ".tsv"))):
        print("Error: the input file does not exist or is not a supported format!")
        exit(2)

    if (not (os.path.isfile(args.tasks) and (os.path.splitext(args.tasks)[-1].lower() == ".json"))):
        print("Error: the tasks file does not exist or is not a supported format!")
        exit(2)

    output_file = args.output if args.output != None else (f"{os.path.splitext(args.input)[0]}_analysis.tsv" if args.analysis else f"{os.path.splitext(args.input)[0]}_eval.tsv")
    if (os.path.exists(output_file) or not os.path.exists(os.path.dirname(os.path.abspath(output_file)))):
        print(f"Error: an output file with path '{output_file}' already exists!")
        exit(2)

    if (not args.postagger in set([ "italian", "english", "russian" ])):
        print(f"Error: '{args.postagger}' is not a supported language to validate against!")
        exit(2)

    return output_file

def load_pos_tagger(language):
    """
    Loads the language specific postagger.
    """
    tagger = None
    match language:
        case "italian":
            tagger = POSTagger(language=Language.IT, method=TAGMethod.STANZA)
        case "english":
            tagger = POSTagger(language=Language.EN, method=TAGMethod.STANZA)
        case "russian":
            tagger = POSTagger(language=Language.RU, method=TAGMethod.SPACY)
        case _:
            return None

    return tagger

def load_evaluator(language, check_syntax):
    """
    loads the language specific evaluation parser.
    """
    evaluator = None
    match language:
        case "italian":
            evaluator = lambda x: parse_italian_analysis(x, check_syntax)
        case "english":
            evaluator = lambda x: parse_english_analysis(x, check_syntax)
        case "russian":
            evaluator = None # to implement
        case _:
            return None

    return evaluator

def setup_llm():
    model = "gpt-4o-2024-11-20"
    temperature = 0
    top_p = 0.95

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        top_p=top_p
    )

def analyze_text(
    text: str,
    tasks: dict,
    llm: ChatOpenAI,
    message_parser: Callable[..., dict],
    tagger: POSTagger,
    analyze_syntax: bool):
    """Analyze a single text chunk
    
    Arguments:
        text (str): the input text to analyze
        tasks (dict): a dict defining analysis subtasks
        llm (ChatOpenAI): the langchain LLM instance
        message_parser (Callable[..., dict]): AIMessage output parser, should return a dict
        tagger (POSTagger): the postagger to use
        analyze_syntax (bool): set to False to skip syntax analysis tasks
    """

    analysis_report = {}
    consumed_tokens = 0
    analysis_warnings = []

    # we drop tasks keys if syntax needs to be skipped
    if not analyze_syntax:
        if 'syntax' in tasks: del tasks['syntax']

    # tag the input text
    tagged_text = tagger.tag_text(text)

    with get_openai_callback() as cb:
        for superkey in tasks.keys():
            for key, value in tasks[superkey].items():

                # extract data
                task_prompt = value["prompt"]
                task_schema = value["schema"]
                task_shots = value["shots"]

                # here we reformat optional shots
                shots = list(map(lambda x: (x["role"], x["content"]), task_shots)) if len(task_shots) != 0 else []

                prompt = ChatPromptTemplate.from_messages(
                    [
                        MessagesPlaceholder("shots", optional=True),
                        ("user", task_prompt)
                    ]
                )
                chain = prompt | llm | message_parser

                results = chain.invoke(
                    input={
                        "shots": shots,
                        "input": json.dumps(tagged_text, ensure_ascii=False),
                        "schema": json.dumps(task_schema, indent=4, ensure_ascii=False)
                    }
                )

                # validate output using schema supplied
                try:
                    validate(instance=results, schema=task_schema)
                    analysis_report[key] = results
                except:
                    analysis_report[key] = []
                    analysis_warnings.append(f"Warning! Got an invalid output when processing '{key}' analysis task!")
        
        consumed_tokens = cb.total_tokens

    return analysis_report, consumed_tokens, analysis_warnings, tagged_text

def add_dictlist_to_dataframe(dictlist, df):
    """
    Takes an existing Pandas DataFrame and a list
    of dict (with same structure and only 1 level).

    Adds each dict property to a new column.
    """
    output_keys = list(dictlist[0].keys())
    output_structure = { key: [] for key in output_keys }

    for elem in dictlist:
        for selection_key in output_keys:
            output_structure[selection_key].append(elem[selection_key])

    for key, value in output_structure.items():
        df.insert(len(df.columns), key, value)


def main():
    # Parse and validate arguments
    args = parser.parse_args()
    output_file = validate_args(args)

    # Load data
    with open(args.tasks, "r", encoding="utf-8") as tasks_in:
        tasks = json.load(tasks_in)

    df = pd.read_csv(args.input, sep="\t", encoding="utf-8", header=0)
    if args.label not in df:
        print(f"Error: no column named '{args.label}' exists in '{args.input}'!")
        exit(2)

    # now we drop unneded columns and rename
    df = df[[args.label]]
    df.rename(columns={args.label :'texts'}, inplace=True)
    
    # Setup processing pipeline
    tagger = load_pos_tagger(args.postagger)
    evaluator = load_evaluator(args.postagger, args.syntax)
    llm = setup_llm()

    # setup chain
    json_parser = JsonOutputParser()

    # analyze data
    pos_tags = []
    analysis_data = []
    tokens = []
    warnings = []

    # --- Step 1 - Analyze
    for input_text in df['texts']:
        report, token_usage, warning_messages, tags = analyze_text(input_text, tasks, llm, json_parser, tagger, args.syntax)

        analysis_data.append(report)
        tokens.append(token_usage)
        pos_tags.append(tags)
        warnings.append(warning_messages)

    # Add results to dataframe
    df.insert(len(df.columns), "pos_tags", list(map(lambda x : json.dumps(x, ensure_ascii=False), pos_tags)))
    df.insert(len(df.columns), "analysis_data", list(map(lambda x : json.dumps(x, ensure_ascii=False), analysis_data)))
    if args.debug:
        df.insert(len(df.columns), "tokens", tokens)
        df.insert(len(df.columns), "warnings", warnings)

    # --- Step 2 - Eval
    if not args.analysis:
        eval_data = []

        for analysis_report in analysis_data:
            eval_report = evaluator(analysis_report)
            eval_data.append(eval_report)
 
        # Add results to df
        add_dictlist_to_dataframe(eval_data, df)

    # Write results
    df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")

if __name__ == "__main__":
    main()