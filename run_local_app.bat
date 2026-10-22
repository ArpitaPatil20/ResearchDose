@echo off
cd /d "%~dp0"
title ResearchDose — Local Platform
echo ========================================================
echo   ResearchDose — Scientific Dose Conversion Platform
echo   Starting Local Server at http://127.0.0.1:8000
echo ========================================================
echo.

:: Check virtual environment
if not exist "venv\Scripts\python.exe" (
    echo Error: Python virtual environment not found in venv\
    echo Run: python -m venv venv
    pause
    exit /b 1
)

:: Automatically open default browser after 1.5 seconds
start "" powershell -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8000'"

:: Start Uvicorn Server in foreground
echo Server is starting... (Press Ctrl+C to stop)
venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
