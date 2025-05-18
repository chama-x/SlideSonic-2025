#!/bin/bash
# SlideSonic (2025) - Quick Installation Script
# https://github.com/chama-x/SlideSonic-2025

set -e

# Colors for terminal output
RESET="\033[0m"
BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
RED="\033[31m"

# Check if colors are supported
if [ -z "$TERM" ] || [ "$TERM" = "dumb" ]; then
    RESET=""
    BOLD=""
    GREEN=""
    YELLOW=""
    BLUE=""
    RED=""
fi

echo -e "${BOLD}${BLUE}SlideSonic (2025) - Installation Script${RESET}"
echo

# Check for git
if ! command -v git &>/dev/null; then
    echo -e "${RED}Git is not installed. Please install git first.${RESET}"
    exit 1
fi

# Check for Python
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.8 or higher.${RESET}"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
required_version="3.8"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Python version $python_version is not supported. Please install Python 3.8 or higher.${RESET}"
    exit 1
fi

# Create temporary directory
temp_dir=$(mktemp -d)
echo -e "${YELLOW}Creating temporary directory: $temp_dir${RESET}"

# Clone the repository
echo -e "${GREEN}Downloading SlideSonic...${RESET}"
git clone https://github.com/chama-x/SlideSonic-2025.git "$temp_dir/SlideSonic-2025"

# Navigate to the directory
cd "$temp_dir/SlideSonic-2025"

# Create target installation directory
install_dir="$HOME/SlideSonic-2025"
echo -e "${YELLOW}Installing to: $install_dir${RESET}"

# Check if directory already exists
if [ -d "$install_dir" ]; then
    echo -e "${RED}Directory $install_dir already exists.${RESET}"
    read -p "Overwrite? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Installation aborted.${RESET}"
        exit 1
    fi
    rm -rf "$install_dir"
fi

# Copy files to installation directory
mkdir -p "$install_dir"
cp -r ./* "$install_dir/"

# Make launcher script executable
chmod +x "$install_dir/slidesonic"

# Create virtual environment and install dependencies
echo -e "${GREEN}Setting up environment...${RESET}"
cd "$install_dir"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r config/requirements.txt

# Create symlink in user's bin directory if it exists and is in PATH
bin_dir="$HOME/.local/bin"
if [[ ":$PATH:" == *":$bin_dir:"* ]]; then
    mkdir -p "$bin_dir"
    ln -sf "$install_dir/slidesonic" "$bin_dir/slidesonic"
    echo -e "${GREEN}Created symlink in $bin_dir${RESET}"
fi

# Clean up
echo -e "${YELLOW}Cleaning up...${RESET}"
rm -rf "$temp_dir"

echo
echo -e "${BOLD}${GREEN}Installation successful!${RESET}"
echo
echo -e "You can now run SlideSonic with:${BOLD}"
echo -e "  $install_dir/slidesonic${RESET}"

if [[ ":$PATH:" == *":$bin_dir:"* ]]; then
    echo -e "Or simply:${BOLD}"
    echo -e "  slidesonic${RESET}"
fi

echo
echo -e "${YELLOW}For more information, visit: https://github.com/chama-x/SlideSonic-2025${RESET}" 