#!/usr/bin/env python
import os
import sys
import argparse
import platform
import logging
import time
from videomaker.FastSlideshow import create_fast_slideshow
from videomaker.DirectFFmpeg import is_apple_silicon

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('fast_app')

def print_info():
    """Print system information"""
    print("\nEnvironment Check:")
    print(f"- CPU Cores: {os.cpu_count()}")
    print(f"- Operating System: {platform.system()}")
    print(f"- Machine Architecture: {platform.machine()}")
    
    # Check for Apple Silicon
    if is_apple_silicon():
        print("- Apple Silicon detected: Using optimized parameters")
    
    # Python version
    print(f"- Python Version: {platform.python_version()}")
    
    # Check FFmpeg version
    try:
        import subprocess
        result = subprocess.run(["ffmpeg", "-version"], 
                                capture_output=True, 
                                text=True, 
                                check=True)
        ffmpeg_version = result.stdout.split('\n')[0]
        print(f"- FFmpeg: {ffmpeg_version}")
    except Exception:
        print("- FFmpeg: Not found or error checking version")
    
    # Count images
    try:
        image_count = len([f for f in os.listdir('images/original') 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))])
        print(f"- Found {image_count} images in images/original/")
    except Exception:
        print("- No images found or error counting images")
    
    # Count audio files
    try:
        audio_count = len([f for f in os.listdir('song') 
                         if f.lower().endswith(('.mp3', '.wav', '.aac', '.ogg', '.m4a'))])
        print(f"- Found {audio_count} audio files in song/")
    except Exception:
        print("- No audio files found or error counting audio files")
    
    print("\n")

def parse_resolution(resolution_str):
    """Parse resolution string in format WIDTHxHEIGHT"""
    if 'x' not in resolution_str:
        raise ValueError("Resolution must be in format WIDTHxHEIGHT (e.g., 1920x1080)")
    
    width, height = resolution_str.lower().split('x')
    try:
        return int(width), int(height)
    except ValueError:
        raise ValueError("Width and height must be integers")

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(
        description="High-Performance Slideshow Video Maker (Apple Silicon Optimized)"
    )
    
    parser.add_argument('--title', type=str, default="Slideshow",
                      help="Title displayed at the beginning")
    
    parser.add_argument('--resolution', type=str, default="1920x1080",
                      help="Video resolution (e.g., 1920x1080)")
    
    parser.add_argument('--duration', type=float, default=None,
                      help="Duration in seconds (default: auto-detect from audio)")
    
    parser.add_argument('--output', type=str, default="video",
                      help="Output filename without extension")
    
    parser.add_argument('--codec', type=str, choices=['h264', 'hevc'], default='hevc',
                      help="Video codec to use (default: hevc)")
    
    parser.add_argument('--quality', type=int, default=50,
                      help="Video quality (0-100, higher is better)")
    
    parser.add_argument('--fps', type=int, default=30,
                      help="Frames per second")
    
    parser.add_argument('--debug', action='store_true',
                      help="Enable debug logging")
    
    parser.add_argument('--max-performance', action='store_true',
                      help="Use maximum performance settings")
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Print system information
    print_info()
    
    # Print title
    print("=== High-Performance Slideshow Video Maker (Apple Silicon Optimized) ===\n")
    
    # Interactive mode if no arguments provided
    if len(sys.argv) == 1:
        title = input("What title do you want to show at the beginning of your video? ")
        args.title = title if title else args.title
        
        resolution = input(f"What is the resolution of your video? (Default: {args.resolution}) ")
        args.resolution = resolution if resolution else args.resolution
        
        duration = input("What is the duration of your audio track in seconds? (Enter for auto-detect) ")
        if duration:
            try:
                args.duration = float(duration)
            except ValueError:
                print("Invalid duration, using auto-detect")
                
        output = input(f"Output filename (without extension, default \"{args.output}\"): ")
        args.output = output if output else args.output
        
        codec = input("Use HEVC codec for better quality/compression? (y/N): ")
        args.codec = 'hevc' if codec.lower() in ('y', 'yes') else 'h264'
        
        quality = input(f"Video quality (0-100, default {args.quality}): ")
        if quality:
            try:
                args.quality = int(quality)
            except ValueError:
                print(f"Invalid quality, using default: {args.quality}")
        
        fps = input(f"Frames per second (default {args.fps}): ")
        if fps:
            try:
                args.fps = int(fps)
            except ValueError:
                print(f"Invalid FPS, using default: {args.fps}")
    
    # Parse resolution
    width, height = parse_resolution(args.resolution)
    
    # Handle max performance flag
    if args.max_performance:
        logger.info("Using maximum performance settings")
        args.quality = 40  # Lower quality for max speed
        args.fps = 24      # Fewer frames to process
    
    # Print summary
    print("\nStarting video creation with:")
    print(f"- Title: {args.title}")
    print(f"- Resolution: {width}x{height}")
    print(f"- Duration: {'Auto-detect' if args.duration is None else f'{args.duration} seconds'}")
    print(f"- Output: {args.output}.mp4")
    print(f"- Codec: {'HEVC (h265)' if args.codec == 'hevc' else 'H.264'}")
    print(f"- FPS: {args.fps}")
    print(f"- Quality: {args.quality}\n")
    
    # Create the slideshow
    start_time = time.time()
    success = create_fast_slideshow(
        title=args.title,
        image_dir="images/original",
        audio_dir="song",
        output_path=args.output + ".mp4",
        width=width,
        height=height,
        duration=args.duration,
        fps=args.fps,
        use_hevc=(args.codec == 'hevc'),
        quality=args.quality
    )
    
    total_time = time.time() - start_time
    
    if success:
        print(f"\nSlideshow video created successfully in {total_time:.2f} seconds!")
        print(f"You can find the output video at: {os.path.abspath(args.output)}.mp4")
    else:
        print("\nAn error occurred while creating the slideshow video.")
        print("Check the above messages for details.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 