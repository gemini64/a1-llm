import os, argparse, json
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pos_tagger import POSTagger, Language, TAGMethod
from parsers import parse_italian_analysis, parse_english_analysis

# load secrets
if(os.getenv("PY_ENV") == "DEVELOPMENT"):
    load_dotenv()

# setup argparse
parser = argparse.ArgumentParser(
    prog='eval_rulebased_it',
    description='performs a series of analysis and evaluation tasks on (italian/english) text using an oai LLM')

parser.add_argument("input", help="a TSV file containing the text completions to evaluate")
parser.add_argument("tasks", help="a JSON file containing analysis tasks to perform")
parser.add_argument("-l", "--language", help="the language to validate constraints against", required=True)
parser.add_argument('-a', '--analysis', help="(optional) skip evaluation, perform analysis only", action='store_true')
parser.add_argument('-o', '--output', help="(optional) output file")

# validate arguments
args = parser.parse_args()

input_file = args.input
tasks_file = args.tasks
analysis_only = args.analysis
input_language = args.language
output_file = args.output if args.output != None else (f"{os.path.splitext(input_file)[0]}_analysis.tsv" if analysis_only else f"{os.path.splitext(input_file)[0]}_eval.tsv")

if (not (os.path.isfile(input_file) and (os.path.splitext(input_file)[-1].lower() == ".tsv"))):
    print("Error: the input file does not exist or is not a supported format!")
    exit(2)

if (not (os.path.isfile(tasks_file) and (os.path.splitext(tasks_file)[-1].lower() == ".json"))):
    print("Error: the tasks file does not exist or is not a supported format!")
    exit(2)

if (os.path.exists(output_file) or not os.path.exists(os.path.dirname(os.path.abspath(output_file)))):
    print(f"Error: an output file with path '{output_file}' already exists!")
    exit(2)

if (not input_language in set(["italian", "english"])):
    print(f"Error: '{input_language}' is not a supported language to validate against!")
    exit(2)

completions = None
tasks = None

with open(tasks_file, "r", encoding="utf-8") as tasks_in:
    tasks = json.load(tasks_in)

df = pd.read_csv(input_file, sep="\t", encoding="utf-8", header=0)
completions = df["completions"]

# set up model
model = "gpt-4o"
temperature = 0
top_p = 0.95

llm = ChatOpenAI(
    model=model,
    temperature=temperature,
    top_p=top_p
)

# set up pos tagger
match input_language:
    case "italian":
        tagger = POSTagger(language=Language.IT, method=TAGMethod.TINT)
    case _:
        tagger = POSTagger(language=Language.EN, method=TAGMethod.SPACY)

# analyze data
analysis_data = []
for text in completions:
    report = {}
    tagged_text = tagger.tag_text(text)

    # run grammar tasks
    for key, value in tasks["grammar"].items():
        prompt = ChatPromptTemplate.from_messages(
            [
                ("user", value)
            ]
        )
        chain = prompt | llm | JsonOutputParser()

        results = chain.invoke(
            input={
                "input": json.dumps(tagged_text)
            }
        )

        report[key] = results
    
    # run syntax tasks
    for key, value in tasks["syntax"].items():
        prompt = ChatPromptTemplate.from_messages(
            [
                ("user", value)
            ]
        )
        chain = prompt | llm | JsonOutputParser()

        results = chain.invoke(
            input={
                "input": text
            }
        )

        report[key] = results
    
    analysis_data.append(report)

# add analysis data to dataframe
df.insert(len(df.columns), "analysis_data", list(map(lambda x : json.dumps(x, ensure_ascii=False), analysis_data)))

# exit if only analysis is required
if analysis_only:
    df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")
    exit(0)

# Step 2 - Rule-based evaluation
eval_data = []
for elem in analysis_data:
    
    match input_language:
        case "italian":
            results = parse_italian_analysis(elem)
        case _:
            results = parse_english_analysis(elem)

    eval_data.append(results)

# now, we select all keys and set everyting for data insertion
output_keys = list(eval_data[0].keys())
output_structure = { key: [] for key in output_keys }

for elem in eval_data:
    for selection_key in output_keys:
        output_structure[selection_key].append(elem[selection_key])

for key, value in output_structure.items():
    df.insert(len(df.columns), key, value)

# write out
df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")