#!/usr/bin/env python3
"""
BootForge Debug Build - Shows console for troubleshooting
"""

import sys
import subprocess
from pathlib import Path

def build_debug():
    """Build BootForge with console window to see errors"""
    root_dir = Path(__file__).parent.parent
    
    print("Building BootForge DEBUG executable (shows console/errors)...")
    
    # Debug PyInstaller command - WITH console window
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",  # Shows console window with errors!
        "--name", "BootForge-Debug",
        "--add-data", "src;src" if sys.platform.startswith("win") else "--add-data", "src:src",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "requests",
        "--hidden-import", "psutil",
        "--hidden-import", "cryptography",
        "--hidden-import", "yaml", 
        "--hidden-import", "click",
        "--hidden-import", "colorama",
        "main.py"
    ]
    
    result = subprocess.run(cmd, cwd=root_dir)
    
    if result.returncode == 0:
        print("\n✅ Debug build successful!")
        print(f"\n📁 Executable: {root_dir}/dist/BootForge-Debug.exe")
        print("\n🔍 Run this to see what errors are happening!")
        return True
    else:
        print("\n❌ Build failed")
        return False

if __name__ == "__main__":
    build_debug()
