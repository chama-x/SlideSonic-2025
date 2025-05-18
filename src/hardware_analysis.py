#!/usr/bin/env python3
# SlideSonic (2025) - Hardware Analysis Tool
# https://github.com/chama-x/SlideSonic-2025

import os
import sys
import platform
import subprocess
import shutil
import json
import re
import argparse
import tempfile
from datetime import datetime
import time

try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    HAVE_PSUTIL = False

try:
    import cpuinfo
    HAVE_CPUINFO = True
except ImportError:
    HAVE_CPUINFO = False

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False

try:
    from PIL import Image, ImageDraw, ImageFont
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

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

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description=f"{PROGRAM_NAME} Hardware Analysis Tool")
    parser.add_argument('--no-colors', action='store_true', help='Disable colors')
    parser.add_argument('--no-unicode', action='store_true', help='Disable Unicode characters')
    parser.add_argument('--no-animations', action='store_true', help='Disable animations')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--save', action='store_true', help='Save results to a file')
    parser.add_argument('--version', action='store_true', help='Show version information')
    return parser.parse_args()

def check_ffmpeg():
    """Check for FFmpeg installation and capabilities"""
    result = {
        'installed': False,
        'version': None,
        'encoders': {
            'h264': False,
            'hevc': False,
            'av1': False,
            'vvc': False
        },
        'hwaccel': {
            'vaapi': False,
            'nvenc': False,
            'qsv': False,
            'videotoolbox': False,
            'amf': False
        }
    }
    
    # Check if FFmpeg is installed
    ffmpeg_path = shutil.which('ffmpeg')
    if not ffmpeg_path:
        return result
    
    result['installed'] = True
    
    # Get FFmpeg version
    try:
        process = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=True)
        version_match = re.search(r'ffmpeg version (\S+)', process.stdout)
        if version_match:
            result['version'] = version_match.group(1)
    except subprocess.SubprocessError:
        pass
    
    # Check encoders
    try:
        process = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True, check=True)
        encoders_output = process.stdout
        
        # H.264 (AVC)
        result['encoders']['h264'] = 'libx264' in encoders_output
        
        # H.265 (HEVC)
        result['encoders']['hevc'] = 'libx265' in encoders_output
        
        # AV1
        result['encoders']['av1'] = any(encoder in encoders_output for encoder in 
                                       ['libaom-av1', 'libsvtav1', 'librav1e'])
        
        # VVC (Versatile Video Coding, H.266)
        result['encoders']['vvc'] = any(encoder in encoders_output for encoder in
                                       ['libvvenc', 'vvc'])
    except subprocess.SubprocessError:
        pass
    
    # Check hardware acceleration
    try:
        process = subprocess.run(['ffmpeg', '-hwaccels'], capture_output=True, text=True, check=True)
        hwaccels_output = process.stdout
        
        # Intel Quick Sync Video
        result['hwaccel']['qsv'] = 'qsv' in hwaccels_output
        
        # NVIDIA NVENC
        result['hwaccel']['nvenc'] = 'cuda' in hwaccels_output or 'nvenc' in hwaccels_output
        
        # AMD AMF
        result['hwaccel']['amf'] = 'amf' in hwaccels_output
        
        # Intel/AMD VAAPI
        result['hwaccel']['vaapi'] = 'vaapi' in hwaccels_output
        
        # Apple VideoToolbox
        result['hwaccel']['videotoolbox'] = 'videotoolbox' in hwaccels_output
    except subprocess.SubprocessError:
        pass
    
    return result

def get_system_info():
    """Get general system information"""
    result = {
        'os': {
            'name': platform.system(),
            'version': platform.version(),
            'release': platform.release(),
            'platform': platform.platform()
        },
        'python': {
            'version': platform.python_version(),
            'implementation': platform.python_implementation(),
            'compiler': platform.python_compiler(),
            'path': sys.executable
        },
        'arch': platform.machine()
    }
    
    # Check for macOS and Apple Silicon
    if platform.system() == 'Darwin':
        result['macos'] = True
        
        # Check for Apple Silicon
        if platform.machine() == 'arm64':
            result['apple_silicon'] = True
        else:
            result['apple_silicon'] = False
    else:
        result['macos'] = False
        result['apple_silicon'] = False
    
    return result

