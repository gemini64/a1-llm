import nltk, json
from nltk.corpus import stopwords

###
# An Utility script that fetches common stopwords
# for a given language (Uses NLTK)
#
#   output -> a JSON string array
###

output_dir = "./inventories/stopwords"
languages = ["italian", "english", "russian"]

output_file = """stopwords_{lang}.json"""

# download corpus
nltk.download('stopwords')

for language in languages:
    content = stopwords.words(language)
    outfile = output_dir + "/" + output_file.format(lang=language)

    with open(outfile, "w", encoding="utf-8") as f_out:
        json.dump(content, f_out, ensure_ascii=False, indent=4)