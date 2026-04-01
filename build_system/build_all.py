#!/usr/bin/env python3
"""
BootForge Complete Build System
Builds all executables and creates USB toolkit
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Build complete BootForge distribution"""
    print("BootForge Complete Build System")
    print("=" * 50)
    
    build_dir = Path(__file__).parent
    
    # Step 1: Install/check PyInstaller
    print("1. Checking PyInstaller...")
    try:
        import PyInstaller
        print("✓ PyInstaller is installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Step 2: Build current platform executable
    print("2. Building platform executable...")
    subprocess.run([sys.executable, str(build_dir / "pyinstaller_config.py")], check=True)
    
    # Step 3: Create USB toolkit
    print("3. Creating USB toolkit...")
    subprocess.run([sys.executable, str(build_dir / "usb_toolkit_builder.py")], check=True)
    
    print("""
🎉 Build Complete!

Your BootForge distribution is ready:
- dist/ contains executables
- usb_toolkit/ contains portable USB toolkit
- dist/BootForge-USB-Toolkit.zip ready for download

Next steps:
1. Test the executable for your platform
2. Extract USB toolkit to a USB drive
3. Copy your OS images to the toolkit
    """)

if __name__ == "__main__":
    main()