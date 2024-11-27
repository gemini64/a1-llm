import os, re, json,argparse
from dotenv import load_dotenv
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# load keys from local settings file
if (os.getenv("PY_ENV") == "DEVELOPMENT"):
    load_dotenv()

# set up parser
parser = argparse.ArgumentParser(
    prog="paraphrase",
    description="Given a set of prompts/completions as input, performs a set of text transformations to make the input text conform to a given list of linguistics constraints."
)

parser.add_argument("input", help="a TSV file containing the text completions to evaluate")
parser.add_argument("constraints", help="a plain-text file containing the linguistics constraints to evaluate against")
parser.add_argument('-o', '--output', help="(optional) output file")

# validate arguments
args = parser.parse_args()

input_file = args.input
constraints_file = args.constraints
output_file = args.output if args.output != None else f"{os.path.splitext(input_file)[0]}_paraphrases.tsv"

if (not (os.path.isfile(input_file) and (os.path.splitext(input_file)[-1].lower() == ".tsv"))):
    print("Error: the input file does not exist or is not a supported format!")
    exit(2)

if (not (os.path.isfile(constraints_file))):
    print("Error: the constraints file provided does not exist!")
    exit(2)

if (os.path.exists(output_file) or not os.path.exists(os.path.dirname(os.path.abspath(output_file)))):
    print(f"Error: an output file with path '{output_file}' already exists!")
    exit(2)

# load data
constraints = ""
with open(constraints_file, "r", encoding="utf-8") as f_in:
    constraints = f_in.read()

df = pd.read_csv(input_file, sep="\t", encoding="utf-8", header=0)
completions = df["completions"]

# set up prompt
user_message = """# Task:
Check if the given text complies with the constraints provided; generate a paraphrase when necessary.

Provide a step-by-step reasoning to elaborate your answer. The expected final output consists of the transformed text, enclosed in square brackets.

# Original Text:
{input_text}

# Constraints checking:
Check every sentence againts ALL constraints given.
- If it violates no constraint, keep it as is.
- If it violates one or more constraints, paraphrase or remove it.

# Paraphrasing:
- A paraphrase has to preserve the original semantic meaning and minimize information loss.
- A paraphrase has to replace every non-constraints conformant element with an equivalent conformant alternative.
- If a paraphrase that preserves the original meaning and completely conforms to the given constraints cannot be formulated, then the original text should be removed.

# Constraints:
{constraints}"""

# setup chat template
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("user", user_message)
    ]
)

# set up llm
model = "gpt-4o"
temperature = 0
top_p = 0.95
max_iterations = 50 # upper bound to paraphrase iterations

llm = ChatOpenAI(
    model=model,
    temperature=temperature,
    top_p=top_p
)

# Output parser (takes an AIMessage as input)
#
# Basically extract the first element enclosed in []
# from the LLM response
parser = lambda x : (re.findall(r'\[(.*?)\]', x.content))[0]

# set up chain
chain = prompt_template | llm

paraphrases = []
iterations = []
messages = []

# iterate over texts
for completion in completions:
    current = completion
    message_session = []
    iteration = None

    # paraphrase until LLM output is unchanged
    # or max iterations number is reached
    for i in range(1,max_iterations):
        iteration = i
    
        # push user message to session log
        message_session.append(
            {
                "role": "user",
                "content": current
            }
        )

        # invoke model
        results = chain.invoke(
            input={
                "input_text": current,
                "constraints": constraints
            }
        )

        # push assistant message to session log
        message_session.append(
            {
                "role": "assistant",
                "content": results.content
            }
        )

        # parse completion and check if output text
        # is unchanged
        assistant_response = parser(results)
        if (assistant_response == current):
            break
        else:
            current = assistant_response

    # push data for insertion
    paraphrases.append(current)
    iterations.append(iteration)
    messages.append(message_session)

# add data columns to original df
df.insert(len(df.columns), "paraphrases", paraphrases)
df.insert(len(df.columns), "iterations", iterations)
df.insert(len(df.columns), "messages", list(map(lambda x: json.dumps(x, ensure_ascii=False), messages)))

# and finally write out our results
df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")