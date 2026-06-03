#!/usr/bin/env python3
"""
Phoenix Core - Universal Ventoy-style Multi-ISO & Recovery USB Creator
Natively formats a USB drive with GPT FAT32 and stages both 32-bit and 64-bit
EFI GRUB bootloaders to support Dell Chromebook 11, iMac 15,1, MacBook Air 4,1,
legacy MacBook 4,1, and other x86_64 UEFI/BIOS systems.
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
    print(f"{BLUE}│{RESET} {CYAN}{BOLD}Aurelia/Arcwyre - Universal Multi-Boot USB Creator{RESET}     {BLUE}│{RESET}")
    print(f"{BLUE}│{RESET} Premium Mixed 32/64-Bit EFI Multi-OS Deployment Suite   {BLUE}│{RESET}")
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

def format_usb_to_universal_layout(disk_path: str):
    """Formats the selected drive using GPT FAT32 for universal compatibility."""
    print(f"\n{BLUE}🔄 Preparing drive {disk_path}...{RESET}")
    try:
        subprocess.run(["diskutil", "unmountDisk", "force", disk_path], check=True)
        
        print(f"{YELLOW}⏳ Settling disk state...{RESET}")
        time.sleep(2)
        
        subprocess.run(["diskutil", "unmountDisk", "force", disk_path], check=False)
        
        print(f"{BLUE}🔄 Partitioning disk with GUID Partition Table (GPT) and single FAT32 volume (AURELIA)...{RESET}")
        subprocess.run([
            "diskutil", "partitionDisk", disk_path, "1", "GPT", 
            "MS-DOS FAT32", "AURELIA", "R"
        ], check=True)
        
        print(f"{GREEN}✓ Disk partitioned successfully with GPT FAT32!{RESET}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{RED}❌ Failed to partition disk: {e}{RESET}")
        return False

def generate_grub_config() -> str:
    """Generates a premium GRUB loopback configuration supporting 32-bit and 64-bit EFI boot loading."""
    return """# GRUB Universal Multi-Boot Configuration
# Supports both 32-bit and 64-bit UEFI firmware targets
# Optimized for Chromebook 11, iMac 15,1, Air 4,1, and Legacy MacBook 4,1

set timeout=15
set default=0

# Graphics Terminal & Theme Setup
insmod part_gpt
insmod part_msdos
insmod fat
insmod loopback
insmod normal
insmod video
insmod video_fb
insmod gfxterm
insmod gfxmenu

# Load the custom premium Aurelia theme if present
set theme=($root)/EFI/BOOT/themes/phoenix/theme.txt

set gfxmode=auto
terminal_output gfxterm

# Premium Visual Color Accents (fallback)
set menu_color_normal=white/black
set menu_color_highlight=yellow/blue

# --- 1. Home Aurelia Edition (32-bit/64-bit Mixed-Mode) ---
menuentry "🔥 Phoenix OS: Home Aurelia Edition (32-bit/64-bit)" --class phoenix {
    set isofile="/iso/bwos-home.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop ($root)$isofile
    if [ -f (loop)/live/vmlinuz-5.10.0-44-amd64 ]; then
        linux (loop)/live/vmlinuz-5.10.0-44-amd64 boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img-5.10.0-44-amd64
    elif [ -f (loop)/live/vmlinuz-5.10.0-43-amd64 ]; then
        linux (loop)/live/vmlinuz-5.10.0-43-amd64 boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img-5.10.0-43-amd64
    else
        linux (loop)/live/vmlinuz boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img
    fi
}

# --- 2. Aurelia OS (64-bit) ---
menuentry "🔥 Phoenix OS: Aurelia OS (64-bit)" --class phoenix {
    set isofile="/iso/bwos-aurelia.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop ($root)$isofile
    if [ -f (loop)/live/vmlinuz-5.10.0-44-amd64 ]; then
        linux (loop)/live/vmlinuz-5.10.0-44-amd64 boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img-5.10.0-44-amd64
    elif [ -f (loop)/live/vmlinuz-5.10.0-43-amd64 ]; then
        linux (loop)/live/vmlinuz-5.10.0-43-amd64 boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img-5.10.0-43-amd64
    else
        linux (loop)/live/vmlinuz boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img
    fi
}

# --- 3. Thundergod Edition (64-bit) ---
menuentry "⚡ Phoenix OS: Thundergod Edition (64-bit)" --class thunder {
    set isofile="/iso/bwos-thunder-god.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop ($root)$isofile
    if [ -f (loop)/live/vmlinuz-5.10.0-44-amd64 ]; then
        linux (loop)/live/vmlinuz-5.10.0-44-amd64 boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img-5.10.0-44-amd64
    elif [ -f (loop)/live/vmlinuz-5.10.0-43-amd64 ]; then
        linux (loop)/live/vmlinuz-5.10.0-43-amd64 boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img-5.10.0-43-amd64
    else
        linux (loop)/live/vmlinuz boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img
    fi
}

