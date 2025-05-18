#!/usr/bin/env python3
# SlideSonic (2025) - Setup Script
# https://github.com/chama-x/SlideSonic-2025

from setuptools import setup, find_packages
import os
import sys

# Add parent directory to path so we can read the README
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Read the README.md for the long description
with open(os.path.join(os.path.dirname(__file__), '..', "README.md"), "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Package metadata
setup(
    name="slidesonic",
    version="2.5.0",
    author="Chamath Thiwanka",
    author_email="chamath.x@example.com",
    description="An intelligent photo slideshow creator with AI features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chama-x/SlideSonic-2025",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video :: Conversion",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=[
        "psutil>=5.9.0",
        "pillow>=9.0.0",
        "imageio>=2.9.0",
        "imageio-ffmpeg>=0.4.2",
    ],
    entry_points={
        'console_scripts': [
            'slidesonic=src.advanced_app:main',
        ],
    },
    include_package_data=True,
    package_data={
        "": ["README.md", "LICENSE", "images/original/.gitkeep", "song/.gitkeep"],
    },
    project_urls={
        "Bug Tracker": "https://github.com/chama-x/SlideSonic-2025/issues",
        "Source Code": "https://github.com/chama-x/SlideSonic-2025",
    },
    keywords="slideshow, video, photo, image, ai, editor, creator, automatic, slideshow-maker",
) 