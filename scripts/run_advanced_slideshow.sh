#!/bin/bash
# SlideSonic (2025) - Advanced Slideshow Runner
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

# Display banner
display_banner() {
    clear
    print_styled "${BLUE}" "   _____ _ _     _      _____             _        _____ _____ _____ _____ "
    print_styled "${BLUE}" "  / ____| (_)   | |    / ____|           (_)      / ____|  __ \\_   _|  __ \\"
    print_styled "${BLUE}" " | (___ | |_  __| | ___| (___   ___  _ __ _  ___  | |    | |__) || | | |  | |"
    print_styled "${BLUE}" "  \\___ \\| | |/ _\` |/ _ \\\\___ \\ / _ \\| '__| |/ __| | |    |  ___/ | | | |  | |"
    print_styled "${BLUE}" "  ____) | | | (_| |  __/____) | (_) | |  | | (__  | |____| |    _| |_| |__| |"
    print_styled "${BLUE}" " |_____/|_|_|\\__,_|\\___|_____/ \\___/|_|  |_|\\___|  \\_____|_|   |_____|_____/"
    echo ""
    print_styled "${CYAN}${BOLD}" "                      Create stunning slideshow videos"
    echo ""
    print_styled "${GRAY}" "Version 2.5.0 | https://github.com/chama-x/SlideSonic-2025"
    echo ""
}

# Check dependencies
check_dependencies() {
    print_styled "${BOLD}" "Checking dependencies..."
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        print_styled "${RED}" "✗ Python 3 not found. Please install Python 3.8 or later."
        exit 1
    fi
    print_styled "${GREEN}" "✓ Python found: $(python3 --version 2>&1)"
    
    # Check for FFmpeg
    if ! command -v ffmpeg &> /dev/null; then
        print_styled "${RED}" "✗ FFmpeg not found. Please install FFmpeg."
        print_styled "${GRAY}" "Visit: https://ffmpeg.org/download.html"
        exit 1
    fi
    print_styled "${GREEN}" "✓ FFmpeg found: $(ffmpeg -version | head -n 1 | awk '{print $3}')"
    
    # Check for virtual environment
    if [ ! -d "venv" ]; then
        print_styled "${YELLOW}" "⚠️ Python virtual environment not found."
        print_styled "${GRAY}" "Running setup script..."
        if [ -f "setup_advanced_encoding.sh" ]; then
            bash setup_advanced_encoding.sh
        else
            print_styled "${RED}" "✗ Setup script not found. Please run setup manually."
            exit 1
        fi
    else
        print_styled "${GREEN}" "✓ Python virtual environment found"
        # Activate virtual environment
        source venv/bin/activate
    fi
}

