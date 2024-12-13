import re, json
from functools import partial
from langchain_core.messages import AIMessage
from pos_tagger import TintTagger, LLMTagger, TAGGING_PROMPT_WITH_LEMMA

JSON_REGEX_PATTERN =  r"```json\n([\s\S]*?)```"
ANGLE_REGEX_PATTERN =  r"<([^>]+)>"
ITALIAN_IRREGULAR_VERBS = "./inventories/italian_irregular_verbs.json"
ITALIAN_ALLOWED_IRREGULARS = [ "esserci", "essere", "esservi", "avercela", "avere", "averla", "aversela", "volercene", "volerci", "volere", "volerne", "volersi", "potere", "dovere" ]

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

def json_message_parser(message: AIMessage):
    """Tries to load JSON object encoded in an AI Message.
    Can be chained with langchain sequences."""
    message_content = message.content

    match = re.search(JSON_REGEX_PATTERN, message_content)

    if match:
        json_str = match.group(1).strip()
        return json.loads(json_str)
    else:
        return {}

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

def check_irregular_it_verbs(input: list[dict]) -> list[dict]:
    sentences = input
    error_message_template = """Use of the verb '{verb}' which is irregular."""
    
    #tagger = LLMTagger(prompt=TAGGING_PROMPT_WITH_LEMMA)
    tagger = TintTagger(include_lemma=True)

    for sentence in sentences:
        text = sentence["content"]

        tokens = tagger.tag(text)
        for token in tokens:
            if token["pos"] == "VERB":
                lemma = token["lemma"]

                if (not is_regular_it_verb(verb=lemma, check_allowed=True)):
                    sentence["errors"].append(error_message_template.format(verb=lemma))

    return sentences

def is_regular_it_verb(verb: str, check_allowed: bool = False) -> bool:
    with open(ITALIAN_IRREGULAR_VERBS, "r", encoding="utf-8") as f_in:
        irregular_verbs = json.load(f_in)

    irregular_verbs = set(irregular_verbs)
    if check_allowed:
        irregular_verbs = irregular_verbs.difference(set(ITALIAN_ALLOWED_IRREGULARS))

    return not (verb in irregular_verbs)
