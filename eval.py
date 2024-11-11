import os, argparse
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, JsonOutputToolsParser
from pydantic import BaseModel, Field


# load env secrets
if (os.getenv("PY_ENV") == "DEVELOPMENT"):
    load_dotenv()

# setup argparse
parser = argparse.ArgumentParser(
    prog='eval',
    description='Given a list of prompts/completions, performs an LLM-based binary evaluation.')

parser.add_argument("input", help="an input tsv file")
parser.add_argument("inventory", help="a plain-text file containing the inventory to cross-check")
parser.add_argument('-o', '--output', help="(optional) output file")

# validate arguments
args = parser.parse_args()

input_file = args.input
inventory_file = args.inventory
output_file = args.output if args.output != None else f"{os.path.splitext(input_file)[0]}_eval.tsv"

if (not (os.path.isfile(input_file) and (os.path.splitext(input_file)[-1].lower() == ".tsv"))):
    print("Error: the input file does not exist or is not a supported format!")
    exit(2)

if (not (os.path.isfile(inventory_file))):
    print("Error: the inventory file does not exist!")
    exit(2)

if (os.path.exists(output_file) or not os.path.exists(os.path.dirname(os.path.abspath(output_file)))):
    print(f"Error: an output file with path '{output_file}' already exists!")
    exit(2)

# load data
df = pd.read_csv(input_file, sep="\t", header=0, encoding="utf-8")

with open(inventory_file, "r", encoding="utf-8") as inventory_in:
    inventory = inventory_in.read()

# model setup
model = "gpt-4o"
temperature = 0.0
top_p = 0.95

llm = ChatOpenAI(
    model=model,
    temperature=temperature,
    top_p=top_p
)

# prompt template setup
message_template = """Check if the following text:
```
{input_text}
```
is using exclusively the morphosintactic structures listes in the inventory attached below:
```
{inventory}
```
Respond following the attached JSON structure:
```
{{
    "compliant": <true/false>,
}}
```"""

prompt_template = ChatPromptTemplate.from_messages(
    [
        ("user", message_template)
    ]
)

# tools
class LabelTextInputs(BaseModel):
    """Inputs to the label_text tool"""
    value: bool = Field(description="True if the input text uses exlusively the morphosintactic structures listed in the inventory")

@tool("label_text", args_schema=LabelTextInputs, return_direct=False)
def label_text(value: bool) -> bool:
    """Labels the input text"""
    return value


llm_with_tools = llm.bind_tools(tools=[label_text], tool_choice="required")

# setup invokable chain
parser = JsonOutputToolsParser(first_tool_only=True) | (lambda x : x["args"]["value"])
chain = prompt_template | llm_with_tools | parser

# setup a second chain without tool calling
parser_2 = JsonOutputParser() | (lambda x : x["compliant"])
chain_2 = prompt_template | llm | parser_2

completions = df["completions"]
evaluations = []
counter = 0

for text in completions:
    counter += 1
    print(f"[SAMPLE {counter}/{len(completions)}]")

    result = chain_2.invoke(
        input={
            "input_text": text,
            "inventory": inventory
        }
    )

    evaluations.append(result)

# add row
df.insert(len(df.columns), "evaluations", evaluations)

df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")