# Check for images and audio files
check_content() {
    print_styled "${BOLD}" "Checking for content files..."
    
    # Create directories if they don't exist
    mkdir -p images/original
    mkdir -p song
    
    # Check for images
    image_count=$(find images/original -type f -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.gif" | wc -l)
    if [ "$image_count" -eq 0 ]; then
        print_styled "${RED}" "✗ No images found in images/original/ directory."
        print_styled "${GRAY}" "Please add your images to the images/original/ directory and try again."
        exit 1
    fi
    print_styled "${GREEN}" "✓ Found $image_count images in images/original/ directory"
    
    # Check for audio
    audio_count=$(find song -type f -name "*.mp3" -o -name "*.wav" -o -name "*.aac" -o -name "*.m4a" -o -name "*.flac" | wc -l)
    if [ "$audio_count" -eq 0 ]; then
        print_styled "${YELLOW}" "⚠️ No audio files found in song/ directory."
        print_styled "${GRAY}" "Would you like to continue without audio? (y/n)"
        read -p "$([[ "$USE_COLORS" = true ]] && echo -e "${BLUE}▶ ${RESET}" || echo "▶ ")" continue_without_audio
        
        if [[ ! "$continue_without_audio" =~ ^[Yy]$ ]]; then
            print_styled "${GRAY}" "Please add your audio file to the song/ directory and try again."
            exit 1
        fi
        
        audio_file=""
    else
        print_styled "${GREEN}" "✓ Found $audio_count audio file(s) in song/ directory"
        
        # If multiple audio files, ask which one to use
        if [ "$audio_count" -gt 1 ]; then
            print_styled "${GRAY}" "Available audio files:"
            audio_files=($(find song -type f -name "*.mp3" -o -name "*.wav" -o -name "*.aac" -o -name "*.m4a" -o -name "*.flac"))
            
            for i in "${!audio_files[@]}"; do
                file="${audio_files[$i]}"
                print_styled "${GRAY}" "$((i+1)). $(basename "$file")"
            done
            
            print_styled "${GRAY}" "Which audio file would you like to use? (1-$audio_count)"
            read -p "$([[ "$USE_COLORS" = true ]] && echo -e "${BLUE}▶ ${RESET}" || echo "▶ ")" audio_choice
            
            if ! [[ "$audio_choice" =~ ^[0-9]+$ ]] || [ "$audio_choice" -lt 1 ] || [ "$audio_choice" -gt "$audio_count" ]; then
                audio_choice=1
            fi
            
            audio_file="${audio_files[$((audio_choice-1))]}"
        else
            audio_file=$(find song -type f -name "*.mp3" -o -name "*.wav" -o -name "*.aac" -o -name "*.m4a" -o -name "*.flac" | head -n 1)
        fi
        
        print_styled "${CYAN}" "Selected audio: $(basename "$audio_file")"
    fi
}

# Generate slideshow with advanced encoding
create_slideshow() {
    local mode="$1"
    local title="$2"
    local resolution="$3"
    local output_file="$4"
    
    print_styled "${BOLD}" "Generating slideshow with advanced encoding..."
    
    # Set quality preset based on mode
    local preset=""
    case "$mode" in
        performance)
            preset="ultrafast"
            ;;
        standard)
            preset="medium"
            ;;
        ultra)
            preset="veryslow"
            ;;
        *)
            preset="medium" # Default to standard quality
            ;;
    esac
    
    print_styled "${CYAN}" "Title:      $title"
    print_styled "${CYAN}" "Resolution: $resolution"
    print_styled "${CYAN}" "Quality:    $preset"
    print_styled "${CYAN}" "Output:     $output_file"
    
    # Determine best encoder for the system
    local encoder="libx264" # Default encoder
    
    # Check for Apple Silicon with VideoToolbox
    if [[ "$(uname)" == "Darwin" && "$(uname -m)" == "arm64" ]]; then
        if ffmpeg -encoders 2>/dev/null | grep -q "h264_videotoolbox"; then
            encoder="h264_videotoolbox"
            print_styled "${GREEN}" "Using Apple Silicon hardware acceleration (VideoToolbox)"
        fi
    # Check for NVIDIA GPU
    elif ffmpeg -hwaccels 2>/dev/null | grep -q "cuda" && ffmpeg -encoders 2>/dev/null | grep -q "h264_nvenc"; then
        encoder="h264_nvenc"
        print_styled "${GREEN}" "Using NVIDIA hardware acceleration (NVENC)"
    # Check for Intel Quick Sync
    elif ffmpeg -hwaccels 2>/dev/null | grep -q "qsv" && ffmpeg -encoders 2>/dev/null | grep -q "h264_qsv"; then
        encoder="h264_qsv"
        print_styled "${GREEN}" "Using Intel hardware acceleration (Quick Sync)"
    # Check for VA-API
    elif ffmpeg -hwaccels 2>/dev/null | grep -q "vaapi" && ffmpeg -encoders 2>/dev/null | grep -q "h264_vaapi"; then
        encoder="h264_vaapi"
        print_styled "${GREEN}" "Using VA-API hardware acceleration"
    fi
    
    # Create necessary directories
    mkdir -p temp
    mkdir -p logs
    
    # Check if running in "dry run" mode
    if [ "$DRY_RUN" = true ]; then
        print_styled "${YELLOW}" "Dry run mode: not performing actual encoding"
        return 0
    fi
    
    # Create filelist.txt for FFmpeg
    print_styled "${GRAY}" "Creating file list..."
    
    local images=($(find images/original -type f -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.gif" | sort))
    local image_count=${#images[@]}
    
    # Get audio duration if audio file is available
    local audio_duration=0
    local slide_duration=3  # Default duration for each slide
    
    if [ -n "$audio_file" ]; then
        audio_duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$audio_file" 2>/dev/null)
        if [ $? -eq 0 ]; then
            # Calculate duration per slide
            slide_duration=$(echo "scale=2; $audio_duration / $image_count" | bc)
            print_styled "${GRAY}" "Audio duration: $audio_duration seconds"
            print_styled "${GRAY}" "Slide duration: $slide_duration seconds"
        else
            print_styled "${YELLOW}" "⚠️ Could not determine audio duration, using default"
        fi
    else
        # Calculate total duration based on default slide duration
        audio_duration=$(echo "scale=2; $image_count * $slide_duration" | bc)
        print_styled "${GRAY}" "No audio file. Total duration: $audio_duration seconds"
    fi
    
    # Create filelist.txt
    echo "" > temp/filelist.txt
    for img in "${images[@]}"; do
        echo "file '$(pwd)/$img'" >> temp/filelist.txt
        echo "duration $slide_duration" >> temp/filelist.txt
    done
    # Add last image again to avoid premature ending
    if [ ${#images[@]} -gt 0 ]; then
        echo "file '$(pwd)/${images[-1]}'" >> temp/filelist.txt
    fi
    
    print_styled "${GRAY}" "Starting encoding process..."
    
    # Log file for FFmpeg output
    local log_file="logs/ffmpeg_output.log"
    
    # Build FFmpeg command
    local ffmpeg_cmd="ffmpeg -y -f concat -safe 0 -i temp/filelist.txt"
    
    # Add audio if available
    if [ -n "$audio_file" ]; then
        ffmpeg_cmd+=" -i \"$audio_file\""
    fi
    
    # Add video encoding options
    ffmpeg_cmd+=" -c:v $encoder -preset $preset -crf 23 -pix_fmt yuv420p"
    
    # Add audio encoding options if audio is available
    if [ -n "$audio_file" ]; then
        ffmpeg_cmd+=" -c:a aac -b:a 192k -shortest"
    fi
    
    # Add output options
    ffmpeg_cmd+=" -s $resolution -r 30 -movflags +faststart \"$output_file\""
    
    # Print command
    print_styled "${GRAY}" "Command: $ffmpeg_cmd"
    
    # Run FFmpeg
    eval $ffmpeg_cmd 2>&1 | tee "$log_file"
    
    # Check if encoding was successful
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_styled "${GREEN}" "✓ Slideshow created successfully: $output_file"
        
        # Get file size
        if [ -f "$output_file" ]; then
            local file_size=$(du -h "$output_file" | cut -f1)
            print_styled "${GRAY}" "File size: $file_size"
            
            # Get video duration
            local video_duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$output_file" 2>/dev/null)
            if [ $? -eq 0 ]; then
                print_styled "${GRAY}" "Video duration: $video_duration seconds"
            fi
            
            print_styled "${GRAY}" "Log file: $log_file"
        else
            print_styled "${RED}" "✗ Output file not found despite successful encoding"
        fi
    else
        print_styled "${RED}" "✗ Encoding failed. Check log file for details: $log_file"
    fi
}

# Function to parse command line arguments and run with appropriate settings
run_with_settings() {
    local mode="standard"
    local title="SlideSonic Slideshow"
    local resolution="1920x1080"
    local output_file="slideshow_$(date +%Y%m%d_%H%M%S).mp4"
    local DRY_RUN=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        key="$1"
        case $key in
            --performance)
                mode="performance"
                shift
                ;;
            --standard)
                mode="standard"
                shift
                ;;
            --ultra)
                mode="ultra"
                shift
                ;;
            --title=*)
                title="${key#*=}"
                shift
                ;;
            --resolution=*)
                resolution="${key#*=}"
                shift
                ;;
            --output=*)
                output_file="${key#*=}"
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help)
                display_help
                exit 0
                ;;
            *)
                print_styled "${RED}" "Unknown option: $key"
                display_help
                exit 1
                ;;
        esac
    done
    
    # Display banner
    display_banner
    
    # Check dependencies
    check_dependencies
    
    # Check for content files
    check_content
    
    # Create slideshow
    create_slideshow "$mode" "$title" "$resolution" "$output_file"
    
    print_styled "${BOLD}${GREEN}" "Slideshow creation process completed"
}

