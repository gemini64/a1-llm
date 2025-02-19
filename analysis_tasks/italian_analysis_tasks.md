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
{schema}
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
{schema}
```
---
# Syntactical analysis
Perform an "analisi logica del periodo" on the following text:
```
{input}
```
The expected output is a JSON object conforming to the schema attached below. No additional comment or data is required.
```json
{schema}
```