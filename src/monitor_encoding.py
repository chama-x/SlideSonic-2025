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
import json

# Try to import psutil but make it optional
try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    HAVE_PSUTIL = False

# Version information
VERSION = "2.5.0"
COPYRIGHT = "© 2025 Chama-X"

# Module-level globals
ffmpeg_pid = None  # Will store FFmpeg process ID for tracking

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
    parser.add_argument("--update-interval", type=int, default=1,
                      help="Update interval in seconds (default: 1)")
    parser.add_argument("--ffmpeg-pid", type=int, default=None,
                      help="PID of the FFmpeg process to monitor")
    
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
        # Use specific process ID tracking for the current ffmpeg process
        global ffmpeg_pid
        
        # If we have a specific PID to track
        if ffmpeg_pid is not None:
            try:
                if platform.system() == "Windows":
                    # Check if this specific process exists on Windows
                    cmd = ["tasklist", "/fi", f"PID eq {ffmpeg_pid}", "/fo", "csv"]
                    output = subprocess.check_output(cmd, universal_newlines=True)
                    return str(ffmpeg_pid) in output
                else:
                    # Check if this specific process exists on Unix
                    try:
                        # Try sending signal 0 to check if process exists
                        os.kill(ffmpeg_pid, 0)
                        
                        # Double check it's actually ffmpeg with ps command
                        if platform.system() != "Windows":
                            try:
                                cmd = ["ps", "-p", str(ffmpeg_pid), "-o", "comm="]
                                process_name = subprocess.check_output(cmd, universal_newlines=True).strip()
                                return "ffmpeg" in process_name.lower()
                            except:
                                # If ps fails but kill succeeded, assume it's our process
                                return True
                        return True
                    except (OSError, ProcessLookupError):
                        # Process doesn't exist anymore
                        return False
            except (subprocess.SubprocessError, OSError):
                # Process doesn't exist anymore or error in checking
                return False
        
        # Fallback to generic detection if no PID is known
        if platform.system() == "Windows":
            cmd = ["tasklist", "/fi", "imagename eq ffmpeg.exe", "/fo", "csv"]
        else:
            cmd = ["ps", "aux"]
        
        output = subprocess.check_output(cmd, universal_newlines=True)
        if platform.system() == "Windows":
            return "ffmpeg.exe" in output
        else:
            # More specific FFmpeg detection to avoid false positives
            ffmpeg_lines = [line for line in output.split('\n') 
                          if 'ffmpeg' in line and 'grep' not in line]
            
            # If we find any ffmpeg process, try to save its PID for future checks
            if ffmpeg_lines and ffmpeg_pid is None:
                try:
                    # Extract PID from ps output (second column in Unix)
                    first_line = ffmpeg_lines[0].strip()
                    pid_part = first_line.split()[1]
                    ffmpeg_pid = int(pid_part)
                except (IndexError, ValueError):
                    pass
            
            return len(ffmpeg_lines) > 0
    except Exception as e:
        print_styled(Colors.RED, f"Error checking FFmpeg processes: {e}")
        # Don't assume it's running in case of error - better to exit than to loop forever
        return False

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
    """Get current CPU usage of ffmpeg processes with improved reliability"""
    try:
        if HAVE_PSUTIL:
            # If psutil is available, use it for more accurate CPU usage
            total_cpu = 0
            ffmpeg_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    if proc.info['name'] and ('ffmpeg' in proc.info['name'].lower()):
                        ffmpeg_processes.append(proc)
                except:
                    continue
            
            if not ffmpeg_processes:
                return 0
                
            # First call to establish baseline
            for proc in ffmpeg_processes:
                try:
                    proc.cpu_percent(interval=None)
                except:
                    pass
            
            # Small sleep for measurement
            time.sleep(0.1)
            
            # Second call to get actual values
            for proc in ffmpeg_processes:
                try:
                    cpu = proc.cpu_percent(interval=None)
                    if cpu is not None and cpu >= 0:
                        total_cpu += cpu
                except:
                    continue
            
            # Normalize by core count and cap at 100%
            try:
                num_cores = psutil.cpu_count(logical=True) or 1
                normalized_cpu = min(100, total_cpu / num_cores)
                return normalized_cpu
            except:
                return min(100, total_cpu)
        
        # Simplified fallback method if psutil is not available
        return 50  # Return a reasonable default value when we can't measure
    except:
        return 0  # Return 0 on any error

