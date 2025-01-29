#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting RapidEye setup...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit
fi

# Function to print progress
print_status() {
    echo -e "${YELLOW}>>> ${1}...${NC}"
}

# Update package lists
print_status "Updating package lists"
apt update

# Install system dependencies
print_status "Installing system dependencies"
apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    libpython3-dev \
    python3-opencv \
    portaudio19-dev \
    python3-pyqt5 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libqt5multimedia5-plugins \
    libasound2-dev \
    cmake

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment"
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment"
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip"
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies"
pip install \
    numpy \
    opencv-python \
    tensorflow \
    PyQt5 \
    joblib \
    mediapipe \
    scikit-learn

# Set environment variables
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Check if models directory exists
if [ ! -d "models" ]; then
    echo -e "${RED}Warning: 'models' directory not found. Please ensure model files are present.${NC}"
fi

# Check if resources directory exists
if [ ! -d "resources" ]; then
    echo -e "${RED}Warning: 'resources' directory not found. Please ensure resource files are present.${NC}"
fi

# Run the application
print_status "Starting RapidEye"
python3 src/main.py

# Deactivate virtual environment on exit
deactivate