#!/bin/bash
# script variables
SAMPLES=100;
PROMPTS_DIR="./prompts";
OUTPUT_DIR="./results";
LORAX_URL="http://127.0.0.1:8080";
PY_SCRIPT="./infer.py";
PY_SCRIPT_OPTIONS="-l";

# colors for readability
GREEN='\033[0;32m';
LIGHT_BLUE='\033[1;34m';
YELLOW='\033[0;33m';
RED='\033[0;31m';
NC='\033[0m'; # No Color

# activate venv
echo -e "${LIGHT_BLUE}[1/3]${NC} - ${GREEN}Activating venv${NC}";
source ./.venv/bin/activate;

# set-up directories
echo -e "${LIGHT_BLUE}[2/3]${NC} - ${GREEN}Setting-up filesystem and variables${NC}";
mkdir -p "${OUTPUT_DIR}";
export LORAX_ENDPOINT="${LORAX_URL}";

# run script
echo -e "${LIGHT_BLUE}[3/3]${NC} - ${GREEN}Running script${NC}";
for filename in "${PROMPTS_DIR}"/*.json; do
    python "${PY_SCRIPT}" "$filename" "${PY_SCRIPT_OPTIONS}" -s "${SAMPLES}" -o "${OUTPUT_DIR}/$(basename "$filename" .json)_results.tsv";
done

# exit
deactivate;
echo -e "${LIGHT_BLUE}[DONE]${NC} - ${GREEN}See output in '$OUTPUT_DIR'${NC}"