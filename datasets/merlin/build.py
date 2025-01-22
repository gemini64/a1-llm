import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path

###
# Extracts data from merlin solr XML files ('merlin-solr-v1.1.zip')
# (Optionally) applies selection filters to retrieved data
#
# See the following link:
#     https://gitlab.inf.unibz.it/commul/merlin-platform/merlin-solr
#
# Expected input path:
#     './data/*.xml'
###

def extract_fields_from_xml(xml_file: str, field_names: list[str] = []) -> dict:
    """
    Extract specified fields from an XML file.
    
    Args:
        xml_file (str): Path to XML file
        field_names (list): List of field names to extract
        
    Returns:
        dict: Dictionary with field names as keys and their values
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Initialize results dictionary with empty strings as default values
        results = {field: "" for field in field_names}
        results['file_name'] = Path(xml_file).name
        
        # Find all field elements
        for doc in root.findall('.//doc'):
            for field in doc.findall('field'):
                name = field.get('name')
                if name in field_names:
                    results[name] = field.text or ""
                    
        return results
    
    except ET.ParseError as e:
        print(f"Error parsing {xml_file}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error processing {xml_file}: {e}")
        return None

def process_xml_files(input_dir: str, field_names: list[str] = []) -> pd.DataFrame:
    """
    Process all XML files in a directory and save results to TSV using pandas.
    
    Args:
        input_dir (str): Directory containing XML files
        output_file (str): Path to output TSV file
        field_names (list): List of field names to extract
    """
    # Get list of XML files
    xml_files = list(Path(input_dir).glob('*.xml'))
    
    if not xml_files:
        print(f"No XML files found in {input_dir}")
        return
    
    # Process all files and collect results
    results = []
    for xml_file in xml_files:
        result = extract_fields_from_xml(xml_file, field_names)
        if result:
            results.append(result)
    
    # Create DataFrame from results
    df = pd.DataFrame(results)
    
    # Reorder columns to put file_name first
    cols = ['file_name'] + field_names
    df = df[cols]

    # we also add a word count
    df["words"] = df["text_it"].map(lambda x: len(x.split()))
    
    # Return DataFrame
    return df

# --- flags
input_dir = "./data" # input directory
output_file = "./output.tsv"

# extracted properties
fields = [
    "_test_level_cefr",
    "_rating_coherence",
    "_rating_coherence",
    "_rating_fair_cefr",
    "_rating_fair_cefr_rough",
    "_rating_general_linguistic_range",
    "_rating_grammatical_accuracy",
    "_rating_orthography",
    "_rating_sociolinguistic_appropriateness",
    "_rating_vocabulary_control",
    "_rating_vocabulary_range",
    "text_it"
]

# all cefr levels
# cefr_l = [ "A1", "A2", "A2+", "B1", "B1+", "B2", "B2+", "C1", "C2" ]

filter_overall_rating = True # if true, filters out records on the basis of overall CEFR rating
filter_grammatical_accuracy = True # if true, filters out records on the basis of rated grammatical accuracy

set_overall_rating = [ "B1", "B1+", "B2", "B2+", "C1", "C2" ]
set_grammatical_accuracy = [ "B2", "B2+", "C1", "C2" ]

# --- extract data
df = process_xml_files(input_dir=input_dir, field_names=fields)

# --- apply filters
# filter out overall rating
if (filter_overall_rating):
    df = df[df["_rating_fair_cefr"].isin(set_overall_rating)]

# filter out grammatical accuracy
if (filter_grammatical_accuracy):
    df = df[df["_rating_grammatical_accuracy"].isin(set_grammatical_accuracy)]

# --- push out data
df.to_csv(output_file, sep="\t", encoding="utf-8", index=False)