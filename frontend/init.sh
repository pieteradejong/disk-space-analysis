#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

echo -e "${GREEN}🚀 TypeScript Web Minimal MVP - Initialization${RESET}"

# Function to check Node.js version
check_node_version() {
    local min_version="18.0.0"
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js is not installed${RESET}"
        echo -e "Install Node.js 18+ from https://nodejs.org/"
        exit 1
    fi
    
    local current_version=$(node -v | cut -d'v' -f2)
    if [ "$(printf '%s\n' "$min_version" "$current_version" | sort -V | head -n1)" != "$min_version" ]; then
        echo -e "${RED}❌ Node.js version 18+ is required. Current: v$current_version${RESET}"
        exit 1
    fi
    echo -e "${GREEN}✅ Node.js version v$current_version${RESET}"
}

# Function to check npm/yarn
check_package_manager() {
    if command -v npm &> /dev/null; then
        echo -e "${GREEN}✅ npm is available${RESET}"
        PACKAGE_MANAGER="npm"
    else
        echo -e "${RED}❌ npm is not available${RESET}"
        exit 1
    fi
}

# Main initialization
echo -e "${GREEN}🔍 Checking prerequisites...${RESET}"
check_node_version
check_package_manager

echo -e "${GREEN}🧹 Cleaning up existing installation...${RESET}"
rm -rf node_modules
rm -f package-lock.json yarn.lock
find . -name "*.log" -delete

echo -e "${GREEN}📦 Installing dependencies...${RESET}"
npm install

echo -e "${GREEN}📋 Setting up environment...${RESET}"
if [ ! -f .env ]; then
    echo -e "${GREEN}Creating .env file...${RESET}"
    cp .env.template .env
    echo -e "${YELLOW}✅ Edit .env with your configuration${RESET}"
fi

echo -e "${GREEN}✅ Initialization complete!${RESET}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}🎉 Your TypeScript React app is ready!${RESET}"
echo -e ""
echo -e "${GREEN}Next steps:${RESET}"
echo -e "  1. ${YELLOW}./run.sh${RESET} - Start development server"
echo -e "  2. ${YELLOW}Open http://localhost:5173${RESET} in your browser"
echo -e ""
echo -e "${GREEN}Available commands:${RESET}"
echo -e "  ${GREEN}./run.sh${RESET}        - Start development server"
echo -e "  ${GREEN}./run.sh build${RESET}  - Build for production"
echo -e "  ${GREEN}./run.sh lint${RESET}   - Run linting"
echo -e "  ${GREEN}./run.sh format${RESET} - Format code"