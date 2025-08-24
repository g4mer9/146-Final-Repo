#!/usr/bin/env python3
"""
Game Launcher
Double-click this file to play the game!
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Main launcher function"""
    try:
        # Get the directory where this launcher script is located
        launcher_dir = Path(__file__).parent.absolute()
        
        # The game files are in the 'src' subdirectory
        game_dir = launcher_dir / "src"
        game_file = game_dir / "game.py"
        
        # Check if the game file exists
        if not game_file.exists():
            print(f"Error: Game file not found at {game_file}")
            print("Make sure the 'src' folder and 'game.py' are in the same directory as this launcher.")
            input("Press Enter to exit...")
            return False
        
        # Check if we have a virtual environment
        venv_dir = launcher_dir / ".venv133"
        if venv_dir.exists():
            # Use the virtual environment's Python
            if os.name == 'nt':  # Windows
                python_exe = venv_dir / "Scripts" / "python.exe"
            else:  # Unix-like systems
                python_exe = venv_dir / "bin" / "python"
            
            if not python_exe.exists():
                print(f"Warning: Virtual environment found but Python executable not found at {python_exe}")
                print("Using system Python instead...")
                python_exe = sys.executable
        else:
            # Use the current Python interpreter
            python_exe = sys.executable
        
        print("Starting the game...")
        print(f"Game directory: {game_dir}")
        print(f"Using Python: {python_exe}")
        print("-" * 50)
        
        # Change to the game directory and run the game
        # We use subprocess to properly handle the working directory
        result = subprocess.run(
            [str(python_exe), "game.py"],
            cwd=str(game_dir),
            capture_output=False  # Let the game output go directly to console
        )
        
        return result.returncode == 0
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {e}")
        print("Make sure all game files are present and Python is installed.")
        input("Press Enter to exit...")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error running the game: {e}")
        print("The game encountered an error during execution.")
        input("Press Enter to exit...")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("An unexpected error occurred while trying to start the game.")
        input("Press Enter to exit...")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\nThe game did not start successfully.")
            input("Press Enter to exit...")
    except KeyboardInterrupt:
        print("\nGame launch cancelled by user.")
    except Exception as e:
        print(f"\nFatal error: {e}")
        input("Press Enter to exit...")
