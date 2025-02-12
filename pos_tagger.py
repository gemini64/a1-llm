import subprocess, spacy, json, stanza
from stanza import DownloadMethod
from udpipe2_client import process_text
from enum import Enum
from abc import ABC, abstractmethod
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

# configuration parameters - all tagging methods
OAI_MODEL = "gpt-4o"
USE_GPU = True
TINT_EXE = "./tools/tint/tint.sh"
TINT_PARAMS = ""

# configuration parameters - udpipe
UDPIPE_SERVER="http://localhost:8001"
UDPIPE_EN_MODEL="en_atis"
UDPIPE_IT_MODEL="it_parlamint"
UDPIPE_RU_MODEL="ru_syntagrus"

# LLM bases tagging prompt
TAGGING_PROMPT = """Given the following text:
```
{input}
```
Tag every word (and punctuation mark) with the corresponding part-of-speech (POS) tag.

Respond with a JSON output, following the schema defined below.
```json
{{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/postagged_text.json",
    "title": "POS-tagged text",
    "description": "Represents a POS-tagged text of arbitrary length",
    "type": "array",
    "items": {{
        "type": "object",
        "description": "A POS-tagged word/symbol/punctuation mark",
        "properties": {{
            "text": {{
                "type": "string",
                "description": "The POS-tagged word/sybol/punctuation mark"
            }},
            "pos": {{
                "enum": ["ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM", "PART", "PRON", "PROPN", "PUNCT", "SCONJ", "SYM", "VERB" ],
                "description": "The universal POS tag associated with the tagged text"
            }},
        }},
        "required": ["text", "pos"]
    }}
}}
```
"""

TAGGING_PROMPT_WITH_LEMMA = """Given the following text:
```
{input}
```
Tag every word (and punctuation mark) with the corresponding part-of-speech (POS) tag.

Respond with a JSON output, following the schema defined below.
```json
{{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/postagged_text.json",
    "title": "POS-tagged text",
    "description": "Represents a POS-tagged text of arbitrary length",
    "type": "array",
    "items": {{
        "type": "object",
        "description": "A POS-tagged word/symbol/punctuation mark",
        "properties": {{
            "text": {{
                "type": "string",
                "description": "The POS-tagged word/sybol/punctuation mark"
            }},
            "pos": {{
                "enum": ["ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM", "PART", "PRON", "PROPN", "PUNCT", "SCONJ", "SYM", "VERB" ],
                "description": "The universal POS tag associated with the tagged text"
            }},
            "pos": {{
                "type": "string"
                "description": "The base lemma."
            }},
        }},
        "required": ["text", "pos", "lemma"]
    }}
}}
```
"""

class Language(str, Enum):
    """Available languages"""
    IT = "Italian"
    EN = "English"
    RU = "Russian"

class TAGMethod(str, Enum):
    """POS Tagging methods
    Note that Tint is available only for Italian text"""
    LLM = "LLM"
    SPACY = "Spacy"
    TINT = "Tint"
    STANZA = "Stanza"
    UDPIPE = "UDPipe"

class POSTagger():
    """A part-of-speech tagger.
    
    Requires a target language and a tagging method
    specification"""
    def __init__(self, language: Language = Language.IT, method: TAGMethod = TAGMethod.LLM) -> None:
        self._language = language
        self._method = method
        
        self._init_tagger()

    def _init_tagger(self) -> None:
        if((not (self._language == Language.IT)) and (self._method == TAGMethod.TINT)):
            raise RuntimeError("ERROR! Tint POS-Tagging backend supports Italian only!")
        
        match self._method:
            case TAGMethod.LLM:
                self._tagger = LLMTagger()
            case TAGMethod.SPACY:
                self._tagger = SpacyTagger(self._language)
            case TAGMethod.STANZA:
                self._tagger = StanzaTagger(self._language)
            case TAGMethod.TINT:
                self._tagger = TintTagger()
            case TAGMethod.UDPIPE:
                self._tagger = UDPipeTagger(self._language)
            case _:
                pass
        
        
    def tag_text(self, input: str) -> list[dict[str, str]]:
        """Returns a POS tagged text from a given string input."""
        results = self._tagger.tag(input)
        return results
    

class Tagger(ABC):
    
    @abstractmethod
    def tag(self, input: str) -> list[dict[str, str]]:
        pass


class LLMTagger(Tagger):
    """An openai LLM based part-of-speech tagger"""
    def __init__(self, temperature: float = 0, top_p = 0.95, prompt: str = TAGGING_PROMPT) -> None:
        self._temperature = temperature
        self._top_p = top_p
        self._prompt = prompt

        self._init_llm()

    def _init_llm(self) -> None:
        self._llm = ChatOpenAI(
            model=OAI_MODEL,
            temperature=self._temperature,
            top_p=self._top_p
        )

        self._prompt_template = ChatPromptTemplate.from_messages(
            [
                ("user", self._prompt)
            ]
        )

        self._chain = self._prompt_template | self._llm | JsonOutputParser()

    # overriding interface method
    def tag(self, input: str) -> list[dict[str, str]]:
        """Returns a POS tagged text from a given string input."""
        results = self._chain.invoke(
            input={
                "input": input
            }
        )

        return results
    
