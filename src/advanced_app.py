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
BLUE = "\033[38;5;32m"      # Apple blue
GRAY = "\033[38;5;242m"     # Dark gray
LIGHT_GRAY = "\033[38;5;248m" # Light gray
GREEN = "\033[38;5;35m"     # Success green
YELLOW = "\033[38;5;220m"   # Warning yellow
RED = "\033[38;5;196m"      # Error red
CYAN = "\033[38;5;87m"      # Info cyan
PURPLE = "\033[38;5;141m"   # Process purple

# Background colors
BG_BLUE = "\033[48;5;24m"   # Blue background
BG_DARK = "\033[48;5;235m"  # Dark background

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
    """Display the SlideSonic logo with modern clean aesthetics"""
    if USE_COLORS and USE_UNICODE:
        # Use a cleaner, more modern logo style
        print(f"{BLUE}{BOLD}SlideSonic{RESET}")
    else:
        center_text(f"{PROGRAM_NAME}")

def show_banner():
    """Display the application banner with modern clean aesthetics"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Get terminal width
    width = shutil.get_terminal_size().columns
    
    # Create styled header bar
    if USE_COLORS:
        print(f"{BG_BLUE}{' ' * width}{RESET}")
    
    # Display clean, modern logo
    width = shutil.get_terminal_size().columns
    title = f"{BLUE}{BOLD}SlideSonic{RESET}"
    padding = (width - len(title.replace(BLUE, "").replace(BOLD, "").replace(RESET, ""))) // 2
    print(f"{' ' * padding}{title}")
    
    # Add subtitle with elegant typography
    if USE_COLORS:
        padding = (width - 32) // 2  # "Create stunning slideshow videos" is 32 chars
        print(f"{' ' * padding}{BOLD}{CYAN}Create stunning slideshow videos{RESET}")
        
        # Add version and branding
        version_text = f"Version {VERSION} | Chamath Thiwanka (CHX)"
        version_padding = (width - len(version_text)) // 2
        print(f"{' ' * version_padding}{GRAY}{version_text}{RESET}")
        
        # Add github link
        github_text = f"https://github.com/chama-x/SlideSonic-2025"
        github_padding = (width - len(github_text)) // 2
        print(f"{' ' * github_padding}{LIGHT_GRAY}{github_text}{RESET}")
        
        # Add elegant separator
        if USE_UNICODE:
            separator = "───────────────────────────────────────────"
            separator = separator.center(width)
            print(f"{GRAY}{separator}{RESET}")
        else:
            print(f"{GRAY}{'-' * width}{RESET}")
    else:
        center_text("Create stunning slideshow videos")
        center_text(f"Version {VERSION} | Chamath Thiwanka (CHX)")
        center_text("https://github.com/chama-x/SlideSonic-2025")
        print("-" * width)
    
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
    """Analyze hardware capabilities with Apple-inspired design aesthetics"""
    show_banner()
    
    # Get terminal width for centered content
    width = shutil.get_terminal_size().columns
    menu_width = min(80, width - 10)
    
    # Display section header
    if USE_COLORS:
        section_title = " Hardware Analysis "
        padding = (menu_width - len(section_title)) // 2
        if USE_UNICODE:
            print(f"{' ' * padding}{BOLD}{BLUE}•{section_title}•{RESET}")
            print(f"{GRAY}{'─' * menu_width}{RESET}")
        else:
            print(f"{' ' * padding}{BOLD}{BLUE}{section_title}{RESET}")
            print(f"{GRAY}{'-' * menu_width}{RESET}")
    else:
        print("Hardware Analysis")
        print("-" * menu_width)
    
    print()
    
    # Show animation while analyzing
    if USE_COLORS:
        print(f"{BOLD}Analyzing system capabilities...{RESET}")
    else:
        print("Analyzing system capabilities...")
    
    show_spinner("Gathering system information", 2)
    
    # Get hardware info
    hw_info = get_hardware_info()
    
    # Output in a nice box
    if USE_COLORS:
        # Box style
        status_box_top = f"{LIGHT_GRAY}┌{'─' * (menu_width - 2)}┐{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}+{'-' * (menu_width - 2)}+{RESET}"
        status_box_bottom = f"{LIGHT_GRAY}└{'─' * (menu_width - 2)}┘{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}+{'-' * (menu_width - 2)}+{RESET}"
        status_side = f"{LIGHT_GRAY}│{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}|{RESET}"
        divider = f"{LIGHT_GRAY}├{'─' * (menu_width - 2)}┤{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}+{'-' * (menu_width - 2)}+{RESET}"
        
        print("\n" + status_box_top)
        print(f"{status_side} {BOLD}System Information{RESET}{' ' * (menu_width - 20)}{status_side}")
        print(divider)
        
        # Create nice rows
        def info_row(label, value, color=CYAN):
            label_display = f"{BOLD}{label}:{RESET}"
            value_display = f"{color}{value}{RESET}"
            padding = menu_width - len(label) - len(value) - 5
            return f"{status_side} {label_display} {value_display}{' ' * padding} {status_side}"
        
        # System info
        print(info_row("Operating System", f"{hw_info.get('os_name', 'Unknown')} {hw_info.get('os_version', '')}"))
        
        # CPU info
        if hw_info.get("apple_silicon"):
            print(info_row("Processor", f"Apple Silicon {hw_info.get('cpu_model', '')}", GREEN))
        else:
            print(info_row("Processor", hw_info.get('cpu_model', 'Unknown')))
        
        print(info_row("CPU Cores", f"{hw_info.get('cpu_cores', 'Unknown')} cores, {hw_info.get('cpu_threads', 'Unknown')} threads"))
        
        # RAM
        if 'memory_gb' in hw_info:
            print(info_row("Memory", f"{hw_info['memory_gb']:.1f} GB"))
        
        print(divider)
        print(f"{status_side} {BOLD}Encoding Capabilities{RESET}{' ' * (menu_width - 23)}{status_side}")
        
        # Video encoders
        if hw_info.get("has_videotoolbox") and hw_info.get("apple_silicon"):
            print(info_row("Apple VideoToolbox", "Available (Hardware Acceleration)", GREEN))
        elif hw_info.get("has_videotoolbox"):
            print(info_row("Apple VideoToolbox", "Available", GREEN))
        else:
            print(info_row("Apple VideoToolbox", "Not Available", YELLOW))
        
        if hw_info.get("has_nvidia"):
            print(info_row("NVIDIA GPU", f"{hw_info.get('gpu_model', 'Available')}", GREEN))
            if hw_info.get("has_nvenc"):
                print(info_row("NVIDIA NVENC", "Available (Hardware Acceleration)", GREEN))
            else:
                print(info_row("NVIDIA NVENC", "Not Available", YELLOW))
        
        if hw_info.get("has_intel_qsv"):
            print(info_row("Intel QuickSync", "Available (Hardware Acceleration)", GREEN))
        elif hw_info.get("has_intel"):
            print(info_row("Intel QuickSync", "Not Available", YELLOW))
        
        if hw_info.get("has_vaapi"):
            print(info_row("VA-API", "Available (Hardware Acceleration)", GREEN))
        
        # FFmpeg version
        if hw_info.get("ffmpeg_version"):
            print(info_row("FFmpeg", hw_info.get("ffmpeg_version", "Unknown")))
        
        print(divider)
        print(f"{status_side} {BOLD}Performance Estimate{RESET}{' ' * (menu_width - 22)}{status_side}")
        
        # Performance rating
        perf_score = 0
        if hw_info.get("apple_silicon"):
            perf_score += 4
        elif hw_info.get("cpu_cores", 0) >= 8:
            perf_score += 3
        elif hw_info.get("cpu_cores", 0) >= 4:
            perf_score += 2
        else:
            perf_score += 1
            
        if hw_info.get("has_videotoolbox") or hw_info.get("has_nvenc") or hw_info.get("has_intel_qsv") or hw_info.get("has_vaapi"):
            perf_score += 2
            
        if hw_info.get("memory_gb", 0) >= 16:
            perf_score += 2
        elif hw_info.get("memory_gb", 0) >= 8:
            perf_score += 1
        
        # Performance tier
        performance_tier = ""
        if perf_score >= 7:
            performance_tier = f"{GREEN}Excellent{RESET} - Can handle 4K with high quality"
        elif perf_score >= 5:
            performance_tier = f"{CYAN}Good{RESET} - Suitable for 1080p high quality"
        elif perf_score >= 3:
            performance_tier = f"{YELLOW}Moderate{RESET} - Best for 1080p standard quality"
        else:
            performance_tier = f"{RED}Basic{RESET} - Recommended 720p, standard quality"
        
        print(info_row("Performance", performance_tier, ""))
        
        # Best settings recommendation
        recommended_res = "3840x2160" if perf_score >= 7 else "1920x1080" if perf_score >= 3 else "1280x720"
        recommended_quality = "veryslow" if perf_score >= 7 else "slow" if perf_score >= 5 else "medium" if perf_score >= 3 else "fast"
        
        print(info_row("Recommended Resolution", recommended_res))
        print(info_row("Recommended Quality", recommended_quality))
        
        # Calculate expected encoding time per minute of video
        base_time = 60  # seconds per minute of video at 1080p medium preset
        time_factor = 1.0
        
        if "3840x2160" in recommended_res:
            time_factor *= 4.0
        elif "1280x720" in recommended_res:
            time_factor *= 0.5
            
        if "veryslow" in recommended_quality:
            time_factor *= 4.0
        elif "slow" in recommended_quality:
            time_factor *= 2.0
        elif "fast" in recommended_quality:
            time_factor *= 0.5
            
        if hw_info.get("has_videotoolbox") or hw_info.get("has_nvenc") or hw_info.get("has_intel_qsv") or hw_info.get("has_vaapi"):
            time_factor *= 0.25
            
        if hw_info.get("apple_silicon"):
            time_factor *= 0.5
        elif hw_info.get("cpu_cores", 0) >= 8:
            time_factor *= 0.7
            
        estimated_time = base_time * time_factor
        estimated_str = f"{int(estimated_time // 60)}:{int(estimated_time % 60):02d}" if estimated_time >= 60 else f"{int(estimated_time)} seconds"
        
        print(info_row("Est. Processing Time", f"{estimated_str} per minute of video"))
        
        print(status_box_bottom)
    else:
        # Non-colored version
        print("\nSystem Information:")
        print("-" * menu_width)
        print(f"Operating System: {hw_info.get('os_name', 'Unknown')} {hw_info.get('os_version', '')}")
        print(f"Processor: {hw_info.get('cpu_model', 'Unknown')}")
        print(f"CPU Cores: {hw_info.get('cpu_cores', 'Unknown')} cores, {hw_info.get('cpu_threads', 'Unknown')} threads")
        
        if 'memory_gb' in hw_info:
            print(f"Memory: {hw_info['memory_gb']:.1f} GB")
        
        print("\nEncoding Capabilities:")
        print("-" * menu_width)
        
        if hw_info.get("has_videotoolbox"):
            print(f"Apple VideoToolbox: Available (Hardware Acceleration)")
        else:
            print(f"Apple VideoToolbox: Not Available")
        
        if hw_info.get("has_nvidia"):
            print(f"NVIDIA GPU: {hw_info.get('gpu_model', 'Available')}")
            if hw_info.get("has_nvenc"):
                print(f"NVIDIA NVENC: Available (Hardware Acceleration)")
            else:
                print(f"NVIDIA NVENC: Not Available")
        
        if hw_info.get("has_intel_qsv"):
            print(f"Intel QuickSync: Available (Hardware Acceleration)")
        elif hw_info.get("has_intel"):
            print(f"Intel QuickSync: Not Available")
        
        if hw_info.get("has_vaapi"):
            print(f"VA-API: Available (Hardware Acceleration)")
        
        if hw_info.get("ffmpeg_version"):
            print(f"FFmpeg: {hw_info.get('ffmpeg_version', 'Unknown')}")
        
        print("\nPerformance Estimate:")
        print("-" * menu_width)
        
        # Performance rating
        perf_score = 0
        if hw_info.get("apple_silicon"):
            perf_score += 4
        elif hw_info.get("cpu_cores", 0) >= 8:
            perf_score += 3
        elif hw_info.get("cpu_cores", 0) >= 4:
            perf_score += 2
        else:
            perf_score += 1
            
        if hw_info.get("has_videotoolbox") or hw_info.get("has_nvenc") or hw_info.get("has_intel_qsv") or hw_info.get("has_vaapi"):
            perf_score += 2
            
        if hw_info.get("memory_gb", 0) >= 16:
            perf_score += 2
        elif hw_info.get("memory_gb", 0) >= 8:
            perf_score += 1
        
        # Performance tier
        if perf_score >= 7:
            performance_tier = "Excellent - Can handle 4K with high quality"
        elif perf_score >= 5:
            performance_tier = "Good - Suitable for 1080p high quality"
        elif perf_score >= 3:
            performance_tier = "Moderate - Best for 1080p standard quality"
        else:
            performance_tier = "Basic - Recommended 720p, standard quality"
        
        print(f"Performance: {performance_tier}")
        
        # Best settings recommendation
        recommended_res = "3840x2160" if perf_score >= 7 else "1920x1080" if perf_score >= 3 else "1280x720"
        recommended_quality = "veryslow" if perf_score >= 7 else "slow" if perf_score >= 5 else "medium" if perf_score >= 3 else "fast"
        
        print(f"Recommended Resolution: {recommended_res}")
        print(f"Recommended Quality: {recommended_quality}")
        
        # Calculate expected encoding time per minute of video
        base_time = 60  # seconds per minute of video at 1080p medium preset
        time_factor = 1.0
        
        if "3840x2160" in recommended_res:
            time_factor *= 4.0
        elif "1280x720" in recommended_res:
            time_factor *= 0.5
            
        if "veryslow" in recommended_quality:
            time_factor *= 4.0
        elif "slow" in recommended_quality:
            time_factor *= 2.0
        elif "fast" in recommended_quality:
            time_factor *= 0.5
            
        if hw_info.get("has_videotoolbox") or hw_info.get("has_nvenc") or hw_info.get("has_intel_qsv") or hw_info.get("has_vaapi"):
            time_factor *= 0.25
            
        if hw_info.get("apple_silicon"):
            time_factor *= 0.5
        elif hw_info.get("cpu_cores", 0) >= 8:
            time_factor *= 0.7
            
        estimated_time = base_time * time_factor
        estimated_str = f"{int(estimated_time // 60)}:{int(estimated_time % 60):02d}" if estimated_time >= 60 else f"{int(estimated_time)} seconds"
        
        print(f"Est. Processing Time: {estimated_str} per minute of video")
    
    # Best encoders selection
    print()
    if USE_COLORS:
        encoder_title = " Optimal Encoder Selection "
        padding = (menu_width - len(encoder_title)) // 2
        if USE_UNICODE:
            print(f"{' ' * padding}{BOLD}{GREEN}•{encoder_title}•{RESET}")
            print(f"{GRAY}{'─' * menu_width}{RESET}")
        else:
            print(f"{' ' * padding}{BOLD}{GREEN}{encoder_title}{RESET}")
            print(f"{GRAY}{'-' * menu_width}{RESET}")
    else:
        print("Optimal Encoder Selection:")
        print("-" * menu_width)
    
    # Detect best encoder and explain why
    encoder = detect_best_encoder()
    encoder_reason = ""
    
    if "videotoolbox" in encoder:
        encoder_reason = "Apple's VideoToolbox for optimal performance on Mac"
    elif "nvenc" in encoder:
        encoder_reason = "NVIDIA hardware encoding for excellent performance"
    elif "qsv" in encoder:
        encoder_reason = "Intel QuickSync for hardware-accelerated encoding"
    elif "vaapi" in encoder:
        encoder_reason = "VA-API hardware acceleration for Linux"
    elif "libx265" in encoder:
        encoder_reason = "H.265/HEVC software encoding for better quality at smaller file sizes"
    else:
        encoder_reason = "H.264/AVC software encoding for optimal compatibility"
    
    if USE_COLORS:
        print(f"\n{' ' * 4}{GREEN}▶{RESET} {BOLD}Recommended encoder:{RESET} {CYAN}{encoder}{RESET}")
        print(f"{' ' * 6}{GRAY}{encoder_reason}{RESET}")
    else:
        print(f"\nRecommended encoder: {encoder}")
        print(f"  {encoder_reason}")
    
    print()
    
    # Add a section for hardware acceleration status
    has_hw_accel = hw_info.get("has_videotoolbox") or hw_info.get("has_nvenc") or hw_info.get("has_intel_qsv") or hw_info.get("has_vaapi")
    
    if USE_COLORS:
        if has_hw_accel:
            hw_icon = f"{GREEN}✓{RESET}" if USE_UNICODE else f"{GREEN}√{RESET}"
            print(f"{' ' * 4}{hw_icon} {BOLD}Hardware acceleration:{RESET} {GREEN}Available{RESET}")
            
            # List available hardware acceleration methods
            if hw_info.get("has_videotoolbox"):
                print(f"{' ' * 6}• Apple VideoToolbox")
            if hw_info.get("has_nvenc"):
                print(f"{' ' * 6}• NVIDIA NVENC")
            if hw_info.get("has_intel_qsv"):
                print(f"{' ' * 6}• Intel QuickSync")
            if hw_info.get("has_vaapi"):
                print(f"{' ' * 6}• VA-API")
        else:
            hw_icon = f"{YELLOW}⚠{RESET}" if USE_UNICODE else f"{YELLOW}!{RESET}"
            print(f"{' ' * 4}{hw_icon} {BOLD}Hardware acceleration:{RESET} {YELLOW}Not available{RESET}")
            print(f"{' ' * 6}{GRAY}Using software encoding only{RESET}")
    else:
        if has_hw_accel:
            print(f"Hardware acceleration: Available")
            
            # List available hardware acceleration methods
            if hw_info.get("has_videotoolbox"):
                print(f"  • Apple VideoToolbox")
            if hw_info.get("has_nvenc"):
                print(f"  • NVIDIA NVENC")
            if hw_info.get("has_intel_qsv"):
                print(f"  • Intel QuickSync")
            if hw_info.get("has_vaapi"):
                print(f"  • VA-API")
        else:
            print(f"Hardware acceleration: Not available")
            print(f"  Using software encoding only")
    
    input("\nPress Enter to return to the main menu...")

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
    """Detect the best encoder based on the system capabilities, prioritizing speed over quality"""
    hw_info = get_hardware_info()
    
    print_styled(CYAN, "Detecting fastest available encoder...")
    
    # Check available encoders
    try:
        process = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True, check=True)
        encoders_output = process.stdout
        
        # Check for hardware acceleration
        process = subprocess.run(['ffmpeg', '-hwaccels'], capture_output=True, text=True, check=True)
        hwaccels_output = process.stdout
        
        # Hardware encoding is always faster, so prioritize any hardware encoder
        
        # Apple Silicon with VideoToolbox - fastest for Mac
        if 'videotoolbox' in hwaccels_output:
            if "h264_videotoolbox" in encoders_output:
                print_styled(GREEN, "✓ Using Apple VideoToolbox hardware acceleration for maximum speed")
                return "h264_videotoolbox"
            
        # NVIDIA GPU with NVENC - extremely fast
        if 'cuda' in hwaccels_output and 'h264_nvenc' in encoders_output:
            print_styled(GREEN, "✓ Using NVIDIA NVENC hardware acceleration for maximum speed")
            return "h264_nvenc"
        
        # Intel QuickSync - good speed
        if 'qsv' in hwaccels_output and 'h264_qsv' in encoders_output:
            print_styled(GREEN, "✓ Using Intel QuickSync hardware acceleration for maximum speed")
            return "h264_qsv"
        
        # VA-API - decent speed on Linux
        if 'vaapi' in hwaccels_output and 'h264_vaapi' in encoders_output:
            print_styled(GREEN, "✓ Using VA-API hardware acceleration for maximum speed")
            return "h264_vaapi"
        
        # No hardware acceleration available, use fastest software encoder
        # H.264 is much faster than H.265 for encoding
        print_styled(YELLOW, "! No hardware acceleration detected. Using libx264 with ultrafast preset")
        return "libx264"
    
    except subprocess.SubprocessError:
        print_styled(RED, "✗ Error detecting encoders, falling back to libx264")
        return "libx264"  # Default

def create_slideshow_interactive():
    """Create a slideshow with smart interactive settings and modern design aesthetics"""
    show_banner()
    
    # Load settings
    settings = load_settings()
    
    # Show a spinner while scanning
    show_spinner("Scanning for media files", 1)
    
    # Get terminal width for centered content
    width = shutil.get_terminal_size().columns
    menu_width = min(80, width - 10)
    
    # Auto-organize images and find matching audio
    if USE_COLORS:
        print(f"\n{BOLD}Analyzing files...{RESET}")
    else:
        print("\nAnalyzing files...")
    
    media_data = auto_organize_images(recursive=settings.get("recursive_scan", False))
    
    # Check if we found any images
    if media_data["images"]["count"] == 0:
        if USE_COLORS:
            print(f"\n{RED}⚠ No images found in images/original/ directory{RESET}")
            print(f"{GRAY}Please add your images to the images/original/ directory and try again.{RESET}")
        else:
            print("\nError: No images found in images/original/ directory")
            print("Please add your images to the images/original/ directory and try again.")
        
        # Offer to create test images for demo purposes
        create_test = ask_question("Would you like to create test images for a demo", default="n", options=["y", "n"]) == "y"
        if create_test:
            create_test_images()
            media_data = auto_organize_images()  # Rescan after creating test images
            if media_data["images"]["count"] == 0:
                if USE_COLORS:
                    print(f"\n{RED}Failed to create test images.{RESET}")
                else:
                    print("\nFailed to create test images.")
                input("\nPress Enter to return to the main menu...")
                return
        else:
            input("\nPress Enter to return to the main menu...")
            return
    
    # Display a status box with file analysis results
    if USE_COLORS:
        # Box style for media status
        status_box_top = f"{LIGHT_GRAY}┌{'─' * (menu_width - 2)}┐{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}+{'-' * (menu_width - 2)}+{RESET}"
        status_box_bottom = f"{LIGHT_GRAY}└{'─' * (menu_width - 2)}┘{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}+{'-' * (menu_width - 2)}+{RESET}"
        status_side = f"{LIGHT_GRAY}│{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}|{RESET}"
        divider = f"{LIGHT_GRAY}├{'─' * (menu_width - 2)}┤{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}+{'-' * (menu_width - 2)}+{RESET}"
        
        print("\n" + status_box_top)
        print(f"{status_side} {BOLD}Media Analysis Results{RESET}{' ' * (menu_width - 22)}{status_side}")
        print(divider)
        
        # Images section
        check = f"{GREEN}✓{RESET}" if USE_UNICODE else f"{GREEN}√{RESET}"
        print(f"{status_side} {BOLD}Images:{RESET} {GREEN}{media_data['images']['count']} found{RESET}{' ' * (menu_width - 18 - len(str(media_data['images']['count'])))} {status_side}")
        
        # Group analysis information
        if media_data["images"]["groups"]["sequence"]:
            largest_sequence = max(media_data["images"]["groups"]["sequence"].values(), key=len)
            if len(largest_sequence) > 1:
                print(f"{status_side} {check} Detected sequence with {len(largest_sequence)} images{' ' * (menu_width - 36 - len(str(len(largest_sequence))))} {status_side}")
        
        if media_data["images"]["groups"]["date"]:
            date_count = len(media_data["images"]["groups"]["date"])
            print(f"{status_side} {check} Detected {date_count} date-based groups{' ' * (menu_width - 31 - len(str(date_count)))} {status_side}")
        
        print(divider)
        
        # Audio section
        if media_data["audio"]["selected"]:
            audio_file = media_data["audio"]["selected"]
            audio_filename = os.path.basename(audio_file)
            max_filename_len = menu_width - 24
            if len(audio_filename) > max_filename_len:
                audio_filename = audio_filename[:max_filename_len-3] + "..."
            
            print(f"{status_side} {BOLD}Audio:{RESET} {GREEN}{audio_filename}{RESET}{' ' * (menu_width - 9 - len(audio_filename))} {status_side}")
            
            if media_data["audio"]["duration"]:
                mins, secs = divmod(media_data["audio"]["duration"], 60)
                duration_str = f"{int(mins)}:{int(secs):02d}"
                print(f"{status_side} {check} Audio duration: {duration_str}{' ' * (menu_width - 18 - len(duration_str))} {status_side}")
                
                slide_duration = f"{media_data['slide_duration']:.2f} seconds"
                print(f"{status_side} {check} Average slide duration: {slide_duration}{' ' * (menu_width - 26 - len(slide_duration))} {status_side}")
        else:
            if media_data["audio"]["files"]["count"] > 0:
                audio_count = media_data["audio"]["files"]["count"] 
                print(f"{status_side} {BOLD}Audio:{RESET} {YELLOW}Found {audio_count} files (no auto-match){RESET}{' ' * (menu_width - 29 - len(str(audio_count)))} {status_side}")
            else:
                print(f"{status_side} {BOLD}Audio:{RESET} {YELLOW}No audio files found{RESET}{' ' * (menu_width - 27)} {status_side}")
        
        print(status_box_bottom)
    else:
        # Non-colored version
        print(f"\nMedia Analysis Results")
        print(f"-" * menu_width)
        print(f"Images: {media_data['images']['count']} found")
        
        if media_data["images"]["groups"]["sequence"]:
            largest_sequence = max(media_data["images"]["groups"]["sequence"].values(), key=len)
            if len(largest_sequence) > 1:
                print(f"✓ Detected sequence with {len(largest_sequence)} images")
        
        if media_data["images"]["groups"]["date"]:
            print(f"✓ Detected {len(media_data['images']['groups']['date'])} date-based groups")
        
        print("-" * menu_width)
        
        if media_data["audio"]["selected"]:
            audio_file = media_data["audio"]["selected"]
            audio_filename = os.path.basename(audio_file)
            print(f"Audio: {audio_filename}")
            
            if media_data["audio"]["duration"]:
                mins, secs = divmod(media_data["audio"]["duration"], 60)
                print(f"✓ Audio duration: {int(mins)}:{int(secs):02d}")
                print(f"✓ Average slide duration: {media_data['slide_duration']:.2f} seconds")
        else:
            if media_data["audio"]["files"]["count"] > 0:
                print(f"Audio: Found {media_data['audio']['files']['count']} files (no auto-match)")
            else:
                print(f"Audio: No audio files found")
        
        print("-" * menu_width)
    
    # Audio selection - if needed
    audio_file = media_data["audio"]["selected"]
    if not audio_file and media_data["audio"]["files"]["count"] > 0:
        print()
        if USE_COLORS:
            print(f"{BLUE}▶{RESET} {BOLD}Audio Selection{RESET}")
        else:
            print("Audio Selection")
        
        select_audio = ask_question("Would you like to select an audio file", default="y", options=["y", "n"]) == "y"
        if select_audio:
            audio_list = [f for f in media_data["audio"]["files"]["files"] if f["type"] == "audio"]
            
            # Display available audio files
            if USE_COLORS:
                print(f"\n{GRAY}Available audio files:{RESET}")
                for i, file_info in enumerate(audio_list, 1):
                    print(f"{' ' * 4}{CYAN}{i}.{RESET} {file_info['name']}")
            else:
                print("\nAvailable audio files:")
                for i, file_info in enumerate(audio_list, 1):
                    print(f"  {i}. {file_info['name']}")
            
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
                    
                    if USE_COLORS:
                        print(f"\n{GREEN}Selected: {os.path.basename(audio_file)}{RESET}")
                    else:
                        print(f"\nSelected: {os.path.basename(audio_file)}")
            except ValueError:
                if USE_COLORS:
                    print(f"\n{YELLOW}Invalid choice, continuing without audio{RESET}")
                else:
                    print("\nInvalid choice, continuing without audio")
    elif not audio_file:
        print()
        use_audio = ask_question("Do you want to continue without audio", default="y", options=["y", "n"]) == "y"
        if not use_audio:
            if USE_COLORS:
                print(f"\n{GRAY}Please add your audio file to the song/ directory and try again.{RESET}")
            else:
                print("\nPlease add your audio file to the song/ directory and try again.")
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
    if USE_COLORS:
        section_title = " Slideshow Settings "
        padding = (menu_width - len(section_title)) // 2
        if USE_UNICODE:
            print(f"{' ' * padding}{BOLD}{PURPLE}•{section_title}•{RESET}")
            print(f"{GRAY}{'─' * menu_width}{RESET}")
        else:
            print(f"{' ' * padding}{BOLD}{PURPLE}{section_title}{RESET}")
            print(f"{GRAY}{'-' * menu_width}{RESET}")
    else:
        print("Slideshow Settings")
        print("-" * menu_width)
    
    print()
    
    # Title with smart suggestion
    slideshow_title = ask_question("Enter slideshow title", default=suggested_name)
    
    # Resolution with smart default based on image analysis
    # TODO: Add image resolution detection for better defaults
    resolutions = ["1280x720", "1920x1080", "2560x1440", "3840x2160"]
    
    if USE_COLORS:
        print(f"\n{GRAY}Available resolutions:{RESET}")
        for i, res in enumerate(resolutions, 1):
            print(f"{' ' * 4}{CYAN}{i}.{RESET} {res}")
    else:
        print("\nAvailable resolutions:")
        for i, res in enumerate(resolutions, 1):
            print(f"  {i}. {res}")
    
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
    
    # Determine sensible default based on hardware - ALWAYS CHOOSE FASTEST
    default_quality = "1"  # Maximum Performance is now default
    
    quality_presets = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
    
    if USE_COLORS:
        print(f"\n{GRAY}Quality presets:{RESET}")
        print(f"{' ' * 4}{CYAN}1.{RESET} Maximum Performance {GREEN}(ultrafast - maximizes speed){RESET} [RECOMMENDED]")
        print(f"{' ' * 4}{CYAN}2.{RESET} Balanced {GRAY}(medium - slower but better quality){RESET}")
        print(f"{' ' * 4}{CYAN}3.{RESET} High Quality {YELLOW}(veryslow - very slow encoding){RESET}")
        print(f"{' ' * 4}{CYAN}4.{RESET} Custom {GRAY}(advanced){RESET}")
    else:
        print("\nQuality presets (faster → better quality):")
        print("  1. Maximum Performance (ultrafast) [RECOMMENDED]")
        print("  2. Balanced (medium)")
        print("  3. High Quality (veryslow)")
        print("  4. Custom")
    
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
            if USE_COLORS:
                print(f"\n{GRAY}Available presets:{RESET}")
                for i, preset in enumerate(quality_presets, 1):
                    print(f"{' ' * 4}{CYAN}{i}.{RESET} {preset}")
            else:
                print("\nAvailable presets:")
                for i, preset in enumerate(quality_presets, 1):
                    print(f"  {i}. {preset}")
            
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
    
    # Create command - Show summary in a nice box
    print()
    if USE_COLORS:
        summary_title = " Slideshow Summary "
        padding = (menu_width - len(summary_title)) // 2
        if USE_UNICODE:
            print(f"{' ' * padding}{BOLD}{GREEN}•{summary_title}•{RESET}")
            print(f"{GRAY}{'─' * menu_width}{RESET}")
        else:
            print(f"{' ' * padding}{BOLD}{GREEN}{summary_title}{RESET}")
            print(f"{GRAY}{'-' * menu_width}{RESET}")
        
        # Box style for summary
        summary_box_top = f"{LIGHT_GRAY}┌{'─' * (menu_width - 2)}┐{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}+{'-' * (menu_width - 2)}+{RESET}"
        summary_box_bottom = f"{LIGHT_GRAY}└{'─' * (menu_width - 2)}┘{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}+{'-' * (menu_width - 2)}+{RESET}"
        summary_side = f"{LIGHT_GRAY}│{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}|{RESET}"
        
        # Function to create summary row
        def summary_row(label, value, extra=""):
            label = f"{BOLD}{label}:{RESET}"
            padding = menu_width - len(label) - len(value) - len(extra) - 5
            if extra:
                return f"{summary_side} {label} {CYAN}{value}{RESET} {GRAY}{extra}{RESET}{' ' * padding} {summary_side}"
            else:
                return f"{summary_side} {label} {CYAN}{value}{RESET}{' ' * padding} {summary_side}"
        
        print(summary_box_top)
        print(summary_row("Title", slideshow_title))
        print(summary_row("Resolution", resolution))
        print(summary_row("Quality", quality))
        print(summary_row("Output", output_filename))
        
        hw_text = "(hardware accelerated)" if use_hardware_accel else ""
        print(summary_row("Encoder", encoder, hw_text))
        
        if audio_file:
            print(summary_row("Audio", os.path.basename(audio_file)))
            duration_str = f"{media_data['audio']['duration']:.2f} seconds"
            print(summary_row("Duration", duration_str))
        
        print(summary_row("Images", str(media_data['images']['count']) + " images"))
        slide_duration_str = f"{media_data['slide_duration']:.2f} seconds"
        print(summary_row("Per slide", slide_duration_str))
        print(summary_box_bottom)
    else:
        print("Slideshow Summary")
        print("-" * menu_width)
        print(f"Title:      {slideshow_title}")
        print(f"Resolution: {resolution}")
        print(f"Quality:    {quality}")
        print(f"Output:     {output_filename}")
        print(f"Encoder:    {encoder}{' (hardware accelerated)' if use_hardware_accel else ''}")
        
        if audio_file:
            print(f"Audio:      {os.path.basename(audio_file)}")
            print(f"Duration:   {media_data['audio']['duration']:.2f} seconds")
        
        print(f"Images:     {media_data['images']['count']} images")
        print(f"Per slide:  {media_data['slide_duration']:.2f} seconds")
        print("-" * menu_width)
    
    print()
    
    # Confirm with styled button
    if USE_COLORS and USE_UNICODE:
        print(f"{' ' * 4}{GREEN}▶{RESET} Ready to begin")
    
    # Confirm
    if ask_question("Start encoding", default="y", options=["y", "n"]) != "y":
        if USE_COLORS:
            print(f"\n{GRAY}Encoding cancelled{RESET}")
        else:
            print("\nEncoding cancelled")
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
    
    # Run encoding with proper monitoring
    print_styled(GREEN, "Starting encoding process...")
    
    # Use the improved run_encoding function
    if run_encoding():
        print_styled(GREEN, "Encoding completed successfully")
    else:
        print_styled(RED, "Encoding failed")
    
    input("\nPress Enter to return to the main menu...")

def create_encoding_script(slideshow_title, resolution, quality, output_filename, encoder, audio_file, image_list, slide_duration):
    """
    Create an encoding script file with the provided slideshow settings.
    This generates the run_encode.py file with all necessary parameters.
    """
    # Create necessary directories
    os.makedirs("temp", exist_ok=True)
    
    # Always override quality to 'ultrafast' for maximum speed
    original_quality = quality
    quality = "ultrafast"  # Force ultrafast for maximum speed
    
    # Always use hardware acceleration when available, otherwise force libx264
    if not any(hw in encoder for hw in ["videotoolbox", "nvenc", "qsv", "vaapi"]):
        encoder = "libx264"
    
    # Build the encoding script content
    script_content = f"""#!/usr/bin/env python3
