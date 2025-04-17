# A1 LLM

## Contents
- `analysis_tasks/*`: JSON/MD language analysis tasks. Structure and content is described in detail in the "Analysis Task" section of this document. Used for automated grammar/morphology analysis.
- `datasets/vikidia*`: Contains RAW data extracted from vikidia and properly formatted dataset TSV files, along with some utility scripts.
- `inventories/*`: JSON/MD/plain-text language inventories. Sub-directories contain various structured lists consisting of language specific vocabularies (used for lexical analysis), and language specific stopwords lists.
- `schemas/analysis/*`: JSON Schemas describing linguistic objects. These are mainly used to format and validate grammar/morphology analysis data.
- `tools/*`: External (third-party) binary tools (this directory is created upon project setup).
- `paraphrase.py`: Paraphrase script. Used to paraphrase texts. Available for all languages, both full-text and sentence-wise. See the "Paraphrase" section of this document for additional details.
- `eval.py`: Evaluation script. Takes a set of texts, a set of grammar/mophology analysis tasks (language specific), annotates the input's content (using an LLM), then validates it using a rule-based approach. See the "Eval (Grammar/Morphology)" section of this document for additional details.
- `lexical_analyzer.py`: Lexical analysis script. Takes a set of texts, a wordlist (vocabulary), an optional stopwords list and returns a lexical analysis report. See the "Lexical Analyzer" section of this document for additional details.
- `parsers.py`: Parsers to validate grammar/mophology analysis data. Available only for EN/IT (and based on the respective A1 inventories).
- `pos_tagger.py`: A python module that defines a part-of-speech tagger (supports various languages and tagging methods).
- `utils.py`: This module defines various helper function and a set of data parsers chainable with langchain runnables.
- `fetch_irregular_verbs.py`: (utility script) to collect a list of known Italian irregular verbs from Wikitionary.
- `fetch_stopwords.py`: (utility script) to collect stopwords list for a set of given languages (uses the NLTK python module).
- `tag_sentences.py`: (utility script) to quickly test available POS tagging methods.
- `mappings.py`: Various pos taggings mappings to convert between various formats.
- `udpipe2_client.py`: This is the python UDPipe-2 client. Some functions have been added to fit our POS tagging output format requirements.
- `install.sh`: Project install script. Sets up the python environment, installs requirements and fetches external tools.
- `collect_paraphrases.sh`: A bash script to batch collect paraphrases and evaluations.

## Project setup

### Requirements

A setup script `install.sh` is provided to automatically set-up the project.

This will orderly: create a python virtual environment, activate it, install the required python modules, set-up a `.env` file to store API keys and secrets, and fetch and configure external tools (tint).

Setup requirements:
- python 3.11 (strongly recommended, use either `homebrew` on macOS or `pyenv` to manage and select multiple python installs)
- curl
- a macOS or linux host

**Note:** This project uses **spacy**, an NLP python module. At the moment the only version that seems to install and work correcly on somewhat recent python versions is **3.8.4**. Spacy **3.8.4** is unaviable for arm64 linux hosts, expect the automated setup to fail if you're using this host/arch combination.

### 1. Install

Clone this repository, `cd` to its `root directory`, and follow the steps described below.

1. Open the `install.sh` script with a text editor and ensure the `PY_EXE` variable is set to the **python binary** you wish to use. In the example provided I'm setting it to the local python3.11 instance installed in my homebrew prefix.
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

To run the included scripts you will need to set an **OPENAI_API_KEY** and, optionally, a **GROQ_API_KEY** and  a **GROQ_MODEL** environment variable.

To do this you can either:
1. Set all of them manually before running the scripts with (`export VAR="value"`)
```bash
export OPENAI_API_KEY="api-key";
export GROQ_API_KEY="api-key";
export GROQ_MODEL="model-name";
```

2. Set them in the `.env` config file provided. Then, to make the `python-dotenv` module load them automatically, set the following environment variable:
```bash
export PY_ENV="DEVELOPMENT";
```

## Paraphrase