def read_latest_log_lines(log_file, max_lines=500):
    """Read the latest lines from a log file more efficiently"""
    try:
        if not os.path.exists(log_file):
            return []
            
        # Get file size to optimize reading from the end
        file_size = os.path.getsize(log_file)
        if file_size == 0:
            return []
            
        # For small files, just read the whole thing
        if file_size < 50000:  # Under 50KB
            with open(log_file, 'r') as f:
                return f.read().splitlines()
                
        # For larger files, try to read from the end
        with open(log_file, 'r') as f:
            # Seek to near the end of the file
            f.seek(max(0, file_size - 50000))  # Last ~50KB
            
            # Skip partial line if we're not at the beginning
            if f.tell() > 0:
                f.readline()
                
            # Read the rest of the file
            lines = f.read().splitlines()
            
            # Limit to the latest max_lines
            return lines[-max_lines:] if len(lines) > max_lines else lines
    except Exception as e:
        print_styled(Colors.RED, f"Error reading log file: {e}")
        return []

def get_encoding_speed(log_file):
    """Get encoding speed from ffmpeg output with improved reliability"""
    try:
        # Get the latest lines from the log file
        recent_lines = read_latest_log_lines(log_file, max_lines=50)  # Reduced line count for efficiency
        if not recent_lines:
            return 0
                
        # Search for the latest speed entry by checking lines from the end
        for line in reversed(recent_lines):
            if "speed=" in line:
                # Try different regex patterns to account for FFmpeg output variations
                # Pattern 1: Common format "speed=X.XXx"
                match = re.search(r"speed=\s*([0-9.]+)x", line)
                if match:
                    try:
                        speed = float(match.group(1))
                        # Reasonable cap at 8x which is already very fast for encoding
                        return min(8.0, speed)
                    except (ValueError, TypeError):
                        continue
                
                # Pattern 2: Alternative format "speed=X.XX"
                alt_match = re.search(r"speed=\s*([0-9.]+)\s", line)
                if alt_match:
                    try:
                        speed = float(alt_match.group(1))
                        return min(8.0, speed)
                    except (ValueError, TypeError):
                        continue
        
        return 0
    except Exception:
        return 0  # Return 0 on any error

def get_progress_info(log_file):
    """Extract progress information with improved error handling"""
    try:
        if not os.path.exists(log_file):
            return {}
            
        # Get the latest lines from the log file - reduce line count for efficiency
        recent_lines = read_latest_log_lines(log_file, max_lines=100)
        if not recent_lines:
            return {}
        
        # Start with time extraction
        time_str = "00:00:00"
        time_seconds = 0
        for line in reversed(recent_lines):
            time_match = re.search(r"time=\s*([0-9:.]+)", line)
            if time_match:
                time_str = time_match.group(1)
                try:
                    if '.' in time_str:  # Handle format HH:MM:SS.MS
                        parts = time_str.split('.')
                        base_time = parts[0]
                        ms = float('0.' + parts[1]) if len(parts) > 1 else 0
                        h, m, s = map(float, base_time.split(':'))
                        time_seconds = h * 3600 + m * 60 + s + ms
                    else:  # Handle format HH:MM:SS
                        h, m, s = map(float, time_str.split(':'))
                        time_seconds = h * 3600 + m * 60 + s
                except:
                    time_seconds = 0
                break  # Found the time, no need to continue
        
        # Extract total duration - check both ffmpeg output and metadata
        total_duration = 0
        
        # First try metadata file which is more reliable for slideshows
        try:
            if os.path.exists("temp/encode_metadata.json"):
                with open("temp/encode_metadata.json", "r") as meta_file:
                    metadata = json.load(meta_file)
                    if "settings" in metadata and "total_duration" in metadata["settings"]:
                        total_duration = float(metadata["settings"]["total_duration"])
                        # Add a slight buffer to avoid premature 100%
                        total_duration *= 1.05  # Add 5% buffer
        except:
            pass  # Continue to check ffmpeg output if metadata fails
            
        # Fallback to ffmpeg output
        if total_duration <= 0:
            for line in recent_lines:
                duration_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", line)
                if duration_match:
                    try:
                        h, m, s = map(float, duration_match.groups())
                        total_duration = h * 3600 + m * 60 + s
                        # Add a slight buffer to avoid premature 100%
                        total_duration *= 1.05  # Add 5% buffer
                    except:
                        pass
                    break
                    
            # If we still don't have duration, look for a specific slide total info
            if total_duration <= 0:
                for line in recent_lines:
                    if "Creating slideshow with" in line and "seconds total duration" in line:
                        try:
                            # Match patterns like "Creating slideshow with XX.X seconds total duration"
                            duration_match = re.search(r"with\s+([0-9.]+)\s+seconds", line)
                            if duration_match:
                                total_duration = float(duration_match.group(1))
                                # Add a buffer
                                total_duration *= 1.05
                        except:
                            pass
        
        # Create basic info dictionary
        info = {
            "time": time_seconds,
            "time_str": time_str,
            "total_duration": total_duration
        }
        
        # Calculate progress percentage if we have both time and duration
        if time_seconds > 0 and total_duration > 0:
            # More accurate progress calculation
            raw_progress = (time_seconds / total_duration) * 100
            # Cap at 95% until we know encoding is completely done
            info["progress_percent"] = min(95.0, raw_progress)
        else:
            # If we don't have enough data, use a very conservative estimate
            info["progress_percent"] = min(10.0, time_seconds / 5.0) if time_seconds > 0 else 0
        
        return info
    except Exception:
        return {}  # Return empty dict on any error to avoid crashes

