#!/usr/bin/env python3
"""
Phoenix Core - MacBook 4,1 64-bit Multi-Boot USB Creator
Creates a premium, standard MBR FAT32 multi-boot drive containing:
1. Aurelia OS (64-bit AMD64)
2. Arcwyre OS (64-bit AMD64)
3. Arcwyre: Thundergod Edition (64-bit AMD64)

Utilizes a custom 32-bit EFI GRUB loopback boot loader to boot 64-bit OS editions.
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
    print(f"{BLUE}│{RESET} {CYAN}{BOLD}Aurelia/Arcwyre - MacBook 4,1 Multi-Boot Creator{RESET}       {BLUE}│{RESET}")
    print(f"{BLUE}│{RESET} Premium 64-bit OS Mixed-Mode Deployment Suite           {BLUE}│{RESET}")
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
    """Generates a premium GRUB loopback configuration for 32-bit EFI to 64-bit OS booting."""
    return """# GRUB 32-bit EFI Mixed-Mode Multi-Boot Configuration
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

# Standard 64-bit kernels inside live-build ISO are vmlinuz-5.10.0-43-amd64
# We provide primary and fallback entries to ensure robust booting

menuentry "⚡ Phoenix OS: Aurelia Edition (64-bit Live)" --class phoenix {
    set isofile="/iso/bwos-aurelia.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop $isofile
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

menuentry "⚡ Phoenix OS: Arcwyre Edition (64-bit Live)" --class arcwyre {
    set isofile="/iso/bwos-arcwyre.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop $isofile
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

menuentry "⚡ Phoenix OS: Thundergod Edition (64-bit Live)" --class thunder {
    set isofile="/iso/bwos-thunder-god.iso"
    search --no-floppy --set=root --file $isofile
    loopback loop $isofile
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
            # Resolve symlinks to find the actual target file if applicable
            resolved = loc.resolve()
            if resolved.exists() and resolved.stat().st_size > 1024 * 1024: # Must be larger than 1MB
                return loc
                
    return None

def build_friendly_name(filename: str) -> str:
    """Maps custom target file to build outputs."""
    if filename == "bwos-thunder-god.iso":
        return "bwos-thunder-god-arm64.iso" # arm64 build variant helper
    return filename

def main():
    print_banner()
    
    workspace_root = Path("/Users/bj90-m1/PhoenixCore-")
    bootloader_source = workspace_root / "bootable_usb" / "bootia32.efi"
    
    if not bootloader_source.exists():
        print(f"{RED}❌ 32-bit EFI bootloader (bootia32.efi) not found in workspace.{RESET}")
        sys.exit(1)
        
    # Define our targets
    iso_targets = {
        "bwos-aurelia.iso": "Aurelia OS (64-bit)",
        "bwos-arcwyre.iso": "Arcwyre OS (64-bit)",
        "bwos-thunder-god.iso": "Thundergod Edition (64-bit)"
    }
    
    found_isos = {}
    print(f"{BLUE}🔍 Scanning for source OS images...{RESET}")
    for filename, display_name in iso_targets.items():
        src_path = resolve_iso_source(workspace_root, filename)
        if src_path:
            # Check size
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
            if src_path != resolved_path:
                print(f"     Resolved Symlink: {resolved_path}")
            print(f"     Size: {size_gb:.2f} GB")
        else:
            print(f"   {YELLOW}ℹ️  {display_name} not found in workspace (staged config ready).{RESET}")
            
    if not found_isos:
        print(f"\n{RED}❌ Error: No valid 64-bit OS image files were detected.{RESET}")
        print(f"   Please make sure at least one ISO is built or placed at: ")
        print(f"   - /Users/bj90-m1/Downloads/bwos-aurelia.iso")
        print(f"   - /Users/bj90-m1/PhoenixCore-/iso/outputs/bwos-aurelia.iso")
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
    print(f"{RED}It will be formatted as a single MBR FAT32 boot drive.{RESET}")
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
    print(f"   📄 Writing GRUB mixed-mode multi-boot configuration...")
    grub_cfg = generate_grub_config()
    with open(boot_dir / "grub.cfg", "w") as f:
        f.write(grub_cfg)
        
    # 3. Copy OS files
    for filename, info in found_isos.items():
        print(f"   🖥️  Copying {info['display']} ({info['size']})...")
        shutil.copy2(info["resolved"], iso_dir / filename)
        
    print(f"\n{GREEN}🎉 Success! Your MacBook 4,1 Mixed-Mode Multi-Boot USB is ready!{RESET}")
    print(f"{BLUE}🔌 Ejecting AURELIA...{RESET}")
    subprocess.run(["diskutil", "eject", selected_disk], capture_output=True)
    print(f"{GREEN}✓ Safe to remove. Plug the USB into your MacBook 4,1,{RESET}")
    print(f"{GREEN}  hold down OPTION (Alt) while booting, select 'EFI Boot', and launch your premium OS!{RESET}")

if __name__ == "__main__":
    main()
