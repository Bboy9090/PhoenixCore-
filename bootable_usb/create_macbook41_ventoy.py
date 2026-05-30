#!/usr/bin/env python3
"""
Phoenix Core - MacBook 4,1 Ventoy-style Multi-ISO & Recovery USB Creator
Natively formats a USB drive and creates a highly stable, premium multi-boot
loopback loader configuration for four critical OS and recovery platforms.
"""

import sys
import os
import subprocess
import shutil
import time
import urllib.request
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
    print(f"{BLUE}│{RESET} {CYAN}{BOLD}Aurelia/Arcwyre - MacBook 4,1 Ventoy Multi-ISO USB{RESET}      {BLUE}│{RESET}")
    print(f"{BLUE}│{RESET} Premium Mixed-Mode Multi-OS & Recovery Deployment Suite {BLUE}│{RESET}")
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

def format_usb_to_ventoy_layout(disk_path: str):
    """Formats the selected drive into two partitions: BOOT (FAT32) and AURELIA (ExFAT) under GPT."""
    print(f"\n{BLUE}🔄 Preparing drive {disk_path} (zeroing out partition table)...{RESET}")
    try:
        subprocess.run(["diskutil", "unmountDisk", "force", disk_path], check=True)
        raw_disk = disk_path.replace("/dev/disk", "/dev/rdisk")
        print(f"{YELLOW}⚡ Wiping legacy partition structures on {raw_disk}... (requires sudo){RESET}")
        subprocess.run(["sudo", "dd", "if=/dev/zero", f"of={raw_disk}", "bs=1m", "count=32"], check=True)
        
        print(f"{YELLOW}⏳ Settling disk state...{RESET}")
        time.sleep(3)
        
        subprocess.run(["diskutil", "unmountDisk", "force", disk_path], check=False)
        
        print(f"{BLUE}🔄 Partitioning disk with Boot-First GPT Layout (BOOT FAT32: 200MB, AURELIA ExFAT: Remainder)...{RESET}")
        # Command: diskutil partitionDisk diskX 2 GPT "MS-DOS FAT32" BOOT 200M ExFAT AURELIA R
        # Changed partition scheme to GPT, ensuring legacy Apple EFI ROM can detect EFI bootloader!
        subprocess.run([
            "diskutil", "partitionDisk", disk_path, "2", "GPT", 
            "MS-DOS FAT32", "BOOT", "200M", "ExFAT", "AURELIA", "R"
        ], check=True)
        
        print(f"{GREEN}✓ Disk partitioned successfully with GPT ExFAT + FAT32!{RESET}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{RED}❌ Failed to partition disk: {e}{RESET}")
        return False