def get_cpu_info():
    """Get detailed CPU information"""
    result = {
        'arch': platform.machine(),
        'bits': platform.architecture()[0],
        'count_logical': os.cpu_count(),
        'count_physical': None,
        'brand': None,
        'features': [],
        'frequency': None,
        'cache': {},
    }
    
    # Get more detailed CPU info if psutil is available
    if HAVE_PSUTIL:
        try:
            result['count_physical'] = psutil.cpu_count(logical=False)
            
            frequencies = psutil.cpu_freq()
            if frequencies:
                result['frequency'] = {
                    'current': frequencies.current,
                    'min': frequencies.min,
                    'max': frequencies.max
                }
        except Exception:
            pass
    
    # Get even more CPU details if cpuinfo is available
    if HAVE_CPUINFO:
        try:
            info = cpuinfo.get_cpu_info()
            result['brand'] = info.get('brand_raw')
            result['features'] = info.get('flags', [])
            result['cache'] = {
                'l1_data': info.get('l1_data_cache_size'),
                'l1_instruction': info.get('l1_instruction_cache_size'),
                'l2': info.get('l2_cache_size'),
                'l3': info.get('l3_cache_size')
            }
        except Exception:
            pass
    
    return result

def get_memory_info():
    """Get system memory information"""
    result = {
        'total': None,
        'available': None,
        'used': None,
        'percent_used': None
    }
    
    if HAVE_PSUTIL:
        try:
            mem = psutil.virtual_memory()
            result['total'] = mem.total
            result['available'] = mem.available
            result['used'] = mem.used
            result['percent_used'] = mem.percent
        except Exception:
            pass
    
    return result

def get_gpu_info():
    """Get GPU information using various methods"""
    result = {
        'detected': False,
        'vendor': None,
        'model': None,
        'driver': None,
        'vram': None
    }
    
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        try:
            process = subprocess.run(['system_profiler', 'SPDisplaysDataType', '-json'], 
                                    capture_output=True, text=True, check=True)
            data = json.loads(process.stdout)
            
            if data and 'SPDisplaysDataType' in data:
                for gpu in data['SPDisplaysDataType']:
                    if 'spdisplays_vendor' in gpu:
                        result['detected'] = True
                        result['vendor'] = gpu.get('spdisplays_vendor')
                        result['model'] = gpu.get('spdisplays_device-name')
                        result['vram'] = gpu.get('spdisplays_vram')
                        break
        except (subprocess.SubprocessError, json.JSONDecodeError):
            pass
    
    elif system == 'Linux':  # Linux
        # Try lspci for NVIDIA/AMD/Intel GPU detection
        try:
            process = subprocess.run(['lspci', '-vnn'], capture_output=True, text=True, check=True)
            output = process.stdout
            
            # Look for GPU information
            vga_match = re.search(r'VGA.*?:\s*(.*?)\[(.*?)\]', output)
            if vga_match:
                result['detected'] = True
                model = vga_match.group(1).strip()
                result['model'] = model
                
                if 'NVIDIA' in model:
                    result['vendor'] = 'NVIDIA'
                elif 'AMD' in model or 'ATI' in model:
                    result['vendor'] = 'AMD'
                elif 'Intel' in model:
                    result['vendor'] = 'Intel'
        except subprocess.SubprocessError:
            pass
        
        # Try nvidia-smi for NVIDIA GPUs
        if not result['detected'] or result['vendor'] == 'NVIDIA':
            try:
                process = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version,memory.total', 
                                         '--format=csv,noheader'], capture_output=True, text=True, check=True)
                output = process.stdout.strip()
                
                if output:
                    parts = output.split(',')
                    result['detected'] = True
                    result['vendor'] = 'NVIDIA'
                    result['model'] = parts[0].strip()
                    result['driver'] = parts[1].strip()
                    result['vram'] = parts[2].strip()
            except subprocess.SubprocessError:
                pass
    
    elif system == 'Windows':  # Windows
        # Try wmic for GPU detection
        try:
            process = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 
                                     'Name,AdapterRAM,DriverVersion', '/format:csv'], 
                                    capture_output=True, text=True, check=True)
            output = process.stdout
            
            if output and ',' in output:
                lines = output.strip().split('\n')
                if len(lines) > 1:  # Skip header line
                    parts = lines[1].split(',')
                    if len(parts) >= 4:
                        result['detected'] = True
                        result['model'] = parts[2].strip()
                        result['driver'] = parts[3].strip()
                        
                        # Try to determine vendor from model name
                        if 'NVIDIA' in result['model']:
                            result['vendor'] = 'NVIDIA'
                        elif 'AMD' in result['model'] or 'Radeon' in result['model']:
                            result['vendor'] = 'AMD'
                        elif 'Intel' in result['model']:
                            result['vendor'] = 'Intel'
                        
                        # Convert adapter RAM from bytes to MB
                        try:
                            vram_bytes = int(parts[1])
                            result['vram'] = f"{vram_bytes / (1024 * 1024):.0f} MB"
                        except (ValueError, IndexError):
                            pass
        except subprocess.SubprocessError:
            pass
    
    return result

