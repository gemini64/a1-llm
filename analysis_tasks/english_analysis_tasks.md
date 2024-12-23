# Nouns
Given the following part-of-speech (POS) tagged text:
```
{input}
```
Extract and analyze the contained nouns.

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
                "description": "True if the noun has a regular plural form."
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
Extract and analyze the contained pronouns.

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
                "description": "The pronoun extracted."
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
Extract and analyze the contained adjectives.

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.
```json
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
                "description": "The adjective extracted."
            },
            "degree": {
                "enum": ["positive", "comparative", "superlative"],
                "description": "The adjective degree."
            },
            "irregular": {
                "type": "boolean",
                "description": "True if the adjective is irregular (i.e. if its comparative and superlative forms do not follow standard formation patterns and/or present thematic changes when compared to the adjective base form)."
            },
            "function": {
                "enum": ["descriptive", "interrogative", "possessive", "other"],
                "description": "The adjective function. It should be labeled as ' other ' if it cannot be cataloged as descriptive, interrogative or possessive."
            }
        },
        "required": ["text", "function"]
    }
}
```
---
# Verbs
Given the following part-of-speech (POS) tagged text:
```
{input}
```
Extract and analyze the contained verbs.

Auxiliary verbs (AUX) should be analyzed and listed with the main verb they accompany (e.g. I've thought).

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
                "description": "The verb analyzed."
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
                "description": "The verb voice (only for finite verb forms)."
            },
            "verb_form": {
                "enum": [ "infinitive", "gerund", "participle" ],
                "description": "The verb form (only for non-finite verb forms)."
            }
        },
        "required": [ "text", "lemma", "modal", "finite" ]
    }
}
```