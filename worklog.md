# Worklog

## F.1 - Constraints based text generation

As a first research objective we focused on text generation given a set of linguistics constraints.

Specifically:
- We chose the CEFR A1 level of language proficiency for our text generation tasks.
- We selected 3 target languages: English, Italian and Russian.
- We selected a set of (multi-lingual) LLMs to use for our text generation tasks (gpt-4o, llama 3.1, Mixtral 8x7b, ~~gemini~~ ...)

### Defining a set of suitable writing tasks
To define a set of suitable writing tasks we referenced the CEFR Companion Volume for teachers and learners.

The CEFR framework defines only a list of language production (oral/written) and reception (oral/written) objectives.

Morpho-syntactic items a learner should be able to use are language specific and may also depend on the specific course program.

We focused primarily on the 'receptive (written)' items listed for the A1 level. A complete list, extracted from the CEFR Companion Volume, is available [here](https://docs.google.com/document/d/1b42g0Jf0bsDng8b3Alx4XeyjpWfw1F5pkZ7YKi06lbU).

We defined 4 tasks:
- Writing a postcard
- Describing the daily routine of a specific professional figure
- Giving directions to a passerby
- Writing a brief social media post

Each task proposed was inspired from a specific item listed in the CEFR inventory. Additional information is available in this [document](https://docs.google.com/document/d/1eqdsPgBh1bsrBlbUPx1yYgrikcze4nYq_iNBtX3RFwU).

To add some variety to our prompts, we parametrized the writing taks 'theme' (e.g. the 'post theme' for the social media post writing task).

By parametrizing the writing tasks 'theme' we were able to build a set of ~100 prompts to submit and then evaluate.

### Linguistics constraints
As stated in the previous section, the CEFR framework does not define which mopho-syntactic language features a learner should know and be able to use.

To build our language inventories we sourced a variety of documents from  language teaching/training entities. When applicable, we selected the morpho-syntactic elements listed as 'language reception' objectives for A1 learners.

The inventories we assembled list every grammatical and syntactical element that can be used to complete the task proposed.

Inventories are language specific. An effort has been made:
- to remove redundant element
- to present information in a hierachical fashion (mainly for information clarity's sake and as a general prompt-engineering good practice, basically we tried to list and organize inventory items in hierarchical markdown lists)

See this [document](https://docs.google.com/document/d/11e0GFoavUTXkjSIVbYkgDbfPdKL7Jjy0qdq9vmepLP0) for additional details.

### Manual evaluation
We used gpt-4o to generate completions for 12 prompts (12 x language). These completions were manually checked and evaluated with a boolean (conforms to constraints/does not conform to constraints) label.

Specifics about errors in constraints compliance were listed when applicable.

This manual evaluation procedure was performed on:
- text generated using prompts in (taget language) for generation of text in (target language). see this [directory](https://drive.google.com/drive/folders/14vfWPtB0h00aFxoFeTBXtoZW6FM-CUgf?usp=drive_link)
- text generated using prompts in english for generation of text in (taget language). see this [directory](https://drive.google.com/drive/folders/1QclYd9l9z23QXJ4dwGq8kT40Hi7Y-_Se?usp=drive_link)

#### Observations
- No major difference in completions quality was observed when prompting the model in english
- The model was found to perform (generally) worse in italian and russian writing tasks

### Wide-sample Manual Evaluation
After collecting completions for our 100 prompt samples across all three languages and using three different models (gpt-4o, Mixtral 8x7b and Llama 3.1), We performed a second manual evaluation on a wider data-sample.

**Note:** Mixtral 8x7b was not trained on Russian. Mixtral output was manually annotated only for Italian and English.

The manually annotated data is available in the following drive [directory](https://drive.google.com/drive/u/0/folders/1hCjmNpQX-DOgpWBZ8gYeX0v_E6N2oymZ).

#### Observations
- Both Mixtral an gpt-4o reach a 24% constraint compliance rate (on 25 samples) for Italian. LLama is the worst performing model on Italian writing tasks and only reaches 16% positive rate.
- All model generally perform better on English writing tasks. LLama specifically reaches a 100% positive rate, followed by mixtral (84%) and gpt-4o (68%)
- All model perform generally worse on Russian writing tasks (below 20% positive rate). This may be due size of Russian input the models we chose were trained on (sadly no data about language training data split has been shared publicly by meta and openai).

### Automatic boolean evaluation
To automate the evaluation procedure we tried to make a LLM perform the inverse tasks, i.e.

```
Given this {text} and {language inventory}, check if the input text conforms to the given linguistics constraints.
```

And basically associate each completion with a boolean compliant/non-compliant label.

We tested this approach on the same 12 prompts/completions couples and noticed very poor results (language-independent generalized issue).

#### Giving the model some examples (shots)
To check if the poor classification performance we observed could be solved by giving the model some examples (shots), we took another 5 (5 x language) prompts/completition couples and performed another round of manual evaluation.

These 15 samples were used to build a set of labeled examples to give the model.

We then re-collected evaluation data for our 12 manually checked examples in:
- 0 shots context
- 5 shots context (using only examples in (target language))
- 6 shots mixed language context
- 15 shots mixed language context

The data collected is available [here](https://drive.google.com/drive/folders/1-jmvOUAvZ3w4FACjZtOV1zc5qUcKxXiB?usp=drive_link).

#### Observations
The confusion matrix build using the manual evaluation labels as ground truth suggests that giving examples to the model, does not improve classification accuracy.

|                | TP | TN | FP | FN | Accuracy          | Precision         | Recall            |
| -------------- | -- | -- | -- | -- | ----------------- | ----------------- | ----------------- |
| 0 Shots        | 11 | 1  | 24 | 0  | 0.33 | 0.31 | 1.00                 |
| 5 Shots        | 9  | 5  | 20 | 2  | 0.39 | 0.31 | 0.82 |
| 6 Shots Mixed  | 11 | 4  | 21 | 0  | 0.42 | 0.34           | 1.00                 |
| 15 Shots Mixed | 11 | 3  | 22 | 0  | 0.39 | 0.33 | 1.00                 |

| Samples | 36 |
| ------- | -- |
| P       | 11 |
| N       | 25 |

Even considering the low amount of data we collected and the possible presence of biases in the set of samples we chose, we can speculate that this task may be too difficult for a LLM.

### Automatic rule-based evaluation
(Only on Italian) We also tested a rule-based evaluation approach.

Core idea: separate the text analysis (grammatical/syntactical features extraction) and evaluation processes.

Starting from our Italian inventory we tried to define a set of user prompts to analyze (separately)e ach part-of-speech listed in our inventory.

Examples:
- **Pronouns:** Extract the pronouns contained in the input text and find out their catagory
- **Verbs:** Extract all verbs and annotate their morphological features
...

A general idea on how this solution was implemented is described in the following sections.

#### Step 1 - POS Tagging
We found out that, even for basic grammar analysis tasks (e.g. pronouns extraction and categorization), gpt-4o struggles a lot on Italian text.

To aid the model in morpho-syntactical analysis tasks we tried to pre-process the input text with a part-of-speech tagging module.

We tested 3 POS tagging methods:
- (Spacy)[https://spacy.io/] (a multi-lingua NLP python library)
- LLM-aided analysis (using a specific user prompt)
- (Tint)[https://dh.fbk.eu/research/tint/] (this italian-specific NLP tool is based on stanza)

The final output of this pre-process step is a JSON array containing each word of the original text along with its POS tag (see universal POS tags [HERE](https://universaldependencies.org/u/pos/)).

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
Using the tagged text as input, we defined a set of user prompt to analyze and extract linguistics information relevant to our Italian inventory.

The prompts used, in a 0 shots context, are POS specific but overall very similar in structure.

Given the tagged text as input, we ask the model to analyze a specific POS (e.g. only verbs) and extract relevant grammatical/morphological information.

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

In this case the prompt contains the original, untagged text.

A complex JSON schema representing an analisi logica del periodo of a text of arbirary length is given as context and used to explain to the model the expected output format.

Information we try to extract include:
- Clauses contained in a sentence
- Clauses kinds (main/coord/sub)
- Clauses functions/types
- Subordination rank (where applicable)

#### Step 4 - Evaluation
The result of the previous 3 steps is an 'analysis document' in JSON format.

Validation is carried out by statically parsing this JSON object via code.

The final output contains a set of boolean labels that tell:
- If the text respects all constraints.
- If it respects specifically the constraint sets on verbs, pronouns, numbers and syntax.
- A list of descriptive error messages if the input is found to be non-compliant.

#### (Note) Dealing with Italian Irregular Verbs
_This issue is explained in-depth in the second part of this worklog._

Gpt-4o specifically was found to be widely unreliable in dealing with Italian Regular Verbs (in 0 shot classification scenarios).

As a solution to this problem we opted for a lexicographic comparison with a list of known Italian Irregular Verbs.

This is the solution that we ultimately chose for the automated evaluation methodology discussed in the previous sections.

#### Observation
- While this approach was found to be more robust than the boolean LLM based evaluation, it is strongly based on the content and structure of our italian invetory (language dependent).
- There are some open issues in regards to Italian syntax analysis (No standard practices/conventions to carry out an 'Analsi Logica del Periodo').
- Grammatical/Morphological analysis is still carried out using an LLM. The output quality of the POS tagging module can greatly influence the overall reliability of this automated evaluation system.
- No comparison was made to find out which POS tagging method is more reliable. Tint seems to perform better on Italian texts but no statistical analysis was performed.

## F.2 - Constraints based paraphrasing
The following sections briefly describe what was done regarding our secodary study focus i.e. iterative paraphrasing of text to fit within constraints of a given linguistics inventory.

### Core Idea
The core idea behind this approach can be described as follows:
1. Take an arbitrary complex text, generated with/without linguistics constraints
2. Ask the model to check, for every sentence, if the constraints we want to validate are satisfied.
    - If satisfied: keep text as is
    - If not satisfied: transform the original text to satisfy the given constraints

This process can then be performed iteratively until no further changes are needed to make the text fit in our constraints lists

### First Iteration
We decided to use a highly structured prompt (following ideas taken from meta-prompting prompt engineering techinques) and ask the model to apply chain-of-thought to formulate their response.

This was found to be a necessity to make the model actually consider all constrainst listed as context.

Additionally, manual analysis of the model's CoT generated response, gives insights about linguistics elements the model fails to catalogue or understand properly.

```
# Task:
Check if the given text complies with the constraints provided; generate a paraphrase when necessary.

# Original Text:
{input_text}

# Constraints checking:
Check every sentence againts ALL constraints given.
- If it violates no constraint, keep it as is.
- If it violates one or more constraints, paraphrase or remove it.

# Paraphrasing:
- A paraphrase has to preserve the original semantic meaning and minimize information loss.
- A paraphrase has to replace every non-constraints conformant element with an equivalent conformant alternative.
- If a paraphrase that preserves the original meaning and completely conforms to the given constraints cannot be formulated, then the original text should be removed.

# Output format:
Provide a step-by-step reasoning to elaborate your answer. The expected final output consists of the transformed text, enclosed in <angle brackets>.

# Constraints:
{constraints}
```

**Issues:** To extract and iterate over the transformed text, we are currently asking the model to use specific delimiters to enclose its final response (this is non-optional as the response also contains all the model's reasoning steps).

The code that parses the model's response uses basic ReGEX expressions to extract the tranformed text.

This means that depending on how closely the model is able to follow the instructions given, the whole iteration process may fail or succeed.

### Sentence-By-Sentence paraphrasing
We informally observed a tendency in looping over paraphrasis of irregular verbs (for Italian input texts) and in some cases the lack of attention on some constraints present in our inventories.

Also, as a language independent issue, we noticed a general lack of logical 'soundness' in the paraphrases formulated by the model (i.e. bad or overall unsound substitutions).

A preliminary analysis on output data using our first system iteration (on English language) is available [here](https://docs.google.com/spreadsheets/d/1h16vICpQyBoTFmUQGMzBrDeMCXLTKZYFmPumB-rRVZc/edit?gid=2129388210#gid=2129388210).

Assuming a difficulty with input length, we also tested a sentence-by-sentence paraphrasing approach. The prompt is very similar to the one attached in the previous section, therefore it is not included here.

**Note:** Sentencizing was carried out using spacy for all languages.

#### Observations
To get an idea about recurring issues/error in paraphrases we manually reviewed a set of 12 paraphrases in Italian and Russian, comparing the two methods (full-text paraphrasing and sentence-by-sentence).

The Italian annotations are available [here](https://drive.google.com/drive/u/0/folders/10AVAk_LPsTgfrOY0oMPCoJt0eEnh1pgn) and the annotation for Russian are available [here](https://drive.google.com/drive/u/0/folders/10AVAk_LPsTgfrOY0oMPCoJt0eEnh1pgn).

We observed:
- (Italian) No performance gain/loss between the two methods. Also we noticed that paraphrases quality seems overall unaffected by the method used.
- (Italian) A generalized difficulty in checking and paraphrasing irregular verbs. Also (less severe) a difficulty in correctly identifying tenses and moods.
- (Russian) A similar issue in checking for irregular verbs
- (Russian) A noticeable improvement in paraphrases quality using the sentence-by-sentence approach
- (Both) Overall a lack of quality, and in some cases logical unsoundness, in proposed paraphrases.

### Dealing with irregular Verbs (Italian)
Our preliminary analysis of paraphrases for Italian texts revealed a widespread issue in dealing and identifiying irregular verbs.

