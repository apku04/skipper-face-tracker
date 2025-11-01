#!/usr/bin/env python3
"""
Setup script for Skipper Face Tracker

Install in development mode:
    pip3 install -e .

Install for production:
    pip3 install .
    
After installation, use CLI commands:
    skipper                    # Run main application
    skipper-enroll             # Enroll new face
    skipper-calibrate          # Calibrate motors
    skipper-sensors            # Monitor sensors
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    requirements = [
        line.strip() 
        for line in requirements_path.read_text().splitlines()
        if line.strip() and not line.startswith('#')
    ]
else:
    requirements = [
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "flask>=2.3.0",
        "pyyaml>=6.0",
        "smbus2>=0.4.0",
        "picamera2>=0.3.0",
        "pillow>=10.0.0",
    ]

setup(
    name="skipper",
    version="2.0.0",
    author="Skipper Team",
    description="AI-powered face tracking with Hailo-8L and Klipper motor control",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/apku04/skipper-face-tracker",
    
    packages=find_packages(exclude=["tests", "docs", "scripts"]),
    python_requires=">=3.9",
    install_requires=requirements,
    
    # Optional dependencies
    extras_require={
        'dev': [
            'pytest>=7.0',
            'pytest-cov>=4.0',
            'black>=23.0',
            'flake8>=6.0',
            'mypy>=1.0',
        ],
        'ai': [
            'openai>=1.0',
            'anthropic>=0.7',
            'chromadb>=0.4',
        ],
        'audio': [
            'sounddevice>=0.4',
            'soundfile>=0.12',
        ],
    },
    
    # CLI entry points
    entry_points={
        'console_scripts': [
            'skipper=main:main',
            'skipper-enroll=scripts.capture_enrollment_photos:main',
            'skipper-calibrate=motors.calibrate_motors:main',
            'skipper-sensors=sensors.read_multiplexed_sensors:main',
        ],
    },
    
    # Package data
    package_data={
        'config': ['*.yaml'],
        'models': ['**/*.hef', '**/*.pkl'],
    },
    include_package_data=True,
    
    # Metadata
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Hardware",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    keywords="face-tracking hailo klipper computer-vision ai raspberry-pi",
)
