@echo off
title Semantic Research Manager
echo.
echo Starting Semantic Research Manager...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Could not create virtual environment
        echo Make sure Python is installed and in your PATH
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update requirements
echo Installing/updating dependencies...
pip install -r requirements.txt --quiet

REM Check if installation was successful
if errorlevel 1 (
    echo Warning: Some dependencies may not have installed correctly
)

REM Run the application
echo.
echo ================================
echo   SEMANTIC RESEARCH MANAGER
echo ================================
echo loading...
python main.py

REM Pause before closing if there was an error
if errorlevel 1 (
    echo.
    echo Application exited with an error
    pause
)