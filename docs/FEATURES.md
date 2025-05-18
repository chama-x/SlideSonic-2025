# SlideSonic Features

SlideSonic offers a wide range of features to create stunning slideshows with minimal effort.

## Smart Media Analysis

- **Intelligent Image Grouping**: Automatically detects patterns in your image collection
  - Sequential patterns (img001.jpg, img002.jpg)
  - Date-based groups (photos taken on the same day)
  - Common prefix grouping
  - Natural sort ordering (img2.jpg comes before img10.jpg)

- **Audio Matching**: Finds the best audio track for your slideshow
  - Analyzes filename patterns to match image sets with appropriate audio
  - Supports multiple audio formats (MP3, WAV, M4A, AAC, FLAC, OGG)

## Slideshow Optimization

- **Auto-optimized Slide Duration**: Perfectly times slides to match your music
  - Calculates optimal display time based on audio length
  - Ensures all images are shown during the audio duration
  - Provides smooth transitions between images

- **Quality Settings**: Multiple presets from quick previews to ultra-high quality
  - Maximum Performance: Fastest encoding for previews
  - Standard Quality: Balanced quality/speed for most purposes
  - Ultra High Quality: Best image quality for final outputs

## Hardware Acceleration

- **Hardware Detection**: Automatically detects and utilizes your system capabilities
  - Apple Silicon (VideoToolbox)
  - NVIDIA GPUs (NVENC)
  - Intel QuickSync
  - AMD GPUs (VA-API)

- **Adaptive Settings**: Optimizes encoding parameters based on available hardware
  - CPU core utilization optimization
  - Memory usage optimization
  - GPU capabilities detection

## Batch Processing

- **Multi-Slideshow Creation**: Process multiple slideshows in one go
  - Automatically organize images into logical groups
  - Apply common settings across projects
  - Process subdirectories as separate slideshows

- **Common Audio Options**: Apply audio settings across multiple slideshows
  - Use one audio track for all slideshows
  - Select appropriate audio for each slideshow automatically

## User Interface

- **Intuitive CLI**: Simple, color-coded interface with visual feedback
  - Progress indicators
  - Color-coded status messages
  - Clear error reporting

- **Accessibility Support**: Designed for all users
  - Color-blind friendly mode
  - ASCII-only mode for limited terminals
  - Screen reader optimized output

## Additional Features

- **Drag and Drop Support**: Simply drag files onto the application
- **Command-line Options**: Automate slideshow creation with command-line parameters
- **Hardware Analysis**: Detailed reports on system capabilities
- **Error Recovery**: Graceful handling of errors during processing 