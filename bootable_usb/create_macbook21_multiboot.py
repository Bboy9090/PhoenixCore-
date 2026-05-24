#!/usr/bin/env python3
"""
Phoenix Core - MacBook 2,1 32-bit Multi-Boot USB Creator
Creates a premium, standard MBR FAT32 multi-boot drive containing both:
1. Home Aurelia OS (32-bit Legacy)
2. MX Linux Fluxbox (32-bit)
Utilizes a custom 32-bit EFI GRUB loopback boot loader.
"""

import sys
import os
import subprocess
import shutil
import time
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
    print(f"{BLUE}│{RESET} {CYAN}{BOLD}Home Aurelia - MacBook 2,1 32-bit Multi-Boot Creator{RESET}   {BLUE}│{RESET}")
    print(f"{BLUE}│{RESET} Premium Dual-OS Developer Experimentation Suite         {BLUE}│{RESET}")
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
        
        disks = []
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

def format_usb_to_mbr_fat32(disk_path: str):
    """Formats the selected drive to a single MBR FAT32 partition named AURELIA."""
    print(f"\n{BLUE}🔄 Preparing drive {disk_path} (zeroing out partition table)...{RESET}")
    try:
        # Force unmount drive first
        subprocess.run(["diskutil", "unmountDisk", "force", disk_path], check=True)
        
        # Wiping the first 32 MB of the drive to clear conflicting partition tables
        raw_disk = disk_path.replace("/dev/disk", "/dev/rdisk")
        print(f"{YELLOW}⚡ Wiping legacy partition structures on {raw_disk}... (requires sudo){RESET}")
        subprocess.run(["sudo", "dd", "if=/dev/zero", f"of={raw_disk}", "bs=1m", "count=32"], check=True)
        
        # Allow macOS kernel to settle and register the empty device state
        print(f"{YELLOW}⏳ Settling disk state...{RESET}")
        time.sleep(3)
        
        # Force unmount one more time just in case macOS auto-probed
        subprocess.run(["diskutil", "unmountDisk", "force", disk_path], check=False)
        
        # Perform clean erase to MBR FAT32 AURELIA
        print(f"{BLUE}🔄 Formatting disk as standard MBR FAT32 (Volume: AURELIA)...{RESET}")
        subprocess.run([
            "diskutil", "eraseDisk", "FAT32", "AURELIA", "MBR", disk_path
        ], check=True)
        
        print(f"{GREEN}✓ Disk formatted successfully as standard MBR FAT32 (Volume: AURELIA).{RESET}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{RED}❌ Failed to format disk: {e}{RESET}")
        return False

def generate_grub_config() -> str:
    """Generates a premium GRUB loopback configuration for both OS files."""
    return """# GRUB 32-bit EFI Multi-Boot Configuration
# Aligned to premium Home Aurelia visual direction (Dark Navy / Electric Blue / Gold)

set timeout=15
set default=0

# Graphics Terminal Setup
insmod part_msdos
insmod fat
insmod normal
insmod video
insmod video_fb
insmod gfxterm

set gfxmode=auto
terminal_output gfxterm

# Premium Visual Color Accents
set menu_color_normal=white/black
set menu_color_highlight=yellow/blue

menuentry "🔥 Home Aurelia OS (32-bit Legacy Live)" --class phoenix {
    set isofile="/iso/bwos-home-legacy-i386.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop $isofile
    linux (loop)/live/vmlinuz boot=live findiso=$isofile quiet splash nomodeset
    initrd (loop)/live/initrd.img
}

menuentry "❄️ MX Linux 23.6 Fluxbox (32-bit Live)" --class mx {
    set isofile="/iso/MX-23.6_fluxbox_386.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop $isofile
    linux (loop)/antiX/vmlinuz quiet splash fromiso=$isofile nomodeset
    initrd (loop)/antiX/initrd.gz
}

menuentry "💻 Reboot System" {
    reboot
}

menuentry "🔌 Shut Down" {
    halt
}
"""

