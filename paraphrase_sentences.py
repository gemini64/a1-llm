import os, re, json, time, argparse, spacy
from dotenv import load_dotenv
import pandas as pd
from parsers import regex_parser, strip_string
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

# load keys from local settings file
if (os.getenv("PY_ENV") == "DEVELOPMENT"):
    load_dotenv()

# set up parser
parser = argparse.ArgumentParser(
    prog="paraphrase_sentences",
    description="Given a set of prompts/completions as input, performs a set of text transformations to make the input text conform to a given list of linguistics constraints."
)

parser.add_argument("input", help="a TSV file containing the text completions to evaluate")
parser.add_argument("-c", "--constraints", help="a plain-text file containing the linguistics constraints to evaluate against", required=True)
parser.add_argument("-l", "--language", help="language used to initialize the sentence tokenizer", type=str, required=True)
parser.add_argument('-o', '--output', help="(optional) output file")
parser.add_argument('-g', '--groq', action='store_true', help="run on groq cloud")

# validate arguments
args = parser.parse_args()

input_file = args.input
constraints_file = args.constraints
output_file = args.output if args.output != None else f"{os.path.splitext(input_file)[0]}_paraphrases_sentences.tsv"
use_groq = args.groq
language = args.language

if (not (os.path.isfile(input_file) and (os.path.splitext(input_file)[-1].lower() == ".tsv"))):
    print("Error: the input file does not exist or is not a supported format!")
    exit(2)

if (not (os.path.isfile(constraints_file))):
    print("Error: the constraints file provided does not exist!")
    exit(2)

if (os.path.exists(output_file) or not os.path.exists(os.path.dirname(os.path.abspath(output_file)))):
    print(f"Error: an output file with path '{output_file}' already exists!")
    exit(2)

if (not (language == "italian" or language == "english")):
    print(f"Error: '{language}' is not a supported sentence tokenizer language!")
    exit(2)

# load spacy and setup sentence tokenizer
spacy.prefer_gpu = True
if language == 'italian':
    nlp = spacy.load("it_core_news_lg")
else:
    nlp = spacy.load("en_core_web_trf")


# load data
constraints = ""
with open(constraints_file, "r", encoding="utf-8") as f_in:
    constraints = f_in.read()

df = pd.read_csv(input_file, sep="\t", encoding="utf-8", header=0)
completions = df["completions"]

# set up prompt
user_message = """# Task:
Check if the given sentence complies with the constraints provided; generate a paraphrase when necessary.

# Original Sentence:
{input_text}

# Constraints checking:
Check the given sentence againts ALL constraints.
- If it violates no constraint, keep it as is.
- If it violates one or more constraints, paraphrase it.

# Paraphrasing:
- A paraphrase has to preserve the original semantic meaning and minimize information loss.
- A paraphrase has to replace each non-constraints conformant element with an equivalent conformant alternative.

# Output format:
Provide a step-by-step reasoning to elaborate your answer. The expected final output consists of the transformed sentence, enclosed in <angle brackets>.

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

if use_groq:
    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL"),
        temperature=temperature,
        model_kwargs={
            "top_p": top_p
        }
    )
else:
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        top_p=top_p
    )

# set up chain
pattern = "<([^>]+)>"
parser = regex_parser(regex=pattern)

chain = prompt_template | llm | parser

paraphrases = []
iterations = []

# iterate over texts
for completion in completions:
    # split sentences
    documents = nlp(completion)
    sentences = [sent.text for sent in documents.sents]

    iter_counter = 0
    output_text = []

    for sentence in sentences:
        current = strip_string(sentence)
        iteration = None

        # paraphrase until LLM output is unchanged
        # or max iterations number is reached
        for i in range(1,max_iterations):
            iteration = i

            # invoke model
            results = chain.invoke(
                input={
                    "input_text": current,
                    "constraints": constraints
                }
            )

            # this is just a test to see if we can reduce iterations
            results = strip_string(results)

            # print("---")
            # print(f"original: '{current}'")
            # print(f"paraph: '{results}'")

            # keep within token limits if we are using groq
            if use_groq:
                time.sleep(30)

            # check if output text is unchanged
            if (results is None or results == current):
                current = "Error! regex did not match" if results is None else current
                break
            else:
                current = results

        # update results
        output_text.append(current)
        iter_counter += iteration


    # push data for insertion
    paraphrases.append(" ".join(output_text))
    iterations.append(iter_counter)

# add data columns to original df
df.insert(len(df.columns), "paraphrases", paraphrases)
df.insert(len(df.columns), "iterations", iterations)

# and finally write out our results
df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")