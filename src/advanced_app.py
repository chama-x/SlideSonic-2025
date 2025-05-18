#!/usr/bin/env python3
# SlideSonic (2025) - Interactive Application
# https://github.com/chama-x/SlideSonic-2025

import os
import sys
import time
import shutil
import platform
import subprocess
import argparse
import json
from datetime import datetime
import re
import glob
from collections import defaultdict
import math

try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    HAVE_PSUTIL = False

# Constants
VERSION = "2.5.0"
PROGRAM_NAME = "SlideSonic (2025)"

# Terminal colors
RESET = "\033[0m"
BOLD = "\033[1m"
BLUE = "\033[38;5;32m"
GRAY = "\033[38;5;242m"
LIGHT_GRAY = "\033[38;5;248m"
GREEN = "\033[38;5;35m"
YELLOW = "\033[38;5;220m"
RED = "\033[38;5;196m"
CYAN = "\033[38;5;87m"
PURPLE = "\033[38;5;141m"

# Accessibility options
USE_COLORS = True
USE_UNICODE = True
USE_ANIMATIONS = True

# Default settings
DEFAULT_SETTINGS = {
    "resolution": "1920x1080",
    "quality": "standard",
    "transition": "fade",
    "transition_duration": 1.0,
    "audio_fade": True,
    "auto_adjust": True,
    "output_format": "mp4",
    "encoder": "auto",
    "hardware_acceleration": True,
    "auto_detect_files": True,
    "auto_match_audio": True,
    "smart_sorting": True
}

# File detection patterns
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.opus']
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm']

# Common patterns in filenames
DATE_PATTERNS = [
    r'(\d{4}[-_]\d{2}[-_]\d{2})',  # YYYY-MM-DD or YYYY_MM_DD
    r'(\d{2}[-_]\d{2}[-_]\d{4})',  # DD-MM-YYYY or DD_MM_YYYY
    r'(\d{8})'  # YYYYMMDD
]

# Sequence pattern (e.g., img001.jpg, photo-2.jpg)
SEQUENCE_PATTERNS = [
    r'.*?(\d+).*?\.',  # Any digits before the extension
]

def print_styled(style, text):
    """Print styled text with fallback for terminals without color support"""
    if USE_COLORS:
        print(f"{style}{text}{RESET}")
    else:
        print(text)

def draw_divider():
    """Draw a horizontal divider line"""
    width = shutil.get_terminal_size().columns
    char = "─" if USE_UNICODE else "-"
    
    if USE_COLORS:
        print(f"{GRAY}{char * width}{RESET}")
    else:
        print(char * width)

def center_text(text, style=BLUE):
    """Center text in the terminal"""
    width = shutil.get_terminal_size().columns
    padding = (width - len(text)) // 2
    
    if USE_COLORS:
        print(f"{' ' * padding}{BOLD}{style}{text}{RESET}")
    else:
        print(f"{' ' * padding}{text}")

def show_logo():
    """Display the SlideSonic logo"""
    if USE_COLORS and USE_UNICODE:
        print(f"{BLUE}")
        print("   _____ _ _     _      _____             _        _____ _____ _____ _____ ")
        print("  / ____| (_)   | |    / ____|           (_)      / ____|  __ \\_   _|  __ \\")
        print(" | (___ | |_  __| | ___| (___   ___  _ __ _  ___  | |    | |__) || | | |  | |")
        print("  \\___ \\| | |/ _` |/ _ \\\\___ \\ / _ \\| '__| |/ __| | |    |  ___/ | | | |  | |")
        print("  ____) | | | (_| |  __/____) | (_) | |  | | (__  | |____| |    _| |_| |__| |")
        print(" |_____/|_|_|\\__,_|\\___|_____/ \\___/|_|  |_|\\___|  \\_____|_|   |_____|_____/")
        print(f"{RESET}")
    else:
        center_text(f"{PROGRAM_NAME}")

def show_banner():
    """Display the application banner"""
    os.system('cls' if os.name == 'nt' else 'clear')
    show_logo()
    center_text("Create stunning slideshow videos", CYAN)
    print_styled(GRAY, f"Version {VERSION} | https://github.com/chama-x/SlideSonic-2025")
    draw_divider()
    print()

def ask_question(prompt, default=None, options=None, password=False):
    """Ask a question and get user input with optional validation"""
    while True:
        if default is not None:
            prompt_text = f"{prompt} [{default}]: "
        else:
            prompt_text = f"{prompt}: "
        
        if USE_COLORS:
            sys.stdout.write(f"{CYAN}{prompt_text}{RESET}")
        else:
            sys.stdout.write(prompt_text)
        
        sys.stdout.flush()
        
        if password:
            import getpass
            answer = getpass.getpass("")
        else:
            answer = input()
        
        if not answer and default is not None:
            return default
        
        if options and answer not in options:
            print_styled(YELLOW, f"Please choose from: {', '.join(options)}")
            continue
        
        if answer:
            return answer

def show_spinner(message, seconds=1):
    """Show a spinner animation with a message"""
    if not USE_ANIMATIONS:
        print_styled(GRAY, f"{message}...")
        time.sleep(seconds)
        return
    
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"] if USE_UNICODE else ["-", "\\", "|", "/"]
    end_time = time.time() + seconds
    
    try:
        # Hide cursor
        print("\033[?25l", end="", flush=True)
        
        i = 0
        while time.time() < end_time:
            sys.stdout.write(f"\r{GRAY}{frames[i]} {message}...{RESET}")
            sys.stdout.flush()
            time.sleep(0.1)
            i = (i + 1) % len(frames)
        
        # Clear the line
        sys.stdout.write("\r" + " " * (len(message) + 15) + "\r")
        sys.stdout.flush()
    finally:
        # Show cursor
        print("\033[?25h", end="", flush=True)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description=f"{PROGRAM_NAME} Interactive Application")
    parser.add_argument('--no-colors', action='store_true', help='Disable colors')
    parser.add_argument('--no-unicode', action='store_true', help='Disable Unicode characters')
    parser.add_argument('--no-animations', action='store_true', help='Disable animations')
    parser.add_argument('--hardware-analysis', action='store_true', help='Run hardware analysis only')
    parser.add_argument('--version', action='store_true', help='Show version information')
    parser.add_argument('--quick', action='store_true', help='Launch quick slideshow creation')
    parser.add_argument('--batch', action='store_true', help='Run batch processing on subdirectories')
    return parser.parse_args()

def get_hardware_info():
    """Get basic hardware information"""
    result = {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_cores": os.cpu_count(),
        "memory_total": None,
        "ffmpeg_version": None,
        "apple_silicon": platform.machine() == "arm64" and platform.system() == "Darwin"
    }
    
    # Get memory info
    if HAVE_PSUTIL:
        try:
            mem = psutil.virtual_memory()
            result["memory_total"] = mem.total
            result["memory_available"] = mem.available
        except Exception:
            pass
    
    # Get FFmpeg version
    try:
        process = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=True)
        version_match = re.search(r'ffmpeg version (\S+)', process.stdout)
        if version_match:
            result["ffmpeg_version"] = version_match.group(1)
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    return result

def format_bytes(bytes_value):
    """Format bytes to human-readable format"""
    if bytes_value is None:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024 or unit == 'TB':
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024

