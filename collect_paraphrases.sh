#!/bin/bash
# script variables
INPUT_DATA="./it_10_sentences.tsv";
OUTPUT_DIR="./it_10_sentences";
PARAPHRASE_OUTPUT="paraphrases.tsv";
EVAL_OUTPUT="eval.tsv";

PARAPHRASE_COL_LABEL="text";
EVAL_COL_LABEL="paraphrases";

PARAPHRASE_SCRIPT="./paraphrase.py";
PARAPHRASE_FLAGS="-d";
PARAPHRASE_CONSTRAINTS="./inventories/constraints_italian_grammar_only.md";

EVAL_SCRIPT="./eval_rulebased.py";
EVAL_FLAGS="-d";
EVAL_TASKS="./analysis_tasks/italian_analysis_tasks.json";
LANGUAGE="italian";

# groq key and model name, used only if paraphrase
# is called with -g flag
GROQ_KEY="";
GROQ_MODEL_NAME="";

# colors for readability
GREEN='\033[0;32m';
LIGHT_BLUE='\033[1;34m';
YELLOW='\033[0;33m';
RED='\033[0;31m';
NC='\033[0m'; # No Color

# activate venv
echo -e "${LIGHT_BLUE}[1/4]${NC} - ${GREEN}Activating venv${NC}";
source ./.venv/bin/activate;

# set-up directories
echo -e "${LIGHT_BLUE}[2/4]${NC} - ${GREEN}Setting-up filesystem and env variables${NC}";
mkdir -p "${OUTPUT_DIR}";
export GROQ_API_KEY="${GROQ_KEY}";
export GROQ_MODEL="${GROQ_MODEL_NAME}";

# paraphrase
echo -e "${LIGHT_BLUE}[3/4]${NC} - ${GREEN}Paraphrase${NC}";
if [ -z "${PARAPHRASE_FLAGS}" ]; then
    python "${PARAPHRASE_SCRIPT}" "${INPUT_DATA}" -c "${PARAPHRASE_CONSTRAINTS}" -l "${PARAPHRASE_COL_LABEL}" -s "${LANGUAGE}" -o "${OUTPUT_DIR}/${PARAPHRASE_OUTPUT}";
else
    python "${PARAPHRASE_SCRIPT}" "${INPUT_DATA}" -c "${PARAPHRASE_CONSTRAINTS}" -l "${PARAPHRASE_COL_LABEL}" -s "${LANGUAGE}" -o "${OUTPUT_DIR}/${PARAPHRASE_OUTPUT}" "${PARAPHRASE_FLAGS}";
fi

# paraphrase
echo -e "${LIGHT_BLUE}[4/4]${NC} - ${GREEN}Evaluation${NC}";
if [ -z "${EVAL_FLAGS}" ]; then
    python "${EVAL_SCRIPT}" "${OUTPUT_DIR}/${PARAPHRASE_OUTPUT}" "${EVAL_TASKS}" -p "${LANGUAGE}" -l "${EVAL_COL_LABEL}" -o "${OUTPUT_DIR}/${EVAL_OUTPUT}";
else
    python "${EVAL_SCRIPT}" "${OUTPUT_DIR}/${PARAPHRASE_OUTPUT}" "${EVAL_TASKS}" -p "${LANGUAGE}" -l "${EVAL_COL_LABEL}" -o "${OUTPUT_DIR}/${EVAL_OUTPUT}" "${EVAL_FLAGS}";
fi

# exit
deactivate;
echo -e "${LIGHT_BLUE}[DONE]${NC} - ${GREEN}See output in '$OUTPUT_DIR'${NC}";