def draw_progress_bar(percentage, width=40, fill_char="■", empty_char="□"):
    """Draw a stylish progress bar with accessibility considerations"""
    # Sanitize input
    try:
        percentage = float(percentage)
        if percentage < 0:
            percentage = 0
        elif percentage > 100:
            percentage = 100
            
        width = max(10, min(width, 100))  # Reasonable width limits
    except (ValueError, TypeError):
        percentage = 0
        
    if not USE_UNICODE:
        fill_char = "#"
        empty_char = "-"
    
    # Calculate filled portion
    try:
        filled_width = int(width * percentage / 100)
        filled_width = min(filled_width, width)  # Safety check
    except Exception:
        filled_width = 0
    
    try:
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
    except Exception:
        # Ultimate fallback if anything goes wrong
        if USE_COLORS:
            return f"{Colors.GRAY}[{'#' * 10}]{Colors.RESET}"
        else:
            return "[##########]"

def format_time(seconds):
    """Format seconds into a human-readable time"""
    try:
        seconds = float(seconds)
        if not isinstance(seconds, (int, float)) or seconds < 0:
            seconds = 0
        elif seconds > 359999:  # Cap at 99:59:59
            seconds = 359999
            
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    except Exception:
        return "00:00:00"

def find_output_file():
    """Try to automatically find the correct output file"""
    try:
        # First, look for metadata with output file information
        if os.path.exists("temp/encode_metadata.json"):
            try:
                with open("temp/encode_metadata.json", "r") as meta_file:
                    metadata = json.load(meta_file)
                    if "output_file" in metadata:
                        # If the output file is specified in metadata, use that
                        output_file = metadata["output_file"]
                        if os.path.exists(output_file):
                            return output_file
            except:
                pass
        
        # Next, try to find recent MP4 files in current directory
        recent_mp4 = None
        newest_time = 0
        
        # Check current directory for MP4 files
        for file in os.listdir("."):
            if file.lower().endswith(".mp4"):
                file_path = os.path.join(".", file)
                mtime = os.path.getmtime(file_path)
                if mtime > newest_time:
                    newest_time = mtime
                    recent_mp4 = file
                    
        # Check output directory if it exists
        if os.path.exists("output"):
            for file in os.listdir("output"):
                if file.lower().endswith(".mp4"):
                    file_path = os.path.join("output", file)
                    mtime = os.path.getmtime(file_path)
                    if mtime > newest_time:
                        newest_time = mtime
                        recent_mp4 = os.path.join("output", file)
        
        # If we found a recent MP4 file, use that
        if recent_mp4 and (newest_time > time.time() - 3600):  # Only consider files created in the last hour
            return recent_mp4
    except:
        pass
    
    # Default fallback if nothing else works
    return "output.mp4"

