import json, os
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# load local settings
if (os.getenv("PY_ENV") == "DEVELOPMENT"):
    load_dotenv()

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
{condition}
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

# load data
input_file = "./test/italian_results.tsv"
output_file = "./test/italian_eval_separate_items.tsv"

df = pd.read_csv(input_file, header=0, sep="\t", encoding="utf-8")

completions = df["completions"]

# load eval conditions
eval_file = "./test/eval_conditions_italian.json"
eval_conditions = []

with open(eval_file, "r", encoding="utf-8") as eval_in:
    eval_conditions = json.load(eval_in)

# check conditions and collect eval data
for key, value in eval_conditions.items():
    eval_data = []

    for text in completions:
        result = chain.invoke(
            input={
                "condition": value,
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