def benchmark_disk_speed():
    """Benchmark disk write and read speeds"""
    result = {
        'write_speed': None,
        'read_speed': None,
        'unit': 'MB/s'
    }
    
    test_size = 100 * 1024 * 1024  # 100 MB
    test_file = os.path.join(tempfile.gettempdir(), 'slidesonic_disk_test')
    
    try:
        # Write test
        data = b'0' * 1024  # 1KB chunk
        start_time = time.time()
        with open(test_file, 'wb') as f:
            for _ in range(test_size // 1024):
                f.write(data)
        
        write_time = time.time() - start_time
        write_speed = test_size / write_time / (1024 * 1024)
        result['write_speed'] = round(write_speed, 2)
        
        # Read test
        start_time = time.time()
        with open(test_file, 'rb') as f:
            while f.read(1024 * 1024):
                pass
        
        read_time = time.time() - start_time
        read_speed = test_size / read_time / (1024 * 1024)
        result['read_speed'] = round(read_speed, 2)
        
        # Clean up
        os.remove(test_file)
    
    except Exception as e:
        print(f"Error during disk benchmark: {e}")
    
    return result

def benchmark_image_processing():
    """Benchmark image processing capabilities using PIL"""
    result = {
        'resize_time': None,
        'filter_time': None,
        'composite_time': None,
        'unit': 'seconds'
    }
    
    if not HAVE_PIL or not HAVE_NUMPY:
        return result
    
    try:
        # Create a test image
        width, height = 1920, 1080
        image = Image.new('RGB', (width, height), color=(73, 109, 137))
        
        # Generate some test content
        draw = ImageDraw.Draw(image)
        for i in range(100):
            x1 = np.random.randint(0, width)
            y1 = np.random.randint(0, height)
            x2 = np.random.randint(0, width)
            y2 = np.random.randint(0, height)
            color = (np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255))
            draw.line((x1, y1, x2, y2), fill=color, width=5)
        
        # Resize benchmark
        start_time = time.time()
        for _ in range(10):
            image.resize((1280, 720))
        resize_time = (time.time() - start_time) / 10
        result['resize_time'] = round(resize_time, 4)
        
        # Filter benchmark
        start_time = time.time()
        for _ in range(5):
            image.filter(getattr(Image, 'BLUR'))
        filter_time = (time.time() - start_time) / 5
        result['filter_time'] = round(filter_time, 4)
        
        # Composite benchmark
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for i in range(50):
            x = np.random.randint(0, width)
            y = np.random.randint(0, height)
            radius = np.random.randint(20, 100)
            color = (np.random.randint(0, 255), np.random.randint(0, 255), 
                     np.random.randint(0, 255), np.random.randint(100, 200))
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
        
        start_time = time.time()
        for _ in range(5):
            Image.alpha_composite(image.convert('RGBA'), overlay)
        composite_time = (time.time() - start_time) / 5
        result['composite_time'] = round(composite_time, 4)
    
    except Exception as e:
        print(f"Error during image processing benchmark: {e}")
    
    return result

def analyze_hardware():
    """Perform comprehensive hardware analysis"""
    print_styled(BOLD, "Starting hardware analysis...")
    
    # Show animation if enabled
    if USE_ANIMATIONS:
        spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'] if USE_UNICODE else ['-', '\\', '|', '/']
        for i in range(20):
            char = spinner[i % len(spinner)]
            print_styled(GRAY, f"\r{char} Analyzing system hardware... {i*5}%"), 
            sys.stdout.flush()
            time.sleep(0.1)
        print("\r" + " " * 50 + "\r", end="")
    
    # Collect all hardware information
    results = {
        'timestamp': datetime.now().isoformat(),
        'version': VERSION,
        'system': get_system_info(),
        'cpu': get_cpu_info(),
        'memory': get_memory_info(),
        'gpu': get_gpu_info(),
        'ffmpeg': check_ffmpeg(),
        'benchmarks': {
            'disk': benchmark_disk_speed(),
            'image_processing': benchmark_image_processing()
        }
    }
    
    return results