# --- 4. Blue Phoenix (Native) ---
menuentry "❄️ Phoenix OS: Blue Phoenix (Native)" --class native {
    set isofile="/iso/bwos-blue-phoenix.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop ($root)$isofile
    if [ -f (loop)/live/vmlinuz-5.10.0-44-amd64 ]; then
        linux (loop)/live/vmlinuz-5.10.0-44-amd64 boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img-5.10.0-44-amd64
    elif [ -f (loop)/live/vmlinuz-5.10.0-43-amd64 ]; then
        linux (loop)/live/vmlinuz-5.10.0-43-amd64 boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img-5.10.0-43-amd64
    else
        linux (loop)/live/vmlinuz boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img
    fi
}

# --- 5. Arcwyre OS (64-bit) ---
menuentry "⚡ Phoenix OS: Arcwyre OS (64-bit)" --class arcwyre {
    set isofile="/iso/bwos-arcwyre.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop ($root)$isofile
    if [ -f (loop)/live/vmlinuz-5.10.0-44-amd64 ]; then
        linux (loop)/live/vmlinuz-5.10.0-44-amd64 boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img-5.10.0-44-amd64
    elif [ -f (loop)/live/vmlinuz-5.10.0-43-amd64 ]; then
        linux (loop)/live/vmlinuz-5.10.0-43-amd64 boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img-5.10.0-43-amd64
    else
        linux (loop)/live/vmlinuz boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
        initrd (loop)/live/initrd.img
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

def robust_copy(src: Path, dst: Path):
    """Copies a file using native cp command-line tool to bypass Python shutil fcopyfile bugs on macOS."""
    try:
        subprocess.run(["cp", str(src), str(dst)], check=True)
    except Exception:
        with open(src, "rb") as fsrc:
            with open(dst, "wb") as fdst:
                while True:
                    buf = fsrc.read(64 * 1024 * 1024)
                    if not buf:
                        break
                    fdst.write(buf)

def main():
    print_banner()
    
    workspace_root = Path("/Users/bj90-m1/PhoenixCore-")
    
    # 64-bit and 32-bit loaders
    bootia32_source = workspace_root / "bootable_usb" / "bootia32.efi"
    bootx64_source = workspace_root / "bootable_usb" / "bootx64.efi"
    grubx64_source = workspace_root / "bootable_usb" / "grubx64.efi"
    
    if not bootia32_source.exists():
        print(f"{RED}❌ 32-bit EFI bootloader (bootia32.efi) not found in workspace.{RESET}")
        sys.exit(1)
        
    if not bootx64_source.exists() or not grubx64_source.exists():
        print(f"{RED}❌ 64-bit EFI bootloaders (bootx64.efi / grubx64.efi) not found in workspace.{RESET}")
        sys.exit(1)
        
    iso_targets = {
        "bwos-home.iso": "Home Aurelia Edition (32-bit/64-bit)",
        "bwos-aurelia.iso": "Aurelia OS (64-bit)",
        "bwos-thunder-god.iso": "Thundergod Edition (64-bit)",
        "bwos-blue-phoenix.iso": "Blue Phoenix (Native)",
        "bwos-arcwyre.iso": "Arcwyre OS (64-bit)"
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
        sys.exit(1)
        
    print()
    
    # Scan and list external drives
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
    print(f"{RED}It will format to Universal GPT FAT32 layout and stage recovery loaders.{RESET}")
    print()
    
    try:
        confirm = input(f"{YELLOW}Type exactly '{BOLD}ERASE{RESET}{YELLOW}' to proceed: {RESET}").strip()
        if confirm != "ERASE":
            print(f"{GREEN}✓ Cancelled safely.{RESET}")
            sys.exit(0)
    except KeyboardInterrupt:
        print(f"\n{GREEN}✓ Operation cancelled safely.{RESET}")
        sys.exit(0)
        
    # Format drive
    if not format_usb_to_universal_layout(selected_disk):
        sys.exit(1)
        
    # Stage Files
    mount_point_aurelia = Path("/Volumes/AURELIA")
    
    # Verify mount
    if not mount_point_aurelia.exists():
        print(f"{YELLOW}⏳ Waiting for partition to auto-mount...{RESET}")
        time.sleep(5)
        if not mount_point_aurelia.exists():
            print(f"{RED}❌ Drive partition failed to auto-mount. Please unplug/replug and try again.{RESET}")
            sys.exit(1)
            
    print(f"\n{BLUE}📂 Staging recovery boot configurations onto AURELIA partition...{RESET}")
    
    # Create directories
    boot_dir = mount_point_aurelia / "EFI" / "BOOT"
    boot_theme_dir = boot_dir / "themes" / "phoenix"
    apple_dir = mount_point_aurelia / "System" / "Library" / "CoreServices"
    iso_dir = mount_point_aurelia / "iso"
    
    boot_dir.mkdir(parents=True, exist_ok=True)
    boot_theme_dir.mkdir(parents=True, exist_ok=True)
    apple_dir.mkdir(parents=True, exist_ok=True)
    iso_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy both 32-bit and 64-bit loaders to Standard EFI path
    print(f"   🚀 Copying 64-bit UEFI bootloader (grubx64.efi directly to BOOTX64.EFI)...")
    shutil.copy2(grubx64_source, boot_dir / "BOOTX64.EFI")
    shutil.copy2(grubx64_source, boot_dir / "grubx64.efi")
    
    print(f"   🚀 Copying 32-bit EFI bootloader (BOOTIA32.EFI)...")
    shutil.copy2(bootia32_source, boot_dir / "BOOTIA32.EFI")
    
    # Copy graphical themes
    print(f"   🎨 Copying and patching premium graphical theme assets to /EFI/BOOT/themes/phoenix/...")
    theme_tmpl_path = workspace_root / "os" / "phoenix-os" / "branding" / "grub" / "phoenix" / "theme.txt"
    if theme_tmpl_path.exists():
        with open(theme_tmpl_path, "r") as f:
            theme_content = f.read()
        
        theme_content = theme_content.replace("__COLOR_BACKGROUND__", "#05070A")
        theme_content = theme_content.replace("__COLOR_PRIMARY__", "#D4AF37")
        theme_content = theme_content.replace("__COLOR_SURFACE__", "#101827")
        theme_content = theme_content.replace("__COLOR_TEXT__", "#F8FAFC")
        theme_content = theme_content.replace("__EDITION_NAME__", "Phoenix OS: Aurelia Suite")
        theme_content = theme_content.replace("__EDITION_TAGLINE__", "Universal UEFI & Legacy Edition")
        
        with open(boot_theme_dir / "theme.txt", "w") as f:
            f.write(theme_content)
            
    background_png = workspace_root / "os" / "phoenix-os" / "branding" / "grub" / "phoenix" / "background.png"
    if background_png.exists():
        shutil.copy2(background_png, boot_theme_dir / "background.png")
    
    # Stage Apple Legacy Handoff (Blessing Path)
    print(f"   🍎 Copying legacy Mac bootloader to /System/Library/CoreServices/boot.efi...")
    shutil.copy2(bootia32_source, apple_dir / "boot.efi")
    
    # Write SystemVersion.plist to satisfy strict Apple ROM checks
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
        
    # Write GRUB configurations
    print(f"   📄 Writing GRUB multi-boot configurations...")
    grub_cfg = generate_grub_config()
    with open(boot_dir / "grub.cfg", "w") as f:
        f.write(grub_cfg)
    with open(apple_dir / "grub.cfg", "w") as f:
        f.write(grub_cfg)
        
    # Copy OS files to AURELIA partition
    print(f"\n{BLUE}📂 Staging ISO payloads onto AURELIA partition...{RESET}")
    for filename, info in found_isos.items():
        print(f"   🖥️  Copying {info['display']} ({info['size']})...")
        robust_copy(info["resolved"], iso_dir / filename)
        
    # Stage Broadcom Offline Wireless Drivers
    drivers_dir = mount_point_aurelia / "drivers" / "broadcom"
    drivers_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{BLUE}📶 Staging offline Broadcom BCM4321 Wi-Fi driver package dependencies...{RESET}")
    
    installer_script = """#!/bin/bash
# install_broadcom_firmware.sh - Automatically installs offline Broadcom BCM4321 wireless firmware
set -e

echo "📶 Initializing Offline Broadcom BCM4321 Wi-Fi Driver Setup..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TARBALL="$SCRIPT_DIR/broadcom-wl-5.100.138.tar.bz2"
if [ ! -f "$TARBALL" ]; then
    echo "❌ Error: broadcom-wl-5.100.138.tar.bz2 not found in $SCRIPT_DIR!"
    exit 1
fi

echo "📦 Installing b43-fwcutter offline..."
sudo dpkg -i "$SCRIPT_DIR"/b43-fwcutter_*.deb || true
sudo apt-get install -f -y || true

echo "📂 Extracting Broadcom firmware..."
rm -rf /tmp/b43-extract
mkdir -p /tmp/b43-extract
tar -xjf "$TARBALL" -C /tmp/b43-extract

echo "⚙️  Cutting Broadcom firmware and moving to /lib/firmware/b43/..."
sudo mkdir -p /lib/firmware
sudo b43-fwcutter -w /lib/firmware /tmp/b43-extract/broadcom-wl-5.100.138/linux/wl_apsta.o

echo "🔌 Loading b43 kernel module..."
sudo modprobe -r b43 || true
sudo modprobe b43

echo "🎉 Wi-Fi driver successfully installed and loaded! Your wireless networks should now be visible."
"""
    with open(drivers_dir / "install.sh", "w") as f:
        f.write(installer_script)
    os.chmod(drivers_dir / "install.sh", 0o755)
    
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
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            )
            with urllib.request.urlopen(req, timeout=15) as response, open(target_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            print(f"     {GREEN}✓ Successfully downloaded {filename}!{RESET}")
        except Exception as e:
            print(f"     {YELLOW}⚠️  Could not pre-download offline resource {filename}: {e}{RESET}")
        
    print(f"\n{GREEN}🎉 Success! Your Universal Multi-ISO & Recovery USB files have been staged!{RESET}")
    print(f"{GREEN}   Ready to be plugged into iMac 15,1, Air 4,1, Dell Chromebook 11, or legacy MacBook 4,1.{RESET}")

if __name__ == "__main__":
    main()
