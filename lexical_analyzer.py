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
parser.add_argument("-c", "--compare", help="(optional) the label of the column that contains text to compare against", default=None)
parser.add_argument("-d", "--dropdata", help="(optional) omit pos specific stats from output", action='store_true')
parser.add_argument('-o', '--output', help="(optional) output file (XLSX)")

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

    output_file = args.output if args.output else f"{os.path.splitext(args.input)[0]}_lexical.xlsx"
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
    """Check a single text entry against the given wordlist."""
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
    all_content_words = [x for x in tagged_text if x['pos'] in ['n','v','a','r']]
    
    # Track words across all POS types
    all_words_by_pos = {}
    for item in all_content_words:
        pos = item["pos"]
        if pos not in all_words_by_pos:
            all_words_by_pos[pos] = []
        all_words_by_pos[pos].append(item)
    
    # Store all words and counts ONCE (not per level)
    all_words_allpos = []
    for pos, words in all_words_by_pos.items():
        words_list = [x["text"] for x in words]
        all_words_allpos.extend(words_list)
        
        results[f"total_{pos}_count"] = len(words)
        results[f"total_{pos}_words"] = sorted(words_list)
    
    # Store allpos word count and list ONCE
    results["total_allpos_count"] = len(all_words_allpos)
    results["total_allpos_words"] = sorted(all_words_allpos)
    
    # Store unique words information ONCE - now using lemma+POS pairs
    unique_words_total = set([(x["lemma"], x["pos"]) for x in all_content_words])
    results["total_unique_count"] = len(unique_words_total)
    
    # iterate over tiered-vocabulary levels
    for i in range(0, len(word_lists)):
        level = list(word_lists.keys())[i]
        vocabulary = merge_dictionaries(word_lists, 0, i)
        
        # Track metrics across all POS for this level
        all_conform_this_level = []
        all_unconform_this_level = []
        
        # Track unique words as lemma+POS pairs
        unique_conform_this_level = set()
        
        # iterate over pos-ordered sublists
        for pos in vocabulary.keys():
            if pos not in all_words_by_pos:
                continue
                
            words_subsection = all_words_by_pos[pos]
            words_list = [x["text"] for x in words_subsection]
            words_count = len(words_subsection)
            
            if words_count > 0:
                # Check conformity based on lemma in the POS-specific vocabulary
                conform_words = list(filter(lambda x: word_in_list(x["lemma"], vocabulary[pos]), words_subsection))
                conform_list = [x["text"] for x in conform_words]
                conform_count = len(conform_words)
                unconform_list = [x for x in words_list if x not in conform_list]
                
                all_conform_this_level.extend(conform_list)
                all_unconform_this_level.extend(unconform_list)
                
                # Update unique conform words with lemma+POS pairs
                unique_conform_this_level.update([(x["lemma"], x["pos"]) for x in conform_words])

                # Per POS metrics - only store conformity data for each level
                results[f"{level}_{pos}_percent"] = round((conform_count/words_count*100), 2)
                results[f"{level}_{pos}_count-conform"] = conform_count
                results[f"{level}_{pos}_count-unconform"] = words_count - conform_count
                results[f"{level}_{pos}_words-conform"] = sorted(conform_list)
                results[f"{level}_{pos}_words-unconform"] = sorted(unconform_list)
            else:
                results[f"{level}_{pos}_percent"] = None
                results[f"{level}_{pos}_count-conform"] = 0
                results[f"{level}_{pos}_count-unconform"] = 0
                results[f"{level}_{pos}_words-conform"] = []
                results[f"{level}_{pos}_words-unconform"] = []

        # Overall level metrics - only store the conformity data
        total_words = results["total_allpos_count"]
        total_conform = len(all_conform_this_level)
        
        results[f"{level}_allpos_percent"] = round((total_conform/total_words*100), 2) if total_words > 0 else None
        results[f"{level}_allpos_count-conform"] = total_conform
        results[f"{level}_allpos_count-unconform"] = total_words - total_conform
        results[f"{level}_allpos_words-conform"] = sorted(all_conform_this_level)
        results[f"{level}_allpos_words-unconform"] = sorted(all_unconform_this_level)
        
        # Unique word coverage based on lemma+POS pairs
        unique_total = results["total_unique_count"]
        unique_conform = len(unique_conform_this_level)
        
        results[f"{level}_unique_percent"] = round((unique_conform/unique_total*100), 2) if unique_total > 0 else None
        results[f"{level}_unique_count-conform"] = unique_conform
        results[f"{level}_unique_count-unconform"] = unique_total - unique_conform

    return results

