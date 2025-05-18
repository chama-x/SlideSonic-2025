#!/bin/bash
# SlideSonic (2025) - Test Encoding Script
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

# Display spinner with message
spinner() {
    local message="$1"
    local duration="${2:-5}"
    local frames=( "⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏" )
    local delay=0.1
    local i=0
    
    # Hide cursor
    tput civis
    
    # Start spinner
    local end_time=$(($(date +%s) + duration))
    
    while [ $(date +%s) -lt $end_time ]; do
        i=$(( (i+1) % ${#frames[@]} ))
        printf "\r${GRAY}${frames[$i]} ${message}${RESET}"
        sleep $delay
    done
    
    # Return to start of line and clear it
    printf "\r%-$(tput cols)s\r"
    
    # Show cursor
    tput cnorm
}

# Check Python
check_python() {
    print_styled "${BOLD}" "Checking Python..."
    if command -v python3 &> /dev/null; then
        local version=$(python3 --version 2>&1)
        print_styled "${GREEN}" "✓ Python found: $version"
        return 0
    else
        print_styled "${RED}" "✗ Python 3 not found"
        return 1
    fi
}

# Check for virtual environment
check_venv() {
    print_styled "${BOLD}" "Checking virtual environment..."
    if [ -d "venv" ]; then
        print_styled "${GREEN}" "✓ Virtual environment found"
        # Activate virtual environment
        source venv/bin/activate
        if [ $? -ne 0 ]; then
            print_styled "${RED}" "✗ Failed to activate virtual environment"
            return 1
        fi
        print_styled "${GREEN}" "✓ Virtual environment activated"
        return 0
    else
        print_styled "${RED}" "✗ Virtual environment not found"
        print_styled "${GRAY}" "Run setup_advanced_encoding.sh to create the virtual environment"
        return 1
    fi
}

# Check FFmpeg
check_ffmpeg() {
    print_styled "${BOLD}" "Checking FFmpeg..."
    if command -v ffmpeg &> /dev/null; then
        local version=$(ffmpeg -version | head -n1 | awk '{print $3}')
        print_styled "${GREEN}" "✓ FFmpeg found: version $version"
        return 0
    else
        print_styled "${RED}" "✗ FFmpeg not found"
        return 1
    fi
}

# Check for Python dependencies
check_dependencies() {
    print_styled "${BOLD}" "Checking Python dependencies..."
    
    # Check PIL/Pillow
    python3 -c "import PIL; print(f'PIL version: {PIL.__version__}')" 2>/dev/null
    if [ $? -eq 0 ]; then
        print_styled "${GREEN}" "✓ PIL/Pillow found"
    else
        print_styled "${RED}" "✗ PIL/Pillow not found"
        return 1
    fi
    
    # Check NumPy
    python3 -c "import numpy; print(f'NumPy version: {numpy.__version__}')" 2>/dev/null
    if [ $? -eq 0 ]; then
        print_styled "${GREEN}" "✓ NumPy found"
    else
        print_styled "${YELLOW}" "⚠️ NumPy not found (optional)"
    fi
    
    # Check psutil
    python3 -c "import psutil; print(f'psutil version: {psutil.__version__}')" 2>/dev/null
    if [ $? -eq 0 ]; then
        print_styled "${GREEN}" "✓ psutil found"
    else
        print_styled "${YELLOW}" "⚠️ psutil not found (optional)"
    fi
    
    return 0
}

# Check for required directories
check_directories() {
    print_styled "${BOLD}" "Checking required directories..."
    
    # Check and create if needed
    for dir in "images/original" "song" "temp" "screenshots" "logs"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_styled "${YELLOW}" "⚠️ Created missing directory: $dir"
        else
            print_styled "${GREEN}" "✓ Directory exists: $dir"
        fi
    done
    
    return 0
}

# Create test images for the slideshow
create_test_images() {
    print_styled "${BOLD}" "Creating test images..."
    
    # Check if PIL/Pillow is available
    python3 -c "import PIL" 2>/dev/null
    if [ $? -ne 0 ]; then
        print_styled "${RED}" "✗ PIL/Pillow not found, cannot create test images"
        return 1
    fi
    
    # Create test images using Python
    python3 - <<EOF
from PIL import Image, ImageDraw, ImageFont
import os
import random
import math

# Ensure directories exist
os.makedirs("images/original", exist_ok=True)

# Create 5 test images with different colors and patterns
print("Creating test images...")

# Image size
width, height = 1920, 1080

# Colors
colors = [
    (73, 109, 137),    # Steel blue
    (189, 79, 108),    # Raspberry
    (96, 153, 102),    # Forest green
    (234, 185, 95),    # Golden yellow
    (165, 105, 189)    # Purple
]

# Create images
for i in range(5):
    img = Image.new('RGB', (width, height), color=colors[i])
    draw = ImageDraw.Draw(img)
    
    # Draw some patterns based on the image index
    if i == 0:  # Circles
        for j in range(20):
            x = random.randint(0, width)
            y = random.randint(0, height)
            r = random.randint(20, 200)
            rgb = (random.randint(180, 255), random.randint(180, 255), random.randint(180, 255))
            draw.ellipse((x-r, y-r, x+r, y+r), fill=rgb)
    
    elif i == 1:  # Lines
        for j in range(30):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            rgb = (random.randint(180, 255), random.randint(180, 255), random.randint(180, 255))
            width_line = random.randint(3, 15)
            draw.line((x1, y1, x2, y2), fill=rgb, width=width_line)
    
    elif i == 2:  # Rectangles
        for j in range(15):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = x1 + random.randint(100, 400)
            y2 = y1 + random.randint(100, 400)
            rgb = (random.randint(180, 255), random.randint(180, 255), random.randint(180, 255))
            draw.rectangle((x1, y1, x2, y2), fill=rgb)
    
    elif i == 3:  # Gradient
        for y in range(height):
            r = int(255 * y / height)
            g = int(255 * (1 - y / height))
            b = int(128 + 127 * math.sin(3 * math.pi * y / height))
            for x in range(width):
                draw.point((x, y), fill=(r, g, b))
    
    elif i == 4:  # Grid
        cell_size = 50
        for y in range(0, height, cell_size):
            for x in range(0, width, cell_size):
                color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
                draw.rectangle((x, y, x+cell_size-1, y+cell_size-1), fill=color)
    
    # Draw text showing slide number for each image
    try:
        # Try to add text (font availability may vary)
        text = f"Test Slide {i+1}"
        text_position = (width // 2 - 100, height // 2 - 50)
        text_color = (255, 255, 255)  # White text
        draw.text(text_position, text, fill=text_color, stroke_width=2, stroke_fill=(0, 0, 0))
    except Exception as e:
        # Fall back to a simpler approach if font issues occur
        print(f"Couldn't add text with font: {e}")
        for offset in range(-2, 3):
            for xoffset in range(-2, 3):
                draw.text((width // 2 - 100 + xoffset, height // 2 - 50 + offset), 
                          text, fill=(0, 0, 0))
        draw.text((width // 2 - 100, height // 2 - 50), text, fill=(255, 255, 255))
    
    # Save the image
    filename = f"images/original/test_slide_{i+1}.jpg"
    img.save(filename, quality=95)
    print(f"Created {filename}")

print("All test images created successfully.")
EOF
    
    if [ $? -eq 0 ]; then
        print_styled "${GREEN}" "✓ Test images created successfully"
        return 0
    else
        print_styled "${RED}" "✗ Failed to create test images"
        return 1
    fi
}

# Create a test audio file (silent)
create_test_audio() {
    print_styled "${BOLD}" "Creating test audio..."
    
    # Check if FFmpeg is available
    if ! command -v ffmpeg &> /dev/null; then
        print_styled "${RED}" "✗ FFmpeg not found, cannot create test audio"
        return 1
    fi
    
    # Create a 10-second silent audio file
    ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -t 10 -q:a 0 -map 0 song/test_audio.mp3 -y &>/dev/null
    
    if [ $? -eq 0 ]; then
        print_styled "${GREEN}" "✓ Test audio created successfully"
        return 0
    else
        print_styled "${RED}" "✗ Failed to create test audio"
        return 1
    fi
}

# Test basic encoding
test_encoding() {
    print_styled "${BOLD}" "Testing basic encoding functionality..."
    
    # Create a simple test script for encoding
    cat > test_encode.py <<EOF
#!/usr/bin/env python3
# SlideSonic Test Encoding Script

import os
import sys
import subprocess
import time

# Create temp directory if it doesn't exist
os.makedirs("temp", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Count number of images
image_dir = "images/original"
image_files = [f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
num_images = len(image_files)

print(f"Found {num_images} images in {image_dir}")
if num_images == 0:
    print("No images found. Please place images in the 'images/original' directory.")
    sys.exit(1)

# Check for audio file
song_dir = "song"
audio_files = [f for f in os.listdir(song_dir) if f.endswith(('.mp3', '.wav', '.aac', '.m4a'))]
if not audio_files:
    print("No audio files found. Please place an audio file in the 'song' directory.")
    sys.exit(1)

audio_file = os.path.join(song_dir, audio_files[0])
print(f"Using audio file: {audio_file}")

# Set duration per slide (total audio duration / number of slides)
audio_duration = 10  # Hardcoded for test audio
slide_duration = audio_duration / num_images
print(f"Duration per slide: {slide_duration:.2f} seconds")

# Create a temporary file list
with open("temp/files.txt", "w") as f:
    for img in sorted(image_files):
        f.write(f"file '../{image_dir}/{img}'\n")
        f.write(f"duration {slide_duration}\n")
    
    # Last image needs to be repeated without duration for correct encoding
    if image_files:
        f.write(f"file '../{image_dir}/{sorted(image_files)[-1]}'\n")

# Run FFmpeg to create the slideshow
print("Creating test slideshow...")
output_file = "temp/test_slideshow.mp4"
log_file = "logs/ffmpeg_output.log"

cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", "temp/files.txt",
    "-i", audio_file,
    "-c:v", "libx264", "-preset", "fast", "-crf", "22",
    "-c:a", "aac", "-b:a", "192k",
    "-pix_fmt", "yuv420p", "-shortest",
    "-r", "30", "-movflags", "+faststart",
    output_file
]

print(f"Running FFmpeg command: {' '.join(cmd)}")

with open(log_file, "w") as log:
    process = subprocess.Popen(cmd, stdout=log, stderr=log)
    
    # Print a simple progress indicator
    start_time = time.time()
    while process.poll() is None:
        elapsed = time.time() - start_time
        sys.stdout.write(f"\rEncoding in progress... {elapsed:.1f}s")
        sys.stdout.flush()
        time.sleep(0.5)
    
    # Check the result
    if process.returncode == 0:
        print(f"\rEncoding completed successfully in {time.time() - start_time:.1f}s!")
        print(f"Output file: {output_file}")
        
        # Get video information
        info_cmd = ["ffprobe", "-v", "error", "-show_entries", 
                    "format=duration:stream=width,height", 
                    "-of", "default=noprint_wrappers=1", output_file]
        
        try:
            info = subprocess.check_output(info_cmd, text=True)
            print("\nVideo information:")
            print(info)
        except subprocess.SubprocessError:
            pass
        
        return True
    else:
        print("\rEncoding failed!")
        print(f"Check log file for details: {log_file}")
        return False
EOF
    
    chmod +x test_encode.py
    
    # Run the test encoding script
    print_styled "${GRAY}" "Running test encoding..."
    python3 test_encode.py
    
    if [ $? -eq 0 ]; then
        print_styled "${GREEN}" "✓ Test encoding completed successfully"
        if [ -f "temp/test_slideshow.mp4" ]; then
            print_styled "${GREEN}" "✓ Output video file created: temp/test_slideshow.mp4"
            
            # Get the file size
            file_size=$(du -h "temp/test_slideshow.mp4" | cut -f1)
            print_styled "${GRAY}" "  File size: $file_size"
            
            # Get video duration
            duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "temp/test_slideshow.mp4" 2>/dev/null)
            if [ $? -eq 0 ]; then
                print_styled "${GRAY}" "  Duration: $duration seconds"
            fi
        else
            print_styled "${RED}" "✗ Output video file not found"
            return 1
        fi
        return 0
    else
        print_styled "${RED}" "✗ Test encoding failed"
        return 1
    fi
}

# Clean up test files
cleanup() {
    local keep_test_files="$1"
    
    if [ "$keep_test_files" = true ]; then
        print_styled "${YELLOW}" "Test files were kept for inspection"
        return 0
    else
        print_styled "${BOLD}" "Cleaning up test files..."
        
        # Remove test images
        rm -f images/original/test_slide_*.jpg
        
        # Remove test audio
        rm -f song/test_audio.mp3
        
        # Remove temporary files
        rm -f temp/files.txt
        rm -f temp/test_slideshow.mp4
        rm -f test_encode.py
        
        print_styled "${GREEN}" "✓ Cleanup completed"
        return 0
    fi
}

# Main function
main() {
    # Parse command line arguments
    local keep_test_files=false
    
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --keep)
                keep_test_files=true
                shift
                ;;
            --help|-h)
                print_styled "${BOLD}" "SlideSonic (2025) - Test Script"
                print_styled "${GRAY}" "Usage: ./test_encoding.sh [options]"
                print_styled "${GRAY}" "Options:"
                print_styled "${GRAY}" "  --keep    Keep test files after testing"
                print_styled "${GRAY}" "  --help    Show this help message"
                exit 0
                ;;
            *)
                print_styled "${RED}" "Unknown option: $1"
                print_styled "${GRAY}" "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Clear the screen and show title
    clear
    center_text "SlideSonic (2025) Test Script"
    draw_divider
    echo ""
    
    # Run tests
    check_python || exit 1
    check_venv || exit 1
    check_ffmpeg || exit 1
    check_dependencies || exit 1
    check_directories || exit 1
    create_test_images || exit 1
    create_test_audio || exit 1
    
    # Pause before encoding test
    echo ""
    print_styled "${BOLD}" "Ready to run encoding test."
    print_styled "${GRAY}" "Press Enter to continue or Ctrl+C to cancel..."
    read
    
    # Run encoding test
    test_encoding || exit 1
    
    # Clean up
    cleanup "$keep_test_files"
    
    # Show success message
    echo ""
    draw_divider
    center_text "Test Completed Successfully"
    print_styled "${GREEN}" "✓ SlideSonic (2025) is ready to use!"
    echo ""
    
    return 0
}

# Run the main function
main "$@" 