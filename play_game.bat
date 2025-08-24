@echo off
echo Starting the game...
echo.

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

REM Check if virtual environment exists
if exist "%SCRIPT_DIR%.venv133\Scripts\python.exe" (
    echo Using virtual environment Python...
    set PYTHON_EXE=%SCRIPT_DIR%.venv133\Scripts\python.exe
) else (
    echo Using system Python...
    set PYTHON_EXE=python
)

REM Change to the src directory and run the game
cd /d "%SCRIPT_DIR%src"
if not exist "game.py" (
    echo Error: game.py not found in src directory!
    echo Make sure you're running this from the correct location.
    pause
    exit /b 1
)

echo Running game from: %CD%
echo Using Python: %PYTHON_EXE%
echo.
echo ========================================

REM Run the game
"%PYTHON_EXE%" game.py

REM If we get here, the game has finished
echo.
echo ========================================
echo Game finished.
pause
