#!/usr/bin/env python3
"""
SlideSonic (2025) - Encoding Progress Monitor
Shows status of ongoing slideshow encoding with Apple-inspired design aesthetics
and comprehensive accessibility features.
https://github.com/chama-x/SlideSonic-2025
"""

import os
import sys
import time
import subprocess
import re
import platform
import shutil
import argparse
import signal
from datetime import datetime, timedelta
import curses
import psutil

# Version information
VERSION = "2.5.0"
COPYRIGHT = "© 2025 Chama-X"

# Terminal colors and styling
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    # Apple-inspired colors
    BLUE = "\033[38;5;32m"      # Apple blue
    GRAY = "\033[38;5;242m"     # Dark gray
    LIGHT_GRAY = "\033[38;5;248m" # Light gray
    GREEN = "\033[38;5;35m"     # Success green
    YELLOW = "\033[38;5;220m"   # Warning yellow
    RED = "\033[38;5;196m"      # Error red
    PURPLE = "\033[38;5;135m"   # Process purple
    CYAN = "\033[38;5;87m"      # Info cyan
    
    # Background colors
    BG_GRAY = "\033[48;5;235m"  # Dark background
    BG_BLUE = "\033[48;5;24m"   # Blue background

# Global settings
USE_COLORS = True
USE_ANIMATIONS = True
USE_UNICODE = True

# Color pairs for curses
COLORS = {
    'normal': 1,
    'info': 2,
    'success': 3,
    'warning': 4,
    'error': 5,
    'progress': 6,
    'highlight': 7,
}

def parse_arguments():
    """Parse command-line arguments for monitor_encoding.py"""
    parser = argparse.ArgumentParser(
        description="SlideSonic (2025) - Encoding Progress Monitor"
    )
    
    parser.add_argument("output_file", nargs="?", default="video.mp4",
                      help="Output video file to monitor (default: video.mp4)")
    parser.add_argument("--accessibility", action="store_true",
                      help="Enable accessibility mode (no colors, animations, or unicode)")
    parser.add_argument("--no-colors", action="store_true",
                      help="Disable colored output")
    parser.add_argument("--no-animations", action="store_true",
                      help="Disable animations")
    parser.add_argument("--no-unicode", action="store_true",
                      help="Use ASCII instead of unicode characters")
    parser.add_argument("--log-file", default="ffmpeg_output.log",
                      help="Path to FFmpeg log file (default: ffmpeg_output.log)")
    parser.add_argument("--version", action="store_true",
                      help="Show version information and exit")
    
    args = parser.parse_args()
    
    # Set global options
    global USE_COLORS, USE_ANIMATIONS, USE_UNICODE
    
    # Handle version request
    if args.version:
        print_version()
        sys.exit(0)
    
    # Apply settings - accessibility trumps individual settings
    if args.accessibility:
        USE_COLORS = False
        USE_ANIMATIONS = False
        USE_UNICODE = False
    else:
        USE_COLORS = not args.no_colors
        USE_ANIMATIONS = not args.no_animations
        USE_UNICODE = not args.no_unicode
        
        # Auto-detect terminal capabilities
        if not sys.stdout.isatty() or os.environ.get('TERM') == 'dumb':
            USE_COLORS = False
            USE_ANIMATIONS = False
    
    return args

def print_version():
    """Print version information"""
    if USE_COLORS:
        print(f"{Colors.BOLD}{Colors.BLUE}SlideSonic (2025) - Encoding Monitor{Colors.RESET}")
        print(f"{Colors.GRAY}Version {VERSION}")
        print(f"{Colors.GRAY}{COPYRIGHT}")
    else:
        print(f"SlideSonic (2025) - Encoding Monitor")
        print(f"Version {VERSION}")
        print(f"{COPYRIGHT}")

def print_styled(style, text):
    """Print styled text with fallback for non-color terminals"""
    if USE_COLORS:
        print(f"{style}{text}{Colors.RESET}")
    else:
        print(text)