def run_hardware_analysis():
    """Run a basic hardware analysis"""
    show_banner()
    print_styled(BOLD, "Running hardware analysis...")
    
    # Show a spinner animation
    show_spinner("Analyzing system", 2)
    
    # Get hardware info
    hw_info = get_hardware_info()
    
    # Display results
    draw_divider()
    print_styled(BOLD, "Hardware Analysis Results")
    print()
    
    # System information
    print_styled(BOLD + BLUE, "System Information:")
    print_styled(CYAN, f"• OS:           {hw_info['os']} {hw_info['os_version']}")
    print_styled(CYAN, f"• Architecture: {hw_info['architecture']}")
    print_styled(CYAN, f"• Python:       {hw_info['python_version']}")
    if hw_info["apple_silicon"]:
        print_styled(GREEN, f"• Apple Silicon: Yes (M-series chip)")
    print()
    
    # CPU information
    print_styled(BOLD + BLUE, "CPU Information:")
    print_styled(CYAN, f"• CPU Cores:    {hw_info['cpu_cores']}")
    print()
    
    # Memory information
    print_styled(BOLD + BLUE, "Memory Information:")
    if hw_info["memory_total"] is not None:
        print_styled(CYAN, f"• Total:        {format_bytes(hw_info['memory_total'])}")
        print_styled(CYAN, f"• Available:    {format_bytes(hw_info['memory_available'])}")
    else:
        print_styled(YELLOW, "• Memory information not available")
    print()
    
    # FFmpeg information
    print_styled(BOLD + BLUE, "FFmpeg Information:")
    if hw_info["ffmpeg_version"] is not None:
        print_styled(GREEN, f"• Installed:    Yes (version {hw_info['ffmpeg_version']})")
        
        # Get encoder information
        try:
            process = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True, check=True)
            encoders_output = process.stdout
            
            encoders = []
            if 'libx264' in encoders_output:
                encoders.append("H.264")
            if 'libx265' in encoders_output:
                encoders.append("HEVC/H.265")
            if 'libaom-av1' in encoders_output:
                encoders.append("AV1")
            
            if encoders:
                print_styled(CYAN, f"• Encoders:     {', '.join(encoders)}")
            
            # Check hardware acceleration
            try:
                process = subprocess.run(['ffmpeg', '-hwaccels'], capture_output=True, text=True, check=True)
                hwaccels_output = process.stdout
                
                hwaccels = []
                if 'videotoolbox' in hwaccels_output:
                    hwaccels.append("Apple VideoToolbox")
                if 'cuda' in hwaccels_output:
                    hwaccels.append("NVIDIA CUDA")
                if 'qsv' in hwaccels_output:
                    hwaccels.append("Intel QuickSync")
                if 'vaapi' in hwaccels_output:
                    hwaccels.append("VA-API")
                
                if hwaccels:
                    print_styled(GREEN, f"• Hardware Accel: {', '.join(hwaccels)}")
            except subprocess.SubprocessError:
                pass
            
        except subprocess.SubprocessError:
            pass
    else:
        print_styled(RED, "• Installed:    No (FFmpeg not found)")
        print_styled(GRAY, "  FFmpeg is required for encoding videos.")
        print_styled(GRAY, "  Please install FFmpeg and run again.")
    
    print()
    draw_divider()
    
    # Wait for user input before returning to main menu
    input("Press Enter to continue...")

def load_settings():
    """Load settings from file or use defaults"""
    settings_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "settings.json")
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            
            # Check for missing settings and add defaults
            for key, value in DEFAULT_SETTINGS.items():
                if key not in settings:
                    settings[key] = value
            
            return settings
        except (json.JSONDecodeError, IOError):
            print_styled(YELLOW, "Warning: Could not load settings, using defaults")
    
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Save settings to file"""
    settings_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "settings.json")
    
    try:
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=4)
        return True
    except IOError:
        print_styled(YELLOW, "Warning: Could not save settings")
        return False

def count_files(directory, extensions):
    """Count files with specific extensions in a directory"""
    if not os.path.exists(directory):
        return 0
    
    return len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and 
                any(f.lower().endswith(ext) for ext in extensions)])

def detect_best_encoder():
    """Detect the best encoder based on the system capabilities"""
    hw_info = get_hardware_info()
    
    # Check available encoders
    try:
        process = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True, check=True)
        encoders_output = process.stdout
        
        # Check for hardware acceleration
        process = subprocess.run(['ffmpeg', '-hwaccels'], capture_output=True, text=True, check=True)
        hwaccels_output = process.stdout
        
        # Apple Silicon with VideoToolbox
        if hw_info["apple_silicon"] and 'videotoolbox' in hwaccels_output:
            return "h264_videotoolbox" if "h264_videotoolbox" in encoders_output else "libx264"
        
        # NVIDIA GPU with NVENC
        if 'cuda' in hwaccels_output and 'h264_nvenc' in encoders_output:
            return "h264_nvenc"
        
        # Intel QuickSync
        if 'qsv' in hwaccels_output and 'h264_qsv' in encoders_output:
            return "h264_qsv"
        
        # VA-API
        if 'vaapi' in hwaccels_output and 'h264_vaapi' in encoders_output:
            return "h264_vaapi"
        
        # Software encoders
        if 'libx265' in encoders_output:
            return "libx265"  # HEVC is better quality but slower
        
        # Default to H.264
        return "libx264"
    
    except subprocess.SubprocessError:
        return "libx264"  # Default

def create_slideshow_interactive():
    """Create a slideshow with smart interactive settings"""
    show_banner()
    
    # Load settings
    settings = load_settings()
    
    # Show a spinner while scanning
    show_spinner("Scanning for media files", 1)
    
    # Auto-organize images and find matching audio
    print_styled(BOLD, "Analyzing files...")
    media_data = auto_organize_images(recursive=settings.get("recursive_scan", False))
    
    # Check if we found any images
    if media_data["images"]["count"] == 0:
        print_styled(RED, "Error: No images found in images/original/ directory")
        print_styled(GRAY, "Please add your images to the images/original/ directory and try again.")
        
        # Offer to create test images for demo purposes
        if ask_question("Would you like to create test images for a demo", default="n", options=["y", "n"]) == "y":
            create_test_images()
            media_data = auto_organize_images()  # Rescan after creating test images
            if media_data["images"]["count"] == 0:
                print_styled(RED, "Failed to create test images.")
                input("\nPress Enter to return to the main menu...")
                return
        else:
            input("\nPress Enter to return to the main menu...")
            return
    
    # Show image analysis results
    print_styled(GREEN, f"Found {media_data['images']['count']} images")
    
    # Group analysis information
    if media_data["images"]["groups"]["sequence"]:
        largest_sequence = max(media_data["images"]["groups"]["sequence"].values(), key=len)
        if len(largest_sequence) > 1:
            print_styled(CYAN, f"✓ Detected sequence with {len(largest_sequence)} images")
    
    if media_data["images"]["groups"]["date"]:
        print_styled(CYAN, f"✓ Detected {len(media_data['images']['groups']['date'])} date-based groups")
    
    # Audio file information
    if media_data["audio"]["selected"]:
        audio_file = media_data["audio"]["selected"]
        audio_filename = os.path.basename(audio_file)
        print_styled(GREEN, f"Found matching audio file: {audio_filename}")
        
        if media_data["audio"]["duration"]:
            mins, secs = divmod(media_data["audio"]["duration"], 60)
            print_styled(CYAN, f"✓ Audio duration: {int(mins)}:{int(secs):02d}")
            print_styled(CYAN, f"✓ Average slide duration: {media_data['slide_duration']:.2f} seconds")
    else:
        audio_file = None
        if media_data["audio"]["files"]["count"] > 0:
            print_styled(YELLOW, f"Found {media_data['audio']['files']['count']} audio files but no good match")
            
            # Ask user if they want to select an audio file
            if ask_question("Would you like to select an audio file", default="y", options=["y", "n"]) == "y":
                print_styled(GRAY, "Available audio files:")
                audio_list = [f for f in media_data["audio"]["files"]["files"] if f["type"] == "audio"]
                for i, file_info in enumerate(audio_list, 1):
                    print_styled(GRAY, f"{i}. {file_info['name']}")
                
                choice = ask_question("Which audio file would you like to use", default="1")
                try:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(audio_list):
                        audio_file = audio_list[choice_idx]["path"]
                        # Update duration information
                        media_data["audio"]["selected"] = audio_file
                        media_data["audio"]["duration"] = get_audio_duration(audio_file)
                        
                        # Recalculate slide duration
                        if media_data["audio"]["duration"] and media_data["images"]["count"] > 0:
                            raw_duration = media_data["audio"]["duration"] / media_data["images"]["count"]
                            if raw_duration < 2.0:
                                media_data["slide_duration"] = 2.0
                            elif raw_duration > 6.0:
                                media_data["slide_duration"] = 6.0
                            else:
                                media_data["slide_duration"] = raw_duration
                except ValueError:
                    print_styled(YELLOW, "Invalid choice, continuing without audio")
        else:
            print_styled(YELLOW, "No audio files found in song/ directory")
            use_audio = ask_question("Do you want to continue without audio", default="y", options=["y", "n"]) == "y"
            if not use_audio:
                print_styled(GRAY, "Please add your audio file to the song/ directory and try again.")
                input("\nPress Enter to return to the main menu...")
                return
    
    # Smart project name suggestion
    suggested_name = ""
    
    # Try to derive a name from common prefixes
    prefix_groups = media_data["images"]["groups"]["prefix"]
    if prefix_groups:
        largest_prefix_group = max(prefix_groups.values(), key=len)
        if len(largest_prefix_group) > 1:
            suggested_name = largest_prefix_group[0]["prefix"].replace("_", " ").replace("-", " ").title()
    
    # If no good prefix, try date-based name
    if not suggested_name and media_data["images"]["groups"]["date"]:
        # Use the most common date
        date_groups = media_data["images"]["groups"]["date"]
        most_common_date = max(date_groups.values(), key=len)[0]["date"]
        suggested_name = f"Slideshow {most_common_date}"
    
    # Default fallback
    if not suggested_name:
        suggested_name = f"Slideshow {datetime.now().strftime('%Y-%m-%d')}"
    
    # Collect slideshow settings with smart defaults
    print()
    print_styled(BOLD, "Slideshow Settings")
    print()
    
    # Title with smart suggestion
    slideshow_title = ask_question("Enter slideshow title", default=suggested_name)
    
    # Resolution with smart default based on image analysis
    # TODO: Add image resolution detection for better defaults
    resolutions = ["1280x720", "1920x1080", "2560x1440", "3840x2160"]
    print_styled(GRAY, "Available resolutions:")
    for i, res in enumerate(resolutions, 1):
        print_styled(GRAY, f"{i}. {res}")
    
    # Default to 1080p for most cases, 4K for large photo sets
    default_res = "2" if media_data["images"]["count"] < 100 else "4"
    res_choice = ask_question("Choose resolution", default=default_res)
    try:
        res_idx = int(res_choice) - 1
        if 0 <= res_idx < len(resolutions):
            resolution = resolutions[res_idx]
        else:
            resolution = resolutions[1]  # Default to 1080p
    except ValueError:
        resolution = resolutions[1]  # Default to 1080p
    
    # Quality presets with hardware-aware defaults
    hw_info = get_hardware_info()
    
    # Determine sensible default based on hardware
    default_quality = "2"  # Standard quality is default
    
    # If we have good CPU or GPU acceleration, suggest higher quality
    if hw_info.get("apple_silicon") or (HAVE_PSUTIL and psutil.cpu_count(logical=False) >= 8):
        default_quality = "3"  # Higher quality for better hardware
    
    quality_presets = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
    print_styled(GRAY, "Quality presets (faster → better quality):")
    print_styled(GRAY, "1. Maximum Performance (ultrafast)")
    print_styled(GRAY, "2. Standard Quality (medium)")
    print_styled(GRAY, "3. Ultra High Quality (veryslow)")
    print_styled(GRAY, "4. Custom")
    
    quality_choice = ask_question("Choose quality preset", default=default_quality)
    try:
        q_choice = int(quality_choice)
        if q_choice == 1:
            quality = "ultrafast"
        elif q_choice == 2:
            quality = "medium"
        elif q_choice == 3:
            quality = "veryslow"
        elif q_choice == 4:
            print_styled(GRAY, "Available presets:")
            for i, preset in enumerate(quality_presets, 1):
                print_styled(GRAY, f"{i}. {preset}")
            
            preset_choice = ask_question("Choose preset", default="6")
            try:
                preset_idx = int(preset_choice) - 1
                if 0 <= preset_idx < len(quality_presets):
                    quality = quality_presets[preset_idx]
                else:
                    quality = "medium"
            except ValueError:
                quality = "medium"
        else:
            quality = "medium"
    except ValueError:
        quality = "medium"
    
    # Smart output filename
    sanitized_title = slideshow_title.replace(' ', '_').replace('/', '_').replace('\\', '_')
    default_filename = f"{sanitized_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    output_filename = ask_question("Output filename", default=default_filename)
    
    # Detect best encoder
    encoder = detect_best_encoder()
    use_hardware_accel = "qsv" in encoder or "nvenc" in encoder or "videotoolbox" in encoder or "vaapi" in encoder
    
    # Create command
    print()
    print_styled(BOLD, "Creating Slideshow")
    print()
    print_styled(CYAN, f"Title:      {slideshow_title}")
    print_styled(CYAN, f"Resolution: {resolution}")
    print_styled(CYAN, f"Quality:    {quality}")
    print_styled(CYAN, f"Output:     {output_filename}")
    print_styled(CYAN, f"Encoder:    {encoder}{' (hardware accelerated)' if use_hardware_accel else ''}")
    
    if audio_file:
        print_styled(CYAN, f"Audio:      {os.path.basename(audio_file)}")
        print_styled(CYAN, f"Duration:   {media_data['audio']['duration']:.2f} seconds")
    
    print_styled(CYAN, f"Images:     {media_data['images']['count']} images")
    print_styled(CYAN, f"Per slide:  {media_data['slide_duration']:.2f} seconds")
    print()
    
    # Confirm
    if ask_question("Start encoding", default="y", options=["y", "n"]) != "y":
        print_styled(GRAY, "Encoding cancelled")
        input("\nPress Enter to return to the main menu...")
        return
    
    # Save settings
    settings["resolution"] = resolution
    settings["quality"] = quality
    save_settings(settings)
    
    # Create encoding script with optimized image order
    create_encoding_script(
        slideshow_title, 
        resolution, 
        quality, 
        output_filename, 
        encoder, 
        audio_file,
        media_data["images"]["suggested_order"],
        media_data["slide_duration"]
    )
    
    # Launch the encoding
    run_encoding()

def create_test_images():
    """Create test images for demo purposes"""
    print_styled(BOLD, "Creating test images...")
    
    # Create directories if needed
    os.makedirs("images/original", exist_ok=True)
    
    # Try to import PIL for image creation
    try:
        from PIL import Image, ImageDraw
        
        # Create 5 test images with different colors
        colors = [
            (73, 109, 137),    # Steel blue
            (189, 79, 108),    # Raspberry
            (96, 153, 102),    # Forest green
            (234, 185, 95),    # Golden yellow
            (165, 105, 189)    # Purple
        ]
        
        width, height = 1920, 1080
        
        for i in range(5):
            img = Image.new('RGB', (width, height), color=colors[i])
            draw = ImageDraw.Draw(img)
            
            # Draw some test content
            margin = 100
            draw.rectangle(
                (margin, margin, width - margin, height - margin),
                outline=(255, 255, 255),
                width=10
            )
            
            # Add text annotation
            text_position = (width // 2 - 100, height // 2 - 50)
            
            # Create text by drawing it manually (no need for fonts)
            for offset in range(-2, 3):
                for xoffset in range(-2, 3):
                    draw.text(
                        (text_position[0] + xoffset, text_position[1] + offset),
                        f"Test Slide {i+1}",
                        fill=(0, 0, 0)
                    )
            draw.text(text_position, f"Test Slide {i+1}", fill=(255, 255, 255))
            
            # Save the image
            filename = f"images/original/test_slide_{i+1:02d}.jpg"
            img.save(filename, quality=95)
            
        print_styled(GREEN, "✓ Created 5 test images in images/original/")
        return True
    
    except ImportError:
        print_styled(RED, "✗ Could not create test images - PIL/Pillow not installed")
        return False
    except Exception as e:
        print_styled(RED, f"✗ Error creating test images: {e}")
        return False

def create_encoding_script(title, resolution, quality, output_filename, encoder, audio_file, image_paths=None, slide_duration=3.0):
    """Create a Python script to run the encoding process"""
    script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "run_encode.py")
    
    # Escape quotes in title
    title = title.replace('"', '\\"')
    
    script_content = f"""#!/usr/bin/env python3
