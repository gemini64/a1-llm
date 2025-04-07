import re, binascii
from pathlib import Path
import pandas as pd
import numpy as np

# --- flags
filenames_to_utf8 = True
min_chars = 240
min_page_edits = 50
sep_char = "_"

# --- I/O
input_dir = "./en-output/html"
input_metadata = "./en-output/en-output.csv"
output_file = "./vikidia_en.tsv"

# --- read data
def read_text(path: str) -> str | None:
    try:
        with open(path, "r", encoding="utf-8") as f_in:
            results = f_in.read()

        return results
    except Exception as e:
        print(f"Error: {e}")
        
        return None
    
def has_category_prefix(input: str) -> bool:
    has_category = re.compile(r'^[^:]+:.+$')
    return bool(has_category.match(input))
    
def convert_filename(encoded_filename):
    """
    Converts filenames with special hex-encoded characters back to proper UTF-8 representation.
    For example: Venerd'C3'AC.txt -> Venerdì.txt
    """
    def hex_to_utf8(match):
        # Extract hex values from the match
        hex_str = match.group(0).replace("'", "")
        # Convert hex string to bytes
        byte_data = binascii.unhexlify(hex_str)
        # Decode bytes to UTF-8 string
        return byte_data.decode('utf-8')
    
    # Regular expression to match 'XX'YY' patterns where XX and YY are hex values
    pattern = r"'[0-9A-F]{2}'(?:[0-9A-F]{2})(?:'[0-9A-F]{2})*"
    
    # Replace all matches with their UTF-8 decoded values
    return re.sub(pattern, hex_to_utf8, encoded_filename)


def advanced_convert_filename(encoded_filename):
    """
    A more advanced version that handles various hex encoding patterns,
    including multi-byte UTF-8 sequences of different lengths.
    """
    # Find all hex sequences like 'XX'YY'ZZ' etc.
    hex_sequences = re.finditer(r"(?:'[0-9A-F]{2})+", encoded_filename)
    
    result = encoded_filename
    # Process each sequence from right to left to avoid offset issues
    for match in sorted(hex_sequences, key=lambda m: m.start(), reverse=True):
        hex_str = match.group(0).replace("'", "")
        byte_data = binascii.unhexlify(hex_str)
        utf8_char = byte_data.decode('utf-8')
        result = result[:match.start()] + utf8_char + result[match.end():]
    
    return result

def rename_files_in_directory(directory_path, file_extension=".txt", dry_run=True):
    """
    Renames all files with the given extension in the specified directory.
    
    Args:
        directory_path: Path to the directory containing files
        file_extension: Only files with this extension will be processed (default: .txt)
        dry_run: If True, shows what would be renamed without actually renaming (default: True)
    
    Returns:
        List of tuples with (old_name, new_name) for all renamed files
    """
    renamed_files = []
    directory = Path(directory_path)
    
    # Ensure the directory exists
    if not directory.is_dir():
        raise ValueError(f"Directory not found: {directory_path}")
    
    # Process each file in the directory
    for file_path in directory.glob(f"*{file_extension}"):
        old_name = file_path.name
        new_name = advanced_convert_filename(old_name)
        
        # Skip files that don't need renaming
        if old_name == new_name:
            continue
        
        renamed_files.append((old_name, new_name))
        
        if not dry_run:
            try:
                file_path.rename(directory / new_name)
                print(f"Renamed: {old_name} → {new_name}")
            except Exception as e:
                print(f"Error renaming {old_name}: {e}")
    
    return renamed_files

# convert filenames
if filenames_to_utf8:
    rename_files_in_directory(input_dir, dry_run=False)

df = pd.read_csv(input_metadata, encoding="utf-8", header=0, sep=",", na_values={'title': ""})

# coherce dtypes
df['title'] = df['title'].astype(str).replace('nan', "")
df['pageID'] = pd.to_numeric(df['pageID'], errors='coerce')
df['revisions_count'] = pd.to_numeric(df['revisions_count'], errors='coerce')

# filter out pages with less than min revisions and NaN pages
df.sort_values(by=["revisions_count"], inplace=True)
df = df[df["revisions_count"] >= min_page_edits]
df = df[df["title"] != ""]

# remove pages with category prefix
df = df[~df['title'].apply(has_category_prefix)]

output_data = []
errors = []

for index, row in df.iterrows():
    page_title = row["title"].replace(" ", sep_char)
    page_content = read_text(f"{input_dir}/{page_title}.txt")

    if page_content != None:
        pars = page_content.split("\n")
        pars = [ " ".join(x.split()) for x in pars] 
        pars = [ x for x in pars if len(x) > min_chars]
        
        if len(pars) > 0:
            for elem in pars:
                output_data.append({
                        "text": elem,
                        "page_id": row["pageID"],
                        "page_title": page_title,
                        "page_revisions": row["revisions_count"],
                        "chars": len(elem)
                    })

# --- write out data
output_df = pd.DataFrame.from_dict(output_data, orient='columns')
output_df.to_csv(output_file ,encoding="utf-8", sep="\t", index=False)