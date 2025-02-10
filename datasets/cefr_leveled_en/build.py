import os, spacy
import pandas as pd

###
# Extracts data from the cefr leveled english dataset
# (Optionally) applies selection filters to retrieved data
#
# Data is hosted on Kaggle:
#     https://www.kaggle.com/datasets/amontgomerie/cefr-levelled-english-texts
#
# Used export is:
#     - raw dataset ('cefr_leveled_texts.csv')
###

def truncate(input: str, min_words: int, max_words: int) -> str:
    """Given an arbitrarily long text, truncates
    it to the last sentence that matches or exceeds the
    minimum word count."""
    if (len(input.split()) <= max_words):
        return input

    words = 0
    nlp = spacy.load("en_core_web_trf") # we also expect english text

    # split into paragraphs
    # Note: we expect that paragraphs are separated by newlines
    pars = input.split("\n")
    results = []

    for par in pars:

        # exit if min_words is reached
        if (words >= min_words):
            break

        par_w = len(par.split())
        
        if (words + par_w < min_words):
            results.append(par)
            words += par_w
        else:
            par_r = []
            sentences = [x for x in nlp(par).sents]

            for sent in sentences:

                text = sent.text
                sent_w = len(text.split())

                if (words < min_words):
                    par_r.append(text)
                    words += sent_w
                else:
                    break

            results.append(" ".join(par_r))

    print("splitted")
    return "\n".join(results)

# --- flags
output_file = "./output.tsv"

remove_duplicates = True # removes any 1:1 duplicates (must be exactly the same)
select_by_wordcount = False # select only sentences within a specified word range
truncate_sentences = True # cut texts if they exceed the maximum word count
take_samples = True

min_words = 40
max_words = 55

samples_split = {
    "A1": 20,
    "A2": 20,
    "B1": 20, 
    "B2": 20,
    "C1": 20,
    "C2": 20
}

# --- input files
input_file = "./cefr_leveled_texts.csv"

df = pd.read_csv(input_file, encoding="utf-8", header=0, sep=",")

# --- add wordcount
df["words"] = df["text"].map(lambda x : len(x.split()))

# --- apply filters
if (remove_duplicates):
    df.drop_duplicates(subset=['text'], keep='first')

if (select_by_wordcount):
    df = df[df["words"].between(min_words, max_words, inclusive='both')]

if (take_samples):
    for key in samples_split.keys():
        n_samples = samples_split[key]
        rows = df[df["label"] == key]
        n_samples = min(rows.index.size, samples_split[key])
        rows = rows.sample(n=n_samples)

        df = df[df["label"] != key]
        frames = [rows, df]
        df = pd.concat(frames)

if truncate_sentences:
    df['text'] = df['text'].map(lambda x: truncate(x, min_words, max_words))
    # recalculate word counts
    df["words"] = df["text"].map(lambda x : len(x.split()))

# --- output data
df.to_csv(output_file, sep="\t", encoding="utf-8", index=False)