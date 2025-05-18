#!/bin/bash

# High-Performance Slideshow Video Maker - Optimized for Apple Silicon
# This script provides an easy way to run the advanced slideshow maker

# Set default values
TITLE="Slideshow"
RESOLUTION="1920x1080"
DURATION="auto"  # Auto-detect from audio by default
OUTPUT="video"
USE_HEVC=true
QUALITY=50
FPS=30
DEBUG=false
MAX_PERFORMANCE=false

# Display help message
show_help() {
    echo "High-Performance Slideshow Video Maker - Optimized for Apple Silicon"
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -t, --title TEXT       Title displayed at the beginning (default: $TITLE)"
    echo "  -r, --resolution WxH   Video resolution (default: $RESOLUTION)"
    echo "  -d, --duration SECONDS Duration of audio track in seconds (auto-detected if not specified)"
    echo "  -o, --output FILENAME  Output filename without extension (default: $OUTPUT)"
    echo "  -c, --codec [h264|hevc] Video codec to use (default: hevc)"
    echo "  -q, --quality VALUE    Video quality (0-100, higher is better, default: $QUALITY)"
    echo "  -f, --fps NUMBER       Frames per second (default: $FPS)"
    echo "  -x, --max-performance  Use maximum performance settings"
    echo "  --debug                Enable debug logging"
    echo "  -h, --help             Display this help message"
    echo ""
    echo "Example:"
    echo "  $0 --title \"My Vacation\" --resolution 1920x1080 --codec hevc"
    echo ""
}

# Process command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--title)
            TITLE="$2"
            shift 2
            ;;
        -r|--resolution)
            RESOLUTION="$2"
            shift 2
            ;;
        -d|--duration)
            DURATION="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        -c|--codec)
            if [[ "$2" == "h264" ]]; then
                USE_HEVC=false
            elif [[ "$2" == "hevc" ]]; then
                USE_HEVC=true
            else
                echo "Error: Invalid codec '$2'. Must be 'h264' or 'hevc'."
                exit 1
            fi
            shift 2
            ;;
        -q|--quality)
            QUALITY="$2"
            shift 2
            ;;
        -f|--fps)
            FPS="$2"
            shift 2
            ;;
        -x|--max-performance)
            # Set maximum performance options
            MAX_PERFORMANCE=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Activate the virtual environment
source venv/bin/activate

# Build the command with all options
CMD="python fast_app.py"

if [[ -n "$TITLE" ]]; then
    CMD="$CMD --title \"$TITLE\""
fi

if [[ -n "$RESOLUTION" ]]; then
    CMD="$CMD --resolution $RESOLUTION"
fi

if [[ "$DURATION" != "auto" ]]; then
    CMD="$CMD --duration $DURATION"
fi

if [[ -n "$OUTPUT" ]]; then
    CMD="$CMD --output $OUTPUT"
fi

if [[ "$USE_HEVC" == true ]]; then
    CMD="$CMD --codec hevc"
else
    CMD="$CMD --codec h264"
fi

if [[ -n "$QUALITY" ]]; then
    CMD="$CMD --quality $QUALITY"
fi

if [[ -n "$FPS" ]]; then
    CMD="$CMD --fps $FPS"
fi

if [[ "$DEBUG" == true ]]; then
    CMD="$CMD --debug"
fi

if [[ "$MAX_PERFORMANCE" == true ]]; then
    CMD="$CMD --max-performance"
fi

# Print the command being executed
echo "Executing: $CMD"
echo ""

# Execute the command
eval "$CMD"

# Check if the command succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo "Slideshow video created successfully!"
    echo "You can find the output video at: $(pwd)/$OUTPUT.mp4"
else
    echo ""
    echo "An error occurred while creating the slideshow video."
    echo "Check the above messages for details."
fi 