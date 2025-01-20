import os, re
import pandas as pd

###
# Extracts data from tatoeba italian sentences datasets
# with (optional) selection filters
#
# See the following link:
#     https://tatoeba.org/en/downloads
#
# Used export are:
#     - Detailed Sentences
#     - User skill level per language
###

# --- flags
output_file = "output.tsv"

only_mothertongue = True # selects only sentences uploaded by italian mothertongue users
remove_duplicates = True # removes any 1:1 duplicates
select_by_wordcount = True # select only sentences within a specified word range

min_words = 40
max_words = 55

# --- input files
sentences = "./sentences_detailed.tsv"
users = "./users.tsv"

# headers
hd_sentences = [ "id", "lang", "text", "username", "date_added", "date_modified" ]
hd_users = [ "lang", "skill_level", "username", "details" ]

df_sentences = pd.read_csv(sentences, sep="\t", encoding="utf-8", names=hd_sentences, header=0)
df_users = pd.read_csv(users, sep="\t", encoding="utf-8", names=hd_users, header=0)

# join on username
df_users_ita = df_users[df_users["lang"] == "ita"]
df_users_ita = df_users_ita.drop(columns="lang")
df_join = df_sentences.merge(df_users_ita, on='username', how='left')

# add a wordcount column
words = [ len(re.findall(r'\w+', x)) for x in df_join["text"] ]
df_join.insert(len(df_join.columns), "words", words)

# now we filter out data
if (remove_duplicates):
    df_join.drop_duplicates(subset=['text'], keep='first')

if (only_mothertongue):
    df_join = df_join[df_join["skill_level"] == '5']

# and select by word count
if (select_by_wordcount):
    df_join = df_join[ df_join["words"].between(min_words, max_words, inclusive='both')]

# --- write out data
out_colums = [ "text", "words", "username", "skill_level"]
df_join[out_colums].to_csv(output_file ,encoding="utf-8", sep="\t", index=False)