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
{schema}
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
{schema}
```
---
# Adjectives
Given the following part-of-speech (POS) tagged text:
```
{input}
```
Extract and analyze ALL the adjectives it contains.

## Analysis Instructions

1. Look EXCLUSIVELY for words tagged as "ADJ" in the given input.
2. For each adjective instance (including repeated occurrences):
   - Record the exact text as it appears
   - Determine its degree (positive, comparative, or superlative)
   - Classify its regularity (true/false)
   - Identify its function (descriptive, interrogative, possessive, or other)

## Important Guidelines for Degree Classification

### For Analytical Purposes Only - Do Not Double Count
When determining adjectives' degrees, check the context carefully:

- **Positive form**: The base form of the adjective (e.g., "beautiful", "good", "tall")

- **Comparative form**: Either:
  - ADJ ending in '-er/r' (e.g., "taller", "bigger")
  - "more" + ADJ as a single unit (e.g., "more beautiful")
    * CRITICAL: When an adjective ("ADJ")  is IMMEDIATELY preceded by "more" (tagged as "ADV"), treat the entire phrase "more + [adjective]" as a SINGLE comparative adjective. DO NOT list the base adjective separately.

- **Superlative form**: Either:
  - ADJ ending in '-est/st' (e.g., "tallest", "biggest") 
  - "most" + ADJ as a single unit (e.g., "most beautiful")
    * CRITICAL: When an adjective ("ADJ") is IMMEDIATELY preceded by "most" (tagged as "ADV"), treat the entire phrase "most + [adjective]" as a SINGLE superlative adjective. DO NOT list the base adjective separately.

## Irregular Adjectives
- **Completely irregular**: All forms are different roots (e.g., 'good' -> 'better' -> 'best')
- **Partially irregular**: Uses standard suffixes but with stem changes (e.g., 'far' -> 'further' -> 'furthest')

### Standalone comparative "more" and superlative "most"
- When "more" is tagged as "ADJ" in the given input, consider it standalone and classify it as:
  - text: "more"
  - degree: comparative
  - regular: false (it's the irregular comparative form of "many/much")
  - function: typically "descriptive" unless context suggests otherwise

- When "most" is tagged as "ADJ" in the given input, consider it standalone and classify it as:
  - text: "most"  
  - degree: superlative
  - regular: false (it's the irregular superlative form of "many/much")
  - function: typically "descriptive" unless context suggests otherwise

## Response Format
Respond with a structured JSON array conforming to the schema below. No additional comment or data is required.

```json
{schema}
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
{schema}
```