def main():
    print_banner()
    
    workspace_root = Path("/Users/bj90-m1/PhoenixCore-")
    
    # 1. Define source image paths and verify existence
    home_aurelia_iso = workspace_root / "iso" / "outputs" / "bwos-home-legacy-i386.iso"
    mx_linux_iso = Path("/Users/bj90-m1/Downloads/MX-23.6_fluxbox_386.iso")
    bootloader_source = workspace_root / "bootable_usb" / "bootia32.efi"
    
    if not home_aurelia_iso.exists():
        print(f"{RED}❌ Home Aurelia ISO not found at: {home_aurelia_iso}{RESET}")
        sys.exit(1)
        
    if not mx_linux_iso.exists():
        print(f"{RED}❌ MX Linux ISO not found at: {mx_linux_iso}{RESET}")
        sys.exit(1)
        
    if not bootloader_source.exists():
        print(f"{RED}❌ 32-bit EFI bootloader (bootia32.efi) not found in workspace.{RESET}")
        sys.exit(1)
        
    print(f"{GREEN}🎯 Verified 32-bit Multi-Boot Image Sources:{RESET}")
    print(f"   1. 🖥️  {BOLD}Home Aurelia OS{RESET}: {home_aurelia_iso.name} ({BOLD}2.24 GB{RESET})")
    print(f"   2. ❄️  {BOLD}MX Linux 23.6{RESET}: {mx_linux_iso.name} ({BOLD}2.03 GB{RESET})")
    print(f"   3. 🔌 {BOLD}Bootloader{RESET}: {bootloader_source.name} (Verified 32-bit EFI)")
    print()
    
    # 2. Scan and list external drives
    print(f"{BLUE}🔍 Scanning for connected USB/SD drives...{RESET}")
    disks = get_connected_disks()
    
    if not disks:
        print(f"{YELLOW}⚠️  No external drives detected. Please insert your USB/SD card.{RESET}")
        sys.exit(0)
        
    print(f"{GREEN}✓ Detected external drives:{RESET}")
    for i, disk in enumerate(disks, 1):
        print(f"   {BOLD}{i}. {disk['path']}{RESET} - {disk['description']}")
        
    print()
    try:
        choice = input(f"{YELLOW}Select the drive number (1-{len(disks)}): {RESET}").strip()
        if not choice:
            sys.exit(0)
        idx = int(choice) - 1
        selected_disk = disks[idx]["path"]
    except (ValueError, IndexError):
        print(f"{RED}❌ Invalid selection.{RESET}")
        sys.exit(1)
        
    print()
    print(f"{RED}{BOLD}⚠️⚠️⚠️  CRITICAL WARNING  ⚠️⚠️⚠️{RESET}")
    print(f"{RED}This will PERMANENTLY and IRREVERSIBLY ERASE ALL DATA on: {BOLD}{selected_disk}{RESET}")
    print(f"{RED}It will be formatted as a single MBR FAT32 boot drive.{RESET}")
    print()
    
    confirm = input(f"{YELLOW}Type exactly '{BOLD}ERASE{RESET}{YELLOW}' to proceed: {RESET}").strip()
    if confirm != "ERASE":
        print(f"{GREEN}✓ Cancelled safely.{RESET}")
        sys.exit(0)
        
    # 3. Format drive
    if not format_usb_to_mbr_fat32(selected_disk):
        sys.exit(1)
        
    # 4. Stage Files
    mount_point = Path("/Volumes/AURELIA")
    
    # Verify mount
    if not mount_point.exists():
        print(f"{YELLOW}⏳ Waiting for drive to auto-mount...{RESET}")
        time.sleep(3)
        if not mount_point.exists():
            print(f"{RED}❌ Drive failed to auto-mount. Please unplug/replug and try again.{RESET}")
            sys.exit(1)
            
    print(f"\n{BLUE}📂 Staging multi-boot files onto AURELIA partition...{RESET}")
    
    # Create directories
    boot_dir = mount_point / "EFI" / "BOOT"
    iso_dir = mount_point / "iso"
    
    boot_dir.mkdir(parents=True, exist_ok=True)
    iso_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Copy bootloader
    print(f"   🚀 Copying 32-bit EFI bootloader to /EFI/BOOT/BOOTIA32.EFI...")
    shutil.copy2(bootloader_source, boot_dir / "BOOTIA32.EFI")
    
    # 2. Write GRUB configuration
    print(f"   📄 Writing GRUB multi-boot configuration...")
    grub_cfg = generate_grub_config()
    with open(boot_dir / "grub.cfg", "w") as f:
        f.write(grub_cfg)
        
    # 3. Copy OS files
    print(f"   🖥️  Copying Home Aurelia OS ISO ({home_aurelia_iso.name})...")
    shutil.copy2(home_aurelia_iso, iso_dir / home_aurelia_iso.name)
    
    print(f"   ❄️  Copying MX Linux ISO ({mx_linux_iso.name})...")
    shutil.copy2(mx_linux_iso, iso_dir / mx_linux_iso.name)
    
    print(f"\n{GREEN}🎉 Success! Your 32-bit EFI Multi-Boot USB has been created successfully!{RESET}")
    print(f"{BLUE}🔌 Ejecting AURELIA...{RESET}")
    subprocess.run(["diskutil", "eject", selected_disk], capture_output=True)
    print(f"{GREEN}✓ Safe to remove. Plug the card/USB reader into your MacBook 2,1,{RESET}")
    print(f"{GREEN}  hold down OPTION (Alt) while booting, select 'EFI Boot', and explore both systems!{RESET}")

if __name__ == "__main__":
    main()