# SlideSonic (2025) - Encoding Script - MAXIMUM SPEED OPTIMIZATION
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

import os
import sys
import time
import subprocess
from datetime import datetime
import json

# Slideshow settings
TITLE = "{slideshow_title}"
RESOLUTION = "{resolution}"
QUALITY_PRESET = "{quality}"  # Using ultrafast preset for maximum speed
OUTPUT_FILENAME = "{output_filename}"
ENCODER = "{encoder}"
AUDIO_FILE = {repr(audio_file) if audio_file else "None"}
SLIDE_DURATION = {slide_duration}

# Print optimization info
print("SPEED OPTIMIZATION: Using maximum speed settings")
print(f"ENCODER: {{ENCODER}} with PRESET: {{QUALITY_PRESET}}")

# Ensure required directories exist
os.makedirs("temp", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Using smart-sorted image list
image_files = {repr(image_list)}
print(f"Using {{len(image_files)}} images in optimized order")

if not image_files:
    print("Error: No images found in images/original/ directory")
    sys.exit(1)

print(f"Found {{len(image_files)}} images")

# Calculate duration per slide based on audio duration
audio_duration = None
if AUDIO_FILE:
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
               '-of', 'default=noprint_wrappers=1:nokey=1', AUDIO_FILE]
        audio_duration = float(subprocess.check_output(cmd, text=True).strip())
        print(f"Audio duration: {{audio_duration:.2f}} seconds")
    except (subprocess.SubprocessError, ValueError):
        print("Warning: Could not determine audio duration")

