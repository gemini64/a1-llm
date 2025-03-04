import pandas as pd



# --- ifles
output_file = "./metadata.tsv"
input_file = "./cefr_leveled_texts.csv"

df = pd.read_csv(input_file, encoding="utf-8", header=0, sep=",")

# --- add wordcount
df["words"] = df["text"].map(lambda x : len(x.split()))

# --- get labels
labels = df["label"].unique()
labels.sort()

# --- compute words metadata
words_meta = {}

for label in labels:
    subset = df[df["label"] == label]

    words_meta[label] = {
        "words_min": int(subset["words"].min()),
        "words_max": int(subset["words"].max()),
        "words_mean": int(subset["words"].mean()),
        "words_median": int(subset["words"].median()),
        "words_mode": int(subset["words"].mode()[0])
    }

# --- also add data for all
words_meta["ALL"] = {
    "words_min": int(df["words"].min()),
    "words_max": int(df["words"].max()),
    "words_mean": int(df["words"].mean()),
    "words_median": int(df["words"].median()),
    "words_mode": int(df["words"].mode()[0])
}

# --- output data
out_df = pd.DataFrame.from_dict(data=words_meta, orient="index")
out_df.to_csv(output_file, sep="\t", encoding="utf-8", index=True)