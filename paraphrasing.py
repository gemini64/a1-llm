import os, re, json
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

if (os.getenv("PY_ENV") == "DEVELOPMENT"):
    load_dotenv()

max_iterations = 50
output_file = "paraphrasing_transcript.json"
messages = []

input_text = "Ciao! Sono a Tokyo e mi piace molto. Ho visitato il tempio Senso-ji e ho mangiato sushi delizioso. Puoi immaginare quanto sia affascinante questa città? Spero di tornare presto. Un abbraccio!"
constraints = """- Nouns, adjectives, adverbs, prepositions, conjunctions, and interjections may be used without limitations.
- Pronouns: Only personal, possessive, demonstrative, interrogative, and indefinite pronouns are allowed.
- Numerals: Cardinal numbers may be used without limitation. Ordinal numbers must be limited to range 1-3.
- Verbs: essere, avere, volere, potere, dovere, and regular Italian verbs are allowed. Any other irregular verb is forbidden.
- Verbs may only be conjugated in active voice.
- Verbs may only be conjugated in the following moods and tenses:
    - Indicativo: presente e passato prossimo
    - Infinito: presente
    - Imperativo: presente (only 2nd singular and plural persons)
- Simple clauses may only assume declarative, volitive (using the imperative), or interrogative functions.
- Coordinate clauses may only be copulative, adversative, or declarative.
- Subordinate clauses may only assume causal, temporal, final (in implicit form), hypothetical (introduced by see), or relative functions."""

user_message = """# Task:
Check if the given text complies with the constraints provided; generate a paraphrase when necessary.

Provide a step-by-step reasoning to elaborate your answer. The expected final output consists of the input text, paraphrased if needed, enclosed in square brackets.

# Original Text:
"{input_text}"

# Constraints checking:
Check every sentence of the input text against the constraints.
- If it violates one or more constraints, paraphrase or remove it.
- If it violates no constraint, keep it as is.

# Paraphrasing:
- A paraphrase has to preserve the original meaning and tone as closely as possible.
- A paraphrase may only contain morpho-syntactical constructs that conform to the given constraints.
- A paraphrase has to replace every non-conformant morpho-syntactical structure with an equivalent constraints conformant alternative.
- If a non-conformant morpho-syntactical structure cannot be replaced with an equivalent constraints conformant alternative, it should be removed.

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

llm = ChatOpenAI(
    model=model,
    temperature=temperature,
    top_p=top_p
)

# set up parser
parser = lambda x : (re.findall(r'\[(.*?)\]', x.content))[0]

# set up chain
chain = prompt_template | llm

current = input_text
for i in range(1,max_iterations):
    
    # push user
    messages.append(
        {
            "role": "user",
            "content": current
        }
    )

    results = chain.invoke(
        input={
            "input_text": current,
            "constraints": constraints
        }
    )

    # push assistant
    messages.append(
        {
            "role": "assistant",
            "content": results.content
        }
    )

    assistant_response = parser(results)

    if (assistant_response == current):
        print(f"---\n[original]: {input_text}\n\n[results]: {assistant_response}\n---\ninfo: stopped at iteration {i}")
        break
    else:
        current = assistant_response

with open(output_file, "w", encoding="utf-8") as f_out:
    json.dump(messages, f_out, ensure_ascii=False)