@echo off
title ResearchDose - Public Shareable Server
echo ========================================================
echo   ResearchDose - Starting Local Server & Public Tunnel
echo ========================================================
echo.

:: Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo Error: Python virtual environment not found in venv\
    pause
    exit /b 1
)

:: Start Uvicorn in the background if not already running
echo [1/2] Starting ResearchDose backend on http://127.0.0.1:8000 ...
start /B venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

:: Wait 2 seconds for server initialization
timeout /t 2 /nobreak >nul

:: Launch Cloudflare Tunnel
echo [2/2] Generating live public HTTPS link via Cloudflare Tunnel ...
echo.
echo ========================================================
echo Look for the https://*.trycloudflare.com URL below!
echo Share that link with anyone on their phone or desktop.
echo (Press Ctrl+C to stop sharing)
echo ========================================================
echo.
cloudflared.exe tunnel --url http://127.0.0.1:8000
