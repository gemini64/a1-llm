import json
import stopwordsiso as stopwords

###
# An Utility script that fetches common language
# stopwords.
#
# Uses this python module:
#   https://github.com/stopwords-iso/stopwords-iso
#
# output -> a JSON word list
###

output_dir = "./inventories/stopwords"
languages = ["it", "en", "ru"]

output_file = """stopwords_{lang}.json"""

for language in languages:
    print(language)
    content = list(stopwords.stopwords(language))

    outfile = output_dir + "/" + output_file.format(lang=language)

    with open(outfile, "w", encoding="utf-8") as f_out:
        json.dump(content, f_out, ensure_ascii=False)