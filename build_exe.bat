@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo   Building DiscordRichPresence.exe with PyInstaller
echo ========================================================

if not exist ".venv\Scripts\python.exe" (
    echo [X] .venv not found. Please run start.bat first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m PyInstaller --noconfirm --onefile --noconsole ^
  --name "DiscordRichPresence" ^
  --collect-submodules winsdk --collect-binaries winsdk --collect-data winsdk ^
  --hidden-import winsdk.windows.media.control ^
  --hidden-import winsdk.windows.foundation ^
  --hidden-import winsdk.windows.foundation.collections ^
  --hidden-import winsdk.windows.storage.streams ^
  --hidden-import pystray._win32 ^
  main.py

if errorlevel 1 (
    echo [X] Build failed!
    pause
    exit /b 1
)

if not exist "dist" mkdir "dist"
copy /y config.json dist\config.json >nul

echo.
echo ========================================================
echo   [OK] Build Succeeded: dist\DiscordRichPresence.exe
echo ========================================================
