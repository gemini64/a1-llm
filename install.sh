#!/bin/bash

# init variable
PY_EXE ="/opt/homebrew/bin/python3.11";
PY_ENV=".venv";
ENV_TEMPLATE="./.env_sample";
ENV_TARGET="./.env";
TOOLS_DIR="./tools";
TINT_PKG="./tint.tar.gz";
TINT_URL="https://dhsite.fbk.eu/tint-release/0.3/tint-0.3-complete.tar.gz";
PY_REQUIREMENTS="./requirements.txt"

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
echo -e "${LIGHT_BLUE}[1/4]${NC} - ${GREEN}Setting up .env local settings${NC}";
if [ ! -f "$ENV_TARGET" ]; then
    cp "$ENV_TEMPLATE" "$ENV_TARGET";
fi

# venv
echo -e "${LIGHT_BLUE}[2/4]${NC} - ${GREEN}Setting up python venv${NC}";
if [ ! -d "${PY_ENV}" ]; then
    ${PY_EXE} -m venv "${PY_ENV}";
fi
source "${PY_ENV}/bin/activate";

# other requirements
echo -e "${LIGHT_BLUE}[3/4]${NC} - ${GREEN}Installing python requirements${NC}";
pip install --upgrade pip;
pip install -r "${PY_REQUIREMENTS}";

# install tint
echo -e "${LIGHT_BLUE}[4/4]${NC} - ${GREEN}Fetching Tint binaries${NC}";
mkdir "${TOOLS_DIR}";
curl -L "${TINT_URL}" -o "${TINT_PKG}";
tar -xf "${TINT_PKG}" -C "${TOOLS_DIR}";
rm "${TINT_PKG}";

# exit
deactivate;
echo -e "${LIGHT_BLUE}[DONE]${NC} - ${GREEN}Remember to activate the venv!${NC}"