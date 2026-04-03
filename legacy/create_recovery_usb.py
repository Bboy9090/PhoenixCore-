
#!/usr/bin/env python3
"""
BootForge Tools USB Creator
Creates a USB with BootForge application and tools (NOT a bootable macOS installer)
"""

import os
import sys
from pathlib import Path

def print_important_info():
    """Print critical information about USB types"""
    print("\n" + "=" * 70)
    print("⚠️  IMPORTANT: UNDERSTAND THE DIFFERENCE")
    print("=" * 70)
    print()
    print("There are TWO types of USBs:")
    print()
    print("1️⃣  BOOTFORGE TOOLS USB (This script)")
    print("   - Contains BootForge application")
    print("   - Run FROM WITHIN macOS (not bootable)")
    print("   - Use to CREATE bootable Mac installers")
    print()
    print("2️⃣  BOOTABLE MACOS INSTALLER USB (Use BootForge GUI)")
    print("   - Actually bootable Mac installer")
    print("   - Can install/reinstall macOS")
    print("   - Created BY running BootForge")
    print()
    print("=" * 70)
    print()

def main():
    print("🚀 BootForge Tools USB Creator")
    print("=" * 40)
    
    print_important_info()
    
    response = input("Do you want to create a BootForge Tools USB? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("\n📖 HOW TO CREATE A BOOTABLE MACOS INSTALLER USB:")
        print("=" * 70)
        print()
        print("REQUIREMENT: You need a working Mac to create bootable installers")
        print()
        print("STEPS:")
        print("1. Run BootForge GUI on your Mac:")
        print("   python3 main.py --gui")
        print()
        print("2. In BootForge, go to 'USB Builder' section")
        print()
        print("3. Select 'macOS OCLP Installer' recipe")
        print()
        print("4. Choose your Mac model (for hardware-specific patches)")
        print()
        print("5. Select target USB drive")
        print()
        print("6. Click 'Build USB' - BootForge will:")
        print("   • Download macOS recovery image from Apple")
        print("   • Create GPT partitions (EFI + Data)")
        print("   • Install OpenCore bootloader")
        print("   • Apply hardware-specific OCLP patches")
        print("   • Make USB bootable")
        print()
        print("7. Boot from USB (hold Option/Alt key at startup)")
        print()
        print("=" * 70)
        print()
        print("❓ DON'T HAVE A WORKING MAC?")
        print("You need a working Mac, Windows, or Linux computer to run BootForge")
        print("and create the bootable USB. BootForge works cross-platform!")
        print()
        sys.exit(0)
    
    print("\n📦 Creating BootForge Tools USB...\n")
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: Please run this from the BootForge directory")
        sys.exit(1)
    
    # Import and run the builder
    try:
        from build_system.create_bootable_usb import BootableUSBCreator
        creator = BootableUSBCreator()
        creator.build_bootable_usb()
        
        print("\n✅ SUCCESS! BootForge Tools USB files are ready!")
        print("\n📋 NEXT STEPS:")
        print("1. Get a USB drive (8GB+ recommended)")
        print("2. Format it as FAT32")
        print("3. Copy all files from 'bootable_usb' folder to USB")
        print("4. Plug USB into your Mac (booted into macOS)")
        print("5. Open the USB and run: Start-BootForge-Mac.command")
        print("6. Use BootForge GUI to CREATE bootable macOS installer USBs")
        print()
        print("⚠️  NOTE: This USB contains BootForge TOOLS, not a Mac installer!")
        print("    To install macOS, create a bootable installer using BootForge.")
        
    except ImportError as e:
        print(f"❌ Error importing builder: {e}")
        print("Running builder directly...")
        
        # Fallback - run the builder script directly
        os.system("python3 build_system/create_bootable_usb.py")

if __name__ == "__main__":
    main()
