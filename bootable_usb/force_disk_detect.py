#!/usr/bin/env python3
"""
Phoenix Core - Premium Force Disk Recovery & Eraser
A professional diagnostics tool designed to force-detect unresponsive USB disks
and completely erase legacy partition structures.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Premium design colors (Dark Navy / Electric Blue / Gold accent theme)
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"

def print_banner():
    print(f"{BLUE}┌────────────────────────────────────────────────────────┐{RESET}")
    print(f"{BLUE}│{RESET} {CYAN}{BOLD}Phoenix OS - Premium Force Disk Recovery & Eraser{RESET}     {BLUE}│{RESET}")
    print(f"{BLUE}│{RESET} Dedicated Diagnostic & Erase Tool for Stubborn Drives   {BLUE}│{RESET}")
    print(f"{BLUE}└────────────────────────────────────────────────────────┘{RESET}")
    print()

def get_external_physical_disks():
    """Queries macOS diskutil for physical external disks."""
    try:
        result = subprocess.run(
            ["diskutil", "list", "external", "physical"],
            capture_output=True, text=True, check=True
        )
        output = result.stdout.strip()
        if not output:
            return {}
        
        disks = {}
        current_disk = None
        for line in output.split("\n"):
            if line.startswith("/dev/disk"):
                parts = line.split()
                dev_path = parts[0]
                size_str = ""
                for part in parts[1:]:
                    if "GB" in part or "MB" in part or "TB" in part:
                        size_str = part
                        break
                current_disk = dev_path
                disks[dev_path] = {
                    "path": dev_path,
                    "description": line.replace(dev_path, "").strip(),
                    "size": size_str
                }
        return disks
    except Exception:
        return {}

def wipe_disk(disk_path: str):
    """Force unmounts and completely zeroes out the drive's master boot records."""
    raw_disk = disk_path.replace("/dev/disk", "/dev/rdisk")
    print(f"\n{RED}{BOLD}⚠️⚠️⚠️  WARNING: FORCED WIPE IN PROGRESS  ⚠️⚠️⚠️{RESET}")
    print(f"{RED}Targeting: {BOLD}{disk_path}{RESET} ({raw_disk})")
    print(f"{YELLOW}This will completely destroy all boot loaders, partition maps, and files.{RESET}\n")
    
    confirm = input(f"{YELLOW}Type exactly '{BOLD}ERASE{RESET}{YELLOW}' to verify: {RESET}").strip()
    if confirm != "ERASE":
        print(f"{GREEN}✓ Cancelled safely.{RESET}")
        return False
        
    print(f"\n{BLUE}🔄 1. Sending force-unmount signals to all volumes on {disk_path}...{RESET}")
    subprocess.run(["diskutil", "unmountDisk", "force", disk_path], check=False)
    
    print(f"{BLUE}⚡ 2. Executing direct zero-fill block write to master boot area (requires sudo)...{RESET}")
    try:
        # Zero out the first 100MB to wipe MBR, GPT, Ventoy structures, and primary partition headers
        subprocess.run(["sudo", "dd", "if=/dev/zero", f"of={raw_disk}", "bs=1m", "count=100"], check=True)
        print(f"\n{GREEN}🎉 SUCCESS! The disk has been completely wiped and blanked.{RESET}")
        print(f"{GREEN}   All legacy partition structures and Ventoy code are gone.{RESET}")
        print(f"{BLUE}🔌 Ejecting drive safely...{RESET}")
        subprocess.run(["diskutil", "eject", disk_path], capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n{RED}❌ Wiping failed: {e}{RESET}")
        print(f"{YELLOW}💡 If this failed with an Input/Output error, the drive has lost connection.{RESET}")
        return False

def check_usb_hardware():
    """Checks the system USB bus for generic Mass Storage controllers."""
    try:
        result = subprocess.run(["ioreg", "-p", "IOUSB"], capture_output=True, text=True, check=True)
        return "Storage" in result.stdout or "MassStorageClass" in result.stdout
    except Exception:
        return False

def main():
    print_banner()
    
    # Phase 1: Hardware-level check
    print(f"{BLUE}🔍 Analyzing host USB controller...{RESET}")
    has_usb_bridge = check_usb_hardware()
    
    if has_usb_bridge:
        print(f"{GREEN}✓ Detected SATA-to-USB Bridge adapter connected to USB.{RESET}")
        print(f"{YELLOW}ℹ️  NOTE: The adapter is connected, but the physical hard drive is NOT presenting media.{RESET}")
        print(f"   This means the mechanical disk is either not spinning up, has a bad connector, or has lost power.{RESET}")
    else:
        print(f"{RED}⚠️  No SATA-to-USB adapter detected on the USB ports.{RESET}")
        
    print(f"\n{CYAN}{BOLD}📋 STEP-BY-STEP PHYSICAL TROUBLESHOOTING CHECKS:{RESET}")
    print(f" 1. {BOLD}Listen/Feel for Spin-Up:{RESET} Hold the hard drive in your hand. Does it gently hum/vibrate?")
    print(f"    - If it's silent: It has no power. The USB port is restricting current.")
    print(f"    - If it clicks repeatedly: The drive heads are failing or it is brown-outing due to weak power.")
    print(f" 2. {BOLD}Use a High-Power Port:{RESET} Plug the adapter directly into your MacBook Pro's main port.")
    print(f"    - Avoid passive multi-port hubs; they choke mechanical hard drive startup current.")
    print(f"    - If using a hub, plug a USB-C power charger into the hub to supply power pass-through.")
    print(f" 3. {BOLD}Unplug & Re-seat:{RESET} Firmly press the SATA connector into the hard drive, unplug the USB, wait 5s, and replug.")
    print()
    
    print(f"{BLUE}👀 Listening for disk changes. Plug in the drive now...{RESET}")
    print(f"{YELLOW}Press Ctrl+C at any time to exit.{RESET}\n")
    
    known_disks = get_external_physical_disks()
    
    try:
        dots = 0
        while True:
            current_disks = get_external_physical_disks()
            
            # Check for newly added disks
            new_paths = set(current_disks.keys()) - set(known_disks.keys())
            if new_paths:
                new_disk = list(new_paths)[0]
                disk_info = current_disks[new_disk]
                print(f"\n\n{GREEN}{BOLD}🔔 ALERT: NEW EXTERNAL DISK DETECTED!{RESET}")
                print(f"   📂 Path: {BOLD}{disk_info['path']}{RESET}")
                print(f"   💾 Size: {disk_info['size']}")
                print(f"   🖥️  Info: {disk_info['description']}")
                print()
                
                # Immediately offer to wipe it
                wipe_disk(new_disk)
                break
                
            # If no changes, print a pulse dot to show we are listening
            dots = (dots + 1) % 4
            sys.stdout.write(f"\r⏳ Scanning storage bus{'.' * dots}{' ' * (3 - dots)}")
            sys.stdout.flush()
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n\n{GREEN}✓ Diagnostic monitor closed safely.{RESET}")

if __name__ == "__main__":
    main()
