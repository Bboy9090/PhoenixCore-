#!/usr/bin/env python3
"""
Phoenix Core - Virtual Testing Suite for Legacy and Modern Platforms
Launches the QEMU emulator on macOS to live-test your recovery ISOs,
emulating either legacy x86_64 Penryn CPUs or native ARM64 Apple Silicon virtue systems.
"""

import sys
import os
import subprocess
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
    print(f"{BLUE}│{RESET} {CYAN}{BOLD}Phoenix OS - Multi-Platform QEMU Testing Suite{RESET}          {BLUE}│{RESET}")
    print(f"{BLUE}│{RESET} Live-Test ISOs on ARM64 or x86_64 Penryn CPU Emulators  {BLUE}│{RESET}")
    print(f"{BLUE}└────────────────────────────────────────────────────────┘{RESET}")
    print()

def resolve_iso_source(workspace_root: Path, filename: str) -> Path:
    locations = [
        workspace_root / "iso" / "outputs" / filename,
        Path("/Users/bj90-m1/Downloads") / filename,
        workspace_root / "os" / "phoenix-os" / "build" / filename,
        workspace_root / "os" / "phoenix-os" / "build" / build_friendly_name(filename)
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
    
    # 1. Choose Virtualization Target Profile
    print(f"{BLUE}Select Virtual Emulation Mode:{RESET}")
    print(f"   {BOLD}1. Legacy Intel Mac / PC (x86_64 - Penryn CPU / 32-bit EFI Bridge){RESET}")
    print(f"   {BOLD}2. Apple Silicon / ARM64 (arm64 - Cortex-A57 CPU / virt board){RESET}")
    print()
    
    try:
        mode_choice = input(f"{YELLOW}Select target mode (1-2) [default: 1]: {RESET}").strip()
        if not mode_choice or mode_choice == "1":
            target_mode = "x86_64"
            qemu_bin = "/opt/homebrew/bin/qemu-system-x86_64"
        elif mode_choice == "2":
            target_mode = "arm64"
            qemu_bin = "/opt/homebrew/bin/qemu-system-aarch64"
        else:
            print(f"{RED}❌ Invalid selection.{RESET}")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{GREEN}✓ Test cancelled safely.{RESET}")
        sys.exit(0)
        
    if not os.path.exists(qemu_bin):
        print(f"{RED}❌ QEMU binary not found at {qemu_bin}. Please install QEMU using brew first.{RESET}")
        sys.exit(1)
        
    # Build list based on target mode
    if target_mode == "x86_64":
        iso_targets = {
            "bwos-aurelia.iso": "Aurelia OS (64-bit AMD64)",
            "Sonoma.iso": "macOS Sonoma Installer (64-bit)",
            "MX-23.6_fluxbox_386.iso": "MX Linux 23.6 Fluxbox (32-bit)",
            "linuxmint-22.3-xfce-64bit.iso": "Linux Mint 22.3 XFCE (64-bit)"
        }
    else:
        # arm64 ISO targets
        iso_targets = {
            "bwos-aurelia-arm64.iso": "Aurelia OS (64-bit ARM64)",
            "bwos-thunder-god-arm64.iso": "Thundergod OS (64-bit ARM64)"
        }
        
    found_isos = []
    print(f"\n{BLUE}🔍 Scanning for available test {target_mode} ISO images...{RESET}")
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
        print(f"\n{RED}❌ Error: No valid {target_mode} recovery ISO files were detected in Downloads or outputs.{RESET}")
        print(f"   (Please compile target '{target_mode}' images or place them in Downloads first!){RESET}")
        sys.exit(1)
        
    print(f"{GREEN}✓ Found bootable ISOs:{RESET}")
    for i, iso in enumerate(found_isos, 1):
        print(f"   {BOLD}{i}. {iso['display']}{RESET} - {iso['size']} ({iso['filename']})")
        
    print()
    try:
        choice = input(f"{YELLOW}Select the ISO number to boot (1-{len(found_isos)}): {RESET}").strip()
        if not choice:
            sys.exit(0)
        idx = int(choice) - 1
        if idx < 0 or idx >= len(found_isos):
            print(f"{RED}❌ Invalid selection.{RESET}")
            sys.exit(1)
        selected_iso = found_isos[idx]
    except (ValueError, IndexError):
        print(f"{RED}❌ Invalid selection.{RESET}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{GREEN}✓ Test cancelled safely.{RESET}")
        sys.exit(0)
        
    print(f"\n{BLUE}🚀 Launching QEMU with {selected_iso['display']}...{RESET}")
    
    # QEMU configurations based on architecture mode
    if target_mode == "x86_64":
        print(f"{YELLOW}ℹ️  Emulating 2.4GHz Intel Core 2 Duo Penryn (MacBook 4,1 CPU)...{RESET}")
        print(f"   Memory: 2048 MB")
        print(f"   Display: Native Cocoa GUI")
        qemu_cmd = [
            qemu_bin,
            "-m", "2048",
            "-smp", "2",
            "-cpu", "Penryn",
            "-cdrom", str(selected_iso["resolved"]),
            "-boot", "d",
            "-vga", "virtio",
            "-device", "intel-hda", "-device", "hda-duplex",
            "-display", "cocoa"
        ]
    else:
        print(f"{YELLOW}ℹ️  Emulating ARM64 System (Cortex-A57 virtue board)...{RESET}")
        print(f"   Memory: 2048 MB")
        print(f"   Display: Native Cocoa GUI")
        # Standard ARM64 Virt board booting directly
        qemu_cmd = [
            qemu_bin,
            "-m", "2048",
            "-smp", "2",
            "-M", "virt",
            "-cpu", "cortex-a57",
            "-device", "virtio-gpu-pci",
            "-device", "qemu-xhci",
            "-device", "usb-kbd", "-device", "usb-tablet",
            "-drive", f"if=pflash,format=raw,readonly=on,file=/opt/homebrew/share/qemu/edk2-aarch64-code.fd",
            "-cdrom", str(selected_iso["resolved"]),
            "-display", "cocoa"
        ]
        
    print(f"   Close the QEMU window or press Ctrl+C in terminal to stop.")
    
    try:
        subprocess.run(qemu_cmd, check=True)
        print(f"\n{GREEN}🎉 QEMU session closed successfully.{RESET}")
    except KeyboardInterrupt:
        print(f"\n{GREEN}✓ QEMU session terminated by user.{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"\n{RED}❌ QEMU failed with exit code: {e.returncode}{RESET}")

if __name__ == "__main__":
    main()

