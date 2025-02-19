# Pronouns
Given the following part-of-speech (POS) tagged text:
```
{input}
```
Extract and analyze the pronouns it contains.

Look for words tagged as "PRON" in the given input. List all pronoun instances, including repeated occurrences.

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.
```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/pronouns_it.json",
    "title": "Pronouns",
    "description": "A list of pronouns",
    "type": "array",
    "items": {
        "type": "object",
        "description": "Describes a pronoun",
        "properties": {
            "text": {
                "type": "string",
                "description": "The pronoun exactly as it appears in the text"
            },
            "kind": {
                "enum": ["personale", "relativo", "possessivo", "dimostrativo", "indefinito", "interrogativo", "esclamativo", "qualificativo", "numerale"],
                "description": "The pronoun kind, based on the Italian language pronouns categories"
            }
        },
        "required": ["text", "kind"]
    }
}
```
---
# Verbs
Given the following part-of-speech (POS) tagged text:
```
{input}
```
Extract and analyze ALL the verbs it contains.

Be particularly careful when dealing with auxiliary verbs:
- **essere/avere**: when used as auxiliary verbs, analyze and list them along with the principal verb they accompany (e.g. "ho mangiato" should be listed as a "passato prossimo").
- **modal verbs**: when a modal verb is used as auxiliary with an infinitive, analyze and list the two verbs separately as if they were two principal verbs (e.g. "posso scrivere" should be broken down and analyzed as "posso" and "scrivere").
- **single auxiliary verb for multiple principal verbs**: sometimes a single auxiliary verb may accompany multiple principal verbs. In Italian, this usually happens when "essere/avere" are used as auxiliary verbs along with multiple participles. In these cases, explicitly list and analyze the two principal verbs as separate items (e.g. "ho mangiato e poi dormito" should be broken down and analyzed as "ho mangiato" and "ho dormito").
- **past gerund**: this Italian verb form is formed using the present gerund of an auxiliary verb ("essere"/"avere") + the past participle of another verb (this is the main verb). List past gerunds as a single item (e.g. "avendo ascoltato").

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.
```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/verbs_it.json",
    "title": "Verbs",
    "description": "A list of verbs",
    "type": "array",
    "items": {
        "type": "object",
        "description": "Describes a verb and its morphological features",
        "properties": {
            "text": {
                "type": "string",
                "description": "The verb exactly as it appears in the text"
            },
            "lemma": {
                "type": "string",
                "description": "The base form of the main verb (eg. ho bevuto -> bere)"
            },
            "person":
            {
                "enum": ["first", "second", "third"],
                "description": "The verb person"
            },
            "number":
            {
                "enum": ["singular", "plural"],
                "description": "The verb number"
            },
            "mood": {
                "enum": ["indicativo", "congiuntivo", "condizionale", "imperativo", "infinito", "participio", "gerundio"],
                "description": "The verb mood, following Italian language verb moods"
            },
            "tense": {
                "enum": ["presente", "imperfetto", "passato prossimo", "passato remoto", "trapassato", "trapassato prossimo", "trapassato remoto", "passato", "futuro semplice", "futuro anteriore", "futuro"],
                "description": "The verb tense, following Italian language verb tenses"
            },
            "voice": {
                "enum": ["attiva", "passiva"],
                "description": "The verb voice, following Italian language verb voices"
            }
        },
        "required": ["text", "lemma", "mood", "tense", "voice" ]
    }
}
```
---
# Numbers
Given the following part-of-speech (POS) tagged text:
```
{input}
```
Extract and analyze EVERY number it contains.

The specific POS tag associated with words representing numbers in the given input is unimportant. List all number instances, including repeated occurrences.

Numbers in Italian text appear in two main categories:
1. **Ordinal numbers (ordinali)**: Numbers that express position or rank in a sequence. They appear in these forms:
   - Written in text: primo, secondo, terzo, quarto, etc.
   - Roman numerals: I, II, III, IV, V, etc.
   - Digits with ordinal markers: 1°, 1ª, 2°, 2ª, etc.
   - Compound forms: ventunesimo (21°), quarantaduesimo (42°), etc.
2. **Cardinal numbers (cardinali)**: Numbers that express quantity or amount. They appear in these forms:
   - Written in text: uno, due, tre, quattro, etc.
   - Written in digits: 1, 2, 3, 4, etc.
   - Compound forms: ventuno (21), quarantadue (42), etc.