The paraphrase script `paraphrase.py` offers a CLI interface to specify various paraphrasing parameters. By default it uses gpt-4o (groq cloud is also available as an option).

Below is its CLI interface:
```
usage: paraphrase [-h] -c CONSTRAINTS [-l LABEL] [-o OUTPUT] [-d] [-g] [-t {fulltext,bysentence,nocot,bysentence_nocot}]
                  [-s {italian,english,russian}] [-r RETRIES]
                  input

Given a set of texts as input, performs text transformations to make the input text conform to given linguistic constraints.

positional arguments:
  input                 a TSV file containing the texts to paraphrase

options:
  -h, --help            show this help message and exit
  -c CONSTRAINTS, --constraints CONSTRAINTS
                        a plain-text file containing the linguistic constraints to follow when paraphrasing
  -l LABEL, --label LABEL
                        (optional) the label of the column that contains input data
  -o OUTPUT, --output OUTPUT
                        (optional) output file
  -d, --debug           (optional) log additional information
  -g, --groq            (optional) run on groq cloud
  -t {fulltext,bysentence,nocot,bysentence_nocot}, --type {fulltext,bysentence,nocot,bysentence_nocot}
                        (optional) how the paraphrase should be performed, default is fulltext
  -s {italian,english,russian}, --sentencizer {italian,english,russian}
                        language used to initialize the sentencizer (required if paraphrasing bysentence)
  -r RETRIES, --retries RETRIES
                        maximum number of retries if model fails to respond as expected
```

The parameters are, briefly:
- **input**: An **input** file, in **TSV format**, containing the **texts to paraphrase**
- **--constraints [file]**: A plain text/MD **constraints list** to paraphrase against (see the `./inventories` directory)
- **--label [str]**: This is the **TSV column label** that will be used to select the texts to paraphrase.
- **--output [file]**: (Optional) The paraphrase **output**, in **TSV format**
- **--debug**: (Optional) flag to output **debug data** (full messages dump, token usage, warnings, etc...)
- **--groq**: (Optional) if set, the script will use a groq hosted model. Remember to set a valid API key and model name in your environment.
- **--type [enum]**: (Optional) paraphrase type. Can be either fulltext (default), bysentece, nocot (without chain-of-thought prompting) or bysentence_nocot.
- **--sentencizer [enum]**: (Required if paraphrasing by sentence) This will be **used to initialize the SPACY sentencizer** (used to split the text into sentences).
- **--retries [int]**: (Optional) the maximim number of retries if the model responds with unparsable output. Default is 0.

An **input example**, in Italian:
```
text  language  words
Ho comprato cinque mele al mercato. italian 6
Il 3° piano è occupato dagli uffici. italian  7
Mia nonna ha 82 anni. italian 5
Sono arrivato secondo nella gara di nuoto. italian 7
Ci sono 12 mesi in un anno. italian 7
```

And this is a **usage example**, using constraints lists stored in `./inventories`:
```bash
python paraphrase.py input_file.tsv -c "./inventories/constraints_italian.md" -l "text" -s "italian" -t "fulltext" -r 1 -o output_file.tsv
```

### Retry Mechanism
The paraphrase script can be called with an optional **retries** parameter.

If a **number of retries** is set, when the model **responds** with a **malformed output** (in case this means the model fails to wrap the **final response** in `<text></text>` **tags**), the request will be made again at least **retries** times.

If the model still fails to give a valid response after **retries** times:
- if this happened at the **i-th** paraphrase iteration, the **last good paraphrase** will be used as output.
- if this happened at the **first** iterations, the "original text" will be used as output.

Descriptive **warning messages** will be visible in the **outputted TSV** if any of these events occur (remember to call the script with the `-d` flag)
- **ERROR**: The paraphrase failed after **retries** times at the **first** iteration (output is original text)
- **WARNING**: The paraphrase failed after **retries** times at the **i-th** iteration (output is the last known good paraphrase)

If the **paraphrase** is performed **sentence by sentence**, this behavior is applied for every sentence (and you will get a list of warnings for every sentence present in the original text).

