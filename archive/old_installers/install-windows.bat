@echo off
echo 🚀 BootForge Windows Quick Install
echo ================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Install from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
python --version
echo.

echo 📦 Installing dependencies...
pip install click colorama psutil pillow pyyaml requests cryptography

echo.
echo 📥 Download bootforge-standalone.py to same folder as this script
echo.
echo 🎯 Then run: python bootforge-standalone.py --help
echo.
echo 🎉 Setup complete!
pause