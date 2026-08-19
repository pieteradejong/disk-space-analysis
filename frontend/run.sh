#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

echo -e "${GREEN}🚀 TypeScript Web Development${RESET}"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${RED}❌ Dependencies not installed. Run ./init.sh first${RESET}"
    exit 1
fi

# Function to show help
show_help() {
    echo -e "${GREEN}TypeScript Web Development Commands${RESET}"
    echo ""
    echo -e "Usage: ./run.sh [command]"
    echo ""
    echo -e "${GREEN}Commands:${RESET}"
    echo -e "  ${GREEN}dev${RESET}     - Start development server (default)"
    echo -e "  ${GREEN}build${RESET}   - Build for production"
    echo -e "  ${GREEN}preview${RESET} - Preview production build"
    echo -e "  ${GREEN}test${RESET}    - Run Vitest"
    echo -e "  ${GREEN}lint${RESET}    - Run ESLint"
    echo -e "  ${GREEN}format${RESET}  - Format code with Prettier"
    echo -e "  ${GREEN}help${RESET}    - Show this help message"
}

# Parse command
case "${1:-dev}" in
    "dev"|"start"|"")
        echo -e "${GREEN}🌐 Starting development server...${RESET}"
        echo -e "${GREEN}Server will be available at: http://localhost:5173${RESET}"
        echo -e "${GREEN}Press Ctrl+C to stop the server${RESET}"
        npm run dev
        ;;
    "build")
        echo -e "${GREEN}🏗️ Building for production...${RESET}"
        npm run build
        echo -e "${GREEN}✅ Build complete! Check the dist/ directory${RESET}"
        ;;
    "preview")
        echo -e "${GREEN}👀 Previewing production build...${RESET}"
        npm run preview
        ;;
    "test")
        echo -e "${GREEN}🧪 Running Vitest...${RESET}"
        npm run test
        ;;
    "lint")
        echo -e "${GREEN}🔍 Running ESLint...${RESET}"
        npm run lint
        ;;
    "format")
        echo -e "${GREEN}✨ Formatting code...${RESET}"
        npm run format
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${RESET}"
        echo -e "Run ${GREEN}./run.sh help${RESET} for available commands"
        exit 1
        ;;
esac