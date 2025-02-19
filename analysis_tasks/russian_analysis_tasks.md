# Nouns
Given the following part-of-speech (POS) tagged text:
```
{input}
```
Extract and analyze the nouns it contains.

Look exclusively for words tagged as "NOUN" or "PROPN" in the given input. List all the noun instances, including repeated occurrences.
For each noun, you will have to define its case and the case general meaning. 
For each combination of case and its general meaning there is a list of specific case meanings, from which you will need to chose one.

Be careful when analyzing case general meanings, follow these definitions:
- **subjective meaning**: there is an action, a state, or a situtation that comes from the noun.
- **objective meaning**: there is an action directed at the noun.
- **attributive meaning**: there is a relation of the noun to another object, action, state, or situation.
- **vocative expression**: the noun is used to directly address someone or something.
- **necessary informational completion**: the meaning of the case as a separate unit cannot be determined. It happens when the noun is a part of a fixed expression or is directed by a verb that requires a specific noun case.

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.
```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/noun_case_meaning_ru.json",
    "title": "noun case meanings",
    "description": "A list of nouns",
    "type": "array",
    "items": {
        "type": "object",
        "description": "Describes a noun",
        "properties": {
            "text": {
                "type": "string",
                "description": "The noun extracted"
            },
            "case": {
                "enum": ["Nominative", "Genitive", "Dative", "Accusative",
                "Instrumental", "Prepositional"],
                "description": "The noun case"
            },

            "case_general_meaning": {
                "enum": ["subjective", 
                "objective", 
                "attributive",
                "vocative expression",
                "necessary informational completion"
                ],
                "meaning": "following the definitions, report the main noun case meaning. The case meaning doesn't always match the syntactic function of the noun."
            },
            "nominative_subjective_meaning": {
                "enum":["субъект активного действия", "субъект состояния", "носитель признака", "наличие предмета/события"],
                "meaning": "choose from these meanings if noun is in Nominative with subjective general meaning"
            },
            "nominative_objective_meaning": {
                "enum": ["предмет обладания", "предмет необходимости", "предмет (лицо) в пассивной конструкции"],
                "meaning": "choose from these meanings if the noun is in Nominative with objective general meaning"
            },
            "nominative_attributive_meaning": {
                "enum": ["характеристика лица/предмета", "дополнительное название лица, звание или титул",
                "общая идентификация лица/предмета", "сравнение после союза 'чем'"],
                "meaning": "choose from these meanings if the noun is in Nominative with attributive general meaning"
            },
            "nominative_necessary_informational_completion_meaning": {
                "enum": ["персональная идентификация лица/предмета", "дата"],
                "meaning": "choose from these meanings if the noun is in Nominative with necessary informational completion general meaning"
            },
            "nominative_vocative_expression": {
                "type": "bool",
                "description": "true if the noun is a vocative expression"
            },
            
            "genitive_subjective_meaning": {
                "enum": ["субъект действия", "отсутствие лица (предмета)"],
                "meaning": "choose from these meanings if the noun is in Genitive with subjective general meaning"
            },
            "genitive_objective_meaning": {
                "enum": ["объект желания", "объект действия", "объект сравнения", "лицо, которое испытывает состояние"],
                "meaning": "choose from these meanings if the noun is in Genitive with objective general meaning"
            },
            "genitive_attributive_meaning": {
                "enum": ["определение предмета (без предлога)", "определение предмета (c предлогами)", 
                "обозначение части целого, меры", "описание предмета через признак", "место предмета/действия", 
                "с предлогом от: удаление от объекта / лица; лицо как исходный пункт движения; лицо-отправитель",
                "с предлогами от... до: расстояние",  "причина", "время действия", "причина действия"],
                "meaning": "choose from these meanings if the noun is in Genitive with attributive general meaning"
            },
            "genitive_necessary_informational_completion_meaning": {
                "enum": ["падеж обусловлен глагольным управлением", "обозначение количества в сочетании с числительным",
                "точная дата действия", "месяц в дате"],
                "meaning": "choose from these meanings if the noun is in Genitive with necessary informational completion general meaning"
            },

            "dative_subjective_meaning": {
                "enum": ["лицо как субъект действия", "лицо как субъект состояния",
                "лицо (предмет), о возрасте которого идет речь"],
                "meaning": "choose from these meanings if the noun is in Dative with subjective general meaning"
            },
            "dative_objective_meaning": {
                "enum": ["адресат действия", "объект действия"],
                "meaning": "choose from these meanings if the noun is in Dative with objective general meaning"
            },
            "dative_attributive_meaning": {
                "enum": ["предмет, к которому направлено движение (к)", "лицо как цель движения (к)",
                "место движения лица (предмета) (по)", "средство связи (по)", "определение (по)", "причина (благодаря)",
                "время регулярно повторяющегося действия (по)", "принадлежность"],
                "meaning": "choose from these meanings if the noun is in Dative with attributive general meaning"
            },
            "dative_necessary_informational_completion_meaning": {
                "enum": ["падеж обусловлен глагольным управлением"],
                "meaning": "choose from these meanings if the noun is in Dative with necessary informational completion general meaning"
            },
            
            "accusative_subjective_meaning": {
                "enum": ["логический субъект при глаголе 'звать'", "лицо как субъект состояния", "количество, мера"],
                "meaning": "choose from these meanings if the noun is in Accusative with subjective general meaning"
            },
            "accusative_objective_meaning": {
                "enum": ["лицо (предмет) как объект действия", "предмет речи, мысли"],
                "meaning": "choose from these meanings if the noun is in Accusative with objective general meaning"
            },
            "accusative_attributive_meaning": {
                "enum": ["время действия", "направление движения", "уступка",
                "количественная характеристика действия", "цель действия", "приблизительное расстояние, количество"],
                "meaning": "choose from these meanings if the noun is in Accusative with attributive general meaning"
            },
            "accusative_necessary_informational_completion_meaning": {
                "enum": ["падеж обусловлен глагольным управлением"],
                "meaning": "choose from these meanings if the noun is in Accusative with necessary informational completion general meaning"
            },
            "instrumental_subjective_meaning": {
                "enum": ["производитель действия (в пассивных конструкциях)"],
                "meaning": "choose from these meanings if the noun is in Instrumental with subjective general meaning"
            },
            "instrumental_objective_meaning": {
                "enum": ["объект действия с глаголом 'заниматься'","объект действия с другими глаголами",
                "орудие, средство действия"],
                "meaning": "choose from these meanings if the noun is in Instrumental with objective general meaning"
            },
            "instrumental_attributive_meaning": {
                "enum": ["характеристика лица, предмета (при глаголах быть, стать, являться и др.)", "совместность",
                "местонахождение", "время действия", "определение предмета", "определение лица", 
                "образ, способ действия", "цель", "орудие, средство действия"],
                "meaning": "choose from these meanings if the noun is in Instrumental with attributive general meaning"
            },
            "instrumental_necessary_informational_completion_meaning": {
                "enum": ["падеж обусловлен глагольным управлением"],
                "meaning": "choose from these meanings if the noun is in Instrumental with necessary informational completion general meaning"
            },
            
            "prepositional_subjective_meaning": {
                "enum": [],
                "meaning": "choose from these meanings if the noun is in Prepositional with subjective general meaning"
            },
            "prepositional_objective_meaning": {
                "enum": ["объект речи, мысли","объект действия"],
                "meaning": "choose from these meanings if the noun is in Prepositional with objective general meaning"
            },
            "prepositional_attributive_meaning": {
                "enum": ["место", "время", "условие", "средство передвижения", "определение"],
                "meaning": "choose from these meanings if the noun is in Prepositional with attributive general meaning"
            },
            "prepositional_necessary_informational_completion_meaning": {
                "enum": ["падеж обусловлен глагольным управлением"],
                "meaning": "choose from these meanings if the noun is in Prepositional with necessary informational completion general meaning"
            }
        },
        "required": ["text", "case", "meaning"]
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

Look exclusively for words tagged as "PRON" in the given input. List all the pronoun instances, including repeated occurrences.

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.
```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/pronouns_ru.json",
    "title": "Pronouns",
    "description": "A list of pronouns",
    "type": "array",
    "items": {
        "type": "object",
        "description": "Describes a pronoun",
        "properties": {
            "text": {
                "type": "string",
                "description": "The pronoun extracted"
            },
            "kind": {
                "enum": ["личное", "возвратное", "притяжательное", "указательное", 
                "определительное", "вопросительное", "относительное", "отрицательное", "неопределённое"],
                "description": "The pronoun kind"
            },
            "case": {
                "enum": ["именительный", "родительный", "дательный", "винительный",
                "творительный", "предложный"],
                "description": "The pronoun case"
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

Look exclusively for words tagged as "ADJ" in the given input. List all the adjective instances, including repeated occurrences.


Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.
```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/adjectives_ru.json",
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
            "form": {
                "enum": ["long-form", "short-form"],
                "description": "The adjective form (long or short)"
            },
            "case": {
                "enum": ["Nominative", "Genitive", "Dative", "Accusative",
                "Instrumental", "Prepositional"],
                "description": "The adjective case"
            },
            "degree": {
                "enum": ["positive", "comparative", "superlative"],
                "description": "The adjective degree."
            }
        },
        "required": ["text", "form"]
    }
}
```
---
# Verbs
Given the following part-of-speech (POS) tagged text:
```
{input}
```
Extract and analyze all the verbs it contains.
Look exclusively for words tagged as "VERB" in the given input. List all the verb instances, including repeated occurrences.

Be careful when defining the verb conjugation class. The verbs of the same conjugation class have similar endings and similar stem changes when conjugated. To define the conjugation class, conjugate the verb lemma and then look for the closest conjugation pattern in the list.

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.
```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/verbs_ru.json",
    "title": "Verbs",
    "description": "A list of verbs",
    "type": "array",
    "items": {
        "type": "object",
        "description": "Describes a verb and its morphological features",
        "properties": {
            "text": {
                "type": "string",
                "description": "The verb extracted"
            },
            "reflexive": {
                "type": "boolean",
                "description": "true is the verb ends in -ся/cь"
            },
            "lemma": {
                "type": "string",
                "description": "The base form of the main verb (eg. читаю -> читать). For the reflexive verbs, remove -cя/-cь"
            },
            "finite": {
                "type": "boolean",
                "description": "true if the verb is conjugated in a finite form"
            },
            "non-finite forms": {
                "enum": ["инфинитив", "причастие", "деепричастие"],
                "description": "only for non-finite verb forms"
            },

            "conjugation class": {
                "enum": ["Second-conjugation verbs in -ить, like 'жалить - жалят'",
                "Second-conjugation verbs in -ать/-ять/-еть, like 'видеть - видят'",
                "First-conjugation verbs in -ать/-ять/-еть, like 'читать - читаю', 'жалеть - жалею'", 
                "First-conjugation verbs in -овать/-eвать, like 'рисовать - рисую'",
                "First-conjugation verbs in -нуть, like 'тянуть - тяну'",
                "First-conjugation verbs in a changing consonant + -ать and -у/-ю ending in the first person like 'сказать - скажу'",
                "First-conjugation verbs in -ать with added vowel in stem and -у/-ю ending in the first person like 'брать - беру'",
                "First-conjugation verbs in -ать/-ять with regular stem and -у/-ю ending in the first person, like 'ждать - жду",
                "First-conjugation verbs in -сть/-сти, like 'упасть - упаду', 'мести - мету'", 
                "First-conjugation verbs in -чь, like 'течь - теку', 'мочь - могу'", 
                "First-conjugation verbs in -оть, like 'колоть - колю'",
                "First-conjugation verbs in -ереть losing stem vowel, like 'тереть - тру'",
                "First-conjugation verbs in -ить losing stem vowel, like 'пить - пью'",
                "First-conjugation verbs in -ить/-ыть/-уть that have stem vowel + -ют ending like 'дуть - дую', 'петь - пою'",
                "First-conjugation verbs in -авать, like 'давать - даю'",
                "First-conjugation verbs in -ти, like 'идти - иду'",
                "First-conjugation verbs in -ехать, like 'приехать - приеду'",
                "First-conjugation irregular verbs with differen endings and with major stem change, like 'обнять - обниму', 'есть - ем', 'жать - жму'"
        ],
                "description": "The verb conjugation class"
            },

            "mood": {
                "enum": ["изъявительное", "повелительное", "сослагательное"],
                "description": "The verb mood, following Russian language moods"
            },
            "tense": {
                "enum": ["past", "present", "future"],
                "description": "The verb tense"
            },
            "voice": {
                "enum": ["действительный", "страдательный"],
                "description": "The verb voice"
            }
        },
        "required": ["text", "lemma", "conjugation_class", "mood", "tense", "voice" ]
    }
}
```
---
# Adverbs
Given the following part-of-speech (POS) tagged text:
```
{input}
```
Extract and analyze all the adverbs it contains. Look for words tagged as "ADV" in the given input. List all the adverb instances, including repeated occurrences.

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.
```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/adverbs_ru.json",
    "title": "Adverbs",
    "description": "A list of adverbs",
    "type": "array",
    "items": {
        "type": "object",
        "description": "Describes the linguistics features of an adverb",
        "properties": {
            "text": {
                "type": "string",
                "description": "The adverb extracted"
            },
            "class": {
                "enum": ["предикативные", "вопросительные", "отрицательные", "неопределённые",
                "образа действия", "степени", "места", "времени", "причины", "цели", "совместности"],
                "description": "The adverb class"
            },
            "degree": {
                "enum": ["positive", "comparative", "superlative"],
                "description": "The adverb degree."
            }
        },
        "required": ["text", "class"]
    }
}
```
---
# Numerals
Given the following part-of-speech (POS) tagged text:
```
{input}
```
Extract and analyze all the numerals it contains. Look for words tagged as "NUM" in the given input. List all the numeral instances, including repeated occurrences.

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.
```json

{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "/schemas/numerals_ru.json",
    "title": "Numerals",
    "description": "A list of numerals",
    "type": "array",
    "items": {
        "type": "object",
        "description": "Describes a numeral",
        "properties": {
            "text": {
                "type": "string",
                "description": "The numeral extracted"
            },
            "kind": {
                "enum": ["ordinal", "cardinal", "collective"],
                "description": "The numeral kind"
            },
            "case": {
                "enum": ["Nominative", "Genitive", "Dative", "Accusative",
                "Instrumental", "Prepositional"],
                "description": "The numeral case"
            }
        },
        "required": ["text", "kind", "case"]
    }
}
```
