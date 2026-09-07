@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title Discord Rich Presence Pro
cd /d "%~dp0"

echo ==========================================================
echo   Discord Rich Presence Pro v2.1.0
echo ==========================================================

:: ---- 1) หา Python 3.10+ บนเครื่อง --------------------------------------
set "PY="
for %%P in (py python python3) do (
    if not defined PY (
        %%P -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1 && set "PY=%%P"
    )
)
if not defined PY (
    echo.
    echo [X] ไม่พบ Python 3.10 ขึ้นไปบนเครื่องนี้
    echo     1. เข้า https://www.python.org/downloads/  แล้วดาวน์โหลด Python ^(แนะนำ 3.12^)
    echo     2. ตอนติดตั้ง **ติ๊ก "Add python.exe to PATH"** ให้ด้วย
    echo     3. ติดตั้งเสร็จแล้วดับเบิลคลิก start.bat ใหม่อีกครั้ง
    echo.
    echo     หรือถ้าไม่อยากลง Python: ดาวน์โหลดไฟล์ .exe สำเร็จรูปจากหน้า Releases ของโปรเจกต์
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

:: ---- 2) ตรวจ venv ว่าใช้ได้จริง (venv ที่ copy มาจากเครื่องอื่นจะเสีย) ------
set "NEED_SETUP="
if not exist ".venv\Scripts\python.exe" set "NEED_SETUP=1"
if not defined NEED_SETUP (
    ".venv\Scripts\python.exe" -c "import pypresence, psutil" >nul 2>&1 || set "NEED_SETUP=1"
)
if defined NEED_SETUP (
    echo [i] กำลังติดตั้งครั้งแรก ^(ใช้เวลา 1-2 นาที ครั้งเดียว^)...
    if exist ".venv" rmdir /s /q ".venv"
    %PY% -m venv .venv || (echo [X] สร้าง virtual environment ไม่สำเร็จ & pause & exit /b 1)
    ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
    ".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt || (
        echo [X] ติดตั้งไลบรารีไม่สำเร็จ - ตรวจอินเทอร์เน็ต แล้วลองใหม่
        pause & exit /b 1
    )
    echo [OK] ติดตั้งเสร็จแล้ว
)

:: ---- 3) รัน ------------------------------------------------------------------
echo [i] เริ่มทำงาน... ^(ปิดหน้าต่างนี้ = หยุดโปรแกรม / ใช้ start_background.vbs เพื่อรันเงียบ^)
".venv\Scripts\python.exe" main.py %*
pause