def setup_signal_handlers():
    """Set up signal handlers for graceful exit"""
    def signal_handler(sig, frame):
        if sig == signal.SIGINT:
            print("")  # Newline after ^C
            print_styled(Colors.YELLOW, "\n⚠️  Monitoring stopped.")
            print_styled(Colors.GRAY, "The encoding process is continuing in the background.")
            sys.exit(130)
        elif sig in (signal.SIGTERM, signal.SIGHUP):
            print_styled(Colors.YELLOW, "\n⚠️  Monitoring terminated.")
            sys.exit(143)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    if platform.system() != "Windows":  # These signals don't exist on Windows
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGHUP, signal_handler)

def get_terminal_size():
    """Get terminal size for better formatting with fallback for non-terminal environments"""
    try:
        columns, rows = shutil.get_terminal_size()
        return columns, rows
    except:
        return 80, 24  # Reasonable defaults

def get_ffmpeg_processes():
    """Get all running ffmpeg processes with improved error handling"""
    try:
        if platform.system() == "Windows":
            cmd = ["tasklist", "/fi", "imagename eq ffmpeg.exe", "/fo", "csv"]
        else:
            cmd = ["ps", "aux"]
        
        output = subprocess.check_output(cmd, universal_newlines=True)
        if platform.system() == "Windows":
            return "ffmpeg.exe" in output
        else:
            return len([line for line in output.split('\n') if 'ffmpeg' in line and 'grep' not in line]) > 0
    except Exception as e:
        print_styled(Colors.RED, f"Error checking FFmpeg processes: {e}")
        # Assume FFmpeg is running if we can't check
        return True

def get_output_video_size(output_file):
    """Get the current size of the output video file"""
    try:
        if os.path.exists(output_file):
            size_bytes = os.path.getsize(output_file)
            if size_bytes > 1024*1024:
                return f"{size_bytes/(1024*1024):.2f} MB"
            else:
                return f"{size_bytes/1024:.2f} KB"
        return "Not created yet"
    except Exception as e:
        print_styled(Colors.RED, f"Error getting file size: {e}")
        return "Unknown"

def get_processor_usage():
    """Get current CPU usage of ffmpeg processes"""
    try:
        if platform.system() == "Darwin":  # macOS
            try:
                pid_output = subprocess.check_output(["pgrep", "ffmpeg"]).decode().strip()
                cmd = ["ps", "-o", "%cpu", "-p", pid_output]
            except:
                return 0
        elif platform.system() == "Linux":
            try:
                pid_output = subprocess.check_output(["pgrep", "ffmpeg"]).decode().strip()
                cmd = ["ps", "-o", "%cpu", "-p", pid_output]
            except:
                return 0
        else:  # Windows
            return 0  # Not easily available on Windows
        
        output = subprocess.check_output(cmd, universal_newlines=True)
        lines = output.strip().split('\n')
        if len(lines) > 1:
            # Skip header line and sum all values
            cpu_values = [float(line.strip()) for line in lines[1:] if line.strip()]
            return sum(cpu_values)
        return 0
    except Exception as e:
        print_styled(Colors.RED, f"Error getting CPU usage: {e}")
        return 0

def get_encoding_speed(log_file):
    """Try to get encoding speed from ffmpeg output"""
    try:
        # This requires ffmpeg output to be directed to a file
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                content = f.read()
                match = re.search(r"speed=([0-9.]+)x", content)
                if match:
                    return float(match.group(1))
        return 0
    except Exception as e:
        print_styled(Colors.RED, f"Error getting encoding speed: {e}")
        return 0

