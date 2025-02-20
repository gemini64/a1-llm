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

## Analysis Instructions
Annotate the following morphological features for every verb, either in finite or non-finite form:
- **finite forms**: its auxiliary (if present) and the mood x tense x aspect combination used.
- **non-finite forms**: the specific non-finite verb form used ("infinitive", "simple gerund", "perfect gerund", "present participle", "past participle").
- **both**: the verb analyzed (as it appears in the given text), its lemma, its voice ("active"/"passive"), if it is finite/non-finite and if it includes a modal verb.

### Dealing with auxiliary ("AUX") verbs 
Apply the following rules when dealing with auxiliary ("AUX") verbs:
- **to be/to have**: when used as auxiliaries in finite verb forms, they should be listed and analyzed as a single unit with the main verb they accompany (e.g. "was playing" should be listed as a "past continuous").
- **modals**: when a modal verb has auxiliary ("AUX") function, it should be listed and analyzed as a single unit with the main verb it accompanies (e.g. "can swim"). Set the verb's "modal" property to true. When a modal verb appears without an explicit main verb (e.g., "I can't, but he can."), analyze it as a standalone implied main verb.
- **multiple auxiliary verbs**: some finite verb form may include multiple auxiliaries. This is the case for some passive verb forms and, as an example, verbs conjugated in "future perfect continuous", where we have both the modal "will" and the verb "to be". When multiple auxiliary verbs accompany a main verb, compile the "auxiliary" property as follows:
    - if a **modal** verb is used, annotate exclusively the lemma of the modal auxiliary verb (e.g. "will have been" should list just "will" as auxiliary)
    - in all other cases, annotate the lemmas of the auxiliaries used.

### Handling negation particles
Negation particles such as "n't", "not", etc. are NOT separate verbs and should NOT be listed as individual entries. Instead:
- For contracted forms like "can't", "don't", "won't", etc., analyze the full auxiliary/modal together with its negation as a single unit.
- Example: "can't" should be analyzed as a single entry with:
  - text: "can't"
  - lemma: "can"
  - modal: true
  - other properties as appropriate

### Marginal verb constructs
- **perfect gerund**: this non-finite verb form is formed by [having] + [past participle] (this is the main verb). Analyze and list this construct a single unit (e.g. "having swum").
- **[be going to] + [verb]**: this construct should always be analyzed as a single unit (e.g. "I'm going to jump"). Annotate these properties as follows:
  - **text**: the full construct, as it appears in the input text
  - **lemma**: the lemma of the [verb] used
  - **auxiliary**: be going to
  - **modal**: true
  - **tense and mood**:
    - when used as **is/are going to**: present continuous
    - when used as **was/were going to**: past continuous
- **[be able to/have to/be to/had better] + [verb]**: these marginal verb forms are referred as semi-modals or semi-auxiliaries. These constructs should always be analyzed as a single unit (e.g. "I have to go"). Annotate these properties as follows:
  - **text**: the full construct, as it appears in the input text
  - **lemma**: the lemma of the [verb] used
  - **auxiliary**: [be able to/have to/be to/had better]
  - **modal**: true

### Handling verbs in marginal constructs
When analyzing marginal verb constructs such as [be going to] + [verb], [be able to] + [verb], [have to] + [verb], etc.:
- The entire construct should be analyzed as a single unit ONLY
- DO NOT analyze the main verb as a separate infinitive
- DO NOT analyze "going" as a separate gerund/participle when it appears in the [be going to] construction
- Example: In "I am going to swim", only analyze "am going to swim" as a single unit, with no separate entries for "going" or "swim"
  
## Output format
Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.

```json
{schema}
```