import json, argparse, os
import pandas as pd
from mappings import upos_to_simple
from utils import word_in_list, merge_dictionaries
from pos_tagger import Language, TAGMethod, POSTagger

# set up parser
parser = argparse.ArgumentParser(
    prog="lexical_analyzer",
    description="Checks the lexical content of input texts againts a given wordlist."
)

parser.add_argument("input", help="a TSV file containing the texts to analyze")
parser.add_argument("-w", "--wordlist", help="a JSON formatted wordlist to check againsts", required=True)
parser.add_argument("-s", "--stopwords", help="(optional) a JSON formatted stopwords list", required=False)
parser.add_argument("-l", "--label", help="(optional) the label of the column that contains input data", default="text")
parser.add_argument("-p", "--postagger", 
                   help="language used to initialize the postagger", 
                   choices=['italian', 'english', 'russian'],
                   type=str)
parser.add_argument('-o', '--output', help="(optional) output file (TSV)")

# --- validate cli arguments
def validate_args(args):
    """Validate command line arguments"""
    if not (os.path.isfile(args.input) and (os.path.splitext(args.input)[-1].lower() == ".tsv")):
        print("Error: the input file does not exist or is not a supported format!")
        exit(2)

    if not (os.path.isfile(args.wordlist) and (os.path.splitext(args.wordlist)[-1].lower() == ".json")):
        print("Error: the supplied wordlist file does not exist or is not a supported format!")
        exit(2)

    if args.stopwords != None and (not (os.path.isfile(args.stopwords) and (os.path.splitext(args.stopwords)[-1].lower() == ".json"))):
        print("Error: the supplied stopwords file does not exist or is not a supported format!")
        exit(2)

    output_file = args.output if args.output else f"{os.path.splitext(args.input)[0]}_lexical.tsv"
    if os.path.exists(output_file) or not os.path.exists(os.path.dirname(os.path.abspath(output_file))):
        print(f"Error: an output file with path '{output_file}' already exists!")
        exit(2)

    return output_file

def load_pos_tagger(language: str) -> POSTagger:
    """
    Loads the language specific postagger.
    """
    tagger = None
    match language:
        case "italian":
            tagger = POSTagger(language=Language.IT, method=TAGMethod.STANZA, include_lemma=True)
        case "english":
            tagger = POSTagger(language=Language.EN, method=TAGMethod.STANZA, include_lemma=True)
        case "russian":
            tagger = POSTagger(language=Language.RU, method=TAGMethod.SPACY, include_lemma=True)
        case _:
            return None

    return tagger

def check_text(
    text: str,
    tagger: POSTagger,
    word_lists: dict,
    stopwords: list[str] = None) -> dict:
    """Check a single text entry against the given
    wordlist."""
    results = {}

    # tag text
    tagged_text = tagger.tag_text(text)

    # convert tags to simple tags
    tagged_text = [{**x, "pos": upos_to_simple[x["pos"]]} for x in tagged_text]

    # remove stopwords if supplied
    if stopwords != None:
        tagged_text = list(filter(lambda x: not word_in_list(x["text"], stopwords), tagged_text))

    # iterate over tiered-vocabulary
    for i in range(0, len(word_lists)):
        level = list(word_lists.keys())[i]
        vocabulary = merge_dictionaries(word_lists,0,i)

        # iterate over pos-ordered sublists
        for pos in vocabulary.keys():
            results_percent = None
            results_conform_list = None
            results_unconform_list = None
            
            words_subsection = list(filter(lambda x: x["pos"] == pos, tagged_text))
            words_list = [x["text"] for x in words_subsection]
            words_count = len(words_subsection)

            if words_count > 0:
                conform_words = list(filter(lambda x: word_in_list(x["lemma"], vocabulary[pos]), words_subsection))
                conform_list = [x["text"] for x in conform_words]
                conform_count = len(conform_words)
                unconform_list = [x for x in words_list if x not in conform_list]

                results_percent = round((conform_count/words_count*100),2)
                results_conform_list = sorted(conform_list)
                results_unconform_list = sorted(unconform_list)

            # push results
            results["text"] = text
            results[f"{level}_{pos}_percent"] = results_percent
            results[f"{level}_{pos}_words"] = sorted(words_list)
            results[f"{level}_{pos}_conform"] = results_conform_list
            results[f"{level}_{pos}_unconform"] = results_unconform_list

    return results
    

def main():
    # Parse and validate arguments
    args = parser.parse_args()
    output_file = validate_args(args)

    # Load data
    with open(args.wordlist, "r", encoding="utf-8") as w_in:
        word_list = json.load(w_in)

    stopwords_list = None
    if args.stopwords != None:
        with open(args.stopwords, "r", encoding="utf-8") as s_in:
            stopwords_list = json.load(s_in)

    # Read sentences
    df = pd.read_csv(args.input, sep="\t", encoding="utf-8", header=0)
    if args.label not in df:
        print(f"Error: no column named '{args.label}' exists in '{args.input}'!")
        exit(2)

    # now we drop unneded columns and rename
    df = df[[args.label]]
    df.rename(columns={args.label :'text'}, inplace=True)
    
    # Setup processing pipeline
    tagger = load_pos_tagger(args.postagger)
    
    eval_data = []
    counter = 0
    for input_text in df['text']:
        counter += 1
        print(f"INFO\t Analyzing sample [{counter}/{len(df['text'])}]")

        results = check_text(input_text, tagger, word_list, stopwords_list)
        eval_data.append(results)

    # Add results to dataframe
    eval_df = pd.DataFrame.from_dict(eval_data, orient='columns')

    # Write out
    eval_df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")


if __name__ == "__main__":
    main()