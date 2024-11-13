import argparse, os, json, math, time
import pandas as pd
from dotenv import load_dotenv
from lorax import Client
from groq import Groq
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# load local env secrets
if (os.getenv("PY_ENV") == "DEVELOPMENT"):
    load_dotenv()

# setup command line arguments
parser = argparse.ArgumentParser(
    prog='infer',
    description='Forwards a list of user prompts to a openai/lorax-hosted LLM')

# add args
parser.add_argument('input', help="an input json file")
parser.add_argument('-l', '--lorax', action='store_true')
parser.add_argument('-g', '--groq', action='store_true')
parser.add_argument('-o', '--output', help="(optional) output file")
parser.add_argument('-s', '--samples', help="(optional) the number of samples to collect [0-100]", type=int, default=100)

# validate args
args = parser.parse_args()

input_file = args.input
use_lorax = args.lorax
use_groq = args.groq
output_file = args.output if args.output != None else f"{os.path.splitext(input_file)[0]}_output.tsv"
samples = max(0, min(args.samples, 100))

if (not (os.path.isfile(input_file) and (os.path.splitext(input_file)[-1].lower() == ".json"))):
    print("Error: the input file does not exist or is not a supported format!")
    exit(2)

if (os.path.exists(output_file) or not os.path.exists(os.path.dirname(os.path.abspath(output_file)))):
    print(f"Error: an output file with path '{output_file}' already exists!")
    exit(2)

if (use_groq and use_lorax):
    print("Error: the program was called using both -l and -g flags. Note that lorax and groq options are mutually exlusive!")
    exit(2)

# read data
data = ""
with open(input_file, "r", encoding="utf-8") as f_in:
    data = json.load(f_in)

# map samples to tasks
tasks = len(data.keys())
samples_per_task = math.floor(samples/tasks)
samples_remainder = max(0, samples - (samples_per_task * tasks))

prompts = []

# select prompts
for key in data.keys():

    if key == list(data.keys())[0]:
        prompts = prompts + (data[key][:(samples_per_task+samples_remainder)])
        continue

    prompts = prompts + (data[key][:samples_per_task])

# initialize dataframe
df = pd.DataFrame(data={"prompts": prompts})

# model params
temperature = 0.0
top_p = 0.95

# init llm - lorax
lorax_endpoint = os.getenv("LORAX_ENDPOINT")
lorax_client = Client(base_url=lorax_endpoint)

# init llm - groq
groq_key = os.getenv("GROQ_API_KEY")
groq_model = os.getenv("GROQ_MODEL")

groq_client = client = Groq(
    api_key=groq_key
)

# init llm - openai
model = "gpt-4o"
llm = ChatOpenAI(
    model=model,
    temperature=temperature,
    top_p=top_p,
)

prompt_template = ChatPromptTemplate.from_messages(
    [
        ("user", "{user_input}")
    ]
)
chain = prompt_template | llm | (lambda x: x.content)

# invoke model
completions = []
counter = 0

for prompt in df["prompts"]:
    counter += 1
    print(f"[SAMPLE {counter}/{len(df['prompts'])}]")

    response = ""

    if (use_lorax):
        try:
            response = lorax_client.generate(prompt=prompt, temperature=temperature, top_p=top_p).generated_text
        except Exception as exc:
            print(f"Error: Something went wrong while connecting to lorax server\n\nException: {exc}")
            exit(2)
    elif (use_groq):
        completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=temperature,
            top_p=top_p,
            model=groq_model)
        response = completion.choices[0].message.content
        
        # this is to keep the requests within the free tier token limits
        time.sleep(5)
    else:
        response = chain.invoke(input={
            "user_input": prompt
        })

    completions.append(response)

# add to df
df.insert(len(df.columns), "completions", completions)

# dump to file
df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")