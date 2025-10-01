@echo off
title BootForge USB Recovery System
echo 🚀 Starting BootForge from USB...
cd /d "%~dp0BootForge"

where python >nul 2>nul
if %errorlevel% == 0 (
    echo ✅ Python found
    python main.py --gui
) else (
    where python3 >nul 2>nul
    if %errorlevel% == 0 (
        echo ✅ Python 3 found
        python3 main.py --gui
    ) else (
        echo ❌ Python not found. Please install Python 3.
        echo Visit: https://www.python.org/downloads/
        pause
    )
)
