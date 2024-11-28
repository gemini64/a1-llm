# Worklog

## F.1 - Constraints based text generation

As a first research objective we focused on text generation given a set of linguistics constraints.

Specifically:
- We chose the CEFR A1 level of language proficiency for our text generation tasks.
- We selected 3 target languages: English, Italian and Russian.
- We selected a set of (multi-lingual) LLMs to use for our text generation tasks (gpt-4o, llama 3.1, gemini ...)

### Defining a set of suitable writing tasks
To define a set of writing tasks suitable for the generation of written material adapt for A1 language learners we referenced the CEFR Companion Volume for teachers and learners.

The CEFR framework defines only a list of language production (oral/written) and reception (oral/written) objectives.

Specifics about the morpho-syntactic structures a learner of a given level has to know depend on the specific language and may also depend on their course program.

To formulate a set of suitable tasks we focused primarily on the "receptive (written)" items listed for the A1 level. A complete list, extracted from the CEFR Companion Volume, is available [here](https://docs.google.com/document/d/1b42g0Jf0bsDng8b3Alx4XeyjpWfw1F5pkZ7YKi06lbU).

We defined 4 tasks:
- Writing a postcard
- Describing the daily routine of a specific professional figure
- Giving directions to a passerby
- Writing a brief social media post

Each task we proposed was inspired from a specific item listed in the CEFR inventory. Additional information is available in this [document](https://docs.google.com/document/d/1eqdsPgBh1bsrBlbUPx1yYgrikcze4nYq_iNBtX3RFwU).

To add some variety to our prompts, we decided to parametrize the 'theme' of the writing taks (e.g. the 'post theme' for the social media post writing task).

By parametrizing the writing tasks 'theme' we were able to build a set of ~100 prompts to submit and then evaluate.

### Linguistics constraints
As stated in the previous section, the CEFR framework does not define which mopho-syntactic language features a learner has to know and be able to use.

To build our language inventories we sourced a variety of documents from various language teaching/training entities. When applicable, we selected the morpho-syntactic elements listed as 'language reception' objectives for A1 learners.

The inventories we built and used to guide our writing tasks list every grammatical and syntactical element that can be used to complete the task proposed.

Inventories are language specific and an effort has been made:
- to remove redundant element
- to follow a precise hierachical structure (mainly for information clarity's sake and as a general prompt-engineering good practice, basically we tried to list and organize inventory items in hierarchical markdown lists)

See this [document](https://docs.google.com/document/d/11e0GFoavUTXkjSIVbYkgDbfPdKL7Jjy0qdq9vmepLP0) for additional details.

### Manual evaluation
As a first evaluation step, we used gpt-4o to generate completitions for 12 prompts (for each language). These completitions were manually checked and evaluated with a boolean (conforms to constraints/does not conform to constraints) label.

Additionally, specifics about errors in constraints compliance were listed when applicable.

This manual evaluation procedure was performed on:
- text generated using prompts in (taget language) for generation of text in (target language). see this [directory](https://drive.google.com/drive/folders/14vfWPtB0h00aFxoFeTBXtoZW6FM-CUgf?usp=drive_link)
- text generated using prompts in english for generation of text in (taget language). see this [directory](https://drive.google.com/drive/folders/1QclYd9l9z23QXJ4dwGq8kT40Hi7Y-_Se?usp=drive_link)

#### Observations
- No major difference in completions quality was observed when prompting the model in english
- The model was found to perform (generally) worse in italian and russian writing tasks

### Automatic boolean evaluation
To automate the evaluation procedure we tried to make a LLM perform the inverse tasks, i.e.

```
Given this {text} and {language inventory}, check if the input text conforms to the given linguistics constraints.
```

And basically associate each completion with a boolean compliant/non-compliant label.

We tested this approach on the same 12 prompts/completions and noticed very poor results for all languages.

#### Giving the model some examples
To check if the poor classification performance issues we observed could be solved by giving the model some examples (shots), we took another 5 (per language) prompts/completition couples and performed a manual evaluation.

These 15 samples were used to build a set of labeled examples to give the model.

We then re-collected evaluation data for our 12 manually checked examples in:
- 0 shots context
- 5 shots context (using only examples in (target language))
- 6 shots mixed language context
- 15 shots mixed language context

The data collected is available [here](https://drive.google.com/drive/folders/1-jmvOUAvZ3w4FACjZtOV1zc5qUcKxXiB?usp=drive_link).

#### Observations
By building a confusion matrix using the manual evaluation data as ground truth we found out that giving examples to the model, does not seem to improve the classification accuracy.

|                | TP | TN | FP | FN | Accuracy          | Precision         | Recall            |
| -------------- | -- | -- | -- | -- | ----------------- | ----------------- | ----------------- |
| 0 Shots        | 11 | 1  | 24 | 0  | 0.333333333333333 | 0.314285714285714 | 1                 |
| 5 Shots        | 9  | 5  | 20 | 2  | 0.388888888888889 | 0.310344827586207 | 0.818181818181818 |
| 6 Shots Mixed  | 11 | 4  | 21 | 0  | 0.416666666666667 | 0.34375           | 1                 |
| 15 Shots Mixed | 11 | 3  | 22 | 0  | 0.388888888888889 | 0.333333333333333 | 1                 |

| Samples | 36 |
| ------- | -- |
| P       | 11 |
| N       | 25 |

Additionally we observed a quite high false positive rate.

Even considering the low amount of data on which this analysis was performed and the possible presence of biases in the set of samples we chose, we can speculate that this task may be too difficult for a LLM.

### Automatic rule-based evaluation
(Only on Italian) We also tested a rule-based evaluation system.

The main idea behind this approach was to separate the text analysis (grammatical/syntactical features extraction) and the evaluation processes.

Starting from our Italian inventory we tried to define a user prompt to analyze each part-of-speech present in our inventory.

Examples:
- **Pronouns:** Extract the pronouns contained in the input text and find out their catagory
- **Verbs:** Extract all verbs and annotate their morphological features
...

A general of how this solution works is described in the following sections.

#### Step 1 - POS Tagging
We found out that, even for basic grammar analysis tasks (e.g. pronouns extraction and categorization), gpt-4o struggles a lot on italian text.

To aid the model in morpho-syntactical analysis tasks we tried to pre-process the input text with a part-of-speech tagging module.

We tested 3 POS tagging methods:
- spacy
- LLM aided analysis using an ad-hoc defined user prompt
- tint (this NLP tool is based on stanza and available only for Italian text analysis)

The final output of this module is a JSON array containing each word of the original text along with its associated POS tag (see universal POS tags [HERE](https://universaldependencies.org/u/pos/)).

```json
[
    {
        "text": "Certo",
        "pos": "INTJ"
    },
    {
        "text": "!",
        "pos": "PUNCT"
    },
    {
        "text": "Vai",
        "pos": "VERB"
    },
    {
        "text": "dritto",
        "pos": "ADV"
    },
    {
        "text": "per",
        "pos": "ADP"
    },
    {
        "text": "due",
        "pos": "NUM"
    },
    {
        "text": "isolati",
        "pos": "NOUN"
    }
]
```

#### Step 2 - (Grammar) Information extraction
Using the tagged text as input, we defined a set of user prompt to, separately, analyze and extract relevant information about the parts-of-speech present in our italian language inventory.

The prompts used, in a 0 shots context, are very similar in structure.

Given the tagged text as input, they ask to analyze a specific part of speech (e.g. only verbs) and extract relevant grammatical/morphological information.

A JSON schema is given as context and the request is to return a JSON object (or array) conformant to the given schema.

```
Given the following part-of-speech (POS) tagged text:

{input}

Extract and analyze any number contained, indipendently from its function within the
source text.

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.
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
                "description": "The number extracted"
            },
            "kind": {
                "enum": ["ordinale", "cardinale"],
                "description": "The number kind"
            }
        },
        "required": ["text", "kind"]
    }
}
```

#### Step 3 - (Syntax) Information extraction
To validate Italian syntactical constraints we basically needed an analisi logica del periodo on the input text.

The approach we followed is similar to the one described in the previous section.

In this case the prompt contains the original, untagged text. A complex JSON schema representing an analisi logica del periodo of a text of arbirary length is given as context and used to explain to the model the expected output format.

#### Step 4 - Evaluation
The result of the previous 3 steps is an "analysis document" in JSON format.

Validation is carried out by statically parsing this JSON object via code.

The final output contains a set of boolean labels that tell if the text respects all constraints, if it respects specifically the constraint sets on verbs, pronouns, numbers and syntax and a list of textual errors in case the text is found to be non-constraint compliant.

#### Observation
- While this approach was found to be a lot more robust than the boolean LLM based evaluation, it is strongly based on the content of our italian invetory.
- There are still open issues regarding the syntactical analysis phase.
- Grammatical/Morphological analysis is still carried out using a LLM. We observed that the output quality of the POS tagging module can influence the quality of the LLM output data (specifically on verbs analyisis)
- While tint generally seems to perform better in Italian text tagging tasks, no rigourous comparison between the tagging methods was performed at the moment of writing

## F.2 - Constraints based paraphrasing