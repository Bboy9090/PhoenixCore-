#!/usr/bin/env python3
"""
Simple BootForge Build - Create executable for current platform
"""

import sys
import subprocess
from pathlib import Path

def build_simple():
    """Build BootForge executable with minimal configuration"""
    root_dir = Path(__file__).parent.parent
    
    print("Building BootForge executable...")
    
    # Simple PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "BootForge",
        "--add-data", "src:src",
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
        print("✅ Build successful!")
        print(f"Executable: {root_dir}/dist/BootForge")
        return True
    else:
        print("❌ Build failed")
        return False

if __name__ == "__main__":
    build_simple()