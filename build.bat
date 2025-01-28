@echo off

REM Clean up any existing build artifacts
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "__pycache__" rmdir /s /q __pycache__

REM Install required packages
pip install pyinstaller

REM Create build directories
mkdir dist
mkdir build

REM Build for Windows
echo Building for Windows...
pyinstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --onedir ^
    --name RapidEye ^
    --add-data "models;models" ^
    --add-data "resources;resources" ^
    --add-data "config.json;." ^
    --hidden-import cv2 ^
    --hidden-import tensorflow ^
    --hidden-import numpy ^
    --hidden-import PyQt5.QtMultimedia ^
    --hidden-import PyQt5.QtCore ^
    --hidden-import PyQt5.QtGui ^
    --hidden-import PyQt5.QtWidgets ^
    src/main.py

REM Create distribution package
cd dist
powershell Compress-Archive -Path "RapidEye" -DestinationPath "RapidEye-Windows.zip"
cd ..

echo Build complete! Distribution package created at dist\RapidEye-Windows.zip