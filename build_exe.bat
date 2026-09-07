@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo สร้างไฟล์ .exe แบบไฟล์เดียว (ใช้ PyInstaller) - ผลลัพธ์อยู่ใน dist\
if not exist ".venv\Scripts\python.exe" call start.bat --help >nul
".venv\Scripts\python.exe" -m pip install --quiet pyinstaller
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --onefile --noconsole ^
  --name "DiscordRichPresence" ^
  --collect-submodules winrt --collect-binaries winrt --collect-data winrt ^
  --hidden-import winrt.windows.media.control ^
  --hidden-import winrt.windows.foundation ^
  --hidden-import winrt.windows.foundation.collections ^
  --hidden-import winrt.windows.storage.streams ^
  --hidden-import pystray._win32 ^
  main.py
if errorlevel 1 (echo [X] build ไม่สำเร็จ & pause & exit /b 1)
copy /y config.json dist\config.json >nul
echo.
echo [OK] เสร็จแล้ว: dist\DiscordRichPresence.exe  (ส่งไฟล์นี้ + config.json ให้คนอื่นได้เลย)
pause