**Closing note:** This mean that the **paraphrases** column of the outputted file will always contain text, being it a valid paraphrase or the original text. To check if something went wrong, check the messages contained in the **warnings** column.

## Eval (Grammar/Morphology)

The eval script `eval.py` performs a grammar/morphology analysis and evaluation on the basis of the contents of our A1 language inventories.

The CLI interface is very similar to the paraphrase script:
```
usage: eval [-h] -t TASKS -p {italian,english,russian} [-l LABEL] [-a] [-s] [-d] [-o OUTPUT] [-r RETRIES] input

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
  -r RETRIES, --retries RETRIES
                        (optional) number of allowed retries if model output is invalid
```

The parameters are, briefly:
- **input**: An **input** file, in **TSV format**, containing the **texts to evaluate**
- **--tasks [file]**: A **JSON** file defining **analysis tasks** (more info in the next sections)
- **--postagger [enum]**: This will be **used to initialize the postagger**.
- **--label [str]**: This is the **TSV column label** that will be used to select the texts to evaluate.
- **--output [file]**: (Optional) The evaulation **output**, in **TSV format**
- **--debug**: (Optional) flag to **output debug data** (token usage, warnings, etc...)
- **--analysis**: (Optional) if set, the script will just return linguistic annotations
- **--syntax**: (Optional) if set, the script will perform both grammar (default) and syntax analysis evaluation tasks.
- **--retries [int]**: (Optional) the maximim number of retries if the model responds with malformed output. Default is 0.

And this, as before, is a **usage example**, using tasks stored in `./analysis_tasks`:
```bash
python eval.py input_file.tsv -t "./analysis_tasks/italian_analysis_tasks.json" -l "text" -p "italian" -r 1 -o output_file.tsv
```

### Retry Mechanism
The eval script can be called with an optional **retries** parameter.

We expect the model to **respond** to each **analysis task** with a **JSON Schema compliant output**. If the model's response contains **invalid** or **malformed JSON** data, the request will be repeated **retries** times, and the model will be asked to **correct its last response**.

If the model still **fails** to respond properly after **retries** times, no data will be returned for the sub-task that failed.

Descriptive **warning messages** will be visible in the **outputted TSV** if any of these events occur (remember to call the script with the `-d` flag)
- **ERROR**: A sub-task failed **retries** times and no data was returned for that sub-task.
- **WARNING**: A sub-task succeded after **i-retries**.

### Analysis Task

An analysis task is a **user prompt** template, defining a **morphological information extraction** task, on an **input** text that we assume _has already been POS-tagged_.

An **example**, asking the model to **annotate** italian **pronouns**:

```
Given the following part-of-speech (POS) tagged text:

{input}

Extract and analyze the pronouns it contains.

Look for words tagged as "PRON" in the given input. List all pronoun instances, including repeated occurrences.

Respond with a structured JSON array conforming to the schema attached below. No additional comment or data is required.

{schema}
```

The **JSON schema** passed to the model is **used** both **to constrain its output** and to **validate it**. This is the one we used for pronouns checking.

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

The tasks **JSON** passed to the **eval** script contains a **collection** of tasks with their own:
- **template**
- **schema**
- (optionally) a set of **shots** to feed to the model

**Tasks** are subdivided in **syntax** and **grammar** sub-categories. A **tasks collection** is **structured** as shown below:
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

## Lexical Analyzer

The lexical analysis script `lexical_analyzer.py` uses the **stanza** python module to check texts against a level-stepped vocabulary (referred as wordlist).

The final output reports the vocabulary coverage on the given texts.

An optional JSON formatted stopwords list can be specified to pre-filter words from the given input.

