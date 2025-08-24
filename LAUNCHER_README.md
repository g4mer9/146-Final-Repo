# Game Launcher Instructions

This folder contains two launcher files that you can double-click to play the game:

## Option 1: Python Launcher (Recommended)
**File:** `play_game.py`
- Double-click this file to start the game
- Works on Windows, Mac, and Linux
- Automatically detects and uses the virtual environment if available
- Provides detailed error messages if something goes wrong

## Option 2: Windows Batch Launcher
**File:** `play_game.bat` 
- Double-click this file to start the game (Windows only)
- Simple batch script alternative
- Also detects and uses the virtual environment

## Requirements
- Python 3.x installed on your system
- All required game dependencies installed (pygame, pyscroll, etc.)
- Game files present in the `src/` folder

## Troubleshooting
If the game doesn't start:
1. Make sure Python is installed and accessible from the command line
2. Ensure all game files are present in the `src/` folder
3. Check that required dependencies are installed
4. Try running from a terminal: `cd src && python game.py`

## Virtual Environment
If you have a virtual environment in `.venv133/`, the launchers will automatically use it. Otherwise, they'll use your system Python installation.

---
*Double-click either launcher file to start playing!*
