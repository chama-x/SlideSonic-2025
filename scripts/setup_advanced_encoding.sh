#!/bin/bash
# SlideSonic (2025) - Setup Script
# https://github.com/chama-x/SlideSonic-2025

# Colors and styling
RESET="\033[0m"
BOLD="\033[1m"
BLUE="\033[38;5;32m"
GRAY="\033[38;5;242m"
LIGHT_GRAY="\033[38;5;248m"
GREEN="\033[38;5;35m"
YELLOW="\033[38;5;220m"
RED="\033[38;5;196m"
CYAN="\033[38;5;87m"

# Check if we're running in a terminal that supports colors
USE_COLORS=true
if [ -z "$TERM" ] || [ "$TERM" = "dumb" ]; then
    USE_COLORS=false
fi

# Function to print styled text with fallback for non-color terminals
print_styled() {
    local style="$1"
    local text="$2"
    
    if [ "$USE_COLORS" = true ]; then
        echo -e "${style}${text}${RESET}"
    else
        echo "$text"
    fi
}

# Function to draw a divider
draw_divider() {
    local width=$(tput cols 2>/dev/null || echo 80)
    if [ "$USE_COLORS" = true ]; then
        printf "${GRAY}"
        printf "%.${width}s" "─"
        printf "${RESET}\n"
    else
        printf "%.${width}s" "-"
        printf "\n"
    fi
}