def reorganize_dataframe(df: pd.DataFrame, levels: list[str], ascending: bool = True, drop_pos_specific: bool = False) -> pd.DataFrame:
    # Get all column names
    all_columns = list(df.columns)
    
    # Extract percentage columns
    total_columns = [col for col in all_columns if 'total_' in col]
    level_specific_columns = [col for col in all_columns if col != 'text' and not col.startswith('total_')]

    # Define level order, we suppose received levels are in ascending order
    level_order = {x: y for (x,y) in zip(levels, range(0, len(levels)+1, 1))} if ascending else {x: y for (x,y) in zip(levels, range(len(levels),-1,-1))}
    data_order = {"percent": 0, "words": 1, "words-conform": 2, "words-unconform": 3, "count": 4, "count-conform": 5, "count-unconform": 6 }
    
    # Custom sorting function for percentage columns
    def sort_key(col_name):
        parts = col_name.split('_')

        level = parts[0]
        kind = parts[1]
        data = parts[2]

        # Set a priority value based on level
        level_priority = level_order.get(level, 999) # 999 is for unknown levels
        data_priority = data_order.get(data, 999)

        # Give priority to "allpos" and "unique" metrics
        if kind == 'allpos':
            pos_priority = 0
        elif kind == 'unique':
            pos_priority = 1
        else:
            # Order other POS types
            pos_map = {'n': 2, 'v': 3, 'a': 4, 'r': 5}
            pos_priority = pos_map.get(kind, 6)
        return (data_priority, pos_priority, level_priority)
    
    # Sort percentage columns
    total_columns.sort(key=sort_key)
    level_specific_columns.sort(key=sort_key)


    # Check if we need to drop pos specific columns
    if (drop_pos_specific):
        new_column_order = total_columns + level_specific_columns
        new_column_order = [col for col in new_column_order if any(map(lambda x: x in col, ["_allpos_", "_unique_"]))]
        new_column_order = ['text'] + new_column_order
    else:
        new_column_order = ['text'] + total_columns + level_specific_columns

    return df[new_column_order]

def assign_percentage_colours_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # List all columns
    all_columns = list(df.columns)

    # Get exclusively percentage columns
    percentage_columns = [col for col in all_columns if '_percent' in col]
    
    return df.style.background_gradient(subset=percentage_columns, cmap="RdYlGn", vmin=0.0, vmax=100.0)

def process_data(data: list[str], tagger, word_list, stopwords_list, drop_pos_specific):
    data_dicts = []
    
    counter = 0
    for text in data:
        counter += 1
        print(f"INFO\t Analyzing sample [{counter}/{len(data)}]")

        results = check_text(text, tagger, word_list, stopwords_list)
        data_dicts.append(results)

    # Add results to dataframe
    df = pd.DataFrame.from_dict(data_dicts, orient='columns')

    # Reorganize dataframe colums
    df = reorganize_dataframe(df, word_list.keys(), drop_pos_specific=drop_pos_specific)

    return df

def alternate_columns_preserve_names(df1, df2, suffix1='_original', suffix2='_paraphrase'):
    # Make sure columns are the same
    if set(df1.columns) != set(df2.columns):
        raise ValueError("Both DataFrames must have the same set of columns")
    
    # Rename columns to avoid conflicts
    df1_renamed = df1.rename(columns={col: f"{col}{suffix1}" for col in df1.columns})
    df2_renamed = df2.rename(columns={col: f"{col}{suffix2}" for col in df2.columns})
    
    # Create a new empty DataFrame
    result = pd.DataFrame()
    
    # Add columns in alternating order
    for col in df1.columns:
        result[f"{col}{suffix1}"] = df1_renamed[f"{col}{suffix1}"]
        result[f"{col}{suffix2}"] = df2_renamed[f"{col}{suffix2}"]
    
    return result

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

    # check if a colum with text to compare againts exists
    if args.compare != None and args.compare not in df:
        print(f"Error: a label for optional text comparison named '{args.compare}' was specified, but a column with that name does not exists in '{args.input}'!")
        exit(2)
    
    # Setup processing pipeline
    tagger = load_pos_tagger(args.postagger)

    # Process data
    print(f"INFO --- Processing input text")
    eval_df = process_data(df[args.label], tagger, word_list, stopwords_list, args.dropdata)

    # If a comparision is specified, process also the text to compare against
    if args.compare != None:
        print(f"INFO --- Processing comparison text")
        compare_df = process_data(df[args.compare], tagger, word_list, stopwords_list, args.dropdata)
        eval_df = alternate_columns_preserve_names(eval_df, compare_df)

    # Assign colours and output data
    eval_df = assign_percentage_colours_dataframe(eval_df)
    eval_df.to_excel(output_file, engine="openpyxl", index=False)

if __name__ == "__main__":
    main()