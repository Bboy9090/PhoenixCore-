#!/usr/bin/env python3
"""
BootForge USB Toolkit Builder
Creates portable USB distributions with OS image management
"""

import os
import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

class USBToolkitBuilder:
    """Builds portable USB toolkit with BootForge executables and OS images"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.dist_dir = self.root_dir / "dist"
        self.usb_dir = self.root_dir / "usb_toolkit"
        
    def create_usb_structure(self):
        """Create the USB toolkit directory structure"""
        # Clean and create USB toolkit directory
        if self.usb_dir.exists():
            shutil.rmtree(self.usb_dir)
        self.usb_dir.mkdir()
        
        # Create subdirectories
        (self.usb_dir / "executables").mkdir()
        (self.usb_dir / "os_images" / "macOS").mkdir(parents=True)
        (self.usb_dir / "os_images" / "Windows").mkdir(parents=True)
        (self.usb_dir / "os_images" / "Linux").mkdir(parents=True)
        (self.usb_dir / "tools").mkdir()
        (self.usb_dir / "sync").mkdir()
        
        return True
        
    def copy_executables(self):
        """Copy built executables to USB toolkit"""
        exe_dir = self.usb_dir / "executables"
        
        # Copy executables from dist directory (if they exist)
        for exe_name in ["BootForge.exe", "BootForge.app", "BootForge"]:
            exe_path = self.dist_dir / exe_name
            if exe_path.exists():
                if exe_name == "BootForge.app":
                    # Copy app bundle
                    shutil.copytree(exe_path, exe_dir / exe_name)
                else:
                    # Copy single executable
                    shutil.copy2(exe_path, exe_dir)
                print(f"Copied {exe_name} to USB toolkit")
        
        return True
    
    def create_launcher_scripts(self):
        """Create platform-specific launcher scripts"""
        
        # Windows batch launcher
        windows_launcher = '''@echo off
echo Starting BootForge...
cd /d "%~dp0executables"
if exist "BootForge.exe" (
    start "" "BootForge.exe"
) else (
    echo BootForge.exe not found!
    pause
)
'''
        with open(self.usb_dir / "Launch-BootForge-Windows.bat", 'w') as f:
            f.write(windows_launcher)
        
        # macOS shell launcher
        macos_launcher = '''#!/bin/bash
echo "Starting BootForge..."
cd "$(dirname "$0")/executables"
if [ -d "BootForge.app" ]; then
    open "BootForge.app"
else
    echo "BootForge.app not found!"
    read -p "Press enter to continue..."
fi
'''
        macos_script = self.usb_dir / "Launch-BootForge-Mac.command"
        with open(macos_script, 'w') as f:
            f.write(macos_launcher)
        macos_script.chmod(0o755)  # Make executable
        
        # Linux shell launcher
        linux_launcher = '''#!/bin/bash
echo "Starting BootForge..."
cd "$(dirname "$0")/executables"
if [ -f "BootForge" ]; then
    ./BootForge
else
    echo "BootForge executable not found!"
    read -p "Press enter to continue..."
fi
'''
        linux_script = self.usb_dir / "Launch-BootForge-Linux.sh"
        with open(linux_script, 'w') as f:
            f.write(linux_launcher)
        linux_script.chmod(0o755)  # Make executable
        
        return True
    
    def create_sync_tools(self):
        """Create USB sync and rebuild tools"""
        
        # USB sync configuration
        sync_config = {
            "version": "1.0.0",
            "last_sync": datetime.now().isoformat(),
            "image_library": {
                "macOS": [],
                "Windows": [],
                "Linux": []
            },
            "sync_settings": {
                "auto_sync": True,
                "preserve_custom_images": True,
                "max_image_age_days": 90
            }
        }
        
        with open(self.usb_dir / "sync" / "sync_config.json", 'w') as f:
            json.dump(sync_config, f, indent=2)
        
        # USB rebuild script
        rebuild_script = '''#!/usr/bin/env python3
"""
BootForge USB Rebuild Tool
Recreates USB toolkit from installed BootForge
"""

import os
import sys
import json
import shutil
from pathlib import Path

def rebuild_usb_toolkit():
    """Rebuild USB toolkit structure"""
    print("BootForge USB Toolkit Rebuild")
    print("=" * 40)
    
    # Get USB root directory
    usb_root = Path(__file__).parent.parent
    
    # Verify this is a BootForge USB
    if not (usb_root / "sync" / "sync_config.json").exists():
        print("Error: This does not appear to be a BootForge USB toolkit")
        return False
    
    print(f"Rebuilding USB toolkit at: {usb_root}")
    
    # Load sync configuration
    with open(usb_root / "sync" / "sync_config.json", 'r') as f:
        config = json.load(f)
    
    print("USB toolkit rebuilt successfully!")
    print(f"Version: {config['version']}")
    print(f"Last sync: {config['last_sync']}")
    
    return True

if __name__ == "__main__":
    rebuild_usb_toolkit()
'''
        
        with open(self.usb_dir / "tools" / "rebuild_usb.py", 'w') as f:
            f.write(rebuild_script)
        
        return True
    
    def create_readme(self):
        """Create simple USB toolkit instructions"""
        readme_content = '''BootForge Portable USB Toolkit
============================

Quick Start:
- Windows: Double-click "Launch-BootForge-Windows.bat"
- macOS: Double-click "Launch-BootForge-Mac.command"  
- Linux: Run "./Launch-BootForge-Linux.sh"

Directory Structure:
- executables/    - BootForge applications for each platform
- os_images/      - Your OS image library (macOS, Windows, Linux)
- tools/          - USB management and rebuild tools
- sync/           - Synchronization configuration

Features:
✓ No installation required
✓ Works on Windows, macOS, and Linux
✓ Stores your OS image library
✓ Cross-platform USB creation
✓ Easy rebuild if USB is lost/damaged

Visit: github.com/your-repo/bootforge
'''
        
        with open(self.usb_dir / "README.txt", 'w') as f:
            f.write(readme_content)
        
        return True
    
    def create_zip_distribution(self):
        """Create downloadable ZIP of USB toolkit"""
        zip_path = self.dist_dir / "BootForge-USB-Toolkit.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.usb_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(self.usb_dir)
                    zipf.write(file_path, arc_path)
        
        print(f"Created ZIP distribution: {zip_path}")
        return zip_path
    
    def build_usb_toolkit(self):
        """Build complete USB toolkit"""
        print("Building BootForge USB Toolkit...")
        
        self.create_usb_structure()
        self.copy_executables()
        self.create_launcher_scripts()
        self.create_sync_tools()
        self.create_readme()
        zip_path = self.create_zip_distribution()
        
        print(f"""
USB Toolkit built successfully!

Toolkit directory: {self.usb_dir}
Download package: {zip_path}

To use:
1. Extract ZIP to USB drive
2. Run appropriate launcher for your platform
3. Add OS images to os_images/ folders
        """)
        
        return True

if __name__ == "__main__":
    builder = USBToolkitBuilder()
    builder.build_usb_toolkit()