def generate_grub_config() -> str:
    """Generates a premium GRUB loopback configuration for a complete recovery suite."""
    return """# GRUB 32-bit EFI Multi-Boot Recovery Suite Configuration
# Designed for MacBook 4,1 (32-bit EFI -> 64-bit Kernel handoff)
# Aligned to premium Home Aurelia visual direction (Dark Navy / Electric Blue / Gold)

set timeout=15
set default=0

# Graphics Terminal & Theme Setup
insmod part_gpt
insmod part_msdos
insmod fat
insmod exfat   # Added for ExFAT support
insmod normal
insmod video
insmod video_fb
insmod gfxterm
insmod gfxmenu # Added for custom graphical themes support

# Load the custom premium Aurelia theme
set theme=($root)/EFI/BOOT/themes/phoenix/theme.txt

set gfxmode=auto
terminal_output gfxterm

# Premium Visual Color Accents (fallback)
set menu_color_normal=white/black
set menu_color_highlight=yellow/blue

# --- 1. Aurelia OS (64-bit AMD64) ---
# nomodeset added for fallback VESA console to safeguard the Intel GMA X3100 GPU
menuentry "🔥 Phoenix OS: Aurelia Edition (64-bit Live - nomodeset)" --class phoenix {
    set isofile="/iso/bwos-aurelia.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop $isofile
    linux (loop)/live/vmlinuz-5.10.0-43-amd64 boot=live components findiso=$isofile quiet splash nomodeset username=phoenix bwos.session=wayland console=tty0
    initrd (loop)/live/initrd.img-5.10.0-43-amd64
}

menuentry "🔥 Phoenix OS: Aurelia Edition (64-bit Live - Legacy Kernel Fallback)" --class phoenix {
    set isofile="/iso/bwos-aurelia.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop $isofile
    linux (loop)/live/vmlinuz boot=live components findiso=$isofile quiet splash nomodeset username=phoenix bwos.session=wayland console=tty0
    initrd (loop)/live/initrd.img
}

# --- 2. MX Linux 23.6 Fluxbox (32-bit Recovery) ---
menuentry "❄️ MX Linux 23.6 Fluxbox (32-bit Live Recovery)" --class mx {
    set isofile="/iso/MX-23.6_fluxbox_386.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop $isofile
    linux (loop)/antiX/vmlinuz quiet splash fromiso=$isofile nomodeset
    initrd (loop)/antiX/initrd.gz
}

# --- 3. Linux Mint 22.3 XFCE (64-bit Recovery) ---
menuentry "🌱 Linux Mint 22.3 XFCE (64-bit Live Recovery - nomodeset)" --class mint {
    set isofile="/iso/linuxmint-22.3-xfce-64bit.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop $isofile
    linux (loop)/casper/vmlinuz boot=casper iso-scan/filename=$isofile quiet splash nomodeset
    initrd (loop)/casper/initrd.lz
}

# --- 4. macOS Sonoma Installer / Recovery (64-bit) ---
# NOTE: Directly chainloading Sonoma boot.efi on MacBook 4,1 requires OCLP!
# You must build/boot OpenCore first to inject 32-to-64bit translation hooks.
menuentry "🍎 macOS Sonoma Recovery & Installer (via OCLP)" --class osx {
    set isofile="/iso/Sonoma.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop $isofile
    chainloader (loop)/System/Library/CoreServices/boot.efi
}

# --- 5. Windows BootCamp Handoff (Chainload Local Partition) ---
menuentry "🏁 Windows BootCamp (EFI / Legacy Boot)" --class windows {
    insmod ntfs
    insmod ntfscomp
    insmod chain
    # Scan all partitions for bootmgfw.efi
    search --no-floppy --set=root --file /EFI/Microsoft/Boot/bootmgfw.efi
    if [ -f ($root)/EFI/Microsoft/Boot/bootmgfw.efi ]; then
        chainloader ($root)/EFI/Microsoft/Boot/bootmgfw.efi
    elif [ -f ($root)/bootmgr ]; then
        # Fallback for legacy BIOS Windows bootmgr on Bootcamp
        ntldr ($root)/bootmgr
    else
        echo "❌ BootCamp Windows bootloader not found on local partitions."
        sleep 3
    fi
}

menuentry "💻 Reboot System" {
    reboot
}

menuentry "🔌 Shut Down" {
    halt
}
"""



def resolve_iso_source(workspace_root: Path, filename: str) -> Path:
    """Checks output, downloads, and build directories for the source ISO, resolving symlinks."""
    locations = [
        workspace_root / "iso" / "outputs" / filename,
        Path("/Users/bj90-m1/Downloads") / filename,
        workspace_root / "os" / "phoenix-os" / build_friendly_name(filename)
    ]
    
    for loc in locations:
        if loc.exists():
            resolved = loc.resolve()
            if resolved.exists() and resolved.stat().st_size > 1024 * 1024:
                return loc
    return None

def build_friendly_name(filename: str) -> str:
    if filename == "bwos-thunder-god.iso":
        return "bwos-thunder-god-arm64.iso"
    return filename

