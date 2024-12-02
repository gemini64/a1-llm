#!/bin/bash
PY_VENV=".venv";
ENV_TEMPLATE="./.env_sample";
ENV_TARGET="./.env";
GEN_SCRIPT="./gen.py"
TOOLS_DIR="./tools";
TINT_PKG="./tint.tar.gz";
TINT_URL="https://dhsite.fbk.eu/tint-release/0.3/tint-0.3-complete.tar.gz";
REQUIREMENTS_LINUX="./requirements.txt"
REQUIREMENTS_DARWIN="./requirements_darwin.txt"

# check os
if ! ( [[ "$OSTYPE" == "linux-gnu"* ]] | [[ "$OSTYPE" == "darwin"* ]] ); then
    echo "Error! Unsupported OS";
    exit 2;
fi

# colors for readability
GREEN='\033[0;32m';
LIGHT_BLUE='\033[1;34m';
YELLOW='\033[0;33m';
RED='\033[0;31m';
NC='\033[0m'; # No Color

# local settings
echo -e "${LIGHT_BLUE}[1/5]${NC} - ${GREEN}Setting up .env local settings${NC}";
if [ ! -f "$ENV_TARGET" ]; then
    cp "$ENV_TEMPLATE" "$ENV_TARGET";
fi

# venv
echo -e "${LIGHT_BLUE}[2/5]${NC} - ${GREEN}Setting up python venv${NC}";
python3 -m venv "$PY_VENV";
source "${PY_VENV}"/bin/activate;

# other requirements
echo -e "${LIGHT_BLUE}[3/5]${NC} - ${GREEN}Installing requirements${NC}";
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    pip install -r "${REQUIREMENTS_LINUX}";
else
    pip install -r "${REQUIREMENTS_DARWIN}";
fi

# generate prompts
echo -e "${LIGHT_BLUE}[4/5]${NC} - ${GREEN}Generating user prompts${NC}";
python "${GEN_SCRIPT}";

# install tint
echo -e "${LIGHT_BLUE}[5/5]${NC} - ${GREEN}Fetching tint binary${NC}";
mkdir "${TOOLS_DIR}";
curl -L "${TINT_URL}" -o "${TINT_PKG}";
tar -xf "${TINT_PKG}" -C "${TOOLS_DIR}";
rm "${TINT_PKG}";

# exit
deactivate;
echo -e "${LIGHT_BLUE}[DONE]${NC} - ${GREEN}Remember to activate the venv!${NC}"