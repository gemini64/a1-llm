import json
from mappings import upos_to_simple
from utils import word_in_list
from pos_tagger import Language, TAGMethod, POSTagger
import pandas as pd

input_file = "./inventories/word_lists/ngsl_lemmatized.tsv"
output_file = "./inventories/word_lists/ngsl_lemmatized.json"

stopwords = "./inventories/stopwords/stopwords_en.json"

tagger = POSTagger(Language.EN, TAGMethod.STANZA, include_lemma=True)

# pos to simple pos, word by word
def simpletag_word(input: str) -> str:
    tag = tagger.tag_text(input)[0]["pos"]
    return upos_to_simple[tag]

# load data
df = pd.read_csv(input_file, sep="\t", encoding="utf-8", header=0)

with open(stopwords, "r", encoding="utf-8") as f_in:
    stopwords_list = set(json.load(f_in))

# remove stopwords
stopwords_mask = df['word'].apply(lambda x: word_in_list(x, stopwords_list))
df = df[stopwords_mask]

# now basically we also need to add a pos cause no pos is given
df['pos'] = df['word'].map(simpletag_word)

tags = ['n','v','a','r']
output_data = {}

# add named entries
for tag in tags:
    elems = df[df['pos'] == tag]['word'].to_list()
    output_data[tag] = elems

with open(output_file, "w", encoding="utf-8") as f_out:
    json.dump(output_data, f_out, ensure_ascii=False, indent=4)