def get_progress_info(log_file):
    """Extract more detailed progress information"""
    try:
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                content = f.read()
                
                # Try to extract current frame/total frames
                frame_match = re.search(r"frame=\s*(\d+)", content)
                current_frame = int(frame_match.group(1)) if frame_match else 0
                
                # Try to extract fps
                fps_match = re.search(r"fps=\s*([0-9.]+)", content)
                fps = float(fps_match.group(1)) if fps_match else 0
                
                # Try to extract time
                time_match = re.search(r"time=\s*([0-9:.]+)", content)
                time_str = time_match.group(1) if time_match else "00:00:00"
                
                # Convert time string to seconds
                try:
                    h, m, s = map(float, time_str.split(':'))
                    time_seconds = h * 3600 + m * 60 + s
                except:
                    time_seconds = 0
                
                return {
                    "frame": current_frame,
                    "fps": fps,
                    "time": time_seconds,
                    "time_str": time_str
                }
        return {}
    except Exception as e:
        print_styled(Colors.RED, f"Error parsing progress: {e}")
        return {}

def draw_progress_bar(percentage, width=40, fill_char="■", empty_char="□"):
    """Draw a stylish progress bar with accessibility considerations"""
    if not USE_UNICODE:
        fill_char = "#"
        empty_char = "-"
    
    filled_width = int(width * percentage / 100)
    
    if USE_COLORS:
        bar = ""
        # Add gradient colors to the progress bar for a more Apple-like look
        for i in range(width):
            if i < filled_width:
                if i < width * 0.3:  # First 30% - blue
                    bar += f"{Colors.BLUE}{fill_char}{Colors.RESET}"
                elif i < width * 0.7:  # Middle 40% - blue-purple gradient
                    bar += f"{Colors.PURPLE}{fill_char}{Colors.RESET}"
                else:  # Last 30% - purple
                    bar += f"{Colors.PURPLE}{fill_char}{Colors.RESET}"
            else:
                bar += f"{Colors.GRAY}{empty_char}{Colors.RESET}"
    else:
        # Simple ASCII progress bar for accessibility mode
        bar = fill_char * filled_width + empty_char * (width - filled_width)
    
    return bar

