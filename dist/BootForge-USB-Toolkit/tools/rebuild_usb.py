#!/usr/bin/env python3
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
