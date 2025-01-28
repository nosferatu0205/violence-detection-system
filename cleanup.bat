@echo off

echo Cleaning up build artifacts...

REM Remove build directory
if exist "build" (
    rmdir /s /q build
    echo Removed build directory
)

REM Remove dist directory
if exist "dist" (
    rmdir /s /q dist
    echo Removed dist directory
)

REM Remove PyInstaller cache
if exist "__pycache__" (
    rmdir /s /q __pycache__
    echo Removed __pycache__ directory
)

REM Remove spec file
if exist "RapidEye.spec" (
    del /f /q RapidEye.spec
    echo Removed spec file
)

REM Remove any temporary PyInstaller files
del /f /q *.spec 2>nul
del /f /q *.pyo 2>nul
del /f /q *.pyc 2>nul

echo Cleanup complete!