Important notes:
- 'I' may be used as uppercase determiner (e.g. 'I Sopranos') or as the first roman numeral (i.e. 'I' as 'primo'). Consider the overall context to differentiate between the two.
- The same number can be ordinal or cardinal depending on its form and context (e.g., "1" is cardinal but "1°" is ordinal)
- Some words like "primo" can appear in non-ordinal contexts (e.g., "di primo mattino") - consider the context
- Compound numbers follow the same rules whether written in text or digits

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.
```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/numbers_it.json",
    "title": "Numbers",
    "description": "A list of numbers",
    "type": "array",
    "items": {
        "type": "object",
        "description": "Describes a number",
        "properties": {
            "text": {
                "type": "string",
                "description": "The number exactly as it appears in the text"
            },
            "kind": {
                "enum": ["ordinale", "cardinale"],
                "description": "Specifies whether the number is cardinal (quantity) or ordinal (position/rank)"
            }
        },
        "required": ["text", "kind"]
    }
}
```
---
# Syntactical analysis
Perform an "analisi logica del periodo" on the following text:
```
{input}
```
The expected output is a JSON object conforming to the schema attached below. No additional comment or data is required.
```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/syntactical_analysis_it_v2.json",
    "title": "Syntactical Analysis",
    "type": "object",
    "description": "Represents the syntactical analysis of an italian text of arbitrary length.",
    "properties": {
        "text": {
            "type": "string",
            "description": "The full, unedited text that is being analyzed."
        },
        "sentences": {
            "type": "array",
            "description": "An array of sentences extracted from the text.",
            "items": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The text of the sentence."
                    },
                    "type": {
                        "enum": [
                            "semplice",
                            "complessa",
                            "composta"
                        ],
                        "description": "The type of sentence."
                    },
                    "clauses": {
                        "type": "object",
                        "description": "The clauses within the sentence.",
                        "properties": {
                            "main_clause": {
                                "type": "object",
                                "description": "The main clause.",
                                "properties": {
                                    "content": {
                                        "type": "string",
                                        "description": "The text of the clause."
                                    },
                                    "function": {
                                        "enum": ["dichiarativa", "interrogativa", "esclamativa", "desiderativa", "volitiva", "concessiva", "potenziale", "dubitativa", "iussiva", "esclamativa"],
                                        "description": "The clause function."
                                    }
                                },
                                "required": ["content", "function"]
                            },
                            "coordinate_clauses": {
                                "type": "array",
                                "description": "The coordinate clauses contained within the sentence.",
                                "items": {
                                    "type": "object",
                                    "description": "A coordinate clause.",
                                    "properties": {
                                        "content": {
                                            "type": "string",
                                            "description": "The text of the clause."
                                        },
                                        "type": {
                                            "enum": ["copulativa", "avversativa", "conclusiva", "correlativa", "disgiuntiva", "esplicativa"],
                                            "description": "The clause type."
                                        }
                                    },
                                    "required": ["content", "type"]
                                }
                            },
                            "subordinate_clauses": {
                                "type": "array",
                                "description": "The subordinate clauses contained within the sentence.",
                                "items": {
                                    "type": "object",
                                    "description": "A subordinate clause.",
                                    "properties": {
                                        "content": {
                                            "type": "string",
                                            "description": "The text of the clause."
                                        },
                                        "function": {
                                            "enum": ["aggiuntiva", "avversativa", "causale", "comparativa", "concessiva", "condizionale", "consecutiva", "dichiarativa", "eccettuativa", "esclusiva", "finale", "incidentale", "interrogativa", "limitativa", "modale", "oggettiva", "relativa", "soggettiva", "temporale"],
                                            "description": "The clause function."
                                        },
                                        "rank": {
                                            "type": "integer",
                                            "description": "The subordinate rank of the clause."
                                        }
                                    },
                                    "required": ["content", "function", "rank"]
                                }
                            }
                        },
                        "required": ["main_clause", "coordinate_clauses", "subordinate_clauses"]
                    }
                },
                "required": [
                    "content",
                    "type",
                    "clauses"
                ]
            }
        }
    },
    "required": [
        "text",
        "sentences"
    ]
}
```