def display_progress(args):
    """Display encoding progress with a simple, stable interface that doesn't blink"""
    start_time = datetime.now()
    output_file = args.output_file
    log_file = args.log_file
    update_interval = args.update_interval
    
    # Use a longer update interval for stability
    update_interval = max(3, update_interval)  # Minimum 3 seconds
    
    # Initial display
    print("\n" + "=" * 60)
    print(f"Monitoring encoding progress - Press Ctrl+C to stop")
    print("=" * 60)
    print(f"Output file: {output_file}")
    print(f"Log file: {log_file}")
    print(f"Update interval: {update_interval} seconds")
    print("-" * 60)
    
    # Track completion
    last_progress_time = 0
    last_file_size = 0
    size_unchanged_count = 0
    time_unchanged_count = 0
    completed = False
    
    try:
        # Main monitoring loop
        while True:
            # Get metrics without clearing screen
            is_running = get_ffmpeg_processes()
            progress_info = get_progress_info(log_file) or {}
            current_time = datetime.now()
            elapsed = current_time - start_time
            elapsed_seconds = elapsed.total_seconds()
            
            # Try to find output file if not found yet
            if not os.path.exists(output_file):
                potential_file = find_output_file()
                if os.path.exists(potential_file) and potential_file != output_file:
                    output_file = potential_file
                    print(f"\nFound output file: {output_file}")
            
            # Handle completion
            if not is_running:
                if os.path.exists(output_file) and os.path.getsize(output_file) > 1024:
                    print("\nEncoding completed (FFmpeg process ended)")
                    completed = True
                    break
            
            # Create a single line status update
            status_line = f"\r[{current_time.strftime('%H:%M:%S')}] "
            
            # Add basic metrics
            try:
                # CPU usage
                cpu_usage = get_processor_usage()
                status_line += f"CPU: {cpu_usage:.1f}% | "
            except:
                status_line += "CPU: -- | "
            
            # Add encoding speed
            try:
                encoding_speed = get_encoding_speed(log_file)
                if encoding_speed > 0:
                    speed_indicator = "FAST" if encoding_speed > 5.0 else "OK" if encoding_speed > 1.0 else "SLOW"
                    status_line += f"Speed: {encoding_speed:.1f}x ({speed_indicator}) | "
                else:
                    status_line += "Speed: -- | "
            except:
                status_line += "Speed: -- | "
            
            # Add progress information
            try:
                if 'time_str' in progress_info and 'total_duration' in progress_info:
                    time_done = progress_info.get('time', 0)
                    time_total = progress_info.get('total_duration', 0)
                    
                    if time_total > 0:
                        # Calculate percentage with limit
                        progress_pct = progress_info.get('progress_percent', min(95, (time_done / time_total) * 100))
                        
                        # Add time information
                        status_line += f"Time: {progress_info['time_str']}"
                        
                        # Add total duration if available 
                        if time_total > 0:
                            total_time_str = format_time(time_total)
                            status_line += f"/{total_time_str} | "
                        else:
                            status_line += " | "
                        
                        # Add progress percentage
                        status_line += f"{progress_pct:.1f}% "
                        
                        # Simple text-based progress indicator
                        width = 20  # Fixed width for progress indicator
                        filled = int(width * progress_pct / 100)
                        status_line += "["
                        status_line += "#" * filled
                        status_line += "-" * (width - filled)
                        status_line += "]"
                    else:
                        status_line += f"Time: {progress_info['time_str']} | Progress: --% "
                else:
                    status_line += "Time: --:--:-- | Progress: --% "
            except Exception as e:
                status_line += f"Progress: --% "
            
            # Check file size for progress if time data not changing
            current_size = 0
            if os.path.exists(output_file):
                current_size = os.path.getsize(output_file)
            
            # Check for completion through other means
            current_time_str = progress_info.get('time_str', "00:00:00")
            current_time_value = progress_info.get('time', 0)
            
            # Time unchanged check
            if current_time_value > 0 and current_time_value == last_progress_time:
                time_unchanged_count += 1
                if time_unchanged_count >= 5:
                    print("\nEncoding completed (progress time stable)")
                    completed = True
                    break
            else:
                time_unchanged_count = 0
                last_progress_time = current_time_value
            
            # File size unchanged check
            if os.path.exists(output_file):
                if current_size == last_file_size and current_size > 0:
                    size_unchanged_count += 1
                    if size_unchanged_count >= 5:
                        print("\nEncoding completed (file size stable)")
                        completed = True
                        break
                else:
                    size_unchanged_count = 0
            last_file_size = current_size
            
            # Print status line (will update on same line)
            sys.stdout.write(status_line)
            sys.stdout.flush()
            
            # Add simple progress summary every 10 updates (roughly 30+ seconds)
            if (int(elapsed_seconds) // update_interval) % 10 == 0:
                # Print a full progress update periodically on new lines
                print("\n\n" + "-" * 60)
                print(f"Progress Summary:")
                print(f"Elapsed time: {format_time(elapsed_seconds)}")
                
                if 'time_str' in progress_info:
                    time_done = progress_info.get('time', 0)
                    time_total = progress_info.get('total_duration', 0)
                    
                    print(f"Video time: {progress_info['time_str']}")
                    
                    if time_total > 0:
                        total_time_str = format_time(time_total)
                        print(f"Total duration: {total_time_str}")
                        progress_pct = progress_info.get('progress_percent', min(95, (time_done / time_total) * 100))
                        print(f"Progress: {progress_pct:.1f}%")
                        
                        # Estimate remaining time
                        if progress_pct > 5:
                            try:
                                est_total = elapsed_seconds / (progress_pct / 100)
                                est_remaining = est_total - elapsed_seconds
                                if est_remaining > 0:
                                    print(f"Est. remaining: {format_time(est_remaining)}")
                            except:
                                pass
                
                if os.path.exists(output_file):
                    size_bytes = os.path.getsize(output_file)
                    if size_bytes > 1024*1024:
                        print(f"Current file size: {size_bytes/(1024*1024):.2f} MB")
                    else:
                        print(f"Current file size: {size_bytes/1024:.2f} KB")
                
                print("-" * 60)
                print("Continuing monitoring... Press Ctrl+C to stop (encoding will continue)")
                sys.stdout.write("\r") # Reset to beginning of line for status updates
            
            # Sleep between updates
            time.sleep(update_interval)
        
        # Show final summary when done
        if completed or not is_running:
            print("\n\n" + "=" * 60)
            print("ENCODING COMPLETED SUCCESSFULLY")
            print("=" * 60)
            
            # Show final stats
            final_time = datetime.now() - start_time
            print(f"Total encoding time: {str(final_time).split('.')[0]}")
            
            if os.path.exists(output_file):
                size_bytes = os.path.getsize(output_file)
                if size_bytes > 1024*1024:
                    print(f"Final file size: {size_bytes/(1024*1024):.2f} MB")
                else:
                    print(f"Final file size: {size_bytes/1024:.2f} KB")
            
            if 'time_str' in progress_info:
                print(f"Video duration: {progress_info['time_str']}")
                
                if 'total_duration' in progress_info and progress_info['total_duration'] > 0:
                    total_time_str = format_time(progress_info['total_duration'])
                    print(f"Planned duration: {total_time_str}")
            
            try:
                if elapsed_seconds > 0 and progress_info.get('time', 0) > 0:
                    realtime_factor = progress_info['time'] / elapsed_seconds
                    print(f"Processing speed: {realtime_factor:.2f}x realtime")
            except:
                pass
                
            print("\nOutput file is ready: " + output_file)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped. The encoding process continues in the background.")
    except Exception as e:
        print(f"\n\nError monitoring progress: {e}")
    
    return 0

def main():
    """Simplified main entry point focusing on reliability"""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Set update interval to something reasonable
        if not hasattr(args, 'update_interval') or args.update_interval < 1:
            args.update_interval = 3
        
        # Use consistent log file path
        if not hasattr(args, 'log_file') or not args.log_file:
            args.log_file = "temp/ffmpeg_output.log"
            
        # Set default output file
        if not hasattr(args, 'output_file') or not args.output_file:
            args.output_file = find_output_file()
            
        # Check if FFmpeg is running or log file exists
        if not os.path.exists(args.log_file) and not get_ffmpeg_processes():
            print("No active FFmpeg processes found and no log file exists.")
            print("Start an encoding process first or specify the correct log file path:")
            print("    python3 monitor_encoding.py --log-file <path_to_log>")
            return 1
            
        # Print startup message
        print("Starting SlideSonic Encoding Monitor...")
        print(f"Log file: {args.log_file}")
        print(f"Output file: {args.output_file}")
        
        # Run the simplified progress display
        return display_progress(args)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 