# Use provided slide duration or calculate from audio
slide_duration = SLIDE_DURATION
if audio_duration:
    # Make sure slides fit within audio, adjusting if necessary
    total_duration = slide_duration * len(image_files)
    if total_duration < audio_duration * 0.9:  # If much shorter than audio
        # Can lengthen slide duration to better use the audio
        slide_duration = min(6.0, audio_duration / len(image_files))
        print(f"Adjusted slide duration to {{slide_duration:.2f}}s to better match audio")

print(f"Using slide duration: {{slide_duration:.2f}} seconds")

# Create temporary file list
with open("temp/filelist.txt", "w") as f:
    for img in image_files:
        # Check if this is a full path or just a filename
        if os.path.isabs(img) or os.path.dirname(img):
            # Use absolute path or path relative to current directory
            absolute_path = os.path.abspath(img)
            f.write(f"file '{{absolute_path}}'\\n")
        else:
            # Just a filename, use IMAGE_DIR
            f.write(f"file '{{os.path.abspath(os.path.join(\"images/original\", img))}}'\\n")
        f.write(f"duration {{slide_duration}}\\n")
    
    # Add last image again to avoid premature ending
    if image_files:
        last_img = image_files[-1]
        if os.path.isabs(last_img) or os.path.dirname(last_img):
            # Use absolute path or path relative to current directory
            absolute_path = os.path.abspath(last_img)
            f.write(f"file '{{absolute_path}}'\\n")
        else:
            # Just a filename, use IMAGE_DIR
            f.write(f"file '{{os.path.abspath(os.path.join(\"images/original\", last_img))}}'\\n")

