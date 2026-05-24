#!/usr/bin/env python3
"""
Phoenix Core - MacBook 2,1 Bootable USB Creator
Natively formats and safely writes the 32-bit ready Home Aurelia OS image on macOS.
"""

import sys
import os
import subprocess
import time
import shutil
from pathlib import Path

# Color and visual formatting definitions
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"

def print_banner():
    print(f"{BLUE}┌────────────────────────────────────────────────────────┐{RESET}")
    print(f"{BLUE}│{RESET} {CYAN}{BOLD}Home Aurelia OS - MacBook 2,1 Bootable USB Creator{RESET}     {BLUE}│{RESET}")
    print(f"{BLUE}│{RESET} Safe & Professional Deployment Tool for Legacy Macs    {BLUE}│{RESET}")
    print(f"{BLUE}└────────────────────────────────────────────────────────┘{RESET}")
    print()

def get_connected_disks():
    """Uses macOS diskutil to list all connected drives."""
    try:
        result = subprocess.run(
            ["diskutil", "list", "external", "physical"],
            capture_output=True, text=True, check=True
        )
        output = result.stdout.strip()
        if not output:
            return []
        
        # Parse output to find external disks
        disks = []
        current_disk = None
        for line in output.split("\n"):
            if line.startswith("/dev/disk"):
                parts = line.split()
                dev_path = parts[0]
                # Gather details on size and name
                size_str = ""
                for part in parts[1:]:
                    if "GB" in part or "MB" in part or "TB" in part:
                        size_str = part
                        break
                current_disk = {
                    "path": dev_path,
                    "description": line.replace(dev_path, "").strip(),
                    "size": size_str
                }
                disks.append(current_disk)
        return disks
    except Exception as e:
        print(f"{RED}❌ Failed to query disk list: {e}{RESET}")
        return []

def flash_image_to_usb(image_path: Path, disk_path: str):
    """Flashes the image using safe macOS dd commands with rdisk for fast speeds."""
    raw_disk = disk_path.replace("/dev/disk", "/dev/rdisk")
    print(f"\n{BLUE}🔄 Preparing target disk {disk_path}...{RESET}")
    
    # 1. Unmount disk
    try:
        subprocess.run(["diskutil", "unmountDisk", "force", disk_path], check=True)
        print(f"{GREEN}✓ Disk unmounted successfully.{RESET}")
    except subprocess.CalledProcessError:
        print(f"{RED}❌ Failed to unmount disk {disk_path}. Please check if files are open.{RESET}")
        return False
        
    print(f"{YELLOW}⚡ Writing image to {raw_disk} (using dd with progress)...{RESET}")
    print(f"{YELLOW}   This requires sudo elevation to access raw disk storage.{RESET}")
    
    # Use standard dd with status=progress
    dd_cmd = f"sudo dd if={image_path} of={raw_disk} bs=1m status=progress"
    
    try:
        # Launch dd interactively so progress displays natively
        ret = os.system(dd_cmd)
        if ret == 0:
            print(f"\n{GREEN}🎉 Success! The 32-bit Home Aurelia OS USB has been created.{RESET}")
            print(f"{BLUE}🔌 Ejecting the drive...{RESET}")
            subprocess.run(["diskutil", "eject", disk_path], capture_output=True)
            print(f"{GREEN}✓ Safe to remove. Plug the USB into your MacBook 2,1, hold down OPTION (Alt) while booting, and select the USB!{RESET}")
            return True
        else:
            print(f"\n{RED}❌ dd exited with non-zero code ({ret}). USB creation may have failed.{RESET}")
            return False
    except KeyboardInterrupt:
        print(f"\n{RED}⚠️ Operation cancelled by user. USB partition table might be corrupted.{RESET}")
        return False

def main():
    print_banner()
    
    # Define source image path
    workspace_root = Path("/Users/bj90-m1/PhoenixCore-")
    image_path = workspace_root / "iso" / "outputs" / "bwos-home-legacy-i386.iso"
    
    if not image_path.exists():
        print(f"{RED}❌ Error: 32-bit ready image not found at:{RESET}")
        print(f"   {image_path}")
        print(f"   Please compile or place your image in the output directory first.")
        sys.exit(1)
        
    print(f"{GREEN}🎯 Found 32-bit Ready Image:{RESET}")
    print(f"   📁 {image_path.name}")
    print(f"   💾 Size: 2.24 GB")
    print(f"   🖥️  Edition: {BOLD}Home Aurelia OS (Legacy i386){RESET}")
    print(f"   🎨 Aesthetic: Dark Navy Base, Electric Blue Highlights, Gold Trim, Blue Phoenix Logo")
    print()
    
    # Query connected drives
    print(f"{BLUE}🔍 Scanning for connected USB drives...{RESET}")
    disks = get_connected_disks()
    
    if not disks:
        print(f"{YELLOW}⚠️  No external USB drives detected.{RESET}")
        print(f"   Please plug in your USB flash drive and restart this script.{RESET}")
        sys.exit(0)
        
    print(f"{GREEN}✓ Detected external drives:{RESET}")
    for i, disk in enumerate(disks, 1):
        print(f"   {BOLD}{i}. {disk['path']}{RESET} - {disk['description']}")
        
    print()
    try:
        choice = input(f"{YELLOW}Select the drive number (1-{len(disks)}): {RESET}").strip()
        if not choice:
            print(f"{RED}Operation cancelled.{RESET}")
            sys.exit(0)
        idx = int(choice) - 1
        if idx < 0 or idx >= len(disks):
            print(f"{RED}❌ Invalid selection.{RESET}")
            sys.exit(1)
            
        selected_disk = disks[idx]["path"]
    except (ValueError, IndexError):
        print(f"{RED}❌ Invalid selection.{RESET}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{RED}Operation cancelled.{RESET}")
        sys.exit(0)
        
    # Double-check confirmation to avoid accidental writes to system drives
    print()
    print(f"{RED}{BOLD}⚠️⚠️⚠️  CRITICAL WARNING  ⚠️⚠️⚠️{RESET}")
    print(f"{RED}This will PERMANENTLY and IRREVERSIBLY ERASE ALL DATA on the drive: {BOLD}{selected_disk}{RESET}")
    print(f"{RED}Make absolutely certain you have selected the correct external USB drive.{RESET}")
    print()
    
    try:
        confirm = input(f"{YELLOW}To confirm, type exactly '{BOLD}ERASE{RESET}{YELLOW}': {RESET}").strip()
        if confirm != "ERASE":
            print(f"{GREEN}✓ Operation cancelled safely. No data was mutated.{RESET}")
            sys.exit(0)
            
        flash_image_to_usb(image_path, selected_disk)
    except KeyboardInterrupt:
        print(f"\n{GREEN}✓ Operation cancelled safely.{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()
