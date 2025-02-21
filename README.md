# A1 LLM

## Contents
- `analysis_tasks/*`: JSON/MD language analysis tasks. Used during the automated evaluation process.
- `datasets/*`: Contains utility scripts to reshape and select data from various sources.
- `inventories/*`: Markdown/plain-text language inventories. They are provided in various formats including: as linguistic items, as lingustic constraints, plus some variants (e.g. with or without syntax constraints).
- `schemas/*`: JSON schemas describing various linguistic objects. These are used to validate automated analysis data.
- `tools/*`: External binary tools (generated upon project setup).
- `paraphrase.py`: Paraphrase script. Used to paraphrase texts. Available for all languages, both full-text and sentence-wise. See the CLI interface for additional details.
- `eval.py`: Evaluation script. Takes a set of texts, a set of linguistic analysis tasks (these are language specific), annotates the input's content, then validates it using a rule-based approach. See the CLI interface for additional details.
- `parsers.py`: Parsers to validate analysis data. Available for EN/IT and based on the respective inventories.
- `pos_tagger.py`: A python module that defines a part-of-speech tagger (supports various languages and tagging methods).
- `agent_tools.py`: This module defines various data parsers chainable with LangChain runnables. Basically it contains mehtods used to parse and extract data from a Langchain LLM invocation.
- `fetch_irregular_verbs.py`: An utility script to collect a list of irregular italian verbs from Wikitionary.
- `tag_sentences.py`: An utility script to quickly test available POS tagging methods.
- `udpipe2_client.py`: This is the python UDPipe-2 client. Some functionalities have been added to fit our POS tagging output format requirements.
- `install.sh`: Simple install script. Sets up the python environment, installs requirements and generates the prompt lists for all languages.
- `collect_paraphrases.sh`: A bash script to batch collect paraphrases and evaluations. Various configuration parameters are available. See the source for additional info.

## Project setup

### Requirements

A setup script `install.sh` is provided to automatically set-up the project.

This will orderly: create a python virtual environment, activate it, install the project required modules, set-up an env file to store local API keys, and fetch and configure external tools (tint).

You will need:
- Python 3.11 (strongly advised)
- curl
- a macOS or linux host

**Note:** This project uses **spacy**, an NLP python module. At the moment the only version that seems to install and work correcly on somewhat recent python versions is **3.8.4**.

### 1. Install

Clone this repository, `cd` to its `root directory`, and follow the steps described below.

1. Open `install.sh` with a text editor and ensure the `PY_EXE` variable is set to the **python binary** you wish to use. In the example provided I'm setting it to the local python3.11 instance installed in my homebrew prefix.
```bash
#!/bin/bash

# init variable
PY_EXE="/opt/homebrew/bin/python3.11";
...
```

2. Run the following command to start the automated install process.
```bash
chmod +x install.sh;
./install.sh;
```

3. The python virtual environment is created by default in `.venv`. To activate it, run;
```bash
source ./.venv/bin/activate;
```

**Note:** If the automated procedure fails during external tools setup (tint), you will get a warning and a message asking you to add the required dependencies manually.

### 2. API keys and Connection settings
To run the **paraphrase** and **eval** scripts you will need to set the **OPENAI_API_KEY** and, optionally, **GROQ_API_KEY** and **GROQ_MODEL** environment variables.

To do this you can either:
1. Set all of them manually (`export VAR="value"`)
```bash
export OPENAI_API_KEY="api-key";
export GROQ_API_KEY="api-key";
export GROQ_MODEL="model-name";
```

2. Set them in the `.env` config file. Then, to make the `python-dotenv` module load them automatically, remeber to set the following environment variable:
```bash
export PY_ENV="DEVELOPMENT";
```

## Paraphrase
The paraphrase script `paraphrase.py` offers a CLI interface to specify various paraphrasing parameters. By default it uses gpt-4o (groq is avaliable as alternative).

Below is its CLI interface:
```
usage: paraphrase [-h] -c CONSTRAINTS [-l LABEL] [-o OUTPUT] [-d] [-g] [--by-sentence] [-s {italian,english,russian}] input

Given a set of texts as input, performs text transformations to make the input text conform to given linguistics constraints.

positional arguments:
  input                 a TSV file containing the texts to paraphrase

options:
  -h, --help            show this help message and exit
  -c CONSTRAINTS, --constraints CONSTRAINTS
                        a plain-text file containing the linguistics constraints to paraphrase against
  -l LABEL, --label LABEL
                        (optional) the label of the column that contains input data
  -o OUTPUT, --output OUTPUT
                        (optional) output file
  -d, --debug           (optional) log additional information
  -g, --groq            (optional) run on groq cloud
  --by-sentence         process text sentence by sentence
  -s {italian,english,russian}, --sentencizer {italian,english,russian}
                        language used to initialize the sentencizer (required if --by-sentence is used)
```

