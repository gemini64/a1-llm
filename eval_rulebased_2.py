import os, argparse, json
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
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
            tagger = POSTagger(language=Language.IT, method=TAGMethod.TINT)
        case "english":
            tagger = POSTagger(language=Language.EN, method=TAGMethod.SPACY)
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
    model = "gpt-4o"
    temperature = 0
    top_p = 0.95

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        top_p=top_p
    )

def analyze_text(
    text,
    tasks,
    llm,
    message_parser,
    tagger,
    analyze_syntax):
    """Analyze a single text chunk"""
    analysis_report = {}
    consumed_tokens = 0

    # we drop tasks keys if syntax needs to be skipped
    if not analyze_syntax:
        if 'syntax' in tasks: del tasks['syntax']

    # tag the input text
    tagged_text = tagger.tag_text(text)

    with get_openai_callback() as cb:
        for superkey in tasks.keys():
            for key, value in tasks[superkey].items():
                prompt = ChatPromptTemplate.from_messages(
                    [
                        ("user", value)
                    ]
                )
                chain = prompt | llm | message_parser

                results = chain.invoke(
                    input={
                        "input": json.dumps(tagged_text)
                    }
                )

                analysis_report[key] = results
        
        consumed_tokens = cb.total_tokens

    return analysis_report, consumed_tokens

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
    analysis_data = []
    tokens = []

    # --- Step 1 - Analyze
    for input_text in df['texts']:
        report, token_usage = analyze_text(input_text, tasks, llm, json_parser, tagger, args.syntax)

        analysis_data.append(report)
        tokens.append(token_usage)

    # Add results to dataframe
    df.insert(len(df.columns), "analysis_data", list(map(lambda x : json.dumps(x, ensure_ascii=False), analysis_data)))
    if args.debug:
        df.insert(len(df.columns), "tokens", tokens)

    # --- Step 2 - Eval
    if not args.analysis:
        eval_data = []

        for analysis_report in analysis_data:
            print(analysis_report)
            eval_report = evaluator(analysis_report)
            print(eval_report)
            eval_data.append(eval_report)
 
        # Add results to df
        add_dictlist_to_dataframe(eval_data, df)

    # Write results
    df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")

if __name__ == "__main__":
    main()