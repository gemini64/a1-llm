import os, json
from pos_tagger import POSTagger, Language, TAGMethod

# --- params
input_file = "./input.json" # a json list of strings to process
output_file = "./output.json" # output

tagger_language = "italian" # one of: ["italian", "russian", "english"]

# --- load data
texts = []

with open(input_file, encoding="utf-8", mode="r") as f_in:
    texts = json.load(f_in)

# --- process
tagger = None

match tagger_language:
    case "italian":
        tagger = POSTagger(language=Language.IT, method=TAGMethod.TINT)
    
    case "english":
        tagger = POSTagger(language=Language.EN, method=TAGMethod.SPACY)

    case "russian":
        tagger = POSTagger(language=Language.RU, method=TAGMethod.SPACY)

    case _:
        print(f"Error! '{tagger_language}' is not a supported POSTagger language!")
        exit(2)

outputs = []

for text in texts:
    outputs.append(tagger.tag_text(text))


results = {str(i): value for i, value in enumerate(outputs)}

# --- write out data
with open(output_file, mode="w", encoding="utf-8") as f_out:
    json.dump(results, f_out,ensure_ascii=False)