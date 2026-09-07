@echo off
title Discord Rich Presence - Antigravity Edition
cd /d "%~dp0"

echo ========================================================
echo   Starting Discord Rich Presence...
echo ========================================================

if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment not found. Setting up...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

python main.py

pause
