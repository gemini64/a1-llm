import json
from utils import word_in_list
import pandas as pd

input_file = "./inventories/word_lists/kilgariff_bnc_lemmatized.tsv"
output_file = "./inventories/word_lists/kilgariff_bnc_lemmatized.json"

stopwords = "./inventories/stopwords/stopwords_en.json"

# load data
df = pd.read_csv(input_file, sep="\t", encoding="utf-8", header=0)

with open(stopwords, "r", encoding="utf-8") as f_in:
    stopwords_list = set(json.load(f_in))

# remove stopwords
stopwords_mask = df['word'].apply(lambda x: word_in_list(x, stopwords_list))
df = df[stopwords_mask]

# rename postags to match the simplified postags
df['pos'] = df['pos'].replace({'adv': 'r'})

tags = ['n', 'v', 'a', 'r']
output_data = {}

# add named entries
for tag in tags:
    elems = df[df['pos'] == tag]['word'].to_list()
    output_data[tag] = elems

with open(output_file, "w", encoding="utf-8") as f_out:
    json.dump(output_data, f_out, ensure_ascii=False, indent=4)