# Parse resolution
width, height = map(int, RESOLUTION.split('x'))

# Determine quality settings based on encoder
crf_value = "30"  # Higher CRF = lower quality but faster encoding
if ENCODER == "libx265":
    crf_value = "35"  # HEVC uses different CRF scale - much higher for speed
elif "av1" in ENCODER:
    crf_value = "40"  # AV1 uses different CRF scale - much higher for speed

# Build FFmpeg command with maximum speed optimizations
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", "temp/filelist.txt",
]

# Add audio if available
if AUDIO_FILE:
    ffmpeg_cmd.extend(["-i", AUDIO_FILE])

# Add video settings optimized for speed
ffmpeg_cmd.extend([
    "-c:v", ENCODER,
    "-preset", QUALITY_PRESET,
    "-crf", crf_value,
    "-pix_fmt", "yuv420p",
    "-g", "999999",           # Reduce keyframes to bare minimum
    "-keyint_min", "999999",  # Minimize keyframes for speed
    "-sc_threshold", "0",     # Disable scene change detection for speed
    "-tune", "fastdecode",    # Optimize for decode speed
])

# Additional encoder-specific optimizations for speed
if "videotoolbox" in ENCODER:
    # Apple VideoToolbox specific optimizations for speed
    ffmpeg_cmd.extend([
        "-allow_sw", "1",       # Allow software fallback
        "-realtime", "1",       # Prioritize realtime encoding
        "-b:v", "1M",           # Use fixed bitrate mode for speed
        "-maxrate", "1M",       # Limit max bitrate
        "-bufsize", "1M",       # Small buffer for speed
    ])
