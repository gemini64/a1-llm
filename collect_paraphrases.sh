#!/bin/bash

# script variables
PY_ENV="./.venv"

SKIP_PARAPHRASE=false; # set to true to skip par
SKIP_EVAL=false; # set to true to skip eval

INPUT_DATA="./it_10_sentences.tsv"; # this is the file that gets passed to paraphrase.py
OUTPUT_DIR="./it_10_sentences";
PARAPHRASE_OUTPUT="${OUTPUT_DIR}/paraphrase.tsv"; # set to input file path if you're skipping par
EVAL_OUTPUT="eval.tsv";

PARAPHRASE_COL_LABEL="text"; # the column that contains the text to paraphrase
EVAL_COL_LABEL="paraphrases"; # the column that contains the text to evaluate, default is "paraphrases"

PARAPHRASE_SCRIPT="./paraphrase.py";
PARAPHRASE_FLAGS="-d";
PARAPHRASE_CONSTRAINTS="./inventories/constraints_italian_grammar_only.md";

EVAL_SCRIPT="./eval.py";
EVAL_FLAGS="-d";
EVAL_TASKS="./analysis_tasks/italian_analysis_tasks.json";
LANGUAGE="italian";

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
echo -e "${LIGHT_BLUE}[1/5]${NC} - ${GREEN}Activating venv${NC}";
source "${PY_ENV}/bin/activate";

# set-up directories
echo -e "${LIGHT_BLUE}[2/5]${NC} - ${GREEN}Setting-up filesystem${NC}";
mkdir -p "${OUTPUT_DIR}";

# set groq env variables
echo -e "${LIGHT_BLUE}[3/5]${NC} - ${GREEN}Setting-up groq cloud env variables${NC}";
if [ ! -z "${GROQ_KEY}" ]; then
    export GROQ_API_KEY="${GROQ_KEY}";
fi
if [ ! -z "${GROQ_MODEL}" ]; then
    export GROQ_MODEL="${GROQ_MODEL_NAME}";
fi

# paraphrase
echo -e "${LIGHT_BLUE}[4/5]${NC} - ${GREEN}Paraphrase${NC}";
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
echo -e "${LIGHT_BLUE}[5/5]${NC} - ${GREEN}Evaluation${NC}";
if [ "${SKIP_EVAL}" = true ]; then
    echo -e "Skipped eval";
else
    if [ -z "${EVAL_FLAGS}" ]; then
        python "${EVAL_SCRIPT}" "${PARAPHRASE_OUTPUT}" -t "${EVAL_TASKS}" -p "${LANGUAGE}" -l "${EVAL_COL_LABEL}" -o "${OUTPUT_DIR}/${EVAL_OUTPUT}";
    else
        python "${EVAL_SCRIPT}" "${PARAPHRASE_OUTPUT}" -t "${EVAL_TASKS}" -p "${LANGUAGE}" -l "${EVAL_COL_LABEL}" -o "${OUTPUT_DIR}/${EVAL_OUTPUT}" ${EVAL_FLAGS};
    fi
fi

# exit
deactivate;
echo -e "${LIGHT_BLUE}[DONE]${NC} - ${GREEN}See output in '$OUTPUT_DIR'${NC}";