class SpacyTagger(Tagger):
    """A spacy based part-of-speech tagger.
    
    Requires a target language specification."""
    def __init__(self, language: Language = Language.IT, use_gpu: bool = USE_GPU, include_lemma: bool = False) -> None:
        self._language = language
        self._use_gpu = use_gpu
        self._include_lemma = include_lemma

        self._init_nlp()

    def _init_nlp(self) -> None:
        if self._use_gpu:
            spacy.prefer_gpu()

        match self._language:
            case Language.IT:
                self._nlp = spacy.load("it_core_news_lg")
            case Language.EN:
                self._nlp = spacy.load("en_core_web_trf")
            case Language.RU:
                self._nlp = spacy.load("ru_core_news_lg")
            case _:
                pass

    # overriding interface method
    def tag(self, input: str) -> list[dict[str, str]]:
        """Returns a POS tagged text from a given string input."""
        results = []

        # tag input data nlp(input)
        doc = self._nlp(input)

        for token in doc:
            if self._include_lemma:
                results.append({
                    "text": token.text,
                    "pos": token.pos_,
                    "lemma": token.lemma_
                })
            else:
                results.append({
                "text": token.text,
                "pos": token.pos_
            })


        return results

class StanzaTagger(Tagger):
    """A stanza based part-of-speech tagger.
    
    Requires a target language specification."""
    def __init__(self, language: Language = Language.IT, use_gpu: bool = USE_GPU, include_lemma: bool = False) -> None:
        self._language = language
        self._include_lemma = include_lemma
        self._use_gpu = use_gpu
        self._init_nlp()

    def _init_nlp(self) -> None:
        match self._language:
            case Language.IT:
                self._nlp = stanza.Pipeline('it', processors='tokenize,pos,lemma', use_gpu=self._use_gpu, download_method=DownloadMethod.REUSE_RESOURCES)
            case Language.EN:
                self._nlp = stanza.Pipeline('en', processors='tokenize,pos,lemma', use_gpu=self._use_gpu, download_method=DownloadMethod.REUSE_RESOURCES)
            case Language.RU:
                self._nlp = stanza.Pipeline('ru', processors='tokenize,pos,lemma', use_gpu=self._use_gpu, download_method=DownloadMethod.REUSE_RESOURCES)
            case _:
                pass

    # overriding interface method
    def tag(self, input: str) -> list[dict[str, str]]:
        """Returns a POS tagged text from a given string input."""
        results = []

        # tag input data nlp(input)
        doc = self._nlp(input)

        for sentence in doc.sentences:
            for word in sentence.words:
                if self._include_lemma:
                    results.append({
                        "text": word.text,
                        "pos": word.pos,
                        "lemma": word.lemma
                    })
                else:
                    results.append({
                    "text": word.text,
                    "pos": word.pos
                })


        return results

class UDPipeTagger(Tagger):
    """An UDPipe based part-of-speech tagger.
    
    Requires a target language specification."""
    def __init__(self, language: Language = Language.IT, server_url: str = UDPIPE_SERVER, include_lemma: bool = False) -> None:
        self._language = language
        self._server_url = server_url
        self._include_lemma = include_lemma
        self._init_nlp()

    def _init_nlp(self) -> None:
        match self._language:
            case Language.IT:
                self._nlp = lambda x : process_text(self._server_url, UDPIPE_IT_MODEL, x)
            case Language.EN:
                self._nlp = lambda x : process_text(self._server_url, UDPIPE_EN_MODEL, x)
            case Language.RU:
                self._nlp = lambda x : process_text(self._server_url, UDPIPE_RU_MODEL, x)
            case _:
                pass

    # overriding interface method
    def tag(self, input: str) -> list[dict[str, str]]:
        """Returns a POS tagged text from a given string input."""
        results = []

        # tag input data nlp(input)
        words = self._nlp(input)

        for word in words:
            if self._include_lemma:
                results.append({
                    "text": word["text"],
                    "pos": word["pos"],
                    "lemma": word["lemma"]
                })
            else:
                results.append({
                "text": word["text"],
                "pos": word["pos"]
            })


        return results
    
class TintTagger(Tagger):
    """A tint-based part-of-speech tagger.
    
    Requires a tint binary to be available in local
    configuration path exe"""
    def __init__(self, exe: str = TINT_EXE, params: str = TINT_PARAMS, include_lemma = False):
        self._exe = exe
        self._params = params
        self._include_lemma = include_lemma

    # overriding interface method
    def tag(self, input: str) -> list[dict[str, str]]:
        """Returns a POS tagged text from a given string input."""
        results = []
        
        proc = subprocess.run(args = [ self._exe ], input=input, encoding="utf-8", stdout=subprocess.PIPE)
        tint_out = proc.stdout

        tint_obj = json.loads(tint_out)

        for sentence in tint_obj["sentences"]:
            for token in sentence["tokens"]:
                if (self._include_lemma):
                    results.append({
                        "text": token["word"],
                        "pos": token["ud_pos"],
                        "lemma": token["lemma"]
                    })
                else:
                    results.append({
                        "text": token["word"],
                        "pos": token["ud_pos"]
                    })
        
        return results