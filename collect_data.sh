#!/bin/bash

# script variables
PY_ENV="./.venv"

SKIP_PARAPHRASE=false; # set to true to skip par
SKIP_EVAL=false; # set to true to skip eval
SKIP_LEXICAL=false; # set to true to skip lexical analysis

# non-optional, supported are ["italian", "english", "russian"]
LANGUAGE="english";

INPUT_DATA="./en_sample.tsv"; # this is the file that gets passed to paraphrase.py
OUTPUT_DIR="./en_sample";
PARAPHRASE_OUTPUT="${OUTPUT_DIR}/paraphrase.tsv"; # set to input file path if you're skipping par
EVAL_OUTPUT="${OUTPUT_DIR}/eval.tsv";
LEXICAL_OUTPUT="${OUTPUT_DIR}/lexical.tsv";

PARAPHRASE_COL_LABEL="text"; # the column that contains the text to paraphrase, default is "text"
EVAL_COL_LABEL="paraphrase"; # the column that contains the text to evaluate, default is "text"
LEXICAL_COL_LABEL="text"; # the column that contains the text to analyze, default is "text"

PARAPHRASE_SCRIPT="./paraphrase.py";
PARAPHRASE_FLAGS="-d -r 1";
PARAPHRASE_CONSTRAINTS="./inventories/constraints_english_grammar_only.md";

EVAL_SCRIPT="./eval.py";
EVAL_FLAGS="-d -r 1";
EVAL_TASKS="./analysis_tasks/english_analysis_tasks.json";

LEXICAL_SCRIPT="./lexical_analyzer.py";
LEXICAL_WORDLIST="./inventories/word_lists/oxford_3000_plus_5000.json";
LEXICAL_STOPWORDS="./inventories/stopwords/stopwords_english.json";

# groq key and model name, used only if paraphrase
# is called with -g flag
GROQ_KEY=""; # leave empty to use local .env setting
GROQ_MODEL_NAME=""; # leave empty to use local .env setting

# colors for readability
GREEN='\033[0;32m';
LIGHT_BLUE='\033[1;34m';
YELLOW='\033[0;33m';
RED='\033[0;31m';
NC='\033[0m'; # No Color

# activate venv
echo -e "${LIGHT_BLUE}[1/6]${NC} - ${GREEN}Activating venv${NC}";
source "${PY_ENV}/bin/activate";

# set-up directories
echo -e "${LIGHT_BLUE}[2/6]${NC} - ${GREEN}Setting-up filesystem${NC}";
mkdir -p "${OUTPUT_DIR}";

# set groq env variables
echo -e "${LIGHT_BLUE}[3/6]${NC} - ${GREEN}Setting-up groq cloud env variables${NC}";
if [ ! -z "${GROQ_KEY}" ]; then
    export GROQ_API_KEY="${GROQ_KEY}";
fi
if [ ! -z "${GROQ_MODEL_NAME}" ]; then
    export GROQ_MODEL="${GROQ_MODEL_NAME}";
fi

# paraphrase
echo -e "${LIGHT_BLUE}[4/6]${NC} - ${GREEN}Paraphrase${NC}";
if [ "${SKIP_PARAPHRASE}" = true ]; then
    echo -e "Skipped paraphrase";
else
    if [ -z "${PARAPHRASE_FLAGS}" ]; then
        python "${PARAPHRASE_SCRIPT}" "${INPUT_DATA}" -c "${PARAPHRASE_CONSTRAINTS}" -l "${PARAPHRASE_COL_LABEL}" -s "${LANGUAGE}" -o "${PARAPHRASE_OUTPUT}";
    else
        python "${PARAPHRASE_SCRIPT}" "${INPUT_DATA}" -c "${PARAPHRASE_CONSTRAINTS}" -l "${PARAPHRASE_COL_LABEL}" -s "${LANGUAGE}" -o "${PARAPHRASE_OUTPUT}" ${PARAPHRASE_FLAGS};
    fi
fi

# eval
echo -e "${LIGHT_BLUE}[5/6]${NC} - ${GREEN}Evaluation${NC}";
if [ "${SKIP_EVAL}" = true ]; then
    echo -e "Skipped eval";
else
    if [ -z "${EVAL_FLAGS}" ]; then
        python "${EVAL_SCRIPT}" "${PARAPHRASE_OUTPUT}" -t "${EVAL_TASKS}" -p "${LANGUAGE}" -l "${EVAL_COL_LABEL}" -o "${EVAL_OUTPUT}";
    else
        python "${EVAL_SCRIPT}" "${PARAPHRASE_OUTPUT}" -t "${EVAL_TASKS}" -p "${LANGUAGE}" -l "${EVAL_COL_LABEL}" -o "${EVAL_OUTPUT}" ${EVAL_FLAGS};
    fi
fi

# lexical
echo -e "${LIGHT_BLUE}[6/6]${NC} - ${GREEN}Lexical Analysis${NC}";
if [ "${SKIP_LEXICAL}" = true ]; then
    echo -e "Skipped lexical analysis";
else
    python "${LEXICAL_SCRIPT}" "${EVAL_OUTPUT}" -w "${LEXICAL_WORDLIST}" -s "${LEXICAL_STOPWORDS}" -p "${LANGUAGE}" -l "${LEXICAL_COL_LABEL}" -o "${LEXICAL_OUTPUT}";
fi

# exit
deactivate;
echo -e "${LIGHT_BLUE}[DONE]${NC} - ${GREEN}See output in '$OUTPUT_DIR'${NC}";