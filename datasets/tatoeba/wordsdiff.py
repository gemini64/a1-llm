import os, re
import pandas as pd

###
# Input data is available here:
#     https://tatoeba.org/en/downloads
#
# Used exports are:
#     - Sentence Pairs [ITA/ENG](sentence_pairs.tsv)
#     - Original and Translated Sentences (sentences_base.tsv)
###

# --- flags
output_file = "diff_stats.tsv"

# --- input files
sentence_pairs = "./sentence_pairs.tsv"
sentences_base = "./sentences_base.tsv"

# headers
head_pairs = [ "original_id", "original_text", "translated_id", "translated_text" ]
head_base = [ "sentence_id", "base_field" ]

# read the pairs file
# Read the file in chunks
chunk_size = 1000  # Adjust based on your memory constraints
chunks = []

for chunk in pd.read_csv(sentence_pairs, sep='\t', chunksize=chunk_size, on_bad_lines='warn', encoding="utf-8", names=head_pairs, header=0, dtype={"original_id": 'Int64', "original_text": 'string', "translated_id": 'Int64', "translated_text": 'string'}):
    chunks.append(chunk)

df_pairs = pd.concat(chunks, ignore_index=True)
df_pairs = df_pairs.dropna()

df_base = pd.read_csv(sentences_base, sep="\t", encoding="utf-8", names=head_base, header=0,dtype={ "sentence_id": 'Int64' })
df_base = df_base.dropna()

# --- get ids of original sentences
original_sentences = df_base[df_base["base_field"] == 0]
original_ids = original_sentences["sentence_id"].unique()

# --- add wordcounts
original_words = [ len(re.findall(r'\w+', x)) for x in df_pairs["original_text"] ]
translated_words = [ len(re.findall(r'\w+', x)) for x in df_pairs["translated_text"] ]

df_pairs.insert(len(df_pairs.columns), "original_words", original_words)
df_pairs.insert(len(df_pairs.columns), "translated_words", translated_words)

df_pairs["words_diff"] = df_pairs.apply(lambda x: x["original_words"] - x["translated_words"], axis=1)

# --- set up data to push out
words_diff = {}

words_diff["ALL"] = {
    "count": len(df_pairs),
    "diff_min": round(df_pairs["words_diff"].min()),
    "diff_max": round(df_pairs["words_diff"].max()),
    "diff_mean": round(df_pairs["words_diff"].mean()),
    "diff_median": round(df_pairs["words_diff"].median()),
    "diff_mode": round(df_pairs["words_diff"].mode()[0])
}

# --- filter out from sentence pairs the non-originals
df_pairs = df_pairs[df_pairs["original_id"].isin(original_ids)]

words_diff["ITA_ORIG"] = {
    "count": len(df_pairs),
    "diff_min": round(df_pairs["words_diff"].min()),
    "diff_max": round(df_pairs["words_diff"].max()),
    "diff_mean": round(df_pairs["words_diff"].mean()),
    "diff_median": round(df_pairs["words_diff"].median()),
    "diff_mode": round(df_pairs["words_diff"].mode()[0])
}

# --- write out data
df_out = pd.DataFrame.from_dict(data=words_diff, orient="index")
df_out.to_csv(output_file ,encoding="utf-8", sep="\t", index=True)