def format_bytes(bytes_value):
    """Format bytes to human-readable format"""
    if bytes_value is None:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024 or unit == 'TB':
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024

def display_results(results):
    """Display hardware analysis results in a user-friendly format"""
    system_info = results['system']
    cpu_info = results['cpu']
    memory_info = results['memory']
    gpu_info = results['gpu']
    ffmpeg_info = results['ffmpeg']
    benchmarks = results['benchmarks']
    
    # Clear the screen and show header
    os.system('cls' if os.name == 'nt' else 'clear')
    center_text(f"{PROGRAM_NAME} - Hardware Analysis")
    print_styled(GRAY, f"Version {VERSION} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    draw_divider()
    print()
    
    # System Information
    print_styled(BOLD + BLUE, "System Information:")
    print_styled(CYAN, f"• OS:           {system_info['os']['name']} {system_info['os']['version']}")
    print_styled(CYAN, f"• Architecture: {system_info['arch']} ({platform.architecture()[0]})")
    print_styled(CYAN, f"• Python:       {system_info['python']['version']} ({system_info['python']['implementation']})")
    
    # Special flags for macOS and Apple Silicon
    if system_info.get('macos'):
        print_styled(CYAN, f"• macOS:        Yes")
        if system_info.get('apple_silicon'):
            print_styled(GREEN, f"• Apple Silicon: Yes (M-series chip)")
        else:
            print_styled(CYAN, f"• Apple Silicon: No (Intel processor)")
    print()
    
    # CPU Information
    print_styled(BOLD + BLUE, "CPU Information:")
    print_styled(CYAN, f"• Processor:    {cpu_info.get('brand') or 'Unknown'}")
    print_styled(CYAN, f"• Cores:        {cpu_info.get('count_physical') or 'Unknown'} physical, {cpu_info.get('count_logical') or 'Unknown'} logical")
    
    # CPU Frequency
    if cpu_info.get('frequency') and cpu_info['frequency'].get('max'):
        print_styled(CYAN, f"• Frequency:    {cpu_info['frequency']['max']/1000:.2f} GHz (max)")
    elif cpu_info.get('frequency') and cpu_info['frequency'].get('current'):
        print_styled(CYAN, f"• Frequency:    {cpu_info['frequency']['current']/1000:.2f} GHz (current)")
    
    # Advanced CPU features relevant for encoding
    if cpu_info.get('features'):
        advanced_features = []
        
        # Check for SIMD instruction sets
        simd_features = []
        if 'avx512' in ' '.join(cpu_info['features']).lower():
            simd_features.append("AVX-512")
        elif 'avx2' in cpu_info['features']:
            simd_features.append("AVX2")
        elif 'avx' in cpu_info['features']:
            simd_features.append("AVX")
        
        if 'sse4_2' in cpu_info['features']:
            simd_features.append("SSE4.2")
        
        if simd_features:
            advanced_features.append(f"SIMD: {', '.join(simd_features)}")
        
        # Check for hardware AES
        if 'aes' in cpu_info['features']:
            advanced_features.append("AES Acceleration")
        
        # Report advanced features
        if advanced_features:
            print_styled(GREEN, f"• Advanced:     {', '.join(advanced_features)}")
    
    print()
    
    # Memory Information
    print_styled(BOLD + BLUE, "Memory Information:")
    if memory_info.get('total'):
        print_styled(CYAN, f"• Total:        {format_bytes(memory_info['total'])}")
        print_styled(CYAN, f"• Available:    {format_bytes(memory_info['available'])}")
        print_styled(CYAN, f"• Used:         {format_bytes(memory_info['used'])} ({memory_info['percent_used']}%)")
    else:
        print_styled(YELLOW, "• Memory information not available")
    print()
    
    # GPU Information
    print_styled(BOLD + BLUE, "GPU Information:")
    if gpu_info.get('detected'):
        print_styled(GREEN, f"• Detected:     Yes")
        print_styled(CYAN, f"• Vendor:       {gpu_info.get('vendor') or 'Unknown'}")
        print_styled(CYAN, f"• Model:        {gpu_info.get('model') or 'Unknown'}")
        
        if gpu_info.get('vram'):
            print_styled(CYAN, f"• VRAM:         {gpu_info.get('vram')}")
        
        if gpu_info.get('driver'):
            print_styled(CYAN, f"• Driver:       {gpu_info.get('driver')}")
    else:
        print_styled(YELLOW, "• No GPU detected or information not available")
    print()
    
    # FFmpeg Information
    print_styled(BOLD + BLUE, "FFmpeg Information:")
    if ffmpeg_info.get('installed'):
        print_styled(GREEN, f"• Installed:    Yes (version {ffmpeg_info.get('version') or 'unknown'})")
        
        # Available encoders
        encoders = []
        if ffmpeg_info['encoders'].get('h264'):
            encoders.append("H.264")
        if ffmpeg_info['encoders'].get('hevc'):
            encoders.append("HEVC/H.265")
        if ffmpeg_info['encoders'].get('av1'):
            encoders.append("AV1")
        if ffmpeg_info['encoders'].get('vvc'):
            encoders.append("VVC/H.266")
        
        if encoders:
            print_styled(CYAN, f"• Encoders:     {', '.join(encoders)}")
        else:
            print_styled(YELLOW, "• Encoders:     None detected")
        
        # Hardware acceleration
        hwaccel = []
        for name, available in ffmpeg_info['hwaccel'].items():
            if available:
                if name == 'nvenc':
                    hwaccel.append("NVIDIA NVENC")
                elif name == 'qsv':
                    hwaccel.append("Intel QuickSync")
                elif name == 'videotoolbox':
                    hwaccel.append("Apple VideoToolbox")
                elif name == 'vaapi':
                    hwaccel.append("VA-API")
                elif name == 'amf':
                    hwaccel.append("AMD AMF")
        
        if hwaccel:
            print_styled(GREEN, f"• Hardware Accel: {', '.join(hwaccel)}")
        else:
            print_styled(YELLOW, "• Hardware Accel: None detected")
    else:
        print_styled(RED, "• Installed:    No (FFmpeg not found)")
        print_styled(GRAY, "  FFmpeg is required for video encoding. Please install it.")
        print_styled(GRAY, "  Visit: https://ffmpeg.org/download.html")
    print()
    
    # Benchmark Results
    print_styled(BOLD + BLUE, "Benchmark Results:")
    
    # Disk benchmark
    disk_bench = benchmarks.get('disk', {})
    if disk_bench.get('write_speed') and disk_bench.get('read_speed'):
        print_styled(CYAN, f"• Disk Write:   {disk_bench.get('write_speed')} MB/s")
        print_styled(CYAN, f"• Disk Read:    {disk_bench.get('read_speed')} MB/s")
    else:
        print_styled(YELLOW, "• Disk:         Benchmark not available")
    
    # Image processing benchmark
    img_bench = benchmarks.get('image_processing', {})
    if img_bench.get('resize_time') is not None:
        print_styled(CYAN, f"• Image Resize: {img_bench.get('resize_time')} seconds")
        print_styled(CYAN, f"• Image Filter: {img_bench.get('filter_time')} seconds")
        print_styled(CYAN, f"• Compositing:  {img_bench.get('composite_time')} seconds")
    else:
        print_styled(YELLOW, "• Image:        Benchmark not available")
    print()
    
    # Performance Analysis
    print_styled(BOLD + BLUE, "Performance Analysis:")
    
    # CPU performance rating
    cpu_score = 0
    if cpu_info.get('count_logical', 0) >= 8:
        cpu_score += 2
    elif cpu_info.get('count_logical', 0) >= 4:
        cpu_score += 1
    
    # Check for SIMD instructions
    if cpu_info.get('features'):
        features_str = ' '.join(cpu_info['features']).lower()
        if 'avx512' in features_str:
            cpu_score += 3
        elif 'avx2' in features_str:
            cpu_score += 2
        elif 'avx' in features_str:
            cpu_score += 1
    
    # Memory performance rating
    memory_score = 0
    if memory_info.get('total'):
        if memory_info['total'] >= 16 * 1024 * 1024 * 1024:  # 16 GB
            memory_score += 2
        elif memory_info['total'] >= 8 * 1024 * 1024 * 1024:  # 8 GB
            memory_score += 1
    
    # GPU performance rating
    gpu_score = 0
    if gpu_info.get('detected'):
        gpu_score += 1
        
        # Check for hardware encoding support
        if ffmpeg_info.get('installed'):
            if any(ffmpeg_info['hwaccel'].values()):
                gpu_score += 2
    
    # Calculate overall performance score
    overall_score = cpu_score + memory_score + gpu_score
    
    # Output performance ratings
    if overall_score >= 6:
        performance_rating = "Excellent"
        color = GREEN
    elif overall_score >= 4:
        performance_rating = "Good"
        color = CYAN
    elif overall_score >= 2:
        performance_rating = "Average"
        color = YELLOW
    else:
        performance_rating = "Basic"
        color = RED
    
    print_styled(color, f"• Overall:      {performance_rating} (Score: {overall_score}/9)")
    
    # Recommendations
    print()
    print_styled(BOLD + BLUE, "Encoding Recommendations:")
    
    if overall_score >= 6:
        print_styled(GREEN, "• Ultra High Quality Mode:")
        print_styled(GRAY, "  - Your system has excellent performance capabilities")
        print_styled(GRAY, "  - Can handle 4K resolution with high-quality encoding")
        print_styled(GRAY, "  - Recommended for professional/archival use")
    elif overall_score >= 4:
        print_styled(CYAN, "• Standard Quality Mode:")
        print_styled(GRAY, "  - Your system has good performance capabilities")
        print_styled(GRAY, "  - 1080p resolution recommended for best balance")
        print_styled(GRAY, "  - Good choice for general-purpose videos")
    else:
        print_styled(YELLOW, "• Maximum Performance Mode:")
        print_styled(GRAY, "  - Your system has basic performance capabilities")
        print_styled(GRAY, "  - 720p resolution recommended for smooth operation")
        print_styled(GRAY, "  - Use faster encoding presets for better experience")
    
    # Hardware upgrade suggestions
    if cpu_score < 2:
        print_styled(YELLOW, "• CPU Upgrade:")
        print_styled(GRAY, "  - Consider a CPU with more cores for better encoding performance")
    
    if memory_score < 1:
        print_styled(YELLOW, "• Memory Upgrade:")
        print_styled(GRAY, "  - Adding more RAM would improve performance for high-resolution videos")
    
    if gpu_score < 1:
        print_styled(YELLOW, "• GPU Acceleration:")
        print_styled(GRAY, "  - Consider adding a GPU with hardware encoding support")
    
    if not ffmpeg_info.get('installed'):
        print_styled(RED, "• Missing FFmpeg:")
        print_styled(GRAY, "  - Install FFmpeg to enable video encoding functions")
    
    # Finish with a divider
    print()
    draw_divider()

def save_results(results, json_format=False):
    """Save analysis results to a file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"slidesonic_hardware_analysis_{timestamp}.{'json' if json_format else 'txt'}"
    
    try:
        if json_format:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        else:
            # Redirect stdout to file temporarily
            original_stdout = sys.stdout
            with open(filename, 'w') as f:
                sys.stdout = f
                display_results(results)
                sys.stdout = original_stdout
        
        print_styled(GREEN, f"Analysis results saved to {filename}")
        return True
    except Exception as e:
        print_styled(RED, f"Error saving results: {e}")
        return False

def main():
    """Main function"""
    global USE_COLORS, USE_UNICODE, USE_ANIMATIONS
    
    # Parse command line arguments
    args = parse_args()
    
    # Check version flag
    if args.version:
        print(f"{PROGRAM_NAME} v{VERSION}")
        return 0
    
    # Set accessibility options
    USE_COLORS = not args.no_colors
    USE_UNICODE = not args.no_unicode
    USE_ANIMATIONS = not args.no_animations
    
    # Show banner
    if not args.json:
        center_text(f"{PROGRAM_NAME} - Hardware Analysis")
        print_styled(GRAY, f"Version {VERSION}")
        draw_divider()
        print()
    
    # Run hardware analysis
    results = analyze_hardware()
    
    # Output results
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        display_results(results)
    
    # Save results if requested
    if args.save:
        save_results(results, args.json)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1) 