#!/bin/bash
# Watchdog Launcher Startup Script
# This script checks for a virtual environment, creates one if needed, and launches the application

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Define venv path
VENV_PATH="$SCRIPT_DIR/venv"
VENV_PYTHON="$VENV_PATH/bin/python"
VENV_ACTIVATE="$VENV_PATH/bin/activate"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
LAUNCHER_SCRIPT="$SCRIPT_DIR/watchdogd-launcher.py"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if venv exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating new venv...${NC}"
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment. Please ensure Python 3 is installed.${NC}"
        read -p "Press Enter to exit"
        exit 1
    fi
    
    echo -e "${GREEN}Virtual environment created successfully.${NC}"
    
    # Install dependencies
    if [ -f "$REQUIREMENTS_FILE" ]; then
        echo -e "${YELLOW}Installing dependencies...${NC}"
        "$VENV_PYTHON" -m pip install --upgrade pip
        "$VENV_PYTHON" -m pip install -r "$REQUIREMENTS_FILE"
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to install dependencies.${NC}"
            read -p "Press Enter to exit"
            exit 1
        fi
        
        echo -e "${GREEN}Dependencies installed successfully.${NC}"
    fi
else
    echo -e "${GREEN}Virtual environment found.${NC}"
    
    # Check if requirements.txt has been updated (optional check)
    if [ -f "$REQUIREMENTS_FILE" ]; then
        if [ "$REQUIREMENTS_FILE" -nt "$VENV_PATH" ]; then
            echo -e "${YELLOW}Requirements file has been updated. Reinstalling dependencies...${NC}"
            "$VENV_PYTHON" -m pip install -r "$REQUIREMENTS_FILE"
        fi
    fi
fi

# Launch the application
echo -e "${CYAN}Starting Watchdog Launcher...${NC}"
"$VENV_PYTHON" "$LAUNCHER_SCRIPT"

# If the application exits with an error, pause to show the error message
if [ $? -ne 0 ]; then
    echo -e "\n${RED}Application exited with error code: $?${NC}"
    read -p "Press Enter to exit"
fi

