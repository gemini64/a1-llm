import os, json
from pos_tagger import POSTagger, Language, TAGMethod

###
# An utility script to test available POS tagging methods.
#
# input_file -> a JSON string list containing text to tag
# output_file -> a JSON file containing the tagged text
#
# Note: remember to specify a language (italian, russian, english).
###

# --- params
input_file = "./input.json" # a json list of strings to process
output_file = "./output.json" # output
include_lemma = True

tagger_language = "italian" # one of: ["italian", "russian", "english"]

# --- load data
texts = []

with open(input_file, encoding="utf-8", mode="r") as f_in:
    texts = json.load(f_in)

# --- process
tagger = None
match tagger_language:
    case "italian":
        tagger = POSTagger(language=Language.IT, method=TAGMethod.STANZA, include_lemma=include_lemma)
    
    case "english":
        tagger = POSTagger(language=Language.EN, method=TAGMethod.STANZA, include_lemma=include_lemma)

    case "russian":
        tagger = POSTagger(language=Language.RU, method=TAGMethod.SPACY, include_lemma=include_lemma)

    case _:
        print(f"Error! '{tagger_language}' is not a supported POSTagger language!")
        exit(2)

outputs = []

for text in texts:
    outputs.append(tagger.tag_text(text))


results = {str(i): value for i, value in enumerate(outputs)}

# --- write out data
with open(output_file, mode="w", encoding="utf-8") as f_out:
    json.dump(results, f_out,ensure_ascii=False, indent=4)