def main():
    print_banner()
    
    workspace_root = Path("/Users/bj90-m1/PhoenixCore-")
    bootloader_source = workspace_root / "bootable_usb" / "bootia32.efi"
    
    if not bootloader_source.exists():
        print(f"{RED}❌ 32-bit EFI bootloader (bootia32.efi) not found in workspace.{RESET}")
        sys.exit(1)
        
    iso_targets = {
        "bwos-aurelia.iso": "Aurelia OS (64-bit AMD64)",
        "Sonoma.iso": "macOS Sonoma Installer (64-bit)",
        "MX-23.6_fluxbox_386.iso": "MX Linux 23.6 Fluxbox (32-bit Recovery)",
        "linuxmint-22.3-xfce-64bit.iso": "Linux Mint 22.3 XFCE (64-bit Recovery)"
    }
    
    found_isos = {}
    print(f"{BLUE}🔍 Scanning for source OS and Recovery images...{RESET}")
    for filename, display_name in iso_targets.items():
        src_path = resolve_iso_source(workspace_root, filename)
        if src_path:
            resolved_path = src_path.resolve()
            size_gb = resolved_path.stat().st_size / (1024 * 1024 * 1024)
            found_isos[filename] = {
                "source": src_path,
                "resolved": resolved_path,
                "display": display_name,
                "size": f"{size_gb:.2f} GB"
            }
            print(f"   {GREEN}✓ Found {display_name}:{RESET}")
            print(f"     Path: {src_path}")
            print(f"     Size: {size_gb:.2f} GB")
        else:
            print(f"   {YELLOW}ℹ️  {display_name} not found (will be skipped).{RESET}")
            
    if not found_isos:
        print(f"\n{RED}❌ Error: No valid OS or recovery ISO files were detected.{RESET}")
        print(f"   Please make sure at least one ISO is present in /Users/bj90-m1/Downloads/")
        sys.exit(1)
        
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
    except KeyboardInterrupt:
        print(f"\n{GREEN}✓ Operation cancelled safely.{RESET}")
        sys.exit(0)
        
    print()
    print(f"{RED}{BOLD}⚠️⚠️⚠️  CRITICAL WARNING  ⚠️⚠️⚠️{RESET}")
    print(f"{RED}This will PERMANENTLY and IRREVERSIBLY ERASE ALL DATA on: {BOLD}{selected_disk}{RESET}")
    print(f"{RED}It will set up the Ventoy-style Multi-ISO recovery boot structures.{RESET}")
    print()
    
    try:
        confirm = input(f"{YELLOW}Type exactly '{BOLD}ERASE{RESET}{YELLOW}' to proceed: {RESET}").strip()
        if confirm != "ERASE":
            print(f"{GREEN}✓ Cancelled safely.{RESET}")
            sys.exit(0)
    except KeyboardInterrupt:
        print(f"\n{GREEN}✓ Operation cancelled safely.{RESET}")
        sys.exit(0)
        
    # 3. Format drive
    if not format_usb_to_ventoy_layout(selected_disk):
        sys.exit(1)
        
    # 4. Stage Files
    mount_point_aurelia = Path("/Volumes/AURELIA")
    mount_point_boot = Path("/Volumes/BOOT")
    
    # Verify mount
    if not mount_point_aurelia.exists() or not mount_point_boot.exists():
        print(f"{YELLOW}⏳ Waiting for partitions to auto-mount...{RESET}")
        time.sleep(5)
        if not mount_point_aurelia.exists() or not mount_point_boot.exists():
            print(f"{RED}❌ Drive partitions failed to auto-mount. Please unplug/replug and try again.{RESET}")
            sys.exit(1)
            
    print(f"\n{BLUE}📂 Staging recovery boot configurations onto BOOT partition...{RESET}")
    
    # Create directories
    boot_dir = mount_point_boot / "EFI" / "BOOT"
    boot_theme_dir = boot_dir / "themes" / "phoenix"
    apple_dir = mount_point_boot / "System" / "Library" / "CoreServices"
    iso_dir = mount_point_aurelia / "iso"
    
    boot_dir.mkdir(parents=True, exist_ok=True)
    boot_theme_dir.mkdir(parents=True, exist_ok=True)
    apple_dir.mkdir(parents=True, exist_ok=True)
    iso_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Copy bootloader to standard EFI path
    print(f"   🚀 Copying 32-bit EFI bootloader to /EFI/BOOT/BOOTIA32.EFI...")
    shutil.copy2(bootloader_source, boot_dir / "BOOTIA32.EFI")
    
    # 1.5. Stage custom graphical bootloader theme (unrecognizable custom GUI wrapper)
    print(f"   🎨 Copying premium graphical theme assets to /EFI/BOOT/themes/phoenix/...")
    shutil.copy2(workspace_root / "os" / "phoenix-os" / "branding" / "grub" / "phoenix" / "theme.txt", boot_theme_dir / "theme.txt")
    shutil.copy2(workspace_root / "os" / "phoenix-os" / "branding" / "grub" / "phoenix" / "background.png", boot_theme_dir / "background.png")
    
    # 2. Stage Apple Legacy Handoff (Blessing Path)
    print(f"   🍎 Copying legacy Mac bootloader to /System/Library/CoreServices/boot.efi...")
    shutil.copy2(bootloader_source, apple_dir / "boot.efi")
    
    # 3. Write SystemVersion.plist to satisfy strict Apple ROM checks
    print(f"   📄 Writing Apple boot metadata SystemVersion.plist...")
    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>ProductBuildVersion</key>
	<string>9G55</string>
	<key>ProductName</key>
	<string>Mac OS X</string>
	<key>ProductVersion</key>
	<string>10.5.8</string>
