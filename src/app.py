from videomaker import create_video, write_video
import argparse
import sys
import os
import multiprocessing as mp
import platform
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('slideshow-maker')

def parse_arguments():
    """Parse command line arguments or prompt for them interactively"""
    # Check if arguments were provided via command line
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description='Create slideshow videos with M1 optimization')
        parser.add_argument('--title', type=str, required=True, help='Title displayed at the beginning')
        parser.add_argument('--resolution', type=str, default='1920x1080', help='Video resolution (e.g., 1920x1080)')
        parser.add_argument('--duration', type=float, required=True, help='Duration of audio track in seconds')
        parser.add_argument('--output', type=str, default='video', help='Output filename (without extension)')
        parser.add_argument('--use-hevc', action='store_true', help='Use HEVC codec for better quality/compression')
        parser.add_argument('--bitrate', type=str, default='20000k', help='Video bitrate')
        parser.add_argument('--fps', type=int, default=30, help='Frames per second')
        parser.add_argument('--debug', action='store_true', help='Enable debug logging')
        
        args = parser.parse_args()
        
        # Set debug logging if requested
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.getLogger('videomaker').setLevel(logging.DEBUG)
        
        try:
            width, height = map(int, args.resolution.split('x'))
        except (ValueError, TypeError):
            parser.error(f"Invalid resolution format: {args.resolution}. Expected format: WIDTHxHEIGHT (e.g. 1920x1080)")
        
        return {
            'title': args.title,
            'width': width,
            'height': height, 
            'duration': args.duration,
            'filename': args.output,
            'use_hevc': args.use_hevc,
            'bitrate': args.bitrate,
            'fps': args.fps
        }
    
    # Interactive mode
    print("\n=== Slideshow Video Maker (M1 Optimized) ===\n")
    
    title = input('What title do you want to show at the beginning of your video? ')
    
    # Get resolution with validation
    resolution_input = input('What is the resolution of your video? (Default: 1920x1080) ') or '1920x1080'
    try:
        width, height = map(int, resolution_input.split('x'))
    except ValueError:
        print("Invalid resolution format. Using default 1920x1080.")
        width, height = 1920, 1080
    
    # Get duration with validation
    duration_input = input('What is the duration of your audio track in seconds? ')
    try:
        duration = float(duration_input)
        if duration <= 0:
            print("Duration must be positive. Using audio file duration if available.")
            duration = None
    except ValueError:
        print("Invalid duration format. Will try to determine from audio file.")
        duration = None
    
    # Get optional parameters
    filename = input('Output filename (without extension, default "video"): ') or 'video'
    
    use_hevc = input('Use HEVC codec for better quality/compression? (y/N): ').lower() == 'y'
    
    bitrate_input = input('Video bitrate (default "20000k"): ')
    if bitrate_input:
        if not (bitrate_input.endswith('k') or bitrate_input.endswith('M')):
            print("Bitrate should end with 'k' or 'M'. Using default 20000k.")
            bitrate = '20000k'
        else:
            bitrate = bitrate_input
    else:
        bitrate = '20000k'
    
    fps_input = input('Frames per second (default 30): ') or '30'
    try:
        fps = int(fps_input)
        if fps <= 0 or fps > 120:
            print("FPS should be between 1 and 120. Using default 30.")
            fps = 30
    except ValueError:
        print("Invalid FPS. Using default 30.")
        fps = 30
    
    return {
        'title': title,
        'width': width,
        'height': height,
        'duration': duration,
        'filename': filename,
        'use_hevc': use_hevc,
        'bitrate': bitrate,
        'fps': fps
    }


def check_environment():
    """Check and report on the environment capabilities"""
    print("\nEnvironment Check:")
    
    # Check CPU cores
    cpu_count = mp.cpu_count()
    print(f"- CPU Cores: {cpu_count}")
    
    # Check OS and architecture
    system = platform.system()
    machine = platform.machine()
    print(f"- Operating System: {system}")
    print(f"- Machine Architecture: {machine}")
    
    # Check for Apple Silicon
    is_apple_silicon = system == 'Darwin' and machine == 'arm64'
    if is_apple_silicon:
        print("- Apple Silicon detected: Using optimized parameters")
    else:
        print("- Apple Silicon not detected: Using standard parameters")
    
    # Check Python version
    py_version = platform.python_version()
    print(f"- Python Version: {py_version}")
    
    # Check for FFmpeg
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, 
                                text=True, 
                                check=False)
        if result.returncode == 0:
            first_line = result.stdout.split('\n')[0]
            print(f"- FFmpeg: {first_line}")
        else:
            print("- FFmpeg: Not found or error running")
    except (FileNotFoundError, subprocess.SubprocessError):
        print("- FFmpeg: Not found in PATH")
    
    # Check directories and files
    check_directories()
    
    print("")


def check_directories():
    """Check directories and their contents"""
    # Check required directories
    required_dirs = ['images/original', 'images/resized', 'song']
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"- WARNING: {directory} directory not found. Creating it.")
            os.makedirs(directory, exist_ok=True)
    
    # Check for images and audio
    image_count = len([f for f in os.listdir('images/original') 
                       if f != '.gitkeep' and f.lower().endswith(
                           ('.jpg', '.jpeg', '.png', '.bmp', '.gif'))])
    
    audio_count = len([f for f in os.listdir('song') 
                       if f != '.gitkeep' and f.lower().endswith(
                           ('.mp3', '.wav', '.aac', '.ogg', '.m4a'))])
    
    print(f"- Found {image_count} images in images/original/")
    print(f"- Found {audio_count} audio files in song/")
    
    if image_count == 0:
        print("  WARNING: No images found. Please add images to images/original/")
    
    if audio_count == 0:
        print("  WARNING: No audio files found. Please add an audio file to song/")


def main():
    """Main function to run the slideshow maker"""
    # Set up timing for performance metrics
    start_time = time.time()
    
    # Check environment
    check_environment()
    
    # Get parameters
    params = parse_arguments()
    
    if params is None:
        logger.error("Error in parameters. Exiting.")
        sys.exit(1)
    
    print("\nStarting video creation with:")
    print(f"- Title: {params['title']}")
    print(f"- Resolution: {params['width']}x{params['height']}")
    
    # Handle duration - might be None if auto-detecting from audio
    if params['duration'] is None:
        print(f"- Duration: Auto-detect from audio")
    else:
        print(f"- Duration: {params['duration']} seconds")
        
    print(f"- Output: {params['filename']}.mp4")
    print(f"- Codec: {'HEVC (h265)' if params['use_hevc'] else 'H.264'}")
    print(f"- FPS: {params['fps']}")
    print(f"- Bitrate: {params['bitrate']}")
    print("")
    
    # Create and write video
    try:
        # Create video
        video_start = time.time()
        video = create_video(params['title'], [params['width'], params['height']], params['duration'])
        video_time = time.time() - video_start
        
        if video:
            # Write video to file
            write_start = time.time()
            success = write_video(
                video, 
                bitrate=params['bitrate'], 
                filename=params['filename'], 
                use_hevc=params['use_hevc'],
                fps=params['fps']
            )
            write_time = time.time() - write_start
            
            if success:
                total_time = time.time() - start_time
                print("\nVideo creation complete!")
                print(f"- Video creation took: {video_time:.2f} seconds")
                print(f"- Video encoding took: {write_time:.2f} seconds")
                print(f"- Total time: {total_time:.2f} seconds")
                print(f"- Output file: {params['filename']}.mp4")
            else:
                print("\nFailed to write the video file. Check error messages above.")
        else:
            print("\nFailed to create video. Check error messages above.")
    
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError creating video: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()