import json
from utils import word_in_list
from mappings import upos_to_simple
from pos_tagger import Language, TAGMethod, POSTagger

input_file = "./inventories/word_lists/cefr_wordlist_en.json"
output_file = "./inventories/word_lists/cefr_wordlist_lemmatized_en.json"

stopwords = "./inventories/stopwords/stopwords_en.json"
language = Language.EN

# read files
with open(input_file, 'r', encoding='utf-8') as f_in:
    wordlist = json.load(f_in)

with open(stopwords, 'r', encoding='utf-8') as s_in:
    stopwords_list = json.load(s_in)

# lemmatize
tagger = POSTagger(language=language, method=TAGMethod.STANZA, include_lemma=True)

# pos to simple pos, word by word
def lemmatize_word(input: str) -> str:
    lemma = tagger.tag_text(input)[0]["lemma"]
    return lemma

def simpletag_word(input: str) -> str:
    tag = tagger.tag_text(input)[0]["pos"]
    return upos_to_simple[tag]

lemmas = list(map(lambda x : lemmatize_word(x), wordlist))

# remove duplicates
lemmas = list(set(lemmas))
lemmas = list(filter(lambda x: word_in_list(x, stopwords_list), lemmas))

# setup output
tags = ['n','v','a','r'] 
output_data = { x: [] for x in tags }

for lemma in lemmas:
    tag = simpletag_word(lemma)
    match tag:
        case 'n'|'v'|'a'|'r':
            output_data[tag].append(lemma)
        case _:
            pass

# output data
with open(output_file, 'w', encoding='utf-8') as f_out:
    json.dump(output_data, f_out, ensure_ascii=False, indent=4)