# Function to center text
center_text() {
    local text="$1"
    local width=$(tput cols 2>/dev/null || echo 80)
    local padding=$(( (width - ${#text}) / 2 ))
    if [ "$USE_COLORS" = true ]; then
        printf "%${padding}s${BOLD}${BLUE}%s${RESET}%${padding}s\n" "" "$text" ""
    else
        printf "%${padding}s%s%${padding}s\n" "" "$text" ""
    fi
}

# Check for Python 3
check_python() {
    print_styled "${BOLD}" "Checking for Python 3..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        print_styled "${GREEN}" "✓ Found Python $PYTHON_VERSION"
        return 0
    else
        print_styled "${RED}" "✗ Python 3 not found"
        print_styled "${GRAY}" "Please install Python 3.8 or later to continue."
        print_styled "${GRAY}" "Visit: https://www.python.org/downloads/"
        exit 1
    fi
}

# Check for FFmpeg
check_ffmpeg() {
    print_styled "${BOLD}" "Checking for FFmpeg..."
    
    if command -v ffmpeg &> /dev/null; then
        FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -n 1 | awk '{print $3}')
        print_styled "${GREEN}" "✓ Found FFmpeg $FFMPEG_VERSION"
        return 0
    else
        print_styled "${RED}" "✗ FFmpeg not found"
        print_styled "${GRAY}" "FFmpeg is required for encoding videos."
        
        # Offer to install FFmpeg based on platform
        if [ "$(uname)" = "Darwin" ]; then
            print_styled "${YELLOW}" "Would you like to install FFmpeg using Homebrew? (y/n)"
            read -p "$(print_styled "${BLUE}" "▶") " INSTALL_FFMPEG
            
            if [[ $INSTALL_FFMPEG == "y" || $INSTALL_FFMPEG == "Y" ]]; then
                # Check if Homebrew is installed
                if command -v brew &> /dev/null; then
                    print_styled "${GRAY}" "Installing FFmpeg with Homebrew..."
                    brew install ffmpeg
                    if [ $? -eq 0 ]; then
                        print_styled "${GREEN}" "✓ FFmpeg installed successfully"
                        return 0
                    else
                        print_styled "${RED}" "✗ Failed to install FFmpeg"
                        exit 1
                    fi
                else
                    print_styled "${YELLOW}" "Homebrew not found. Would you like to install it? (y/n)"
                    read -p "$(print_styled "${BLUE}" "▶") " INSTALL_HOMEBREW
                    
                    if [[ $INSTALL_HOMEBREW == "y" || $INSTALL_HOMEBREW == "Y" ]]; then
                        print_styled "${GRAY}" "Installing Homebrew..."
                        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                        if [ $? -eq 0 ]; then
                            print_styled "${GREEN}" "✓ Homebrew installed successfully"
                            print_styled "${GRAY}" "Installing FFmpeg..."
                            brew install ffmpeg
                            if [ $? -eq 0 ]; then
                                print_styled "${GREEN}" "✓ FFmpeg installed successfully"
                                return 0
                            else
                                print_styled "${RED}" "✗ Failed to install FFmpeg"
                                exit 1
                            fi
                        else
                            print_styled "${RED}" "✗ Failed to install Homebrew"
                            exit 1
                        fi
                    else
                        print_styled "${GRAY}" "Please install FFmpeg manually and run this script again."
                        exit 1
                    fi
                fi
            else
                print_styled "${GRAY}" "Please install FFmpeg manually and run this script again."
                exit 1
            fi
        elif [ "$(uname)" = "Linux" ]; then
            # Detect Linux distribution
            if command -v apt-get &> /dev/null; then
                # Debian/Ubuntu
                print_styled "${YELLOW}" "Would you like to install FFmpeg using apt? (y/n)"
                read -p "$(print_styled "${BLUE}" "▶") " INSTALL_FFMPEG
                
                if [[ $INSTALL_FFMPEG == "y" || $INSTALL_FFMPEG == "Y" ]]; then
                    print_styled "${GRAY}" "Installing FFmpeg with apt..."
                    sudo apt-get update && sudo apt-get install -y ffmpeg
                    if [ $? -eq 0 ]; then
                        print_styled "${GREEN}" "✓ FFmpeg installed successfully"
                        return 0
                    else
                        print_styled "${RED}" "✗ Failed to install FFmpeg"
                        exit 1
                    fi
                else
                    print_styled "${GRAY}" "Please install FFmpeg manually and run this script again."
                    exit 1
                fi
            elif command -v dnf &> /dev/null; then
                # Fedora
                print_styled "${YELLOW}" "Would you like to install FFmpeg using dnf? (y/n)"
                read -p "$(print_styled "${BLUE}" "▶") " INSTALL_FFMPEG
                
                if [[ $INSTALL_FFMPEG == "y" || $INSTALL_FFMPEG == "Y" ]]; then
                    print_styled "${GRAY}" "Installing FFmpeg with dnf..."
                    sudo dnf install -y ffmpeg
                    if [ $? -eq 0 ]; then
                        print_styled "${GREEN}" "✓ FFmpeg installed successfully"
                        return 0
                    else
                        print_styled "${RED}" "✗ Failed to install FFmpeg"
                        exit 1
                    fi
                else
                    print_styled "${GRAY}" "Please install FFmpeg manually and run this script again."
                    exit 1
                fi
            else
                print_styled "${GRAY}" "Unable to detect package manager. Please install FFmpeg manually."
                exit 1
            fi
        elif [ "$(uname -o 2>/dev/null)" = "Msys" ] || [ "$(uname -o 2>/dev/null)" = "Cygwin" ] || [ "$OSTYPE" = "msys" ] || [ "$OSTYPE" = "cygwin" ]; then
            # Windows with MSYS/Cygwin
            print_styled "${GRAY}" "For Windows, please download FFmpeg from:"
            print_styled "${CYAN}" "https://ffmpeg.org/download.html#build-windows"
            print_styled "${GRAY}" "Add FFmpeg to your PATH and run this script again."
            exit 1
        else
            print_styled "${GRAY}" "Unknown operating system. Please install FFmpeg manually."
            exit 1
        fi
    fi
}

# Create and set up virtual environment
setup_venv() {
    print_styled "${BOLD}" "Setting up Python virtual environment..."
    
    # Check if venv already exists
    if [ -d "venv" ]; then
        print_styled "${YELLOW}" "Virtual environment already exists. Would you like to recreate it? (y/n)"
        read -p "$(print_styled "${BLUE}" "▶") " RECREATE
        
        if [[ $RECREATE == "y" || $RECREATE == "Y" ]]; then
            print_styled "${GRAY}" "Removing existing virtual environment..."
            rm -rf venv
        else
            print_styled "${GRAY}" "Using existing virtual environment."
            return 0
        fi
    fi
    
    # Create virtual environment
    print_styled "${GRAY}" "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        print_styled "${RED}" "✗ Failed to create virtual environment"
        print_styled "${GRAY}" "Make sure the 'venv' module is installed:"
        print_styled "${GRAY}" "  - Ubuntu/Debian: sudo apt-get install python3-venv"
        print_styled "${GRAY}" "  - Fedora: sudo dnf install python3-venv"
        print_styled "${GRAY}" "  - macOS: pip3 install virtualenv"
        exit 1
    fi
    
    print_styled "${GREEN}" "✓ Virtual environment created successfully"
    return 0
}

# Install Python dependencies
install_dependencies() {
    print_styled "${BOLD}" "Installing Python dependencies..."
    
    # Activate virtual environment
    source venv/bin/activate
    if [ $? -ne 0 ]; then
        print_styled "${RED}" "✗ Failed to activate virtual environment"
        exit 1
    fi
    
    # Upgrade pip
    print_styled "${GRAY}" "Upgrading pip..."
    pip install --upgrade pip &> /dev/null
    if [ $? -ne 0 ]; then
        print_styled "${YELLOW}" "⚠️ Failed to upgrade pip, continuing anyway..."
    fi
    
    # Install dependencies from requirements.txt
    if [ -f "requirements.txt" ]; then
        print_styled "${GRAY}" "Installing dependencies from requirements.txt..."
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            print_styled "${RED}" "✗ Failed to install dependencies"
            exit 1
        fi
    else
        print_styled "${YELLOW}" "⚠️ requirements.txt not found, installing core dependencies..."
        pip install pillow numpy psutil py-cpuinfo
        if [ $? -ne 0 ]; then
            print_styled "${RED}" "✗ Failed to install core dependencies"
            exit 1
        fi
    fi
    
    print_styled "${GREEN}" "✓ Dependencies installed successfully"
    return 0
}

# Create required directories
create_directories() {
    print_styled "${BOLD}" "Creating required directories..."
    
    mkdir -p images/original
    mkdir -p song
    mkdir -p temp
    mkdir -p screenshots
    mkdir -p logs
    
    print_styled "${GREEN}" "✓ Directories created successfully"
    return 0
}

# Set file permissions
set_permissions() {
    print_styled "${BOLD}" "Setting file permissions..."
    
    chmod +x slidesonic
    if [ -f "run_advanced_slideshow.sh" ]; then
        chmod +x run_advanced_slideshow.sh
    fi
    if [ -f "monitor_encoding.py" ]; then
        chmod +x monitor_encoding.py
    fi
    if [ -f "advanced_app.py" ]; then
        chmod +x advanced_app.py
    fi
    
    print_styled "${GREEN}" "✓ File permissions set successfully"
    return 0
}

# Main setup function
main() {
    clear
    center_text "SlideSonic (2025) Setup"
    draw_divider
    echo ""
    
    print_styled "${BOLD}" "Welcome to the SlideSonic setup script!"
    print_styled "${GRAY}" "This script will set up your environment for SlideSonic."
    echo ""
    
    check_python
    check_ffmpeg
    setup_venv
    install_dependencies
    create_directories
    set_permissions
    
    echo ""
    draw_divider
    print_styled "${GREEN}" "✓ SlideSonic setup completed successfully!"
    print_styled "${GRAY}" "You can now run SlideSonic by executing: ./slidesonic"
    echo ""
    
    exit 0
}

# Run the main function
main 