# SlideSonic (2025) - Encoding Script
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

import os
import sys
import time
import subprocess
from datetime import datetime
import json

# Slideshow settings
TITLE = "{title}"
RESOLUTION = "{resolution}"
QUALITY_PRESET = "{quality}"
OUTPUT_FILENAME = "{output_filename}"
ENCODER = "{encoder}"
AUDIO_FILE = {repr(audio_file)}
SLIDE_DURATION = {slide_duration}

# Ensure required directories exist
os.makedirs("temp", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Get all images in the original directory
IMAGE_DIR = "images/original"
"""

    # If we have optimized image paths, use them
    if image_paths and len(image_paths) > 0:
        # Convert paths to relative if they're absolute
        relative_paths = []
        for path in image_paths:
            if os.path.isabs(path):
                try:
                    rel_path = os.path.relpath(path)
                    relative_paths.append(rel_path)
                except ValueError:
                    # If can't make relative, use as is
                    relative_paths.append(path)
            else:
                relative_paths.append(path)
                
        script_content += f"""
# Using smart-sorted image list
image_files = {json.dumps(relative_paths)}
print(f"Using {{len(image_files)}} images in optimized order")
"""
    else:
        script_content += """
# Get all images in the original directory
image_files = [f for f in os.listdir(IMAGE_DIR) if os.path.isfile(os.path.join(IMAGE_DIR, f)) and 
               any(f.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif'])]

# Sort images by name
image_files.sort()
"""

    script_content += """
if not image_files:
    print("Error: No images found in images/original/ directory")
    sys.exit(1)

print(f"Found {len(image_files)} images")

# Calculate duration per slide based on audio duration
audio_duration = None
if AUDIO_FILE:
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
               '-of', 'default=noprint_wrappers=1:nokey=1', AUDIO_FILE]
        audio_duration = float(subprocess.check_output(cmd, text=True).strip())
        print(f"Audio duration: {audio_duration:.2f} seconds")
    except (subprocess.SubprocessError, ValueError):
        print("Warning: Could not determine audio duration")

# Use provided slide duration or calculate from audio
slide_duration = SLIDE_DURATION
if audio_duration:
    # Make sure slides fit within audio, adjusting if necessary
    total_duration = slide_duration * len(image_files)
    if total_duration > audio_duration * 1.1:  # Allow slight overflow
        # Need to shorten slide duration to fit audio
        slide_duration = max(1.5, audio_duration / len(image_files))
        print(f"Adjusted slide duration to {slide_duration:.2f}s to fit audio")
    elif total_duration < audio_duration * 0.9:  # If much shorter than audio
        # Can lengthen slide duration to better use the audio
        slide_duration = min(6.0, audio_duration / len(image_files))
        print(f"Adjusted slide duration to {slide_duration:.2f}s to better match audio")

print(f"Using slide duration: {slide_duration:.2f} seconds")

# Create temporary file list
with open("temp/filelist.txt", "w") as f:
    for img in image_files:
        # Check if this is a full path or just a filename
        if os.path.dirname(img):
            f.write(f"file '{img}'\n")
        else:
            f.write(f"file '../{IMAGE_DIR}/{img}'\n")
        f.write(f"duration {slide_duration}\n")
    
    # Add last image again to avoid premature ending
    if image_files:
        last_img = image_files[-1]
        if os.path.dirname(last_img):
            f.write(f"file '{last_img}'\n")
        else:
            f.write(f"file '../{IMAGE_DIR}/{last_img}'\n")

# Parse resolution
width, height = map(int, RESOLUTION.split('x'))

# Determine quality settings based on encoder
crf_value = "23"  # Default for H.264
if ENCODER == "libx265":
    crf_value = "28"  # HEVC uses different CRF scale
elif "av1" in ENCODER:
    crf_value = "30"  # AV1 uses different CRF scale

# Add fade transitions between slides
transitions_enabled = True

# Build FFmpeg command with advanced options
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", "temp/filelist.txt",
]

# Add audio if available
if AUDIO_FILE:
    ffmpeg_cmd.extend(["-i", AUDIO_FILE])

# Add video settings
ffmpeg_cmd.extend([
    "-c:v", ENCODER,
    "-preset", QUALITY_PRESET,
    "-crf", crf_value,
    "-pix_fmt", "yuv420p",
])

# Add audio settings if available
if AUDIO_FILE:
    ffmpeg_cmd.extend([
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
    ])

# Enable fade transitions if requested
if transitions_enabled:
    ffmpeg_cmd.extend([
        "-vf", "fade=t=in:st=0:d=0.5,fade=t=out:st={:.1f}:d=0.5".format(
            slide_duration * len(image_files) - 0.5
        )
    ])

# Add resolution and other settings
ffmpeg_cmd.extend([
    "-s", RESOLUTION,
    "-r", "30",
    "-movflags", "+faststart",
    OUTPUT_FILENAME
])

# Save metadata about the encoding
metadata = {
    "title": TITLE,
    "created": datetime.now().isoformat(),
    "settings": {
        "resolution": RESOLUTION,
        "quality": QUALITY_PRESET,
        "encoder": ENCODER,
        "slide_duration": slide_duration,
        "total_duration": slide_duration * len(image_files),
        "image_count": len(image_files),
        "audio": AUDIO_FILE is not None
    }
}

with open("temp/encode_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

# Log the command
print(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")

# Create log file
log_file = "logs/ffmpeg_output.log"
log_file_handle = open(log_file, "w")

# Record start time
start_time = time.time()

# Run FFmpeg
try:
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                               universal_newlines=True, bufsize=1)
    
    # Process output in real-time
    for line in process.stdout:
        sys.stdout.write(line)
        log_file_handle.write(line)
        log_file_handle.flush()
    
    # Wait for process to complete
    process.wait()
    
    # Check result
    if process.returncode == 0:
        elapsed_time = time.time() - start_time
        print(f"\\nEncoding completed successfully in {elapsed_time:.2f} seconds")
        print(f"Output file: {OUTPUT_FILENAME}")
        
        # Show file size
        try:
            file_size = os.path.getsize(OUTPUT_FILENAME)
            print(f"File size: {file_size / (1024*1024):.2f} MB")
        except:
            pass
    else:
        print(f"\\nEncoding failed with error code {process.returncode}")
        print(f"Check log file for details: {log_file}")
except Exception as e:
    print(f"Error running FFmpeg: {e}")
finally:
    log_file_handle.close()
"""
    
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # Make the script executable
    os.chmod(script_path, 0o755)

def run_encoding():
    """Run the encoding script"""
    script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "run_encode.py")
    
    if not os.path.exists(script_path):
        print_styled(RED, "Error: Encoding script not found")
        return
    
    # Run the script
    try:
        subprocess.run([sys.executable, script_path], check=True)
        print()
        print_styled(GREEN, "Encoding completed successfully")
    except subprocess.SubprocessError:
        print()
        print_styled(RED, "Encoding failed")
    
    input("\nPress Enter to return to the main menu...")

def show_help():
    """Show help information"""
    show_banner()
    
    print_styled(BOLD, "SlideSonic (2025) Help")
    print()
    
    print_styled(BOLD + BLUE, "Basic Usage:")
    print_styled(GRAY, "1. Place your images in the 'images/original/' directory")
    print_styled(GRAY, "2. Place your audio file in the 'song/' directory")
    print_styled(GRAY, "3. Run './slidesonic' to start the application")
    print_styled(GRAY, "4. Follow the on-screen instructions")
    print()
    
    print_styled(BOLD + BLUE, "Command Line Options:")
    print_styled(GRAY, "./slidesonic               - Launch main menu")
    print_styled(GRAY, "./slidesonic --help        - Show this help")
    print_styled(GRAY, "./slidesonic --quick       - Launch interactive mode directly")
    print_styled(GRAY, "./slidesonic --monitor     - Monitor encoding progress")
    print_styled(GRAY, "./slidesonic --analyze     - Analyze hardware capabilities")
    print_styled(GRAY, "./slidesonic --version     - Show version information")
    print_styled(GRAY, "./slidesonic --accessibility - Enable accessibility features")
    print()
    
    print_styled(BOLD + BLUE, "Quality Modes:")
    print_styled(GRAY, "1. Maximum Performance - Fastest encoding, suitable for quick previews")
    print_styled(GRAY, "2. Standard Quality - Balanced quality/speed, good for most purposes")
    print_styled(GRAY, "3. Ultra High Quality - Best quality, slower encoding")
    print()
    
    print_styled(BOLD + BLUE, "For More Information:")
    print_styled(GRAY, "Visit: https://github.com/chama-x/SlideSonic-2025")
    
    input("\nPress Enter to return to the main menu...")

def show_main_menu():
    """Show the main menu and handle user input"""
    while True:
        show_banner()
        
        # Check for quick-start readiness
        images_ready = False
        audio_ready = False
        
        image_count = count_files("images/original", IMAGE_EXTENSIONS)
        audio_count = count_files("song", AUDIO_EXTENSIONS)
        
        if image_count > 0:
            images_ready = True
        if audio_count > 0:
            audio_ready = True
        
        # Determine if we can offer a quick start option
        quick_start_ready = images_ready
        
        print_styled(BOLD, "Select an option:")
        print()
        
        if quick_start_ready:
            print_styled(BOLD + GREEN, "✓ Media Ready: " + 
                        f"{image_count} images" + 
                        (f", {audio_count} audio files" if audio_count > 0 else ""))
            print()
            print_styled(GREEN, "1. Quick Create Slideshow (Auto Settings)")
            print_styled(CYAN, "2. Interactive Mode (Guided Settings)")
            print_styled(YELLOW, "3. Batch Processing")
            print_styled(PURPLE, "4. Media Management")
            print_styled(BLUE, "5. Hardware Analysis")
            print_styled(GRAY, "6. Help & Documentation")
            print_styled(LIGHT_GRAY, "7. Exit")
        else:
            print_styled(YELLOW, "⚠️ No images found in images/original/ directory")
            print()
            print_styled(CYAN, "1. Interactive Mode (Guided Settings)")
            print_styled(PURPLE, "2. Media Management")
            print_styled(BLUE, "3. Hardware Analysis")
            print_styled(GRAY, "4. Help & Documentation")
            print_styled(LIGHT_GRAY, "5. Exit")
        
        print()
        
        choice = ask_question("Enter your choice", default="1")
        
        if quick_start_ready:
            # Menu with quick start option
            if choice == "1":
                # Quick create with automatic settings
                quick_create_slideshow()
            elif choice == "2":
                create_slideshow_interactive()
            elif choice == "3":
                batch_process_slideshows()
            elif choice == "4":
                media_management_menu()
            elif choice == "5":
                run_hardware_analysis()
            elif choice == "6":
                show_help()
            elif choice == "7":
                print_styled(GRAY, "Exiting SlideSonic...")
                return
            else:
                print_styled(RED, "Invalid choice. Please try again.")
                time.sleep(1)
        else:
            # Menu without quick start option
            if choice == "1":
                create_slideshow_interactive()
            elif choice == "2":
                media_management_menu()
            elif choice == "3":
                run_hardware_analysis()
            elif choice == "4":
                show_help()
            elif choice == "5":
                print_styled(GRAY, "Exiting SlideSonic...")
                return
            else:
                print_styled(RED, "Invalid choice. Please try again.")
                time.sleep(1)

def media_management_menu():
    """Menu for media management options"""
    while True:
        show_banner()
        
        print_styled(BOLD, "Media Management")
        print()
        print_styled(GREEN, "1. Import Images from Directory")
        print_styled(CYAN, "2. Import Audio from Directory")
        print_styled(YELLOW, "3. Create Test Images")
        print_styled(PURPLE, "4. Organize Existing Images")
        print_styled(BLUE, "5. View Media Information")
        print_styled(GRAY, "6. Return to Main Menu")
        print()
        
        choice = ask_question("Enter your choice", default="1")
        
        if choice == "1":
            import_images()
        elif choice == "2":
            import_audio()
        elif choice == "3":
            create_test_images()
            input("\nPress Enter to continue...")
        elif choice == "4":
            organize_images()
        elif choice == "5":
            view_media_info()
        elif choice == "6":
            return
        else:
            print_styled(RED, "Invalid choice. Please try again.")
            time.sleep(1)

def quick_create_slideshow():
    """Create a slideshow with fully automatic settings"""
    show_banner()
    
    # Load settings
    settings = load_settings()
    
    # Show a spinner while scanning
    show_spinner("Analyzing media files", 1)
    
    # Auto-organize images and find matching audio
    media_data = auto_organize_images()
    
    # Check if we found any images
    if media_data["images"]["count"] == 0:
        print_styled(RED, "Error: No images found in images/original/ directory")
        print_styled(GRAY, "Please add your images to the images/original/ directory and try again.")
        input("\nPress Enter to return to the main menu...")
        return
    
    # Smart project name suggestion
    suggested_name = ""
    
    # Try to derive a name from common prefixes
    prefix_groups = media_data["images"]["groups"]["prefix"]
    if prefix_groups:
        largest_prefix_group = max(prefix_groups.values(), key=len)
        if len(largest_prefix_group) > 1:
            suggested_name = largest_prefix_group[0]["prefix"].replace("_", " ").replace("-", " ").title()
    
    # If no good prefix, try date-based name
    if not suggested_name and media_data["images"]["groups"]["date"]:
        # Use the most common date
        date_groups = media_data["images"]["groups"]["date"]
        most_common_date = max(date_groups.values(), key=len)[0]["date"]
        suggested_name = f"Slideshow {most_common_date}"
    
    # Default fallback
    if not suggested_name:
        suggested_name = f"Slideshow {datetime.now().strftime('%Y-%m-%d')}"
    
    # Auto settings
    hw_info = get_hardware_info()
    
    # Set resolution based on hardware
    if hw_info.get("apple_silicon") or (HAVE_PSUTIL and psutil.cpu_count(logical=False) >= 8):
        resolution = "1920x1080"  # 1080p for good hardware
    else:
        resolution = "1280x720"   # 720p for lower-end hardware
    
    # Set quality based on hardware
    if hw_info.get("apple_silicon") or (HAVE_PSUTIL and psutil.cpu_count(logical=False) >= 8):
        quality = "medium"      # Better quality for good hardware
    else:
        quality = "faster"      # Faster preset for lower-end hardware
    
    # Create output filename
    sanitized_title = suggested_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    output_filename = f"{sanitized_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    
    # Get best encoder
    encoder = detect_best_encoder()
    use_hardware_accel = "qsv" in encoder or "nvenc" in encoder or "videotoolbox" in encoder or "vaapi" in encoder
    
    # Show summary
    print()
    print_styled(BOLD, "Creating Slideshow with Automatic Settings")
    print()
    print_styled(CYAN, f"Title:      {suggested_name}")
    print_styled(CYAN, f"Resolution: {resolution}")
    print_styled(CYAN, f"Quality:    {quality}")
    print_styled(CYAN, f"Output:     {output_filename}")
    print_styled(CYAN, f"Encoder:    {encoder}{' (hardware accelerated)' if use_hardware_accel else ''}")
    
    if media_data["audio"]["selected"]:
        audio_file = media_data["audio"]["selected"]
        print_styled(CYAN, f"Audio:      {os.path.basename(audio_file)}")
        print_styled(CYAN, f"Duration:   {media_data['audio']['duration']:.2f} seconds")
    else:
        audio_file = None
        print_styled(YELLOW, "No audio file selected")
    
    print_styled(CYAN, f"Images:     {media_data['images']['count']} images")
    print_styled(CYAN, f"Per slide:  {media_data['slide_duration']:.2f} seconds")
    print()
    
    # Create encoding script
    create_encoding_script(
        suggested_name, 
        resolution, 
        quality, 
        output_filename, 
        encoder, 
        audio_file,
        media_data["images"]["suggested_order"],
        media_data["slide_duration"]
    )
    
    # Immediate start
    print_styled(GREEN, "Starting encoding process...")
    run_encoding()

def batch_process_slideshows():
    """Process multiple slideshows from subdirectories"""
    show_banner()
    
    print_styled(BOLD, "Batch Processing")
    print()
    
    # Check if we have images in the original directory first
    root_images = count_files("images/original", IMAGE_EXTENSIONS)
    if root_images > 0:
        print_styled(YELLOW, f"Warning: Found {root_images} images in main images/original/ directory")
        print_styled(YELLOW, "These will not be included in batch processing of subdirectories")
        print()
    
    # Look for subdirectories
    batch_dirs = []
    if os.path.exists("images"):
        for item in os.listdir("images"):
            full_path = os.path.join("images", item)
            if os.path.isdir(full_path) and item != "original":
                # Check if this directory has images
                image_count = count_files(full_path, IMAGE_EXTENSIONS)
                if image_count > 0:
                    batch_dirs.append({
                        "name": item,
                        "path": full_path,
                        "image_count": image_count
                    })
    
    if not batch_dirs:
        print_styled(RED, "No subdirectories with images found in the images/ directory")
        print_styled(GRAY, "To use batch processing, create subdirectories in the images/ folder")
        print_styled(GRAY, "Each subdirectory should contain images for a separate slideshow")
        input("\nPress Enter to return to the main menu...")
        return
    
    # Show found directories
    print_styled(GREEN, f"Found {len(batch_dirs)} subdirectories with images:")
    for i, dir_info in enumerate(batch_dirs, 1):
        print_styled(CYAN, f"{i}. {dir_info['name']} ({dir_info['image_count']} images)")
    
    print()
    mode = ask_question("Process all directories or select one? (all/select)", default="all")
    
    dirs_to_process = []
    if mode.lower() == "select":
        dir_num = ask_question("Enter directory number to process", default="1")
        try:
            dir_idx = int(dir_num) - 1
            if 0 <= dir_idx < len(batch_dirs):
                dirs_to_process = [batch_dirs[dir_idx]]
            else:
                print_styled(RED, "Invalid selection, processing all")
                dirs_to_process = batch_dirs
        except ValueError:
            print_styled(RED, "Invalid input, processing all")
            dirs_to_process = batch_dirs
    else:
        dirs_to_process = batch_dirs
    
    # Ask for a common prefix for output files
    print()
    batch_prefix = ask_question("Enter a common prefix for all output files (optional)", default="")
    
    # Process audio choice
    print()
    audio_mode = ask_question("Audio selection: auto/common/none", default="auto")
    
    common_audio = None
    if audio_mode.lower() == "common":
        # Let user select one audio file for all slideshows
        audio_files = smart_scan_directory("song", AUDIO_EXTENSIONS)
        if audio_files["count"] > 0:
            print_styled(GRAY, "Available audio files:")
            audio_list = [f for f in audio_files["files"] if f["type"] == "audio"]
            for i, file_info in enumerate(audio_list, 1):
                print_styled(GRAY, f"{i}. {file_info['name']}")
            
            choice = ask_question("Which audio file would you like to use for all slideshows", default="1")
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(audio_list):
                    common_audio = audio_list[choice_idx]["path"]
            except ValueError:
                print_styled(YELLOW, "Invalid choice, using automatic audio matching")
    
    # Process each directory
    print()
    print_styled(BOLD, f"Processing {len(dirs_to_process)} directories...")
    
    # Auto settings
    hw_info = get_hardware_info()
    
    # Set resolution based on hardware
    if hw_info.get("apple_silicon") or (HAVE_PSUTIL and psutil.cpu_count(logical=False) >= 8):
        resolution = "1920x1080"  # 1080p for good hardware
    else:
        resolution = "1280x720"   # 720p for lower-end hardware
    
    # Set quality based on hardware
    if hw_info.get("apple_silicon") or (HAVE_PSUTIL and psutil.cpu_count(logical=False) >= 8):
        quality = "medium"      # Better quality for good hardware
    else:
        quality = "faster"      # Faster preset for lower-end hardware
    
    # Get best encoder
    encoder = detect_best_encoder()
    
    # Process each directory
    success_count = 0
    for i, dir_info in enumerate(dirs_to_process, 1):
        print()
        print_styled(BOLD, f"Processing directory {i}/{len(dirs_to_process)}: {dir_info['name']}")
        
        # Analyze directory
        dir_images = smart_scan_directory(dir_info['path'], IMAGE_EXTENSIONS)
        
        # Get audio based on mode
        audio_file = None
        if audio_mode.lower() == "auto":
            # Find best match for this directory
            audio_files = smart_scan_directory("song", AUDIO_EXTENSIONS)
            audio_file = find_matching_audio(dir_images, audio_files)
        elif audio_mode.lower() == "common" and common_audio:
            audio_file = common_audio
        
        # Get audio duration if available
        audio_duration = None
        if audio_file:
            audio_duration = get_audio_duration(audio_file)
        
        # Calculate slide duration
        slide_duration = 3.0  # Default
        if audio_duration and dir_images["count"] > 0:
            # Aim for a reasonable duration per slide between 2 and 6 seconds
            raw_duration = audio_duration / dir_images["count"]
            if raw_duration < 2.0:
                slide_duration = 2.0
            elif raw_duration > 6.0:
                slide_duration = 6.0
            else:
                slide_duration = raw_duration
        
        # Create output filename
        output_name = dir_info['name']
        if batch_prefix:
            output_name = f"{batch_prefix}_{output_name}"
        
        output_filename = f"{output_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        # Show info
        print_styled(CYAN, f"Images:     {dir_images['count']} images")
        if audio_file:
            print_styled(CYAN, f"Audio:      {os.path.basename(audio_file)}")
            if audio_duration:
                print_styled(CYAN, f"Duration:   {audio_duration:.2f} seconds")
        else:
            print_styled(YELLOW, "No audio file selected")
        
        # Create encoding script
        create_encoding_script(
            output_name, 
            resolution, 
            quality, 
            output_filename, 
            encoder, 
            audio_file,
            dir_images["suggested_order"],
            slide_duration
        )
        
        # Run encoding
        try:
            subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.realpath(__file__)), "run_encode.py")], check=True)
            print_styled(GREEN, f"✓ Successfully created slideshow: {output_filename}")
            success_count += 1
        except subprocess.SubprocessError as e:
            print_styled(RED, f"✗ Failed to create slideshow for {dir_info['name']}: {e}")
    
    # Show summary
    print()
    print_styled(BOLD, "Batch Processing Complete")
    print_styled(GREEN if success_count == len(dirs_to_process) else YELLOW, 
                f"Successfully created {success_count}/{len(dirs_to_process)} slideshows")
    
    input("\nPress Enter to return to the main menu...")

def import_images():
    """Import images from another directory"""
    show_banner()
    
    print_styled(BOLD, "Import Images")
    print()
    
    source_dir = ask_question("Enter the path to the directory containing images", default="")
    if not source_dir or not os.path.isdir(source_dir):
        print_styled(RED, "Invalid directory path")
        input("\nPress Enter to return to the menu...")
        return
    
    # Check if the source directory has images
    image_files = [f for f in os.listdir(source_dir) 
                 if os.path.isfile(os.path.join(source_dir, f)) and 
                 any(f.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)]
    
    if not image_files:
        print_styled(RED, "No image files found in the specified directory")
        input("\nPress Enter to return to the menu...")
        return
    
    print_styled(GREEN, f"Found {len(image_files)} image files")
    
    # Ask if user wants to copy to main directory or create a subdirectory
    print()
    mode = ask_question("Import to: 1) Main images/original directory, 2) Create a new subdirectory", default="1")
    
    target_dir = "images/original"
    if mode == "2":
        subdir_name = ask_question("Enter subdirectory name", default="imported")
        target_dir = f"images/{subdir_name}"
    
    # Create target directory if needed
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy files
    print()
    print_styled(BOLD, f"Copying {len(image_files)} files to {target_dir}...")
    
    import shutil
    copied = 0
    for filename in image_files:
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)
        
        try:
            shutil.copy2(source_path, target_path)
            copied += 1
            sys.stdout.write(f"\rCopied {copied}/{len(image_files)} files...")
            sys.stdout.flush()
        except Exception as e:
            print_styled(RED, f"\nError copying {filename}: {e}")
    
    print()
    print_styled(GREEN, f"✓ Successfully imported {copied}/{len(image_files)} images to {target_dir}")
    
    input("\nPress Enter to return to the menu...")

def import_audio():
    """Import audio files from another directory"""
    show_banner()
    
    print_styled(BOLD, "Import Audio")
    print()
    
    source_dir = ask_question("Enter the path to the directory containing audio files", default="")
    if not source_dir or not os.path.isdir(source_dir):
        print_styled(RED, "Invalid directory path")
        input("\nPress Enter to return to the menu...")
        return
    
    # Check if the source directory has audio files
    audio_files = [f for f in os.listdir(source_dir) 
                 if os.path.isfile(os.path.join(source_dir, f)) and 
                 any(f.lower().endswith(ext) for ext in AUDIO_EXTENSIONS)]
    
    if not audio_files:
        print_styled(RED, "No audio files found in the specified directory")
        input("\nPress Enter to return to the menu...")
        return
    
    print_styled(GREEN, f"Found {len(audio_files)} audio files")
    
    # Create target directory if needed
    target_dir = "song"
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy files
    print()
    print_styled(BOLD, f"Copying {len(audio_files)} files to {target_dir}...")
    
    import shutil
    copied = 0
    for filename in audio_files:
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)
        
        try:
            shutil.copy2(source_path, target_path)
            copied += 1
            sys.stdout.write(f"\rCopied {copied}/{len(audio_files)} files...")
            sys.stdout.flush()
        except Exception as e:
            print_styled(RED, f"\nError copying {filename}: {e}")
    
    print()
    print_styled(GREEN, f"✓ Successfully imported {copied}/{len(audio_files)} audio files to {target_dir}")
    
    input("\nPress Enter to return to the menu...")

def organize_images():
    """Organize existing images into folders based on patterns"""
    show_banner()
    
    print_styled(BOLD, "Organize Images")
    print()
    
    # Check if we have images
    image_count = count_files("images/original", IMAGE_EXTENSIONS)
    if image_count == 0:
        print_styled(RED, "No images found in images/original/ directory")
        input("\nPress Enter to return to the menu...")
        return
    
    print_styled(GREEN, f"Found {image_count} images in images/original/")
    
    # Analyze images
    print_styled(GRAY, "Analyzing images...")
    images = smart_scan_directory("images/original", IMAGE_EXTENSIONS)
    
    # Show grouping options
    print()
    print_styled(BOLD, "Available Grouping Options:")
    
    grouping_methods = []
    
    # Date-based grouping
    if images["groups"]["date"]:
        date_count = len(images["groups"]["date"])
        print_styled(CYAN, f"1. By Date ({date_count} date groups)")
        grouping_methods.append("date")
    else:
        print_styled(GRAY, "1. By Date (no date patterns found)")
    
    # Prefix-based grouping
    if images["groups"]["prefix"]:
        prefix_count = len(images["groups"]["prefix"])
        print_styled(CYAN, f"2. By Prefix ({prefix_count} prefix groups)")
        grouping_methods.append("prefix")
    else:
        print_styled(GRAY, "2. By Prefix (no common prefixes found)")
    
    # Sequence-based grouping
    if images["groups"]["sequence"]:
        sequence_count = len(images["groups"]["sequence"])
        print_styled(CYAN, f"3. By Sequence ({sequence_count} sequence groups)")
        grouping_methods.append("sequence")
    else:
        print_styled(GRAY, "3. By Sequence (no sequence patterns found)")
    
    # Equal groups
    print_styled(CYAN, "4. Into Equal-Sized Groups")
    grouping_methods.append("equal")
    
    print()
    choice = ask_question("Select grouping method", default="1")
    
    try:
        method_idx = int(choice) - 1
        if 0 <= method_idx < len(grouping_methods):
            method = grouping_methods[method_idx]
        else:
            print_styled(RED, "Invalid choice")
            input("\nPress Enter to return to the menu...")
            return
    except (ValueError, IndexError):
        print_styled(RED, "Invalid choice")
        input("\nPress Enter to return to the menu...")
        return
    
    # Handle grouping methods
    if method == "date":
        organize_by_groups(images["groups"]["date"], "date")
    elif method == "prefix":
        organize_by_groups(images["groups"]["prefix"], "prefix")
    elif method == "sequence":
        organize_by_groups(images["groups"]["sequence"], "sequence")
    elif method == "equal":
        # Get number of groups
        print()
        try:
            num_groups = int(ask_question("Number of equal-sized groups to create", default="3"))
            if num_groups < 1:
                num_groups = 3
        except ValueError:
            num_groups = 3
        
        # Create equal-sized groups
        organize_equal_groups(images["files"], num_groups)
    
    input("\nPress Enter to return to the menu...")

def organize_by_groups(groups, group_type):
    """Organize images into subdirectories based on group data"""
    if not groups:
        print_styled(RED, "No valid groups found")
        return
    
    print()
    print_styled(BOLD, f"Found {len(groups)} {group_type} groups")
    
    # Ask which groups to organize
    print()
    mode = ask_question("Organize: 1) All groups, 2) Select specific groups", default="1")
    
    groups_to_organize = []
    if mode == "2":
        # Show available groups
        print()
        print_styled(BOLD, "Available groups:")
        for i, (group_name, files) in enumerate(groups.items(), 1):
            print_styled(CYAN, f"{i}. {group_name} ({len(files)} files)")
        
        print()
        group_choices = ask_question("Enter group numbers to organize (comma-separated)", default="1")
        
        try:
            indices = [int(idx.strip()) - 1 for idx in group_choices.split(",")]
            group_names = list(groups.keys())
            
            for idx in indices:
                if 0 <= idx < len(group_names):
                    groups_to_organize.append((group_names[idx], groups[group_names[idx]]))
        except ValueError:
            print_styled(RED, "Invalid input, organizing all groups")
            groups_to_organize = list(groups.items())
    else:
        groups_to_organize = list(groups.items())
    
    # Create base directory name
    base_dir = f"images/{group_type}_groups"
    
    # Create directories and move files
    print()
    print_styled(BOLD, f"Organizing {len(groups_to_organize)} groups...")
    
    import shutil
    total_moved = 0
    
    for group_name, files in groups_to_organize:
        # Create sanitized directory name
        dir_name = re.sub(r'[^\w\-_]', '_', group_name)
        target_dir = os.path.join(base_dir, dir_name)
        
        # Create directory
        os.makedirs(target_dir, exist_ok=True)
        
        # Move files
        moved = 0
        for file_info in files:
            source_path = file_info["path"]
            target_path = os.path.join(target_dir, os.path.basename(source_path))
            
            try:
                shutil.copy2(source_path, target_path)
                moved += 1
                total_moved += 1
            except Exception as e:
                print_styled(RED, f"Error copying {os.path.basename(source_path)}: {e}")
        
        print_styled(GREEN, f"✓ Group '{group_name}': moved {moved}/{len(files)} files to {target_dir}")
    
    print()
    print_styled(BOLD + GREEN, f"Successfully organized {total_moved} files into {len(groups_to_organize)} directories")
    print_styled(GRAY, f"Files remain in the original location and can now be used for batch processing")

def organize_equal_groups(files, num_groups):
    """Organize images into a specified number of equal-sized groups"""
    if not files:
        print_styled(RED, "No files found")
        return
    
    # Sort files by name
    sorted_files = sorted(files, key=lambda x: x["name"])
    
    # Calculate group size
    total_files = len(sorted_files)
    group_size = total_files // num_groups
    remainder = total_files % num_groups
    
    # Create groups
    groups = []
    start = 0
    for i in range(num_groups):
        # Add one extra item to early groups if we have a remainder
        current_size = group_size + (1 if i < remainder else 0)
        end = start + current_size
        groups.append(sorted_files[start:end])
        start = end
    
    # Create base directory
    base_dir = "images/equal_groups"
    
    # Create directories and move files
    print()
    print_styled(BOLD, f"Organizing into {num_groups} equal groups...")
    
    import shutil
    total_moved = 0
    
    for i, group_files in enumerate(groups, 1):
        # Create directory
        target_dir = os.path.join(base_dir, f"group_{i:02d}")
        os.makedirs(target_dir, exist_ok=True)
        
        # Move files
        moved = 0
        for file_info in group_files:
            source_path = file_info["path"]
            target_path = os.path.join(target_dir, os.path.basename(source_path))
            
            try:
                shutil.copy2(source_path, target_path)
                moved += 1
                total_moved += 1
            except Exception as e:
                print_styled(RED, f"Error copying {os.path.basename(source_path)}: {e}")
        
        print_styled(GREEN, f"✓ Group {i}: moved {moved}/{len(group_files)} files to {target_dir}")
    
    print()
    print_styled(BOLD + GREEN, f"Successfully organized {total_moved} files into {num_groups} directories")
    print_styled(GRAY, f"Files remain in the original location and can now be used for batch processing")

def view_media_info():
    """View detailed information about available media"""
    show_banner()
    
    print_styled(BOLD, "Media Information")
    print()
    
    # Show spinner while scanning
    show_spinner("Scanning media files", 1)
    
    # Scan all directories
    images_original = smart_scan_directory("images/original", IMAGE_EXTENSIONS)
    audio_files = smart_scan_directory("song", AUDIO_EXTENSIONS)
    
    # Check images in subdirectories
    image_subdirs = []
    if os.path.exists("images"):
        for item in os.listdir("images"):
            full_path = os.path.join("images", item)
            if os.path.isdir(full_path) and item != "original":
                # Check if this directory has images
                subdir_images = smart_scan_directory(full_path, IMAGE_EXTENSIONS)
                if subdir_images["count"] > 0:
                    image_subdirs.append({
                        "name": item,
                        "path": full_path,
                        "data": subdir_images
                    })
    
    # Main images directory
    print_styled(BOLD + CYAN, "Main Images Directory:")
    if images_original["count"] > 0:
        print_styled(GREEN, f"✓ Found {images_original['count']} images in images/original/")
        
        # Show group information
        if images_original["groups"]["date"]:
            print_styled(CYAN, f"  - {len(images_original['groups']['date'])} date groups")
        if images_original["groups"]["prefix"]:
            print_styled(CYAN, f"  - {len(images_original['groups']['prefix'])} prefix groups")
        if images_original["groups"]["sequence"]:
            print_styled(CYAN, f"  - {len(images_original['groups']['sequence'])} sequence groups")
            
        # Show file types
        ext_groups = images_original["groups"]["extension"]
        if ext_groups:
            print_styled(GRAY, "  File types:")
            for ext, files in ext_groups.items():
                print_styled(GRAY, f"    {ext}: {len(files)} files")
    else:
        print_styled(YELLOW, "⚠️ No images found in main images/original/ directory")
    
    # Image subdirectories
    if image_subdirs:
        print()
        print_styled(BOLD + CYAN, "Image Subdirectories:")
        for subdir in image_subdirs:
            print_styled(GREEN, f"✓ {subdir['name']}: {subdir['data']['count']} images")
    
    # Audio files
    print()
    print_styled(BOLD + CYAN, "Audio Files:")
    if audio_files["count"] > 0:
        print_styled(GREEN, f"✓ Found {audio_files['count']} audio files in song/ directory")
        
        # Show file types
        ext_groups = audio_files["groups"]["extension"]
        if ext_groups:
            print_styled(GRAY, "  File types:")
            for ext, files in ext_groups.items():
                print_styled(GRAY, f"    {ext}: {len(files)} files")
                
        # Show audio durations if possible
        audio_list = [f for f in audio_files["files"] if f["type"] == "audio"]
        if audio_list:
            print_styled(GRAY, "  Audio details:")
            for i, file_info in enumerate(audio_list[:5], 1):  # Show only first 5 for brevity
                duration = get_audio_duration(file_info["path"])
                if duration:
                    mins, secs = divmod(duration, 60)
                    print_styled(GRAY, f"    {i}. {file_info['name']}: {int(mins)}:{int(secs):02d}")
                else:
                    print_styled(GRAY, f"    {i}. {file_info['name']}")
            
            if len(audio_list) > 5:
                print_styled(GRAY, f"    ... and {len(audio_list) - 5} more")
    else:
        print_styled(YELLOW, "⚠️ No audio files found in song/ directory")
    
    # Show suggested slideshow configurations
    if images_original["count"] > 0:
        print()
        print_styled(BOLD + CYAN, "Suggested Configurations:")
        
        # Find best matching audio
        best_audio = find_matching_audio(images_original, audio_files)
        if best_audio:
            audio_filename = os.path.basename(best_audio)
            audio_duration = get_audio_duration(best_audio)
            
            print_styled(GREEN, f"✓ Best matching audio: {audio_filename}")
            if audio_duration:
                mins, secs = divmod(audio_duration, 60)
                print_styled(CYAN, f"  - Audio duration: {int(mins)}:{int(secs):02d}")
                
                # Calculate optimal slide duration
                slide_duration = 3.0  # Default
                if images_original["count"] > 0:
                    raw_duration = audio_duration / images_original["count"]
                    if raw_duration < 2.0:
                        slide_duration = 2.0
                    elif raw_duration > 6.0:
                        slide_duration = 6.0
                    else:
                        slide_duration = raw_duration
                
                print_styled(CYAN, f"  - Suggested slide duration: {slide_duration:.2f} seconds")
                print_styled(CYAN, f"  - Total slideshow duration: {slide_duration * images_original['count']:.2f} seconds")
        else:
            print_styled(YELLOW, "⚠️ No matching audio found")
            print_styled(CYAN, f"  - Suggested slide duration: 3.00 seconds (default)")
            print_styled(CYAN, f"  - Total slideshow duration: {3.0 * images_original['count']:.2f} seconds")
    
    input("\nPress Enter to return to the menu...")

def get_audio_duration(audio_path):
    """Get the duration of an audio file using FFmpeg"""
    try:
        process = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 
                               'default=noprint_wrappers=1:nokey=1', audio_path], 
                               capture_output=True, text=True, check=True)
        duration = float(process.stdout.strip())
        return duration
    except (subprocess.SubprocessError, ValueError):
        return None

def find_matching_audio(images_data, audio_data):
    """Find the best matching audio file for the given images"""
    if not audio_data or audio_data["count"] == 0:
        return None
    
    # Get all audio files
    audio_files = [f["path"] for f in audio_data["files"] if f["type"] == "audio"]
    if not audio_files:
        return None
    
    # If we only have one audio file, return it
    if len(audio_files) == 1:
        return audio_files[0]
    
    # If we have date-based image groups, try to match audio files by date
    if images_data["groups"]["date"]:
        # Get the most common date
        most_common_date = max(images_data["groups"]["date"].values(), key=len)[0]["date"]
        
        # Try to find audio files with matching date in filename
        for audio_file in audio_files:
            audio_name = os.path.basename(audio_file)
            if most_common_date in audio_name:
                return audio_file
    
    # If we have a prefix group, try to match by prefix
    if images_data["groups"]["prefix"]:
        largest_prefix_group = max(images_data["groups"]["prefix"].items(), key=lambda x: len(x[1]))
        prefix = largest_prefix_group[0]
        
        # Try to find audio files with similar prefix
        for audio_file in audio_files:
            audio_name = os.path.basename(audio_file)
            if prefix in audio_name:
                return audio_file
    
    # Default to the first audio file
    return audio_files[0]

def smart_scan_directory(directory, extensions):
    """Scan a directory for files and organize them into groups"""
    result = {
        "count": 0,
        "files": [],
        "groups": {
            "date": {},
            "prefix": {},
            "sequence": {},
            "extension": {}
        }
    }
    
    # Check if directory exists
    if not os.path.exists(directory):
        return result
    
    # Scan for files with the requested extensions
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # Skip directories and hidden files
        if os.path.isdir(file_path) or filename.startswith('.'):
            continue
        
        # Check file extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in extensions:
            continue
        
        # Determine file type
        file_type = None
        if ext in IMAGE_EXTENSIONS:
            file_type = "image"
        elif ext in AUDIO_EXTENSIONS:
            file_type = "audio"
        elif ext in VIDEO_EXTENSIONS:
            file_type = "video"
        
        # Add file to the result
        file_info = {
            "name": filename,
            "path": file_path,
            "ext": ext,
            "type": file_type
        }
        
        result["files"].append(file_info)
        result["count"] += 1
        
        # Add to extension group
        if ext not in result["groups"]["extension"]:
            result["groups"]["extension"][ext] = []
        result["groups"]["extension"][ext].append(file_info)
        
        # Skip the rest for non-image files
        if file_type != "image":
            continue
        
        # Extract date from filename
        date_found = False
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1)
                if date_str not in result["groups"]["date"]:
                    result["groups"]["date"][date_str] = []
                
                file_info["date"] = date_str
                result["groups"]["date"][date_str].append(file_info)
                date_found = True
                break
        
        # Extract sequence number
        sequence_found = False
        for pattern in SEQUENCE_PATTERNS:
            match = re.search(pattern, filename)
            if match:
                seq_num = match.group(1)
                
                # Find common prefix (part before the sequence number)
                prefix_parts = filename.split(seq_num, 1)
                if len(prefix_parts) == 2:
                    prefix = prefix_parts[0]
                    
                    # Add to sequence group
                    if prefix not in result["groups"]["sequence"]:
                        result["groups"]["sequence"][prefix] = []
                    
                    file_info["sequence"] = {
                        "prefix": prefix,
                        "number": int(seq_num)
                    }
                    
                    result["groups"]["sequence"][prefix].append(file_info)
                    sequence_found = True
                    break
        
        # Extract prefix (first part of the filename)
        if not sequence_found:
            # Use first word/segment as prefix
            name_parts = re.split(r'[-_\s]', os.path.splitext(filename)[0], 1)
            if len(name_parts) > 1:
                prefix = name_parts[0]
                
                if prefix not in result["groups"]["prefix"]:
                    result["groups"]["prefix"][prefix] = []
                
                file_info["prefix"] = prefix
                result["groups"]["prefix"][prefix].append(file_info)
    
    return result

def auto_organize_images(recursive=False):
    """Automatically analyze and organize images and audio files"""
    result = {
        "images": {
            "count": 0,
            "files": [],
            "groups": {
                "date": {},
                "prefix": {},
                "sequence": {}
            },
            "suggested_order": []
        },
        "audio": {
            "files": {
                "count": 0,
                "files": []
            },
            "selected": None,
            "duration": None
        },
        "slide_duration": 3.0  # Default slide duration
    }
    
    # Scan images directory
    images_data = smart_scan_directory("images/original", IMAGE_EXTENSIONS)
    
    # Update result with image data
    result["images"]["count"] = images_data["count"]
    result["images"]["files"] = images_data["files"]
    result["images"]["groups"] = images_data["groups"]
    
    # Determine optimal order for images
    if images_data["count"] > 0:
        # First try to use sequence data
        has_sequence = False
        for prefix, files in images_data["groups"]["sequence"].items():
            if len(files) > 1:
                # Sort by sequence number
                sorted_files = sorted(files, key=lambda x: x["sequence"]["number"])
                result["images"]["suggested_order"] = [file_info["path"] for file_info in sorted_files]
                has_sequence = True
                break
        
        # If no sequence found, try to use date
        if not has_sequence and images_data["groups"]["date"]:
            # Find the largest date group
            largest_date_group = max(images_data["groups"]["date"].values(), key=len)
            if len(largest_date_group) > 1:
                # Sort by name within the same date
                sorted_files = sorted(largest_date_group, key=lambda x: x["name"])
                result["images"]["suggested_order"] = [file_info["path"] for file_info in sorted_files]
                
                # Add remaining files
                remaining = [f for f in images_data["files"] if f["path"] not in result["images"]["suggested_order"]]
                remaining_sorted = sorted(remaining, key=lambda x: x["name"])
                result["images"]["suggested_order"].extend([file_info["path"] for file_info in remaining_sorted])
            else:
                # Sort all files by name
                sorted_files = sorted(images_data["files"], key=lambda x: x["name"])
                result["images"]["suggested_order"] = [file_info["path"] for file_info in sorted_files]
        else:
            # Sort all files by name
            sorted_files = sorted(images_data["files"], key=lambda x: x["name"])
            result["images"]["suggested_order"] = [file_info["path"] for file_info in sorted_files]
    
    # Scan audio directory
    audio_data = smart_scan_directory("song", AUDIO_EXTENSIONS)
    
    # Update result with audio data
    result["audio"]["files"]["count"] = audio_data["count"]
    result["audio"]["files"]["files"] = audio_data["files"]
    
    # Find matching audio file
    best_audio = find_matching_audio(images_data, audio_data)
    if best_audio:
        result["audio"]["selected"] = best_audio
        
        # Get audio duration
        audio_duration = get_audio_duration(best_audio)
        if audio_duration:
            result["audio"]["duration"] = audio_duration
            
            # Calculate optimal slide duration based on audio length
            if images_data["count"] > 0:
                raw_duration = audio_duration / images_data["count"]
                if raw_duration < 2.0:
                    result["slide_duration"] = 2.0
                elif raw_duration > 6.0:
                    result["slide_duration"] = 6.0
                else:
                    result["slide_duration"] = raw_duration
    
    return result

def main():
    """Main function"""
    global USE_COLORS, USE_UNICODE, USE_ANIMATIONS
    
    # Parse command line arguments
    args = parse_args()
    
    # Check version flag
    if args.version:
        print(f"{PROGRAM_NAME} v{VERSION}")
        return
    
    # Set accessibility options
    USE_COLORS = not args.no_colors
    USE_UNICODE = not args.no_unicode
    USE_ANIMATIONS = not args.no_animations
    
    # Run hardware analysis if requested
    if args.hardware_analysis:
        run_hardware_analysis()
        return
        
    # Run quick slideshow creation if requested
    if args.quick:
        quick_create_slideshow()
        return
        
    # Run batch processing if requested
    if args.batch:
        batch_process_slideshows()
        return
    
    # Show main menu
    show_main_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 