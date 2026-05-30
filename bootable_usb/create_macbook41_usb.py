#!/usr/bin/env python3
"""
Phoenix Core - MacBook 4,1 64-bit Single-Edition USB Creator
Natively formats and safely writes a premium 64-bit OS image
(Aurelia OS, Arcwyre, or Thundergod Edition) for 32-bit EFI booting.
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
    print(f"{BLUE}│{RESET} {CYAN}{BOLD}Aurelia/Arcwyre - MacBook 4,1 USB Flasher{RESET}             {BLUE}│{RESET}")
    print(f"{BLUE}│{RESET} Safe & Professional Single-Edition Deployment Tool      {BLUE}│{RESET}")
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
        subprocess.run(["diskutil", "unmountDisk", "force", disk_path], check=True)
        raw_disk = disk_path.replace("/dev/disk", "/dev/rdisk")
        print(f"{YELLOW}⚡ Wiping legacy partition structures on {raw_disk}... (requires sudo){RESET}")
        subprocess.run(["sudo", "dd", "if=/dev/zero", f"of={raw_disk}", "bs=1m", "count=32"], check=True)
        
        print(f"{YELLOW}⏳ Settling disk state...{RESET}")
        time.sleep(3)
        
        subprocess.run(["diskutil", "unmountDisk", "force", disk_path], check=False)
        
        print(f"{BLUE}🔄 Formatting disk as standard MBR FAT32 (Volume: AURELIA)...{RESET}")
        subprocess.run([
            "diskutil", "eraseDisk", "FAT32", "AURELIA", "MBR", disk_path
        ], check=True)
        
        print(f"{GREEN}✓ Disk formatted successfully as standard MBR FAT32 (Volume: AURELIA).{RESET}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{RED}❌ Failed to format disk: {e}{RESET}")
        return False

def generate_grub_config(iso_name: str, display_name: str) -> str:
    """Generates a premium GRUB loopback configuration for a single selected OS."""
    return f"""# GRUB 32-bit EFI Mixed-Mode Configuration
# Aligned to premium visual direction (Dark Navy / Electric Blue / Gold)

set timeout=5
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

menuentry "⚡ Phoenix OS: {display_name} (64-bit Live)" --class phoenix {{
    set isofile="/iso/{iso_name}"
    search --no-floppy --set=root --file $isofile
    loopback loop $isofile
    linux (loop)/live/vmlinuz-5.10.0-43-amd64 boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
    initrd (loop)/live/initrd.img-5.10.0-43-amd64
}}

menuentry "⚡ Phoenix OS: {display_name} (64-bit Live - Legacy Kernel Fallback)" --class phoenix {{
    set isofile="/iso/{iso_name}"
    search --no-floppy --set=root --file $isofile
    loopback loop $isofile
    linux (loop)/live/vmlinuz boot=live components findiso=$isofile quiet splash username=phoenix bwos.session=wayland console=tty0
    initrd (loop)/live/initrd.img
}}

menuentry "💻 Reboot System" {{
    reboot
}}