elif "nvenc" in ENCODER:
    # NVIDIA NVENC specific optimizations for speed
    ffmpeg_cmd.extend([
        "-preset", "p1",         # Fastest preset for NVENC
        "-tune", "ll",           # Low latency tuning
        "-rc", "constqp",        # Constant QP mode for speed
        "-qp", "32",             # Higher QP = faster encoding
        "-b:v", "0",             # Disable bitrate control
    ])
elif "qsv" in ENCODER:
    # Intel QuickSync specific optimizations
    ffmpeg_cmd.extend([
        "-low_power", "1",      # Use low power mode for speed
        "-async_depth", "1",    # Minimize frame queue
    ])
else:
    # Software encoder optimizations
    ffmpeg_cmd.extend([
        "-threads", "0",         # Use all available threads
        "-slices", "4",          # Slice frames for parallel encoding
        "-flags", "+cgop",       # Closed GOP for faster encoding
        "-movflags", "+faststart", # Optimize for streaming
        "-bf", "0",              # No B-frames for speed
        "-refs", "1",            # Minimal reference frames
    ])

# Add fast audio encoding settings if available
if AUDIO_FILE:
    ffmpeg_cmd.extend([
        "-c:a", "aac",
        "-b:a", "128k",         # Lower audio bitrate for speed
        "-ar", "44100",         # Lower sample rate for speed
    ])

# Optimize filter settings for speed
ffmpeg_cmd.extend([
    "-vf", f"scale={{RESOLUTION}}:flags=fast_bilinear",  # Fast scaling algorithm
    "output/" + OUTPUT_FILENAME
])

# Save metadata about the encoding
metadata = {{
    "title": TITLE,
    "created": datetime.now().isoformat(),
    "settings": {{
        "resolution": RESOLUTION,
        "quality": QUALITY_PRESET,
        "encoder": ENCODER,
        "slide_duration": slide_duration,
        "total_duration": slide_duration * len(image_files),
        "image_count": len(image_files),
        "audio": AUDIO_FILE is not None
    }}
}}

