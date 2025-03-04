import os, re
import pandas as pd

###
# Input data is available here:
#     https://tatoeba.org/en/downloads
#
# Used exports are:
#     - Detailed Sentences [ITA] (sentences_detailed.tsv)
#     - User skill level per language (users.tsv)
###

# --- flags
output_file = "metadata.tsv"

# --- input files
sentences = "./sentences_detailed.tsv"
users = "./users.tsv"

# headers
head_sentences = [ "id", "lang", "text", "username", "date_added", "date_modified" ]
head_users = [ "lang", "skill_level", "username", "details" ]

df_sentences = pd.read_csv(sentences, sep="\t", encoding="utf-8", names=head_sentences, header=0)
df_users = pd.read_csv(users, sep="\t", encoding="utf-8", names=head_users, header=0)

# join on username
df_users_ita = df_users[df_users["lang"] == "ita"]
df_users_ita = df_users_ita.drop(columns="lang") # this is just to avoid duplicate columns
df_join = df_sentences.merge(df_users_ita, on='username', how='left')

# remove duplicates
df_join.drop_duplicates(subset=['text'], keep='first')

# add a wordcount column
words = [ len(re.findall(r'\w+', x)) for x in df_join["text"] ]
df_join.insert(len(df_join.columns), "words", words)

# --- get words metadata
words_meta = {}

words_meta["MOTHERTONGUE"] = {
    "words_min": round(df_join[df_join["skill_level"] == '5']["words"].min()),
    "words_max": round(df_join[df_join["skill_level"] == '5']["words"].max()),
    "words_mean": round(df_join[df_join["skill_level"] == '5']["words"].mean()),
    "words_median": round(df_join[df_join["skill_level"] == '5']["words"].median()),
    "words_mode": round(df_join[df_join["skill_level"] == '5']["words"].mode()[0])
}

words_meta["ALL"] = {
    "words_min": round(df_join["words"].min()),
    "words_max": round(df_join["words"].max()),
    "words_mean": round(df_join["words"].mean()),
    "words_median": round(df_join["words"].median()),
    "words_mode": round(df_join["words"].mode()[0])
}


# --- write out data
df_out = pd.DataFrame.from_dict(data=words_meta, orient="index")
df_out.to_csv(output_file ,encoding="utf-8", sep="\t", index=True)