The parameters are, briefly:
- **input**: An input file, in TSV format, containing the texts to paraphrase
- **--constraints [file]**: A plain text/MD constraints list to paraphrase against (see the `./inventories` directory)
- **--label [str]**: This is the TSV header label that will be used to select the texts to paraphrase.
- **--output [file]**: The paraphrase output, in TSV format
- **--debug**: (Optional) flag to output debug data (messages, token usage, etc...)
- **--groq**: (Optional) if set, the script will use a groq hosted model. Remember to set the API key and model name in your environment.
- **--by-sentence**: (Optional) if set, the script will paraphrase the text sentence by sentence.
- **--sentencizer [enum]**: (Required if paraphrasing by sentence) This will be used to initialize the sentencizer (used to split the text into sentences).

This is an input example, in Italian:
```
text
Ho comprato cinque mele al mercato.
Il 3° piano è occupato dagli uffici.
Mia nonna ha 82 anni.
Sono arrivato secondo nella gara di nuoto."
Ci sono 12 mesi in un anno.
```

And this is a call example, using constraints lists stored in `./inventories`:
```bash
python paraphrase.py input_file.tsv -c "./inventories/constraints_italian_grammar_only.md" -l "text" -s "italian" -o output_file.tsv
```

## Eval
The eval script `eval.py` offers a CLI interface to specify various evaluation parameters. At the moment it uses exclusively gpt-4o.

The CLI interface is very similar to our paraphrase script:
```
usage: eval [-h] -t TASKS -p {italian,english,russian} [-l LABEL] [-a] [-s] [-d] [-o OUTPUT] input

Performs a series of analysis and evaluation tasks on input texts using an OAI LLM

positional arguments:
  input                 a TSV file containing the texts to evaluate

options:
  -h, --help            show this help message and exit
  -t TASKS, --tasks TASKS
                        a JSON file containing analysis tasks to perform
  -p {italian,english,russian}, --postagger {italian,english,russian}
                        the language to validate constraints against, used to initialize the postagger
  -l LABEL, --label LABEL
                        (optional) the label of the column that contains input data
  -a, --analysis        (optional) perform analysis only
  -s, --syntax          (optional) perform syntax analysis
  -d, --debug           (optional) log additional information
  -o OUTPUT, --output OUTPUT
                        (optional) output file
```

The parameters are, briefly:
- **input**: An input file, in TSV format, containing the texts to evaulate
- **--tasks [file]**: A JSON file defining analysis tasks (more info in the next sections)
- **--postagger [enum]**: This will be used to initialize the postagger.
- **--label [str]**: This is the TSV header label that will be used to select the texts to evaluate.
- **--output [file]**: The evaulation output, in TSV format
- **--debug**: (Optional) flag to output debug data (token usage, warnings, etc...)
- **--analysis**: (Optional) if set, the script will just perform the input's lingustic analysis.
- **--syntax**: (Optional) if set, the script will perform both grammar (default) and syntax analysis evaluation tasks.

And this, as before, is a call example, using tasks stored in `./analysis_tasks`:
```bash
python eval.py input_file.tsv -t "./analysis_tasks/italian_analysis_tasks.json" -l "text" -p "italian" -o output_file.tsv
```

### Analysis Tasks

An analysis tasks is a **user prompt** template, that asks an LLM to perform **morphological features** extraction from an input text, of arbitrary length, that we assume _has already been POS-tagged_.

An example, asking the model to annotate italian pronouns:

```
Given the following part-of-speech (POS) tagged text:

{input}

Extract and analyze the pronouns it contains.

Look for words tagged as "PRON" in the given input. List all pronoun instances, including repeated occurrences.

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.

{schema}
```

The **JSON schema** passed to the model is used both to constrain its output and to validate it. This is the one used for pronouns checking.

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

#### Analysis Tasks collection

The JSON passed to the model for **eval** contains a set of tasks with their own:
- **prompt template**
- **schema** to validate againsts
- (optionally) a set of **shots** to feed to the model

**Tasks** are subdivided in **syntax** and grammar **analysis**. A task collection is **structured** as shown below:
```json
{
  "grammar": {
    "task_1": {
      "prompt": "[take {input} do stuff, respond following the format {schema}]",
      "schema": <JSON schema>,
      "shots": [
        {
          "role": "user",
          "content": "[user message]"
        },
        {
          "role": "assistant",
          "content": "[assistant message]"
        }
      ]
    }
  },
  "syntax": {}
}
```

