import json, os, argparse
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# load local settings
if (os.getenv("PY_ENV") == "DEVELOPMENT"):
    load_dotenv()

# setup argparse
parser = argparse.ArgumentParser(
    prog='eval_separate_items',
    description='Given a list of prompts/completions and a set of tests, performs an LLM-based evaluation.')

parser.add_argument("input", help="an input tsv file")
parser.add_argument("tests", help="a json file containing the evaluation tests to perform")
parser.add_argument('-o', '--output', help="(optional) output file")

# validate arguments
args = parser.parse_args()

input_file = args.input
tests_file = args.tests
output_file = args.output if args.output != None else f"{os.path.splitext(input_file)[0]}_eval_separate_items.tsv"

# validate arguments
if (not (os.path.isfile(input_file) and (os.path.splitext(input_file)[-1].lower() == ".tsv"))):
    print("Error: the input file does not exist or is not a supported format!")
    exit(2)

if ((not (tests_file is None)) and (not (os.path.isfile(tests_file) and (os.path.splitext(tests_file)[-1].lower() == ".json")))):
    print("Error: the shots file does not exist or is not a supported format!")
    exit(2)

if (os.path.exists(output_file) or not os.path.exists(os.path.dirname(os.path.abspath(output_file)))):
    print(f"Error: an output file with path '{output_file}' already exists!")
    exit(2)

# setup model
temperature = 0.0
top_p = 0.95
model = "gpt-4o"

llm = ChatOpenAI(
    model=model,
    temperature=temperature,
    top_p=top_p
)

# setup chat template
message_template = """Check wheter the following text:
```
{text}
```
{test}
Respond following the attached JSON structure:
```
{{
    "compliant": <true/false>,
}}
"""

chat_template = ChatPromptTemplate.from_messages(
    [
        ("user", message_template)
    ]
)

# setup parser and chain
parser = JsonOutputParser() | (lambda x : x["compliant"])
chain = chat_template | llm | parser

df = pd.read_csv(input_file, header=0, sep="\t", encoding="utf-8")
completions = df["completions"]

# load eval tests
eval_tests = {}

with open(tests_file, "r", encoding="utf-8") as tests_in:
    eval_tests = json.load(tests_in)

# check conditions and collect eval data
for key, value in eval_tests.items():
    eval_data = []

    for text in completions:
        result = chain.invoke(
            input={
                "test": value,
                "text": text
            }
        )

        eval_data.append(result)

    # add column
    df.insert(len(df.columns), key, eval_data)

# add logical and column
df_eval = df.iloc[:,2:]
logical_and = df_eval.all(axis=1)

df.insert(len(df.columns), "logical_and", logical_and)

# output data
df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")
