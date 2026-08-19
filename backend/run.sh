#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m'

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Run ./init.sh first${RESET}"
    exit 1
fi

source venv/bin/activate

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

show_help() {
    echo -e "${GREEN}FastAPI Backend Commands${RESET}"
    echo ""
    echo -e "Usage: ./run.sh [command]"
    echo ""
    echo -e "${GREEN}Commands:${RESET}"
    echo -e "  ${GREEN}dev${RESET}    - Start development server (default)"
    echo -e "  ${GREEN}test${RESET}   - Run pytest"
    echo -e "  ${GREEN}help${RESET}   - Show this help message"
}

case "${1:-dev}" in
    "dev"|"start"|"")
        echo -e "${GREEN}🚀 Starting FastAPI Development Server${RESET}"
        echo -e "${GREEN}🌐 Server will be available at: http://localhost:${PORT:-8000}${RESET}"
        echo -e "${GREEN}📚 API docs will be available at: http://localhost:${PORT:-8000}/docs${RESET}"
        echo -e "${GREEN}Press Ctrl+C to stop the server${RESET}"
        uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --reload
        ;;
    "test")
        echo -e "${GREEN}🧪 Running pytest...${RESET}"
        pytest
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