Below is its CLI interface:
```
usage: lexical_analyzer [-h] -w WORDLIST -p {italian,english,russian} [-s STOPWORDS] [-l LABEL] [-c COMPARE] [-d] [-o OUTPUT] input

Checks the lexical content of input texts againts a given wordlist.

positional arguments:
  input                 a TSV file containing the texts to check

options:
  -h, --help            show this help message and exit
  -w WORDLIST, --wordlist WORDLIST
                        a JSON formatted wordlist to check againsts
  -p {italian,english,russian}, --postagger {italian,english,russian}
                        language used to initialize the postagger
  -s STOPWORDS, --stopwords STOPWORDS
                        (optional) a JSON formatted stopwords array
  -l LABEL, --label LABEL
                        (optional) the label of the column that contains input data
  -c COMPARE, --compare COMPARE
                        (optional) the label of the column that contains text to compare against
  -d, --dropdata        (optional) omit pos specific stats from output
  -o OUTPUT, --output OUTPUT
                        (optional) output file (TSV/XLSX)
```

The parameters are, briefly:
- **input**: An **input** file, in **TSV format**, containing the **texts to check**
- **--wordlist [file]**: A **JSON** formatted vocabulary to check coverage against.
- **--postagger [enum]**: This will be **used to initialize the stanza postagger**.
- **--wordlist [file]**: (Optional) A **JSON** string array containing stopwords to pre-filter.
- **--label [str]**: (Optional) This is the **TSV column label** that will be used to select the texts to evaluate.
- **--compare [str]**: (Optional) This is the **TSV column label** that will be used to select the texts to compare against. If this arg is set, the output will contain both the coverage for the texts listed under the column named **label** and the **compare** colum, in an alternate fashion.
- **--dropdata**: (Optional) flag to drop all pos-specific stats. If used the final output will contain only pos-aggregated coverage percentages, word lists and raw counts.
- **--output [file]**: The evaulation **output**, in **TSV/XLSX format**

The **--dropdata** flag and XLSX output format support have been added to generate more human-readable outputs. **XLSX** formatted outputs include **percentage coverage data coloured using a heatmap**. Additionally, the dropdata flag can be used to omit the pos broken down stats, keeping in only the aggregate, level-stepped coverage percentages, word lists, and raw counts.

Assuming we're using an input file containing the original and paraphrased texts, a **usage example** would look something like this:
```bash
python lexical_analyzer.py input_file.tsv -w ./inventories/word_lists/demauro.json -s ./inventories/stopwords/stopwords_italian.json -p italian -l text -c paraphrase
```

### Vocabularies (Word Lists)

The `lexical_analyzer.py` script uses **level stepped** vocabularies (referred as wordlist), ordered by complexity (either using CEFR levels, or other dictionary specific ).

Wordlists consist of **lemmas** grouped into **nouns**, **verbs**, **adjectives** and **adverbs** sub-categories.

These are the sources that were used to build the **wordlists** included in the `./inventories/word_lists` directory:
- **English**
    - **Oxford 3000** and **5000** [Here](https://www.oxfordlearnersdictionaries.com/about/wordlists/oxford3000-5000): These are available in split and merged format, both in the British English and American English format. Words are grouped by CEFR Level [A1 to C1]. Data was extracted from the PDF vocabulary files available on Oxford's website.
- **Italian**
    - **Università di Perugia - Profilo della lingua Italiana** [Here](https://www.unistrapg.it/profilo_lingua_italiana/site/index.html): Words are grouped by CEFR Level [A1 to B2]. Data was extracted and cleaned up from the official website.
    - **Il Nuovo vocabolario di base della lingua italiana - Tullio De Mauro** [Here](https://www.internazionale.it/opinione/tullio-de-mauro/2016/12/23/il-nuovo-vocabolario-di-base-della-lingua-italiana): Words are grouped into "Fondamentali", "Alto Uso" and "Alta Disponibilità" categories.

## Licenses
- This project includes the `udpipe2_client.py` script, that is part of the [UDPipe](https://github.com/ufal/udpipe/tree/udpipe-2) project. This is released under the Mozilla Public License V2. A full copy of said license is included in the `./licenses` directory.
- This project uses [Tint](https://dh.fbk.eu/research/tint/). Tint is released under the GNU General Public License (GPL) version 3. A full copy of said license is included in the `./licenses` directory.