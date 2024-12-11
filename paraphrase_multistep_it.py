import os, json, argparse
from dotenv import load_dotenv
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agent_tools import json_message_parser, check_irregular_it_verbs

if (os.getenv("PY_ENV") ==  "DEVELOPMENT"):
    load_dotenv()

# --- argument parser
# set up parser
parser = argparse.ArgumentParser(
    prog="paraphrase_multistep_it",
    description="Given a set of prompts/completions as input, performs a set of text transformations to make the input text conform to a given list of linguistics constraints."
)

parser.add_argument("input", help="a TSV file containing the text completions to evaluate")
parser.add_argument('-o', '--output', help="(optional) output file")

# validate arguments
# --- Note that only a minimum path validation is performed
args = parser.parse_args()

input_file = args.input
output_file = args.output if args.output != None else f"{os.path.splitext(input_file)[0]}_paraphrases_multistep_it.tsv"

if (not (os.path.isfile(input_file) and (os.path.splitext(input_file)[-1].lower() == ".tsv"))):
    print("Error: the input file does not exist or is not a supported format!")
    exit(2)

if (os.path.exists(output_file) or not os.path.exists(os.path.dirname(os.path.abspath(output_file)))):
    print(f"Error: an output file with path '{output_file}' already exists!")
    exit(2)

# --- load data
df = pd.read_csv(input_file, sep="\t", encoding="utf-8", header=0)

max_iterations = 10
constraints_file = "./inventories/constraints_italian.md"
constraints_noverbs_file = "./inventories/constraints_italian_noverbs.md"

with open(constraints_file, "r", encoding='utf-8') as f_in:
    constraints = f_in.read()

with open(constraints_noverbs_file, "r", encoding='utf-8') as f_in:
    constraints_noverbs = f_in.read()

model = "gpt-4o"
temperature = 0
top_p = 0.95

llm = ChatOpenAI(
    model=model,
    temperature=temperature,
    top_p=top_p
)

control_prompt = """# Task:
Check if the given text complies with the constraints provided.

# Original Text:
{input_text}

# Constraints checking:
Check each sentence againts ALL constraints given.
- If it violates no constraint, continue.
- If it violates one or more constraints, report it in your final response.

# Constraints:
{constraints}

# Output format:
Provide a step-by-step reasoning to elaborate your answer. The expected final answer consists of a sentence-wise report of found errors in constraint adherence. Follow the JSON schema provided to formulate your answer:

```json
{{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/report.json",
    "title": "Constraints validation report",
    "description": "A linguistics constraints text validation report.",
    "type": "array",
    "items": {{
        "type": "object",
        "description": "A sentence-level report.",
        "properties": {{
            "content": {{
                "type": "string",
                "description": "The full raw-text of the sentence analyzed."
            }},
            "errors": {{
                "type": "array",
                "description": "A list of detected errors in constraints compliance.",
                "items": {{
                    "type": "string",
                    "description": "A brief description of the error detected."
                }}
            }}
        }},
        "required": [ "content", "errors" ]
    }}
}}
```"""

correction_prompt = """# Task:
Reference the linguistics constraints provided to paraphrase the given sentences in a way that solves all issues detected.

# Input data:
```json
{input_text}
```

# Paraphrasing:
Each sentence is associated with a constraints compliance error list.
- If the error list is empty, keep the sentence as is.
- If one or more errors are present, generate a paraphrase.

# How to paraphrase:
- A paraphrase has to preserve the original semantic meaning and minimize information loss.
- A paraphrase has to replace each non-constraints conformant element with an equivalent conformant alternative.
- If a paraphrase that preserves the original meaning and completely conforms to the given constraints cannot be formulated, then the original text should be removed.

# Constraints:
{constraints}

# Output format:
Provide a step-by-step reasoning to elaborate your answer. The expected final answer is the list of sentences, transformed to solve the issues detected in constraints compliance. Follow the JSON schema provided to formulate your answer:

```json
{{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/paraphrases.json",
    "title": "Paraphrases",
    "description": "A list of sentence paraphrases.",
    "type": "array",
    "items": {{
        "type": "object",
        "description": "A sentence paraphrase.",
        "properties": {{
            "original": {{
                "type": "string",
                "description": "The full raw-text of the original sentence."
            }},
            "paraphrase": {{
                "type": "string",
                "description": "The sentence paraphrase."
            }}
        }},
        "required": [ "original", "paraphrase" ]
    }}
}}
```"""

control_template = ChatPromptTemplate.from_messages(
    [
        ("user", control_prompt)
    ]
)

correction_template = ChatPromptTemplate.from_messages(
    [
        ("user", correction_prompt)
    ]
)

control_chain = control_template | llm | json_message_parser
correction_chain = correction_template | llm | json_message_parser

# --- fetch completions from input data
completions = df["completions"]
paraphrases = []
iterations = []

# iterate
for completion in completions:
    
    counter = 0
    text = completion

    for i in range (1, max_iterations):
        counter = i
        control_results = control_chain.invoke(
            input={
                "input_text": text,
                "constraints": constraints_noverbs
            }
        )

        # add irregular verbs
        control_results = check_irregular_it_verbs(control_results)

        # check if any error has been reported
        errors = [ x["errors"] for x in control_results]
        if (all(list(map(lambda x: x == [], errors)))):
            break

        else:
            correction_results = correction_chain.invoke(
                input={
                    "input_text": json.dumps(control_results),
                    "constraints": constraints
                }
            )

            # update text
            text = " ".join([ x["paraphrase"] for x in correction_results])
    
    # push data
    paraphrases.append(text)
    iterations.append(counter)

# --- Output data
df.insert(len(df.columns), "paraphrases", paraphrases)
df.insert(len(df.columns), "iterations", iterations)

# and finally write out our results
df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")