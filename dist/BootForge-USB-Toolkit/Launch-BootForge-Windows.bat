@echo off
echo Starting BootForge...
cd /d "%~dp0executables"
if exist "BootForge.exe" (
    start "" "BootForge.exe"
) else (
    echo BootForge.exe not found!
    pause
)
