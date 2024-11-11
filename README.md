# A1 LLM

## Contents
- `references/*`: Markdown/plain-text language inventories.
- `schemas/*`: JSON schemas describing Tasks and Eval report objects. Useful for data validation.
- `eval.py`: Evaluation script. Takes a prompts/completions TSV and perform an LLM-based binary (true/false) evaluation.
- `infer.py`: Inference script. Given a list of user prompts in JSON format, forwards them to a LLM and returns a TSV prompts/completions output.
- `gen.py`: Given a set of tasks, generates and returns the related prompts.
- `data_model.py`: Pydantic defined data models.
- `install.sh`: Simple install script. Sets up the python environment, installs requirements and generates the prompt lists for all languages.

## Install
A bash script is included to set-up the python environment and install the project requirements.

Clone this repository, `cd` to its `root directory`, and follow these steps:
```
chmod +x install.sh
./install.sh
```

### Setting API Keys and Connection URLs
Open the `.env` file and set the **OPENAI_API_KEY** and **LORAX_ENDPOINT** variables.

If **running locally**, also remember to set the following ENV variable:
```
export PY_ENV="DEVELOPMENT"
```
