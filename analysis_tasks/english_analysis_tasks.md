# Nouns
Given the following part-of-speech (POS) tagged text:
```
{input}
```
Extract and analyze the nouns it contains.

Look for words tagged as "NOUN" or "PROPN" in the given input. List all noun instances, including repeated occurrences.

Be especially careful when analyzing nouns' regularity:
- **regular nouns**: regular English nouns follow the following pluralization rules:
  - **general rule**: add -s to form the plural (e.g. 'book/books')
  - **nouns ending in -s, -sh, -ch, -x, -z**: add -es (e.g. 'box/boxes', 'church/churches', 'buzz/buzzes')
  - **nouns ending in consonant + -y**: change the 'y' to 'i' and add '-es' (e.g. 'story/stories')
  - **nouns ending in vowel + -y**: just add -s (e.g. 'day/days')
  - **nouns ending in -o**: 
    - after a consonant: usually add '-es' (e.g. 'tomato/tomatoes', 'hero/heroes')
    - after a vowel: add '-s' (e.g. 'radio/radios', 'studio/studios')
    - some exceptions exist (e.g. 'piano/pianos', 'photo/photos')
- **irregular nouns**: irregular English nouns form their plurals in unique ways:
  - **internal vowel change**: (e.g. 'man/men', 'woman/women', 'foot/feet', 'tooth/teeth')
  - **-en endings**: (e.g. 'child/children', 'ox/oxen')
  - **most nouns ending in -f/fe**: replace the 'f/fe' with 'v' and add '-es' (e.g. 'knife/knives', 'leaf/leaves')
    - exceptions: some -f endings just add -s (e.g. 'roof/roofs', 'chief/chiefs')
  - **same form**: some nouns have identical singular and plural forms (e.g. 'sheep', 'deer', 'fish')
  - **foreign origin**: some retain their original language plurals (e.g. 'criterion/criteria', 'phenomenon/phenomena')

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.
```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/nouns_en.json",
    "title": "Nouns",
    "description": "A list of nouns",
    "type": "array",
    "items": {
        "type": "object",
        "description": "Describes the linguistics features of a noun.",
        "properties": {
            "text": {
                "type": "string",
                "description": "The noun extracted."
            },
            "number": {
                "enum": ["singular", "plural"],
                "description": "The noun number."
            },
            "possessive": {
                "type": "boolean",
                "description": "True if the noun is in possessive form (e.g. boy's)."
            },
            "regular": {
                "type": "boolean",
                "description": "True if the noun follows standard English pluralization rules."
            }
        },
        "required": ["text", "number", "possessive", "regular"]
    }
}
```
---
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
    "$id": "/schemas/pronouns_en.json",
    "title": "Pronouns",
    "description": "A list of pronouns",
    "type": "array",
    "items": {
        "type": "object",
        "description": "Describes the linguistics features of a pronoun.",
        "properties": {
            "text": {
                "type": "string",
                "description": "The pronoun exactly as it appears in the text"
            },
            "kind": {
                "enum": [ "personal", "reflexive", "possessive", "reciprocal", "relative", "interrogative", "demonstrative", "indefinite" ],
                "description": "The pronoun kind, based on the English language pronouns categories."
            }
        },
        "required": ["text", "kind"]
    }
}
```
---
# Adjectives
Given the following part-of-speech (POS) tagged text:
```
{input}
```
Extract and analyze the adjectives it contains.

Look for words tagged as "ADJ" in the given input. List all adjective instances, including repeated occurrences.

Be especially careful when analyzing adjectives' regularity:
- **comparative form**: Regular adjectives form their comparative either by:
  - Adding 'more' before the positive form (typically for 2+ syllable words, e.g. 'capable' -> 'more capable'). In these cases, the adjective will be directly preceded by 'more' in the provided input. List and analyze them as a single item.
  - Adding the suffix '-er/r' (typically for 1 syllable words, e.g. 'fast' -> 'faster')

- **superlative form**: Regular adjectives form their superlative either by:
  - Adding 'most' before the positive form (typically for 2+ syllable words, e.g. 'capable' -> 'most capable'). In these cases, the adjective will be directly preceded by 'most' in the provided input. List and analyze them as a single item
  - Adding the suffix '-est/st' (typically for 1 syllable words, e.g. 'fast' -> 'fastest')

- **irregular adjectives**: Some adjectives don't follow these patterns. They can be irregular in two ways:
  1. Complete irregularity: All forms are different (e.g. 'good' -> 'better' -> 'best', 'bad' -> 'worse' -> 'worst')
  2. Partial irregularity: Using standard suffixes but with stem changes (e.g. 'far' -> 'further' -> 'furthest')

- **edge cases (more/most)**: 'more' and 'most' may also be used on their own as the comparative and superlative irregular forms of 'many/much'. Be extra attentive and check if any other adjective directly follows them or if they are indeed used as standalone.

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/adjectives_en.json",
    "title": "Adjectives",
    "description": "A list of adjectives",
    "type": "array",
    "items": {
        "type": "object",
        "description": "Describes the linguistics features of an adjective.",
        "properties": {
            "text": {
                "type": "string",
                "description": "The adjective exactly as it appears in the text."
            },
            "degree": {
                "enum": ["positive", "comparative", "superlative"],
                "description": "The adjective degree."
            },
            "regular": {
                "type": "boolean",
                "description": "True if the adjective follows standard English formation patterns for its comparative and superlative forms."
            },
            "function": {
                "enum": ["descriptive", "interrogative", "possessive", "other"],
                "description": "The adjective function. It should be labeled as 'other' if it cannot be cataloged as descriptive, interrogative or possessive."
            }
        },
        "required": ["text", "function", "degree", "regular"]
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

Be particularly careful when analyzing auxiliary verbs:
- **to be/to have**: when used as auxiliary in finite verb forms, they should be listed and analyzed as a single item along with the main verb they accompany (e.g. "was playing" should be listed as a "past continuous").
- **modals**: if used as auxiliary, should be listed and analyzed as a single item along with the main verb they accompany (e.g. "can swim").
- **multiple auxiliary verbs**: some verb forms may include multiple auxiliary verbs. This is the case, for example for the "future perfect continous", where we have both the modal "will" and the verb "to be". In cases where multiple auxiliary verbs accompany a main verb, if a modal verb is used, list only the lemma of the modal auxiliary verb (e.g. "will have been" should list just "will" as auxiliary).
- **perfect gerunds**: this non-finite verb form is formed by "having" + "past participle" (this is the main verb). Analyze and list perfect gerunds as a single item (e.g. "having swum").

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.
```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/verbs_en.json",
    "title": "Verbs",
    "description": "A list of verbs",
    "type": "array",
    "items": {
        "type": "object",
        "description": "Describes a verb and its morphological features",
        "properties": {
            "text": {
                "type": "string",
                "description": "The verb analyzed (written as it appears in the original text)."
            },
            "lemma": {
                "type": "string",
                "description": "The base form of the verb (e.g., 'go' for 'went')."
            },
            "auxiliary": {
                "type": "string",
                "description": "The base form of the auxiliary verb (where applicable)."
            },
            "modal": {
                "type": "boolean",
                "description": "True if the verb is a modal verb."
            },
            "finite": {
                "type": "boolean",
                "description": "True if the verb is conjugated in a finite form."
            },
            "mood": {
                "enum": [ "indicative", "imperative", "subjunctive"],
                "description": "The verb mood (only for finite verb forms)."
            },
            "tense": {
                "enum": [ "present", "past", "future"],
                "description": "The verb tense (only for finite verb forms)."
            },
            "aspect": {
                "enum": [ "simple", "continous", "perfect", "perfect continous"],
                "description": "The verb aspect (only for finite verb forms)."
            },
            "voice": {
                "enum": [ "active", "passive"],
                "description": "The verb voice."
            },
            "verb_form": {
                "enum": [ "infinitive", "simple gerund", "perfect gerund", "present participle", "past participle" ],
                "description": "The verb form (only for non-finite verb forms)."
            }
        },
        "required": [ "text", "lemma", "modal", "finite", "voice" ]
    }
}
```