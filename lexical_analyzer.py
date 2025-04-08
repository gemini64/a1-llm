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
parser.add_argument("-p", "--postagger", 
                   help="language used to initialize the postagger", 
                   choices=['italian', 'english', 'russian'],
                   type=str, required=True)
parser.add_argument("-s", "--stopwords", help="(optional) a JSON formatted stopwords list", required=False)
parser.add_argument("-l", "--label", help="(optional) the label of the column that contains input data", default="text")
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
    results["text"] = text

    # tag text
    tagged_text = tagger.tag_text(text)

    # convert tags to simple tags
    tagged_text = [{**x, "pos": upos_to_simple[x["pos"]]} for x in tagged_text]

    # remove stopwords if supplied
    if stopwords != None:
        tagged_text = list(filter(lambda x: not word_in_list(x["text"], stopwords), tagged_text))

     # Get all content words (after stopword removal)
    all_content_words = tagged_text
    
    # Track words across all POS types
    all_words_by_pos = {}
    for item in all_content_words:
        pos = item["pos"]
        if pos not in all_words_by_pos:
            all_words_by_pos[pos] = []
        all_words_by_pos[pos].append(item)

    # iterate over tiered-vocabulary
    for i in range(0, len(word_lists)):
        level = list(word_lists.keys())[i]
        vocabulary = merge_dictionaries(word_lists, 0, i)
        
        # Track metrics across all POS for this level
        all_words_this_level = []
        all_conform_this_level = []
        all_unconform_this_level = []
        
        # Track unique words
        unique_words_this_level = set()
        unique_conform_this_level = set()
        
        # iterate over pos-ordered sublists
        for pos in vocabulary.keys():
            if pos not in all_words_by_pos:
                continue
                
            words_subsection = all_words_by_pos[pos]
            words_list = [x["text"] for x in words_subsection]
            words_count = len(words_subsection)
            
            all_words_this_level.extend(words_list)
            unique_words_this_level.update([x["lemma"] for x in words_subsection])

            if words_count > 0:
                conform_words = list(filter(lambda x: word_in_list(x["lemma"], vocabulary[pos]), words_subsection))
                conform_list = [x["text"] for x in conform_words]
                conform_count = len(conform_words)
                unconform_list = [x for x in words_list if x not in conform_list]
                
                all_conform_this_level.extend(conform_list)
                all_unconform_this_level.extend(unconform_list)
                unique_conform_this_level.update([x["lemma"] for x in conform_words])

                # Per POS metrics
                results[f"{level}_{pos}_percent"] = round((conform_count/words_count*100), 2)
                results[f"{level}_{pos}_count"] = words_count
                results[f"{level}_{pos}_conform_count"] = conform_count
                results[f"{level}_{pos}_unconform_count"] = len(unconform_list)
                
                # Only include full word lists if requested
                results[f"{level}_{pos}_words"] = sorted(words_list)
                results[f"{level}_{pos}_conform"] = sorted(conform_list)
                results[f"{level}_{pos}_unconform"] = sorted(unconform_list)
            else:
                results[f"{level}_{pos}_percent"] = None
                results[f"{level}_{pos}_count"] = 0
                results[f"{level}_{pos}_conform_count"] = 0
                results[f"{level}_{pos}_unconform_count"] = 0
                results[f"{level}_{pos}_words"] = []
                results[f"{level}_{pos}_conform"] = []
                results[f"{level}_{pos}_unconform"] = []

        # Overall level metrics
        total_words = len(all_words_this_level)
        total_conform = len(all_conform_this_level)
        
        results[f"{level}_overall_percent"] = round((total_conform/total_words*100), 2) if total_words > 0 else None
        results[f"{level}_all_words"] = sorted(all_words_this_level)
        results[f"{level}_all_conform"] = sorted(all_conform_this_level)
        results[f"{level}_all_unconform"] = sorted(all_unconform_this_level)
        
        # Unique word coverage
        unique_total = len(unique_words_this_level)
        unique_conform = len(unique_conform_this_level)
        
        results[f"{level}_unique_percent"] = round((unique_conform/unique_total*100), 2) if unique_total > 0 else None
        results[f"{level}_unique_count"] = unique_total
        results[f"{level}_unique_conform_count"] = unique_conform

    return results

def reorganize_dataframe(df):
    # Get all column names
    all_columns = list(df.columns)
    
    # Extract percentage columns
    percentage_columns = [col for col in all_columns if '_percent' in col]
    
    # Custom sorting function for percentage columns
    def sort_key(col_name):
        parts = col_name.split('_')
        level = parts[0]
        # Give priority to "overall" and "unique" metrics
        if parts[1] == 'overall':
            pos_priority = 0
        elif parts[1] == 'unique':
            pos_priority = 1
        else:
            # Order other POS types
            pos_map = {'n': 2, 'v': 3, 'a': 4, 'r': 5}
            pos_priority = pos_map.get(parts[1], 6)
        return (level, pos_priority)
    
    # Sort percentage columns
    percentage_columns.sort(key=sort_key)
    
    # Create a new column order
    other_columns = [col for col in all_columns if col != 'text' and col not in percentage_columns]
    new_column_order = ['text'] + percentage_columns + other_columns
    
    return df[new_column_order]

def assign_percentage_colours_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # List all columns
    all_columns = list(df.columns)

    # Get exclusively percentage columns
    percentage_columns = [col for col in all_columns if '_percent' in col]
    
    return df.style.background_gradient(subset=percentage_columns, cmap="RdYlGn", vmin=0.0, vmax=100.0)

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

    # Reorganize dataframe colums
    eval_df = reorganize_dataframe(eval_df)

    # Write out
    eval_df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")

    # Write out to XLSX to preserve colors
    eval_df = assign_percentage_colours_dataframe(eval_df)
    eval_df.to_excel("styled_output.xlsx", engine="openpyxl", index=False)

if __name__ == "__main__":
    main()