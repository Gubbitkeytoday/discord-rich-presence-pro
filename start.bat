@echo off
chcp 65001 >nul
title Discord Rich Presence - Antigravity Edition
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [!] Creating virtual environment...
    python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
    ".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
)

".venv\Scripts\python.exe" main.py %*
pause