def format_time(seconds):
    """Format seconds into a human-readable time"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def display_progress(args):
    """Display encoding progress information with Apple-like design aesthetics"""
    start_time = datetime.now()
    columns, rows = get_terminal_size()
    output_file = args.output_file
    log_file = args.log_file
    
    # Track stats for simple graph
    speeds = []
    max_speed = 1  # Avoid division by zero
    
    try:
        while get_ffmpeg_processes():
            current_time = datetime.now()
            elapsed = current_time - start_time
            elapsed_seconds = elapsed.total_seconds()
            
            # Clear previous output if not in accessibility mode
            if not args.accessibility and platform.system() != "Windows":
                os.system('clear')
            elif not args.accessibility and platform.system() == "Windows":
                os.system('cls')
            else:
                # In accessibility mode, just add a separator
                print("\n" + ("-" * 40) + "\n")
            
            # Get updated terminal size
            columns, rows = get_terminal_size()
            
            # Get current metrics
            cpu_usage = get_processor_usage()
            encoding_speed = get_encoding_speed(log_file)
            progress_info = get_progress_info(log_file)
            file_size = get_output_video_size(output_file)
            
            # Update tracking
            if encoding_speed > 0:
                speeds.append(encoding_speed)
                max_speed = max(max_speed, encoding_speed)
            
            # Title bar
            title = "SlideSonic Encoding Monitor"
            if USE_COLORS:
                padding = (columns - len(title)) // 2
                print(f"{Colors.BG_BLUE}{Colors.BOLD}{' ' * padding}{title}{' ' * padding}{Colors.RESET}")
            else:
                print(title)
                print("=" * columns)
            
            # Main area
            print_styled(Colors.BOLD, "\nEncoding Progress\n")
            
            # Status indicator with accessibility considerations
            status_text = "Excellent" if encoding_speed > 15 else "Good" if encoding_speed > 5 else "Slow"
            
            if USE_COLORS:
                status_color = Colors.GREEN if encoding_speed > 15 else Colors.YELLOW if encoding_speed > 5 else Colors.RED
                print(f"Status: {status_color}●{Colors.RESET} {status_color}{status_text}{Colors.RESET}")
            else:
                status_symbol = "+" if encoding_speed > 15 else "~" if encoding_speed > 5 else "-"
                print(f"Status: [{status_symbol}] {status_text}")
            
            # Output file and size
            print(f"\nOutput: {output_file}")
            print(f"Size:   {file_size}")
            
            # Time information
            print(f"\nTime Elapsed: {format_time(elapsed_seconds)}")
            if 'time_str' in progress_info:
                print(f"Video Time:   {progress_info.get('time_str', '00:00:00')}")
            
            # Performance metrics
            print_styled(Colors.BOLD, "\nPerformance Metrics")
            print(f"CPU Usage:      {cpu_usage:.1f}%")
            
            # Encoding speed with colored indicator or text-based alternative
            if encoding_speed > 0:
                if USE_COLORS:
                    speed_color = Colors.GREEN if encoding_speed > 15 else Colors.YELLOW if encoding_speed > 5 else Colors.RED
                    print(f"Encoding Speed: {speed_color}{encoding_speed:.2f}x{Colors.RESET}")
                else:
                    speed_indicator = "FAST" if encoding_speed > 15 else "NORMAL" if encoding_speed > 5 else "SLOW"
                    print(f"Encoding Speed: {encoding_speed:.2f}x ({speed_indicator})")
            
            # Progress bar (if we can estimate progress)
            if 'time' in progress_info and 'time_str' in progress_info:
                # Try to estimate progress based on audio duration from the log
                try:
                    with open(log_file, "r") as f:
                        content = f.read()
                        audio_duration_match = re.search(r"Duration: (\d+:\d+:\d+\.\d+)", content)
                        
                    if audio_duration_match:
                        duration_str = audio_duration_match.group(1)
                        h, m, s = map(float, duration_str.split(':'))
                        total_seconds = h * 3600 + m * 60 + s
                        
                        if total_seconds > 0:
                            progress_percent = min(100, (progress_info['time'] / total_seconds) * 100)
                            
                            print("\nProgress:")
                            print(draw_progress_bar(progress_percent, width=min(columns-10, 50)))
                            
                            if USE_COLORS:
                                print(f"{Colors.GRAY}{progress_percent:.1f}%{Colors.RESET}")
                            else:
                                print(f"{progress_percent:.1f}%")
                except Exception as e:
                    print_styled(Colors.RED, f"Error estimating progress: {e}")
            
            # Simple encoding speed graph if not in accessibility mode
            if len(speeds) > 1 and not args.accessibility and USE_UNICODE:
                graph_width = min(columns-10, 50)
                graph_height = 5
                print_styled(Colors.BOLD, "\nEncoding Speed History")
                
                # Use the most recent speeds for the graph
                recent_speeds = speeds[-graph_width:] if len(speeds) > graph_width else speeds
                
                # Draw simple ASCII graph
                for h in range(graph_height, 0, -1):
                    line = ""
                    threshold = max_speed * h / graph_height
                    for s in recent_speeds:
                        if s >= threshold:
                            if USE_COLORS:
                                line += f"{Colors.BLUE}█{Colors.RESET}"
                            else:
                                line += "#"
                        else:
                            line += " "
                    # Add scale
                    if h == graph_height:
                        if USE_COLORS:
                            line += f" {Colors.GRAY}{max_speed:.1f}x{Colors.RESET}"
                        else:
                            line += f" {max_speed:.1f}x"
                    elif h == 1:
                        if USE_COLORS:
                            line += f" {Colors.GRAY}{(max_speed/graph_height):.1f}x{Colors.RESET}"
                        else:
                            line += f" {(max_speed/graph_height):.1f}x"
                    print(line)
            
            # Key controls - different for accessibility mode
            if args.accessibility:
                print("\nProgress updates automatically. Press Ctrl+C to stop monitoring.")
            else:
                if USE_COLORS:
                    print(f"\n{Colors.GRAY}Press Ctrl+C to stop monitoring (encoding will continue){Colors.RESET}")
                else:
                    print("\nPress Ctrl+C to stop monitoring (encoding will continue)")
            
            # Sleep with or without animation
            if USE_ANIMATIONS and not args.accessibility:
                frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"] if USE_UNICODE else ["-", "\\", "|", "/"]
                for i in range(5):  # Shorter update interval for more responsive UI
                    if USE_COLORS:
                        sys.stdout.write(f"\r{Colors.BLUE}{frames[i % len(frames)]}{Colors.RESET} Updating...")
                    else:
                        sys.stdout.write(f"\r{frames[i % len(frames)]} Updating...")
                    sys.stdout.flush()
                    time.sleep(0.2)
            else:
                # Simple wait without animation for accessibility mode
                time.sleep(1)
        
        # When done
        # Clear screen one last time if not in accessibility mode
        if not args.accessibility:
            if platform.system() != "Windows":
                os.system('clear')
            else:
                os.system('cls')
            
            # Title bar
            title = "SlideSonic Encoding Complete"
            if USE_COLORS:
                padding = (columns - len(title)) // 2
                print(f"{Colors.BG_BLUE}{Colors.BOLD}{' ' * padding}{title}{' ' * padding}{Colors.RESET}")
            else:
                print(title)
                print("=" * columns)
        else:
            # In accessibility mode, just add a separator
            print("\n" + ("-" * 40) + "\n")
            print("ENCODING COMPLETE")
            print("-" * 40 + "\n")
        
        # Completion information
        if USE_COLORS:
            print(f"\n{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}Encoding process completed successfully!{Colors.RESET}")
        else:
            print("\n[SUCCESS] Encoding process completed successfully!")
            
        print(f"\nOutput: {output_file}")
        print(f"File Size: {get_output_video_size(output_file)}")
        
        final_time = datetime.now() - start_time
        print(f"Total Time: {str(final_time).split('.')[0]}")
        
        if len(speeds) > 0:
            avg_speed = sum(speeds) / len(speeds)
            if USE_COLORS:
                print(f"Average Speed: {Colors.GREEN}{avg_speed:.2f}x{Colors.RESET}")
            else:
                print(f"Average Speed: {avg_speed:.2f}x")
        
        # Calculate realtime factor
        if 'time' in progress_info and elapsed_seconds > 0:
            realtime_factor = progress_info['time'] / elapsed_seconds
            print(f"Realtime Factor: {realtime_factor:.2f}x")
        
        if USE_COLORS:
            print(f"\n{Colors.GRAY}Your video is ready to play.{Colors.RESET}")
        else:
            print("\nYour video is ready to play.")
        
    except KeyboardInterrupt:
        if USE_COLORS:
            print(f"\n\n{Colors.YELLOW}⏹️  Monitoring stopped.{Colors.RESET}")
            print(f"{Colors.GRAY}The encoding process is continuing in the background.{Colors.RESET}")
        else:
            print("\n\n[STOPPED] Monitoring stopped.")
            print("The encoding process is continuing in the background.")
    except Exception as e:
        if USE_COLORS:
            print(f"\n\n{Colors.RED}❌ Error monitoring progress: {e}{Colors.RESET}")
        else:
            print(f"\n\n[ERROR] Error monitoring progress: {e}")
    
    return 0

def main():
    """Main entry point with error handling and signal management"""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Set up signal handlers
        setup_signal_handlers()
        
        # Check if FFmpeg is running
        if not get_ffmpeg_processes():
            if USE_COLORS:
                print(f"{Colors.YELLOW}⚠️  No active FFmpeg processes found.{Colors.RESET}")
            else:
                print("[WARNING] No active FFmpeg processes found.")
                
            print("Start an encoding process first or specify the output file:")
            
            if USE_COLORS:
                print(f"{Colors.GRAY}    python3 monitor_encoding.py [output_file]{Colors.RESET}")
            else:
                print("    python3 monitor_encoding.py [output_file]")
                
            return 1
        
        # Run the progress display
        return display_progress(args)
    
    except Exception as e:
        if USE_COLORS:
            print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        else:
            print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 