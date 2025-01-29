import os, re, json, time, argparse, spacy
from dotenv import load_dotenv
import pandas as pd
from agent_tools import regex_message_parser, strip_string, ANGLE_REGEX_PATTERN, token_usage_message_parser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

# load keys from local settings file
if (os.getenv("PY_ENV") == "DEVELOPMENT"):
    load_dotenv()

# set up parser
parser = argparse.ArgumentParser(
    prog="paraphrase_sentences",
    description="Given a list of texts as input, performs a set of text transformations to make the input text conform to a given list of linguistics constraints."
)

parser.add_argument("input", help="a TSV file containing the texts to paraphrase")
parser.add_argument("-c", "--constraints", help="a plain-text file containing the linguistics constraints to paraphrase against", required=True)
parser.add_argument("-s", "--sentencizer", help="the language used to initialize the sentencizer", type=str, required=True)
parser.add_argument("-l", "--label", help="(optional) the label of the column that contains input data", default="completions")
parser.add_argument('-d', '--debug', action='store_true', help="(optional) log additional information")
parser.add_argument('-o', '--output', help="(optional) output file")
parser.add_argument('-g', '--groq', action='store_true', help="(optional) run on groq cloud")

# validate arguments
args = parser.parse_args()

input_file = args.input
constraints_file = args.constraints
output_file = args.output if args.output != None else f"{os.path.splitext(input_file)[0]}_paraphrases_sentences.tsv"
use_groq = args.groq
language = args.sentencizer
log_debug_data = args.debug
column_label = args.label

if (not (os.path.isfile(input_file) and (os.path.splitext(input_file)[-1].lower() == ".tsv"))):
    print("Error: the input file does not exist or is not a supported format!")
    exit(2)

if (not (os.path.isfile(constraints_file))):
    print("Error: the constraints file provided does not exist!")
    exit(2)

if (os.path.exists(output_file) or not os.path.exists(os.path.dirname(os.path.abspath(output_file)))):
    print(f"Error: an output file with path '{output_file}' already exists!")
    exit(2)

if (not (language in set(['italian', 'english', 'russian']))):
    print(f"Error: '{language}' is not a supported sentencizer language!")
    exit(2)

# load spacy and setup sentence tokenizer
spacy.prefer_gpu = True
match language:
    case 'italian':
        nlp = spacy.load("it_core_news_lg")
    case 'english':
        nlp = spacy.load("en_core_web_trf")
    case _:
        nlp = spacy.load("ru_core_news_lg")


# load data
constraints = ""
with open(constraints_file, "r", encoding="utf-8") as f_in:
    constraints = f_in.read()

df = pd.read_csv(input_file, sep="\t", encoding="utf-8", header=0)

# check if submitted label exists
if column_label not in df:
    print(f"Error: no column named '{column_label}' exists in '{input_file}'!")
    exit(2)

# now we drop unneded columns and rename
df = df[[column_label]]
df.rename(columns={column_label :'texts'}, inplace=True)

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
- If a paraphrase that preserves the original meaning and completely conforms to the given constraints cannot be formulated, then the non conformant text should be removed.

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
max_iterations = 10 # upper bound to paraphrase iterations

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
message_parser = regex_message_parser(regex=ANGLE_REGEX_PATTERN)
token_parser = token_usage_message_parser

chain = prompt_template | llm

paraphrases = []
tokens = []
iterations = []
messages = []

# iterate over texts
input_texts = df["texts"]
for input_text in input_texts:
    # split sentences
    documents = nlp(input_text)
    sentences = [strip_string(sent.text) for sent in documents.sents]

    session_text = []
    session_messages = []
    session_iterations = []
    session_tokens = 0
    

    for sentence in sentences:
        current = sentence
        sent_iter = None
        sent_messages = []

        # paraphrase until LLM output is unchanged
        # or max iterations number is reached
        for i in range(1,max_iterations):
            sent_iter = i

            # push user message to session log
            sent_messages.append(
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
            sent_messages.append(
                {
                    "role": "assistant",
                    "content": results.content
                }
            )

            # extract response and update token usage data
            model_output = message_parser(results)
            session_tokens += token_parser(results)
            
            # sanitize output to avoid 
            model_output = strip_string(model_output) if model_output is not None else model_output

            # keep within token limits if we are using groq
            if use_groq:
                time.sleep(30)

            # check if output text is unchanged
            if (model_output is None or model_output == current):
                current = "ERROR" if model_output is None else current
                break
            else:
                current = model_output

        # update results
        session_text.append(current)
        session_iterations.append(sent_iter)
        session_messages.append(sent_messages)


    # push data for insertion
    paraphrases.append(" ".join(session_text) if "ERROR" not in session_text else "ERROR")
    iterations.append(session_iterations)
    tokens.append(session_tokens)
    messages.append(session_messages)

# add data columns to original df
df.insert(len(df.columns), "paraphrases", paraphrases)

# log additional debug data
if (log_debug_data):
    df.insert(len(df.columns), "iterations", list(map(lambda x: json.dumps(x, ensure_ascii=False), iterations)))
    df.insert(len(df.columns), "total_iterations", list(map(lambda x: sum(x), iterations)))
    df.insert(len(df.columns), "tokens", tokens)
    df.insert(len(df.columns), "messages", list(map(lambda x: json.dumps(x, ensure_ascii=False), messages)))

# and finally write out our results
df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")