</dict>
</plist>
"""
    with open(apple_dir / "SystemVersion.plist", "w") as f:
        f.write(plist_content)
        
    # 4. Write GRUB configuration to both load directories
    print(f"   📄 Writing GRUB multi-boot configurations...")
    grub_cfg = generate_grub_config()
    with open(boot_dir / "grub.cfg", "w") as f:
        f.write(grub_cfg)
    with open(apple_dir / "grub.cfg", "w") as f:
        f.write(grub_cfg)
        
    # 3. Copy OS files to AURELIA partition (ExFAT)
    print(f"\n{BLUE}📂 Staging ISO payloads onto AURELIA (ExFAT) partition (bypassing 4GB limit)...{RESET}")
    for filename, info in found_isos.items():
        print(f"   🖥️  Copying {info['display']} ({info['size']})...")
        shutil.copy2(info["resolved"], iso_dir / filename)
        
    # 5. Stage Broadcom Offline Wireless Drivers
    drivers_dir = mount_point_aurelia / "drivers" / "broadcom"
    drivers_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{BLUE}📶 Staging offline Broadcom BCM4321 Wi-Fi driver package dependencies...{RESET}")
    
    # Write custom installer script to Partition 2
    installer_script = """#!/bin/bash
# install_broadcom_firmware.sh - Automatically installs offline Broadcom BCM4321 wireless firmware
set -e

echo "📶 Initializing Offline Broadcom BCM4321 Wi-Fi Driver Setup..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if broadcom-wl tarball exists
TARBALL="$SCRIPT_DIR/broadcom-wl-5.100.138.tar.bz2"
if [ ! -f "$TARBALL" ]; then
    echo "❌ Error: broadcom-wl-5.100.138.tar.bz2 not found in $SCRIPT_DIR!"
    exit 1
fi

# Ensure b43-fwcutter is installed (or extract firmware using pre-packaged offline debs)
echo "📦 Installing b43-fwcutter offline..."
sudo dpkg -i "$SCRIPT_DIR"/b43-fwcutter_*.deb || true
sudo apt-get install -f -y || true

# Extract firmware
echo "📂 Extracting Broadcom firmware..."
rm -rf /tmp/b43-extract
mkdir -p /tmp/b43-extract
tar -xjf "$TARBALL" -C /tmp/b43-extract

echo "⚙️  Cutting Broadcom firmware and moving to /lib/firmware/b43/..."
sudo mkdir -p /lib/firmware
sudo b43-fwcutter -w /lib/firmware /tmp/b43-extract/broadcom-wl-5.100.138/linux/wl_apsta.o

# Load module
echo "🔌 Loading b43 kernel module..."
sudo modprobe -r b43 || true
sudo modprobe b43

echo "🎉 Wi-Fi driver successfully installed and loaded! Your wireless networks should now be visible."
"""
    with open(drivers_dir / "install.sh", "w") as f:
        f.write(installer_script)
    os.chmod(drivers_dir / "install.sh", 0o755)
    
    # Download files dynamically
    downloads = {
        "b43-fwcutter_019-4+b1_amd64.deb": "http://ftp.de.debian.org/debian/pool/main/b/b43-fwcutter/b43-fwcutter_019-4+b1_amd64.deb",
        "broadcom-wl-5.100.138.tar.bz2": "https://www.lwfinger.com/b43-firmware/broadcom-wl-5.100.138.tar.bz2"
    }
    
    for filename, url in downloads.items():
        target_path = drivers_dir / filename
        if target_path.exists():
            print(f"   {GREEN}✓ {filename} already exists (skipping download).{RESET}")
            continue
            
        print(f"   📥 Downloading offline driver resource: {filename}...")
        try:
            # Add user-agent header to prevent HTTP 403 Forbidden errors
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            )
            with urllib.request.urlopen(req, timeout=15) as response, open(target_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            print(f"     {GREEN}✓ Successfully downloaded {filename}!{RESET}")
        except Exception as e:
            print(f"     {YELLOW}⚠️  Could not pre-download offline resource {filename}: {e}{RESET}")
            print(f"     {YELLOW}   (You can still manually download it to Partition 2 under /drivers/broadcom/ later if needed.){RESET}")
        
    print(f"\n{GREEN}🎉 Success! Your Ventoy-style Multi-ISO & Recovery USB is ready!{RESET}")
    print(f"{BLUE}🔌 Ejecting drive...{RESET}")
    subprocess.run(["diskutil", "eject", selected_disk], capture_output=True)
    print(f"{GREEN}✓ Safe to remove. Plug the USB into your MacBook 4,1,{RESET}")
    print(f"{GREEN}  hold down OPTION (Alt) while booting, select 'EFI Boot', and launch any system!{RESET}")

if __name__ == "__main__":
    main()
