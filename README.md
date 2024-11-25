# A1 LLM

## Contents
- `analysis_tasks/*`: JSON/MD Italian analysis tasks (see **eval_rulebased_it.py**)
- `eval_tasks/*`: JSON/MD boolean evaluation tasks (see **eval_boolean_tests.py**)
- `inventories/*`: Markdown/plain-text language inventories.
- `schemas/*`: JSON schemas describing various objects. Used for prompting and data validation.
- `shots/*`: A list of labeled examples (in JSON format) to provide for the LLM-driven evaluation (see **eval_boolean.py**).
- `tools/*`: External binary tools.
- `eval_boolean.py`: Evaluation script. Takes a prompts/completions TSV and perform an LLM-based binary (true/false) evaluation. Returns an extendend TSV file as output.
- `eval_boolean_test.py`: Evaluation script. Takes a prompts/completions TSV and perform an LLM-based binary (true/false) evaluation based on a set of evaluation tasks. Returns an extendend TSV file as output.
- `eval_rulebased_it.py`: Evaluation script. Takes a prompts/completions TSV and perform an LLM-based evaluation based on grammar/syntactical rules. Only for italian text evaluation.
- `infer.py`: Inference script. Given a list of user prompts in JSON format, forwards them to a LLM and returns a TSV prompts/completions file as output.
- `gen.py`: Given a set of tasks, generates and returns the related prompts.
- `data_model.py`: Pydantic defined data models.
- `parsers.py`: Parsers to validate analysis data based on grammar/syntactical rules.
- `pos_tagger/py`: A python module that defines a part-of-speech tagger (supports various languages and tagging methods).
- `tasks.json`: A collection of Task objects. See the task.json schema for more info. Used to generate prompts.
- `install.sh`: Simple install script. Sets up the python environment, installs requirements and generates the prompt lists for all languages.
- `collect_data.sh`: A bash script to collect inference data from lorax hosted LLMs in batches.

## Project setup
A bash script is included to set-up the python environment and install the project requirements.

Clone this repository, `cd` to its `root directory`, and follow these steps:
```
chmod +x install.sh
./install.sh
```

To activate the **python venv**, assuming you're either on a macOS or Linux host:
```
source ./.venv/bin/activate
```

### Setting API Keys and Connection URLs
To run the **inference** and **evaluation** script you will need to set the **OPENAI_API_KEY**, **GROQ_API_KEY**, **GROQ_MODEL** and **LORAX_ENDPOINT** environment variables (depending on the LLM models you will use).

To do this you can either:
1. Set them manually (`export VAR="value"`)
2. Set them in the `.env` config file. Then remember to run the following command to tell the scripts you want to load variables from a local settings file:
```
export PY_ENV="DEVELOPMENT"
```
## Inference
The inference script `infer.py` is a simple cli utility. By default it uses gpt4-o to collect data. Authentication happens via api key using the langchain openai module.

To use a **lorax-server**/**groq** hosted model, call the script using the `-l` or `-g` flags.
```
usage: infer [-h] [-l] [-o OUTPUT] [-s SAMPLES] input

Forwards a list of user prompts to a openai/groq/lorax-hosted LLM

positional arguments:
  input                 an input json file

options:
  -h, --help            show this help message and exit
  -l, --lorax
  -g, --groq
  -o OUTPUT, --output OUTPUT
                        (optional) output file
  -s SAMPLES, --samples SAMPLES
                        (optional) the number of samples to collect [0-100]
```

### Collecting data in batches (lorax/groq)
A bash script is available to collect inference data using groq/lorax-hosted models in batches for all languages.

#### Lorax
To use the `collect_data.sh` script:
1. Clone and set-up the project (see the **Project setup** section of this README).
2. Open the `collect_data.sh` script with an editor and set the **OUTPUT_DIR** and **LORAX_URL** variables. Also set the value of **PY_SCRIPT_OPTIONS** to `"-l"`.
3. Ensure your **lorax-server** instance is available and running.
4. From the `root directory` of this project run:
```
chmod +x ./collect_data.sh
./collect_data.sh
```

#### Groq
To use the `collect_data.sh` script:
1. Clone and set-up the project (see the **Project setup** section of this README).
2. Open the `collect_data.sh` script with an editor and set the **OUTPUT_DIR**, **GROQ_KEY** and **GROQ_MODEL_NAME** variables. Also set the value of **PY_SCRIPT_OPTIONS** to `"-g"`.
3. From the `root directory` of this project run:
```
chmod +x ./collect_data.sh
./collect_data.sh
```