import re, json
from functools import partial
from langchain_core.messages import AIMessage

JSON_REGEX_PATTERN =  r"```json\n([\s\S]*?)```"
ANGLE_REGEX_PATTERN =  r"<([^>]+)>"
TEXT_TAG_REGEX_PATTERN = r"<text[^>]*>((?:(?!</text>)[\s\S])*)</text>"
ITALIAN_IRREGULAR_VERBS = "./inventories/word_lists/italian_irregular_verbs.json"
ITALIAN_ALLOWED_IRREGULARS = [ "esserci", "essere", "esservi", "avercela", "avere", "averla", "aversela", "volercene", "volerci", "volere", "volerne", "volersi", "potere", "dovere", "andare", "dare", "darsi", "dire", "dirsi", "fare", "farsi", "sapere", "sapersi", "stare", "venire", "chiudere", "chiudersi", "mettere", "mettersi", "morire", "nascere", "prendere", "prendersi", "scrivere"]

def regex_parser(message: AIMessage, regex: str) -> str | None:
    """Given a langchain AIMessage and a
    regular expression, tries to find matches
    in the model's reponse, then if any are found
    return the first matching group"""
    message_content = message.content

    match = re.search(fr"{regex}", message_content)

    if match:
        return match.group(1)
    else:
        return None

def regex_message_parser(regex: str) -> partial[str | None]:
    """Partial regex_parser application.
    Can be chained with a langchain sequences."""
    return partial(regex_parser, regex=regex)

def json_message_parser(message: AIMessage) -> dict:
    """Tries to load JSON object encoded in an AI Message.
    Can be chained with langchain sequences."""
    message_content = message.content

    match = re.search(JSON_REGEX_PATTERN, message_content)

    if match:
        json_str = match.group(1).strip()
        return json.loads(json_str)
    else:
        return {}

def token_usage_message_parser(message: AIMessage) -> int | None:
    """Given an AI Message, return the total token consumed
    by that call."""
    metadata = message.response_metadata
    results = None

    if metadata:
        token_usage = metadata.get('token_usage')
        results = token_usage.get('total_tokens')

    return results

def strip_string(input: str) -> str:
    """Takes a string as input. Uses regular
    expressions to remove traling and leading white
    spaces + substitutes any newline sequence with
    a (1) white space. Returns the transformed text."""
    transformed = input
    transformed = re.sub(r'^\s*', '', transformed)
    transformed = re.sub(r'\s*$', '', transformed)
    transformed = re.sub(r' +', ' ',transformed)
    transformed = re.sub(r'\n+', ' ',transformed)

    return transformed

def is_regular_it_verb(verb: str, check_allowed: bool = False) -> bool:
    with open(ITALIAN_IRREGULAR_VERBS, "r", encoding="utf-8") as f_in:
        irregular_verbs = json.load(f_in)

    irregular_verbs = set(irregular_verbs)
    if check_allowed:
        irregular_verbs = irregular_verbs.difference(set(ITALIAN_ALLOWED_IRREGULARS))

    return not (verb in irregular_verbs)

def word_in_list(word: str, comparison_list: list[str]) -> bool:
    """Given a string and a string list
    performs a case-insensitive comparison"""
    return any(word.lower() == x.lower() for x in comparison_list)

def merge_dictionaries(json_data: dict, start_idx: int, end_idx:int):
    """
    Merge multiple nested dictionaries from a JSON structure using numerical indices
    from start_idx to end_idx (inclusive).
    
    Parameters:
        json_data (dict): The JSON data containing nested dictionaries
        start_idx (int): Starting index of the dictionaries to merge (0-based)
        end_idx (int): Ending index of the dictionaries to merge (inclusive)
    
    Returns:
        dict: A new dictionary with merged contents where values from each category are combined
    """
    # Get the keys of the dictionaries to merge based on indices
    all_keys = list(json_data.keys())
    
    # Ensure indices are valid
    start_idx = max(0, min(start_idx, len(all_keys) - 1))
    end_idx = max(start_idx, min(end_idx, len(all_keys) - 1))
    
    # Get the dictionary keys to merge
    dict_keys_to_merge = all_keys[start_idx:end_idx + 1]
    
    # Create a new dictionary for the merged result
    merged_dict = {}
    
    # Find all unique category keys across all dictionaries to merge
    all_category_keys = set()
    for dict_key in dict_keys_to_merge:
        all_category_keys.update(json_data[dict_key].keys())
    
    # Merge the content for each category key
    for category_key in all_category_keys:
        # Initialize empty list for this category
        merged_list = []
        
        # Collect all items from all dictionaries for this category
        for dict_key in dict_keys_to_merge:
            if category_key in json_data[dict_key]:
                merged_list.extend(json_data[dict_key][category_key])
        
        # Remove duplicates and sort
        merged_dict[category_key] = sorted(list(set(merged_list)))
    
    return merged_dict