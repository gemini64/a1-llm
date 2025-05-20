import os
import pandas as pd
from thefuzz import fuzz

# -- i/o
root_dir = "./vikidia_100"
output_file = "analysis_report.xlsx"

original_files = {
    "en": {
        "original": "./vikidia_en_100.tsv",
        "grammar": "./vikidia_en_100_grammar.tsv",
        "lexical": "./vikidia_en_100_lexical.tsv"
    },
    "it": {
        "original": "./vikidia_it_100.tsv",
        "grammar": "./vikidia_it_100_grammar.tsv",
        "lexical": "./vikidia_it_100_lexical.tsv"
    },
}

strategies = ["a", "b", "c", "d"]

def list_subdirectories(path: str) -> list:
    contents = os.listdir(path=path)
    return [ x for x in contents if os.path.isdir(os.path.join(path, x)) ]

main_df = pd.DataFrame()

# --- loop over known folder structure
idioms = list_subdirectories(root_dir)

for idiom in idioms:
    original_df = pd.read_csv(original_files[idiom]["original"], sep="\t", encoding="utf-8", header=0)

    original_df_g = pd.read_csv(original_files[idiom]["grammar"], sep="\t", encoding="utf-8", header=0)
    error_cols = [x for x in list(original_df_g.columns.values) if x.startswith("errors_")]

    original_df_l = pd.read_csv(original_files[idiom]["lexical"], sep="\t", encoding="utf-8", header=0)
    percentages_cols = ["A1_allpos_percent", "A2_allpos_percent"]

    original_df = pd.concat([original_df[["text"]], original_df_l[percentages_cols], original_df_g[error_cols]], axis=1)

    # apply needed renames
    to_rename = error_cols + percentages_cols
    prefix = 'original_'
    original_df = original_df.rename(columns={c: prefix+c for c in to_rename})

    # and also rename the text column
    original_df = original_df.rename(columns={"text": "original"})

    # ok, now we loop over the models
    models_parent_dir = os.path.join(root_dir, idiom)
    models = list_subdirectories(models_parent_dir)

    for model in models:

        strategies_parent_dir = os.path.join(root_dir, idiom, model)
        # iterate over stategies
        for letter in strategies:
            strategy_df = pd.read_csv(os.path.join(strategies_parent_dir, f"{letter}.tsv"), sep="\t", encoding="utf-8", header=0)

            strategy_df_g = pd.read_csv(os.path.join(strategies_parent_dir, f"{letter}_grammar.tsv"), sep="\t", encoding="utf-8", header=0)
            error_cols = [x for x in list(strategy_df_g.columns.values) if x.startswith("errors_")]

            strategy_df_l = pd.read_csv(os.path.join(strategies_parent_dir, f"{letter}_lexical.tsv"), sep="\t", encoding="utf-8", header=0)
            percentages_cols = ["A1_allpos_percent", "A2_allpos_percent"]

            strategy_df = pd.concat([strategy_df[["text"]], strategy_df_l[percentages_cols], strategy_df_g[error_cols]], axis=1)

            # and also rename the text column
            strategy_df = strategy_df.rename(columns={"text": "modified"})

            # merge with original data
            strategy_df = pd.concat([original_df, strategy_df], axis=1)

            # add ident row
            strategy_df["idiom"] = idiom
            strategy_df["model"] = model
            strategy_df["letter"] = letter

            # add difference colum
            strategy_df['diff'] = strategy_df.apply(lambda row: fuzz.ratio(row['original'], row['modified']), axis=1)

            # and then we attach to the main dataframe
            main_df = pd.concat([main_df, strategy_df], axis=0)

# reorder our collected data
colum_order = ["original", "modified", "idiom", "model", "letter", "diff", "A1_allpos_percent", "A2_allpos_percent", "original_A1_allpos_percent", "original_A2_allpos_percent", "errors_pronouns", "errors_verbs", "errors_numbers", "errors_nouns", "errors_adjectives", "original_errors_pronouns", "original_errors_verbs", "original_errors_numbers", "original_errors_nouns", "original_errors_adjectives"]
main_df = main_df[colum_order]

# write out all
main_df.to_excel(output_file, engine="openpyxl", index=False)