with open("temp/encode_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

# Log the command
print(f"Running FFmpeg command: {{' '.join(ffmpeg_cmd)}}")

# Create log file - IMPORTANT: This must match the path expected by monitor_encoding.py
log_file = "temp/ffmpeg_output.log"

# Run FFmpeg
try:
    # First, create a subprocess that runs FFmpeg and redirects output to a log file
    print(f"Starting encoding process...")
    print(f"For detailed progress, you can view the log file: {{log_file}}")
    
    # Open log file for FFmpeg output
    log_file_handle = open(log_file, "w")
    
    # Start the FFmpeg process
    process = subprocess.Popen(
        ffmpeg_cmd, 
        stdout=log_file_handle, 
        stderr=subprocess.STDOUT, 
        universal_newlines=True
    )
    
    # Record start time
    start_time = time.time()
    
    # Write the PID to a file for the monitor to pick up
    with open("temp/ffmpeg_pid.txt", "w") as f:
        f.write(str(process.pid))
    
    # Wait for the process to complete
    process.wait()
    returncode = process.returncode
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Close log file
    log_file_handle.close()
    
    # Final output based on success or failure
    if returncode == 0:
        print(f"\\n\\033[38;5;35m✓\\033[0m \\033[1mEncoding completed successfully\\033[0m in {{elapsed_time:.2f}} seconds")
        print(f"Output: output/{{OUTPUT_FILENAME}}")
        
        # Show file size
        try:
            file_size = os.path.getsize("output/" + OUTPUT_FILENAME)
            print(f"File size: {{file_size / (1024*1024):.2f}} MB")
        except:
            pass
    else:
        print(f"\\n\\033[38;5;196m✗\\033[0m \\033[1mEncoding failed\\033[0m with code {{returncode}}")
        print(f"Check log file for details: {{log_file}}")
except Exception as e:
    print(f"Error running FFmpeg: {{e}}")
    if 'log_file_handle' in locals() and not log_file_handle.closed:
        log_file_handle.close()
"""

    # Write the script to the run_encode.py file
    script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "run_encode.py")
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # Make the script executable
    try:
        os.chmod(script_path, 0o755)
    except Exception:
        pass
    
    # Save the metadata for reference
    metadata = {
        "title": slideshow_title,
        "resolution": resolution,
        "quality": quality,
        "output": output_filename,
        "encoder": encoder,
        "audio": os.path.basename(audio_file) if audio_file else None,
        "images": len(image_list),
        "slide_duration": slide_duration,
        "timestamp": datetime.now().isoformat()
    }
    
    os.makedirs("temp", exist_ok=True)
    with open("temp/slideshow_config.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    return script_path

def run_encoding():
    """Run the encoding script with progress monitoring, optimized for maximum speed"""
    script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "run_encode.py")
    monitor_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "monitor_encoding.py")
    
    # Make sure temp directory exists
    os.makedirs("temp", exist_ok=True)
    
    # Define the log file path - must be consistent with what's in run_encode.py
    log_file = "temp/ffmpeg_output.log"
    
    print_styled(BLUE, "▶ Starting encoding with MAXIMUM SPEED OPTIMIZATION")
    print_styled(GRAY, "  Using ultrafast preset and hardware acceleration when available")
    print_styled(GRAY, "  Quality is reduced to achieve the fastest possible encoding speed")
    
    try:
        # Set high process priority if possible
        high_priority_cmd = []
        if platform.system() == "Windows":
            # On Windows, use start command with high priority
            high_priority_cmd = ["start", "/HIGH", "/B", sys.executable, script_path]
        elif platform.system() == "Darwin":  # macOS
            # On Mac, use nice command with low value (higher priority)
            high_priority_cmd = ["nice", "-n", "-10", sys.executable, script_path]
        elif platform.system() == "Linux":
            # On Linux, use nice command with low value (higher priority)
            high_priority_cmd = ["nice", "-n", "-10", sys.executable, script_path]
        
        # Use high priority if we could set it up, otherwise use normal priority
        if high_priority_cmd:
            print_styled(GRAY, "  Running with high CPU priority for maximum performance")
            try:
                # For Mac/Linux, may require sudo, catch permission errors
                encoding_process = subprocess.Popen(
                    high_priority_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
            except (PermissionError, subprocess.SubprocessError):
                # Fall back to normal priority
                print_styled(YELLOW, "  Could not set high priority (permission denied), using normal priority")
                encoding_process = subprocess.Popen(
                    [sys.executable, script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
        else:
            # Use normal priority
            encoding_process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
        # Wait a moment for the process to start
        time.sleep(1)
        
        # Check if the process is still running
        if encoding_process.poll() is not None:
            print_styled(RED, "Encoding process failed to start or exited immediately")
            return False
        
        # Start monitoring
        try:
            # Build command with specific log file parameter
            monitor_cmd = [
                sys.executable, 
                monitor_path,
                "--log-file", log_file,
                "--ffmpeg-pid", str(encoding_process.pid)
            ]
            
            print_styled(GRAY, f"Starting monitoring with PID {encoding_process.pid}")
            
            # Run the monitor with all necessary parameters
            subprocess.run(monitor_cmd, check=True)
        except subprocess.SubprocessError:
            # Monitor might have been interrupted, but encoding continues
            pass
        except KeyboardInterrupt:
            print_styled(YELLOW, "Monitor stopped. Encoding continues in background.")
        
        # Wait for encoding to complete
        encoding_process.wait()
        
        if encoding_process.returncode == 0:
            print()
            print_styled(GREEN, "Encoding completed successfully")
            return True
        else:
            print()
            print_styled(RED, f"Encoding failed with code {encoding_process.returncode}")
            return False
    except Exception as e:
        print()
        print_styled(RED, f"Error running encoding: {e}")
        return False

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
    """Show the main menu with responsive layout"""
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
        
        # Get terminal width for responsive content
        width = shutil.get_terminal_size().columns
        # Calculate responsive menu width - adapt to terminal size
        menu_width = min(75, max(40, width - 10))
        
        # Display elegant menu header
        if USE_COLORS:
            header = " Menu Options "
            padding = (menu_width - len(header)) // 2
            if USE_UNICODE:
                print(f"{' ' * padding}{BOLD}{BLUE}•{header}•{RESET}")
                print(f"{GRAY}{'─' * menu_width}{RESET}")
            else:
                print(f"{' ' * padding}{BOLD}{BLUE}{header}{RESET}")
                print(f"{GRAY}{'-' * menu_width}{RESET}")
        else:
            print(f"Menu Options")
            print("-" * menu_width)
        
        # Show media status in a cleaner box style
        if USE_COLORS and USE_UNICODE:
            if quick_start_ready:
                status_text = f"Media Ready: {image_count} images" + (f", {audio_count} audio files" if audio_count > 0 else "")
                print(f"\n{' ' * 4}{GREEN}✓{RESET} {BOLD}{status_text}{RESET}")
            else:
                print(f"\n{' ' * 4}{YELLOW}⚠{RESET} {BOLD}No images found in images/original/ directory{RESET}")
        else:
            if quick_start_ready:
                print(f"\nMedia Ready: {image_count} images" + (f", {audio_count} audio files" if audio_count > 0 else ""))
            else:
                print(f"\nNo images found in images/original/ directory")
        
        print()
        
        # Define menu items with icons and responsive design
        if quick_start_ready:
            menu_items = [
                ("Quick Create Slideshow", "Auto-generate with optimized settings", GREEN, "1"),
                ("Interactive Mode", "Customize your slideshow settings", CYAN, "2"),
                ("Batch Processing", "Create multiple slideshows in sequence", YELLOW, "3"),
                ("Media Management", "Import, organize, and manage media files", PURPLE, "4"),
                ("Hardware Analysis", "Check system capabilities", BLUE, "5"),
                ("Help & Documentation", "View usage instructions", GRAY, "6"),
                ("Exit", "Quit SlideSonic", LIGHT_GRAY, "7")
            ]
        else:
            menu_items = [
                ("Interactive Mode", "Customize your slideshow settings", CYAN, "1"),
                ("Media Management", "Import, organize, and manage media files", PURPLE, "2"),
                ("Hardware Analysis", "Check system capabilities", BLUE, "3"),
                ("Help & Documentation", "View usage instructions", GRAY, "4"),
                ("Exit", "Quit SlideSonic", LIGHT_GRAY, "5")
            ]
        
        # Responsive menu display based on terminal width
        for i, (title, description, color, key) in enumerate(menu_items):
            if USE_COLORS:
                icon = "•" if USE_UNICODE else "*"
                
                # Responsive layout based on terminal width
                if width > 80:
                    # Wide terminal - show everything on one line
                    if USE_UNICODE:
                        print(f"{' ' * 4}{color}{icon}{RESET} {BOLD}{title}{RESET} {GRAY}— {description}{RESET} {color}[{key}]{RESET}")
                    else:
                        print(f"{' ' * 4}{color}{icon}{RESET} {BOLD}{title}{RESET} {GRAY}- {description}{RESET} {color}[{key}]{RESET}")
                elif width > 60:
                    # Medium width - slightly compact
                    if USE_UNICODE:
                        print(f"{' ' * 2}{color}{icon}{RESET} {BOLD}{title}{RESET} {GRAY}— {description}{RESET} {color}[{key}]{RESET}")
                    else:
                        print(f"{' ' * 2}{color}{icon}{RESET} {BOLD}{title}{RESET} {GRAY}- {description}{RESET} {color}[{key}]{RESET}")
                else:
                    # Narrow terminal - stack title and description
                    print(f"{' ' * 2}{color}{icon}{RESET} {BOLD}{title}{RESET} {color}[{key}]{RESET}")
                    print(f"{' ' * 5}{GRAY}{description}{RESET}")
            else:
                print(f"  {i+1}. {title} - {description}")
        
        print()
        
        # Add a subtle prompt
        if USE_COLORS:
            prompt = "Enter your choice"
            print(f"{' ' * 4}{BLUE}▶{RESET} {prompt} ", end="")
        else:
            prompt = "Enter your choice: "
            print(prompt, end="")
        
        # Get user choice with timeout to enable responsive updates
        try:
            # Using a short timeout allows for more responsive UI updates if needed
            choice = input()
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            if USE_COLORS:
                print(f"\n{GRAY}Exiting SlideSonic...{RESET}")
            else:
                print("\nExiting SlideSonic...")
            return
        
        # Process menu choice
        if quick_start_ready:
            # Menu with quick start option
            if choice == "1":
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
                if USE_COLORS:
                    print(f"\n{GRAY}Exiting SlideSonic...{RESET}")
                else:
                    print("\nExiting SlideSonic...")
                return
            else:
                if USE_COLORS:
                    print(f"\n{RED}Invalid choice. Please try again.{RESET}")
                else:
                    print("\nInvalid choice. Please try again.")
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
                if USE_COLORS:
                    print(f"\n{GRAY}Exiting SlideSonic...{RESET}")
                else:
                    print("\nExiting SlideSonic...")
                return
            else:
                if USE_COLORS:
                    print(f"\n{RED}Invalid choice. Please try again.{RESET}")
                else:
                    print("\nInvalid choice. Please try again.")
                time.sleep(1)

def media_management_menu():
    """Media management options with Apple-inspired design aesthetics"""
    while True:
        show_banner()
        
        # Get terminal width for centered content
        width = shutil.get_terminal_size().columns
        menu_width = min(60, width - 10)  # Keep menu width reasonable
        
        # Display elegant menu header
        if USE_COLORS:
            header = " Media Management "
            padding = (menu_width - len(header)) // 2
            if USE_UNICODE:
                print(f"{' ' * padding}{BOLD}{PURPLE}•{header}•{RESET}")
                print(f"{GRAY}{'─' * menu_width}{RESET}")
            else:
                print(f"{' ' * padding}{BOLD}{PURPLE}{header}{RESET}")
                print(f"{GRAY}{'-' * menu_width}{RESET}")
        else:
            print("Media Management")
            print("-" * menu_width)
        
        print()
        
        # Define menu items with Apple-style icons
        menu_items = [
            ("Import Images", "Copy images from another directory", GREEN, "1"),
            ("Import Audio", "Copy audio from another directory", CYAN, "2"),
            ("Create Test Images", "Generate sample images", YELLOW, "3"),
            ("Organize Images", "Sort images into logical groups", PURPLE, "4"),
            ("View Media Information", "Show details about available media", BLUE, "5"),
            ("Return to Main Menu", "Go back to main options", GRAY, "6")
        ]
        
        # Display menu items in a cleaner, more modern style
        for i, (title, description, color, key) in enumerate(menu_items):
            if USE_COLORS:
                icon = "•" if USE_UNICODE else "*"
                if USE_UNICODE:
                    print(f"{' ' * 4}{color}{icon}{RESET} {BOLD}{title}{RESET} {GRAY}— {description}{RESET} {color}[{key}]{RESET}")
                else:
                    print(f"{' ' * 4}{color}{icon}{RESET} {BOLD}{title}{RESET} {GRAY}- {description}{RESET} {color}[{key}]{RESET}")
            else:
                print(f"  {i+1}. {title} - {description}")
        
        print()
        
        # Add a subtle prompt
        if USE_COLORS:
            prompt = "Enter your choice"
            print(f"{' ' * 4}{BLUE}▶{RESET} {prompt} ", end="")
        else:
            prompt = "Enter your choice: "
            print(prompt, end="")
        
        # Get user choice
        choice = input()
        
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
            if USE_COLORS:
                print(f"\n{RED}Invalid choice. Please try again.{RESET}")
            else:
                print("\nInvalid choice. Please try again.")
            time.sleep(1)

def quick_create_slideshow():
    """Quick creation of a slideshow with Apple-inspired design aesthetics"""
    show_banner()
    
    # Get terminal width for centered content
    width = shutil.get_terminal_size().columns
    menu_width = min(80, width - 10)
    
    # Display section header
    if USE_COLORS:
        section_title = " Quick Slideshow "
        padding = (menu_width - len(section_title)) // 2
        if USE_UNICODE:
            print(f"{' ' * padding}{BOLD}{BLUE}•{section_title}•{RESET}")
            print(f"{GRAY}{'─' * menu_width}{RESET}")
        else:
            print(f"{' ' * padding}{BOLD}{BLUE}{section_title}{RESET}")
            print(f"{GRAY}{'-' * menu_width}{RESET}")
    else:
        print("Quick Slideshow")
        print("-" * menu_width)
    
    print()
    
    # Show a spinner while scanning
    show_spinner("Scanning for media files", 1)
    
    # Auto-organize images and find matching audio
    if USE_COLORS:
        print(f"{BOLD}Analyzing media files...{RESET}")
    else:
        print("Analyzing media files...")
    
    media_data = auto_organize_images(recursive=True)
    
    # Check if we found any images
    if media_data["images"]["count"] == 0:
        if USE_COLORS:
            print(f"\n{RED}⚠ No images found{RESET}")
            print(f"{GRAY}Please add images to the images/original/ directory first.{RESET}")
        else:
            print("\nError: No images found")
            print("Please add images to the images/original/ directory first.")
        
        create_test = ask_question("Would you like to create test images for a demo", default="y", options=["y", "n"]) == "y"
        if create_test:
            create_test_images()
            media_data = auto_organize_images()  # Rescan after creating test images
            if media_data["images"]["count"] == 0:
                if USE_COLORS:
                    print(f"\n{RED}Failed to create test images.{RESET}")
                else:
                    print("\nFailed to create test images.")
                input("\nPress Enter to return to the main menu...")
                return
        else:
            input("\nPress Enter to return to the main menu...")
            return
    
    # Display status info in an elegant box
    if USE_COLORS:
        status_box_top = f"{LIGHT_GRAY}┌{'─' * (menu_width - 2)}┐{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}+{'-' * (menu_width - 2)}+{RESET}"
        status_box_bottom = f"{LIGHT_GRAY}└{'─' * (menu_width - 2)}┘{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}+{'-' * (menu_width - 2)}+{RESET}"
        status_side = f"{LIGHT_GRAY}│{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}|{RESET}"
        divider = f"{LIGHT_GRAY}├{'─' * (menu_width - 2)}┤{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}+{'-' * (menu_width - 2)}+{RESET}"
        
        print("\n" + status_box_top)
        print(f"{status_side} {BOLD}Media Analysis{RESET}{' ' * (menu_width - 15)}{status_side}")
        print(divider)
        
        check = f"{GREEN}✓{RESET}" if USE_UNICODE else f"{GREEN}√{RESET}"
        print(f"{status_side} {check} Found {media_data['images']['count']} images{' ' * (menu_width - 16 - len(str(media_data['images']['count'])))} {status_side}")
        
        if media_data["audio"]["selected"]:
            audio_file = media_data["audio"]["selected"]
            audio_name = os.path.basename(audio_file)
            # Truncate long filenames
            if len(audio_name) > menu_width - 24:
                audio_name = audio_name[:menu_width-27] + "..."
            print(f"{status_side} {check} Found audio: {audio_name}{' ' * (menu_width - 15 - len(audio_name))} {status_side}")
            
            if media_data["audio"]["duration"]:
                mins, secs = divmod(media_data["audio"]["duration"], 60)
                duration_str = f"{int(mins)}:{int(secs):02d}"
                print(f"{status_side} {check} Audio duration: {duration_str}{' ' * (menu_width - 18 - len(duration_str))} {status_side}")
        else:
            print(f"{status_side} {YELLOW}⚠ No audio selected{RESET}{' ' * (menu_width - 19)} {status_side}")
        
        print(status_box_bottom)
    else:
        print(f"\nMedia Analysis:")
        print(f"-" * menu_width)
        print(f"✓ Found {media_data['images']['count']} images")
        
        if media_data["audio"]["selected"]:
            audio_file = media_data["audio"]["selected"]
            print(f"✓ Found audio: {os.path.basename(audio_file)}")
            
            if media_data["audio"]["duration"]:
                mins, secs = divmod(media_data["audio"]["duration"], 60)
                print(f"✓ Audio duration: {int(mins)}:{int(secs):02d}")
        else:
            print("⚠ No audio selected")
        print(f"-" * menu_width)
    
    # Smart title suggestion
    suggested_name = ""
    
    # Try to derive a name from common prefixes or dates
    if media_data["images"]["groups"]["prefix"]:
        # Find the largest prefix group
        largest_prefix_group = max(media_data["images"]["groups"]["prefix"].values(), key=len)
        if len(largest_prefix_group) > 1:
            suggested_name = largest_prefix_group[0]["prefix"].title()
    
    if not suggested_name and media_data["images"]["groups"]["date"]:
        # Find the most common date
        largest_date_group = max(media_data["images"]["groups"]["date"].values(), key=len)
        if largest_date_group:
            date_str = largest_date_group[0]["date"]
            suggested_name = f"Slideshow {date_str}"
    
    # Default fallback
    if not suggested_name:
        suggested_name = f"Slideshow {datetime.now().strftime('%Y-%m-%d')}"
    
    # We'll try to keep the UI minimal for quick mode
    print()
    title = ask_question("Enter slideshow title", default=suggested_name)
    
    # Smart output filename
    sanitized_title = re.sub(r'[^a-zA-Z0-9_-]', '_', title)
    default_filename = f"{sanitized_title}_{datetime.now().strftime('%Y%m%d')}.mp4"
    
    # Quality detection based on hardware
    hw_info = get_hardware_info()
    
    if USE_COLORS:
        # Create summary box
        summary_title = " Slideshow Configuration "
        padding = (menu_width - len(summary_title)) // 2
        if USE_UNICODE:
            print(f"\n{' ' * padding}{BOLD}{GREEN}•{summary_title}•{RESET}")
            print(f"{GRAY}{'─' * menu_width}{RESET}")
        else:
            print(f"\n{' ' * padding}{BOLD}{GREEN}{summary_title}{RESET}")
            print(f"{GRAY}{'-' * menu_width}{RESET}")
        
        summary_box_top = f"{LIGHT_GRAY}┌{'─' * (menu_width - 2)}┐{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}+{'-' * (menu_width - 2)}+{RESET}"
        summary_box_bottom = f"{LIGHT_GRAY}└{'─' * (menu_width - 2)}┘{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}+{'-' * (menu_width - 2)}+{RESET}"
        summary_side = f"{LIGHT_GRAY}│{RESET}" if USE_UNICODE else f"{LIGHT_GRAY}|{RESET}"
        
        # Calculate optimal settings
        resolution = "1920x1080"  # Default to 1080p
        if media_data["images"]["count"] > 50:
            resolution = "3840x2160"  # Use 4K for larger sets
        
        # Auto-detect encoder
        encoder = detect_best_encoder()
        
        # Choose quality based on hardware
        if hw_info.get("apple_silicon") or (hw_info.get("cpu_cores", 4) >= 8):
            quality = "slow"  # Better quality for good hardware
        else:
            quality = "medium"  # Default quality
        
        # Auto-select slide duration
        slide_duration = 3.0  # Default duration
        if media_data["audio"]["duration"] and media_data["images"]["count"] > 0:
            raw_duration = media_data["audio"]["duration"] / media_data["images"]["count"]
            slide_duration = max(2.0, min(6.0, raw_duration))
        
        # Function to create summary row
        def summary_row(label, value, extra=""):
            label = f"{BOLD}{label}:{RESET}"
            padding = menu_width - len(label) - len(value) - len(extra) - 5
            if extra:
                return f"{summary_side} {label} {CYAN}{value}{RESET} {GRAY}{extra}{RESET}{' ' * padding} {summary_side}"
            else:
                return f"{summary_side} {label} {CYAN}{value}{RESET}{' ' * padding} {summary_side}"
        
        print(summary_box_top)
        print(summary_row("Title", title))
        print(summary_row("Resolution", resolution))
        print(summary_row("Quality", quality))
        print(summary_row("Output", default_filename))
        
        hw_text = "(hardware accelerated)" if "videotoolbox" in encoder or "nvenc" in encoder or "qsv" in encoder else ""
        print(summary_row("Encoder", encoder, hw_text))
        
        if media_data["audio"]["selected"]:
            print(summary_row("Audio", os.path.basename(media_data["audio"]["selected"])))
        
        print(summary_row("Images", str(media_data["images"]["count"])))
        print(summary_row("Per slide", f"{slide_duration:.2f} seconds"))
        print(summary_box_bottom)
    else:
        # Calculate optimal settings
        resolution = "1920x1080"  # Default to 1080p
        if media_data["images"]["count"] > 50:
            resolution = "3840x2160"  # Use 4K for larger sets
        
        # Auto-detect encoder
        encoder = detect_best_encoder()
        
        # Choose quality based on hardware
        if hw_info.get("apple_silicon") or (hw_info.get("cpu_cores", 4) >= 8):
            quality = "slow"  # Better quality for good hardware
        else:
            quality = "medium"  # Default quality
        
        # Auto-select slide duration
        slide_duration = 3.0  # Default duration
        if media_data["audio"]["duration"] and media_data["images"]["count"] > 0:
            raw_duration = media_data["audio"]["duration"] / media_data["images"]["count"]
            slide_duration = max(2.0, min(6.0, raw_duration))
        
        print("\nSlideshow Configuration:")
        print("-" * menu_width)
        print(f"Title:      {title}")
        print(f"Resolution: {resolution}")
        print(f"Quality:    {quality}")
        print(f"Output:     {default_filename}")
        print(f"Encoder:    {encoder}{' (hardware accelerated)' if 'videotoolbox' in encoder or 'nvenc' in encoder or 'qsv' in encoder else ''}")
        
        if media_data["audio"]["selected"]:
            print(f"Audio:      {os.path.basename(media_data['audio']['selected'])}")
        
        print(f"Images:     {media_data['images']['count']}")
        print(f"Per slide:  {slide_duration:.2f} seconds")
        print("-" * menu_width)
    
    print()
    
    # Confirm with styled button
    if USE_COLORS and USE_UNICODE:
        print(f"{' ' * 4}{GREEN}▶{RESET} Ready to begin")
    
    # Confirm
    if ask_question("Create slideshow now", default="y", options=["y", "n"]) != "y":
        if USE_COLORS:
            print(f"\n{GRAY}Slideshow creation cancelled{RESET}")
        else:
            print("\nSlideshow creation cancelled")
        input("\nPress Enter to return to the main menu...")
        return
    
    # Create encoding script
    if USE_COLORS:
        print(f"\n{BLUE}▶{RESET} {BOLD}Creating slideshow...{RESET}")
    else:
        print("\nCreating slideshow...")
    
    # Calculate optimal settings if not already done
    if not 'resolution' in locals():
        resolution = "1920x1080"  # Default to 1080p
        if media_data["images"]["count"] > 50:
            resolution = "3840x2160"  # Use 4K for larger sets
    
    if not 'encoder' in locals():
        encoder = detect_best_encoder()
    
    if not 'quality' in locals():
        quality = "medium"  # Default quality
        if hw_info.get("apple_silicon") or (hw_info.get("cpu_cores", 4) >= 8):
            quality = "slow"  # Better quality for good hardware
    
    if not 'slide_duration' in locals():
        slide_duration = 3.0  # Default duration
        if media_data["audio"]["duration"] and media_data["images"]["count"] > 0:
            raw_duration = media_data["audio"]["duration"] / media_data["images"]["count"]
            slide_duration = max(2.0, min(6.0, raw_duration))
    
    # Save settings for future use
    settings = load_settings()
    settings["last_resolution"] = resolution
    settings["last_quality"] = quality
    settings["quick_mode"] = True
    save_settings(settings)
    
    # Create encoding script
    create_encoding_script(
        title, 
        resolution, 
        quality, 
        default_filename, 
        encoder, 
        media_data["audio"]["selected"], 
        media_data["images"]["suggested_order"],
        slide_duration
    )
    
    # Run encoding
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
            run_encoding()
            print_styled(GREEN, f"✓ Successfully created slideshow: {output_filename}")
            success_count += 1
        except Exception as e:
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

def create_test_images():
    """Create sample test images for demo purposes"""
    print_styled(CYAN, "Creating test images...")
    
    # Ensure directories exist
    os.makedirs("images/original", exist_ok=True)
    os.makedirs("song", exist_ok=True)
    
    # Create 10 test images with different colors
    colors = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255),
        (255, 255, 0), (255, 0, 255), (0, 255, 255),
        (128, 0, 0), (0, 128, 0), (0, 0, 128),
        (128, 128, 128)
    ]
    
    # Try to get a font, fall back to default if not available
    try:
        # Try to use a system font that might be available
        font_size = 40
        if platform.system() == "Darwin":  # macOS
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        elif platform.system() == "Windows":
            font = ImageFont.truetype("arial.ttf", font_size)
        else:  # Linux
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except Exception:
        # Use default font if we can't load a system font
        font = None
    
    # Create images
    for i in range(1, 11):
        img = Image.new('RGB', (800, 600), colors[i-1])
        draw = ImageDraw.Draw(img)
        
        # Add text
        text = f"Test Image {i}"
        
        # If we have a font, use it
        if font:
            # Center the text
            text_width = draw.textlength(text, font=font)
            text_position = ((800 - text_width) // 2, 280)
            draw.text(text_position, text, fill=(255, 255, 255), font=font)
        else:
            # Without a specific font, just draw centered text
            text_position = (350, 280)
            draw.text(text_position, text, fill=(255, 255, 255))
        
        # Save image
        img_path = os.path.join("images/original", f"test{i}.jpg")
        img.save(img_path)
    
    # Create a test audio file
    try:
        # Just create an empty file for demonstration
        audio_path = os.path.join("song", "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("This is a placeholder for a real MP3 file.")
        
        print_styled(GREEN, f"✓ Created 10 test images and a placeholder audio file")
        return True
    except Exception as e:
        print_styled(RED, f"Error creating test audio: {e}")
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 