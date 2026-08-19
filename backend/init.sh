#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m'

echo -e "${GREEN}🚀 Python FastAPI Minimal MVP - Initialization${RESET}"

# Check Python version
check_python_version() {
    local min_version="3.11.0"
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is not installed${RESET}"
        exit 1
    fi
    
    local current_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
    echo -e "${GREEN}✅ Python version $current_version${RESET}"
}

# Check Python version
check_python_version

# Create virtual environment
echo -e "${GREEN}🐍 Creating virtual environment...${RESET}"
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo -e "${GREEN}📦 Upgrading pip...${RESET}"
python -m pip install --upgrade pip

# Install dependencies
echo -e "${GREEN}📦 Installing dependencies...${RESET}"
pip install -r requirements.txt

# Create .env file from template if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${GREEN}📋 Creating .env file...${RESET}"
    cp .env.template .env
    echo -e "${GREEN}✅ Edit .env file with your configuration${RESET}"
fi

echo -e "${GREEN}✅ Initialization complete!${RESET}"
echo -e "${GREEN}To activate virtual environment: source venv/bin/activate${RESET}"
echo -e "${GREEN}To start development server: ./run.sh${RESET}"