menuentry "🔌 Shut Down" {{
    halt
}}
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
        "bwos-aurelia.iso": "Aurelia OS (64-bit)",
        "bwos-arcwyre.iso": "Arcwyre OS (64-bit)",
        "bwos-thunder-god.iso": "Thundergod Edition (64-bit)"
    }
    
    found_isos = []
    print(f"{BLUE}🔍 Scanning for source OS images...{RESET}")
    for filename, display_name in iso_targets.items():
        src_path = resolve_iso_source(workspace_root, filename)
        if src_path:
            resolved_path = src_path.resolve()
            size_gb = resolved_path.stat().st_size / (1024 * 1024 * 1024)
            found_isos.append({
                "filename": filename,
                "source": src_path,
                "resolved": resolved_path,
                "display": display_name,
                "size": f"{size_gb:.2f} GB"
            })
            
    if not found_isos:
        print(f"\n{RED}❌ Error: No valid 64-bit OS image files were detected.{RESET}")
        print(f"   Please make sure at least one ISO is built or placed at: ")
        print(f"   - /Users/bj90-m1/Downloads/bwos-aurelia.iso")
        sys.exit(1)
        
    print(f"{GREEN}✓ Detected OS images:{RESET}")
    for i, iso in enumerate(found_isos, 1):
        print(f"   {BOLD}{i}. {iso['display']}{RESET} - {iso['size']} ({iso['filename']})")
        
    print()
    try:
        os_choice = input(f"{YELLOW}Select the OS number to flash (1-{len(found_isos)}): {RESET}").strip()
        if not os_choice:
            sys.exit(0)
        os_idx = int(os_choice) - 1
        selected_os = found_isos[os_idx]
    except (ValueError, IndexError):
        print(f"{RED}❌ Invalid selection.{RESET}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{GREEN}✓ Operation cancelled safely.{RESET}")
        sys.exit(0)
        
    print(f"\n{BLUE}🔍 Scanning for connected USB/SD drives...{RESET}")
    disks = get_connected_disks()
    
    if not disks:
        print(f"{YELLOW}⚠️  No external drives detected.{RESET}")
        sys.exit(0)
        
    print(f"{GREEN}✓ Detected external drives:{RESET}")
    for i, disk in enumerate(disks, 1):
        print(f"   {BOLD}{i}. {disk['path']}{RESET} - {disk['description']}")
        
    print()
    try:
        drive_choice = input(f"{YELLOW}Select the drive number (1-{len(disks)}): {RESET}").strip()
        if not drive_choice:
            sys.exit(0)
        drive_idx = int(drive_choice) - 1
        selected_disk = disks[drive_idx]["path"]
    except (ValueError, IndexError):
        print(f"{RED}❌ Invalid selection.{RESET}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{GREEN}✓ Operation cancelled safely.{RESET}")
        sys.exit(0)
        
    print()
    print(f"{RED}{BOLD}⚠️⚠️⚠️  CRITICAL WARNING  ⚠️⚠️⚠️{RESET}")
    print(f"{RED}This will PERMANENTLY and IRREVERSIBLY ERASE ALL DATA on: {BOLD}{selected_disk}{RESET}")
    print(f"{RED}It will flash {selected_os['display']} onto this drive.{RESET}")
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
    if not format_usb_to_mbr_fat32(selected_disk):
        sys.exit(1)
        
    # Stage Files
    mount_point = Path("/Volumes/AURELIA")
    
    if not mount_point.exists():
        print(f"{YELLOW}⏳ Waiting for drive to auto-mount...{RESET}")
        time.sleep(3)
        if not mount_point.exists():
            print(f"{RED}❌ Drive failed to auto-mount.{RESET}")
            sys.exit(1)
            
    print(f"\n{BLUE}📂 Staging files onto AURELIA partition...{RESET}")
    
    boot_dir = mount_point / "EFI" / "BOOT"
    iso_dir = mount_point / "iso"
    
    boot_dir.mkdir(parents=True, exist_ok=True)
    iso_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Copy bootloader
    print(f"   🚀 Copying 32-bit EFI bootloader to /EFI/BOOT/BOOTIA32.EFI...")
    shutil.copy2(bootloader_source, boot_dir / "BOOTIA32.EFI")
    
    # 2. Write GRUB configuration
    print(f"   📄 Writing GRUB single-OS configuration...")
    grub_cfg = generate_grub_config(selected_os["filename"], selected_os["display"])
    with open(boot_dir / "grub.cfg", "w") as f:
        f.write(grub_cfg)
        
    # 3. Copy OS files
    print(f"   🖥️  Copying {selected_os['display']} ({selected_os['size']})...")
    shutil.copy2(selected_os["resolved"], iso_dir / selected_os["filename"])
    
    print(f"\n{GREEN}🎉 Success! Your MacBook 4,1 Single-Edition USB is ready!{RESET}")
    print(f"{BLUE}🔌 Ejecting AURELIA...{RESET}")
    subprocess.run(["diskutil", "eject", selected_disk], capture_output=True)
    print(f"{GREEN}✓ Safe to remove. Plug the USB into your MacBook 4,1,{RESET}")
    print(f"{GREEN}  hold down OPTION (Alt) while booting, select 'EFI Boot', and run!{RESET}")

if __name__ == "__main__":
    main()
