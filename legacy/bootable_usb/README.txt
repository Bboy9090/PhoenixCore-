BootForge Bootable USB Recovery System
=====================================

🚀 QUICK START:
- macOS: Double-click "Start-BootForge-Mac.command"
- Linux: Run "./Start-BootForge-Linux.sh"
- Windows: Double-click "Start-BootForge-Windows.bat"

📁 DIRECTORY STRUCTURE:
├── EFI/           - UEFI boot files
├── BootForge/     - Main application
├── Tools/         - Recovery utilities
├── OS_Images/     - Store your OS images here
└── Recovery/      - Emergency recovery tools

🔧 FEATURES:
✓ Cross-platform bootable USB creation
✓ Mac OCLP integration for legacy hardware
✓ Windows bypass tools for TPM/Secure Boot
✓ Linux live system creation
✓ Hardware detection and profiling
✓ Safety validation and rollback
✓ Real-time progress monitoring

💾 USAGE FOR MAC RECOVERY:
1. Boot from this USB (hold Option/Alt at startup)
2. Launch BootForge GUI
3. Select your Mac model for OCLP patches
4. Create macOS installer with legacy support
5. Install macOS with OpenCore Legacy Patcher

🛡️ SAFETY FEATURES:
- Comprehensive device validation
- Automatic safety checks
- Rollback on failure
- Audit logging
- Permission verification

📋 REQUIREMENTS:
- Python 3.7+ (usually pre-installed on macOS/Linux)
- 8GB+ USB drive for OS creation
- Admin/root privileges for disk operations

🆘 TROUBLESHOOTING:
- If Python not found: Install from python.org
- If permission denied: Run as administrator
- If USB not detected: Check USB port/cable
- For Mac boot issues: Reset NVRAM (Cmd+Opt+P+R)

Created: 2025-10-01 01:12:04
Version: BootForge USB Recovery v1.0