# Display help information
display_help() {
    print_styled "${BOLD}" "SlideSonic (2025) - Advanced Slideshow Runner"
    echo ""
    print_styled "${BOLD}${BLUE}" "Usage:"
    print_styled "${GRAY}" "  ./run_advanced_slideshow.sh [options]"
    echo ""
    print_styled "${BOLD}${BLUE}" "Options:"
    print_styled "${GRAY}" "  --performance      Use maximum performance mode (faster, lower quality)"
    print_styled "${GRAY}" "  --standard         Use standard quality mode (balanced) [default]"
    print_styled "${GRAY}" "  --ultra            Use ultra high quality mode (slower, best quality)"
    print_styled "${GRAY}" "  --title=TITLE      Set slideshow title"
    print_styled "${GRAY}" "  --resolution=WxH   Set resolution (e.g., 1920x1080) [default: 1920x1080]"
    print_styled "${GRAY}" "  --output=FILE      Set output filename"
    print_styled "${GRAY}" "  --dry-run          Show what would be done without encoding"
    print_styled "${GRAY}" "  --help             Show this help message"
    echo ""
    print_styled "${BOLD}${BLUE}" "Examples:"
    print_styled "${GRAY}" "  ./run_advanced_slideshow.sh --performance"
    print_styled "${GRAY}" "  ./run_advanced_slideshow.sh --ultra --resolution=3840x2160"
    print_styled "${GRAY}" "  ./run_advanced_slideshow.sh --title=\"My Vacation\" --output=vacation.mp4"
    echo ""
    print_styled "${BOLD}${BLUE}" "Instructions:"
    print_styled "${GRAY}" "1. Place your images in 'images/original/' directory"
    print_styled "${GRAY}" "2. Place your audio file in 'song/' directory"
    print_styled "${GRAY}" "3. Run this script with desired options"
    echo ""
}

# Main entry point
run_with_settings "$@" 