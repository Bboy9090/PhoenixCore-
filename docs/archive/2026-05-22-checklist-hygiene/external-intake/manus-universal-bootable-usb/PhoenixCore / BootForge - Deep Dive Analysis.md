# PhoenixCore / BootForge - Deep Dive Analysis

## Executive Summary

**BootForge (Phoenix Core)** is a professional, cross-platform OS deployment engine built on a **Rust safety core** with a **Python application layer**. It's NOT just a USB creator — it's a complete system for:

1. **Universal USB Creation** — Windows, Linux, macOS installers on any platform
2. **Multi-Boot USB Building** — GRUB-based multi-boot with chainloading
3. **Hardware Auto-Detection** — Platform-specific detection (Windows PowerShell/WMI, macOS diskutil, Linux lsblk)
4. **OS Recovery & Repair** — Detect and repair Windows/macOS/Linux systems
5. **OCLP Integration** — Embedded OpenCore Legacy Patcher for unsupported Macs
6. **Safety-First Architecture** — Multi-layer validation before destructive operations

---

## Architecture Overview

### Core Components

#### 1. **Rust Engine (Phoenix Core)**
- **Location:** `crates/` directory (workspace)
- **Key Crates:**
  - `crates/core` — Device graph, safety gates, imaging primitives
  - `crates/safety` — Safety validation engine
  - `crates/imaging` — Read-only imaging with SHA-256 verification
  - `crates/workflow-engine` — Workflow runner and pack export
  - `crates/wim` — Windows Imaging Format support
  - `crates/host-windows`, `crates/host-macos`, `crates/host-linux` — Platform-specific implementations
  - `apps/cli` — Rust CLI (`phoenix-cli`) for low-level workflows

**Purpose:** Provides a safety-focused, cross-platform foundation for disk operations, device enumeration, and imaging.

#### 2. **Python Application Layer**
- **Location:** `src/` directory
- **Key Modules:**
  - `src/core/` — Configuration, disk management, safety validation, hardware detection
  - `src/gui/` — PyQt6 GUI with wizard workflows
  - `src/cli/` — Command-line interface
  - `src/recovery/` — OS detection and repair (Windows/macOS/Linux)
  - `src/plugins/` — Plugin system for diagnostics and driver injection
  - `src/imaging/` — Cold Fuse imaging engine

**Purpose:** Provides user-facing workflows, hardware detection, and OS-specific repair logic.

#### 3. **Web Server (Flask)**
- **Location:** `web_server.py`
- **Purpose:** Demo web interface, download serving, file integrity verification

---

## Key Capabilities

### 1. Hardware Detection (`src/core/hardware_detector.py`)

**Platform-Specific Detectors:**

| Platform | Method | Data Collected |
|----------|--------|-----------------|
| **Windows** | PowerShell CIM queries (WMI) | System name, CPU, RAM, GPU, network, storage, BIOS |
| **macOS** | `diskutil`, system profiler | System model, CPU, GPU, storage, EFI partition |
| **Linux** | `lsblk`, `/proc`, `/sys` | CPU, RAM, storage, network, device tree |

**Output:** `DetectedHardware` dataclass with confidence levels (EXACT_MATCH, HIGH, MEDIUM, LOW, UNKNOWN)

**Use Case:** Automatically match detected hardware to predefined profiles for optimal deployment.

---

### 2. Disk Management (`src/core/disk_manager.py`)

**Capabilities:**
- List removable drives with vendor/model/health status
- Write images with progress monitoring
- Verify written data with SHA-256
- Unmount devices safely
- Platform-specific device path handling (`/dev/sdX` on Linux, `\\.\PhysicalDriveX` on Windows, `/dev/diskX` on macOS)

**Safety Features:**
- Dry-run mode (preview without executing)
- Multi-step confirmations
- Device health checks
- Removable device detection

---

### 3. USB Builder (`src/core/usb_builder.py`)

**Workflow:**
1. Validate build inputs (recipe, device, source files)
2. Prepare target device (unmount, clear)
3. Create partition scheme (GPT, MBR, hybrid)
4. Format partitions (FAT32, NTFS, ext4, APFS)
5. Mount partitions
6. Deploy files based on recipe
7. Configure bootloader (GRUB, UEFI, Legacy BIOS)
8. Finalize and verify

**Deployment Types:**
- `SINGLE_BOOT` — One OS per USB
- `MULTIBOOT` — Multiple OSes with GRUB menu
- `RECOVERY` — System recovery/repair tools

**Partition Schemes:**
- GPT (UEFI-only)
- MBR (Legacy BIOS-only)
- HYBRID (UEFI + Legacy BIOS)

---

### 4. OS Image Management (`src/core/os_image_manager.py`)

**Features:**
- Download OS images from multiple providers
- Verify checksums (SHA256, SHA512, MD5, GPG)
- Cache images locally
- Track download progress
- Support for Windows, Linux, macOS

**Image Status Tracking:**
- AVAILABLE → DOWNLOADING → VERIFYING → VERIFIED → CACHED

**Providers:**
- `WindowsProvider` — Manual Windows ISO upload with verification
- `LinuxProvider` — Ubuntu, Fedora, Mint, Arch, etc.
- `macOSProvider` — macOS recovery images

---

### 5. GRUB Multi-Boot Manager (`src/core/grub_manager.py`)

**Capabilities:**
- Generate GRUB menu entries for Windows, macOS, Linux, custom ISOs
- Support chainloading to EFI bootloaders
- Configure boot modes (UEFI, Legacy BIOS, Hybrid)
- Generate GRUB configuration files

**Example Entry (Windows):**
```
menuentry "Windows 11" {
    insmod part_gpt
    insmod fat
    insmod ntfs
    insmod chain
    search --fs-uuid --set=root {UUID}
    chainloader /EFI/BOOT/BOOTX64.EFI
}
```

---

### 6. OS Recovery & Repair (`src/recovery/`)

**Detection (`detect.py`):**
- Probe disks for Windows, macOS, Linux
- Mount partitions read-only
- Identify OS by filesystem markers:
  - Windows: `Windows/System32/config/SYSTEM`
  - macOS: `System/Library/CoreServices/SystemVersion.plist`
  - Linux: `etc/os-release`

**Repair Modules:**
- `windows_repair.py` — Windows boot repair, driver injection, system file repair
- `macos_repair.py` — macOS boot repair, OCLP patching, firmware updates
- `linux_repair.py` — GRUB repair, filesystem check, package manager recovery

---

### 7. Safety Validation (`src/core/safety_validator.py`)

**Multi-Layer Validation:**

1. **Device Safety** — Check if device is removable, not system disk, adequate size
2. **Prerequisites** — Verify required tools available (dd, mkfs, mount, etc.)
3. **Source Files** — Validate image files exist, checksums match, no corruption
4. **Patch Validation** — Verify patches are safe for target hardware

**Risk Levels:**
- `SAFE` — Proceed
- `CAUTION` — Warn user
- `DANGEROUS` — Require explicit confirmation
- `BLOCKED` — Prevent operation

---

### 8. OCLP Integration (`docs/oclp_integration.md`)

**What it does:**
- Embed OpenCore Legacy Patcher as git submodule
- Provide one-click access from GUI
- Configure target Mac model, macOS version, kexts (Graphics, Audio, WiFi, USB)
- Configure SIP, SecureBootModel, verbose boot

**Supported Macs (via OCLP):**
- iMac (2012-2019)
- MacBook Pro (2012-2019)
- MacBook Air (2010-2017)
- Mac mini (2012-2018)
- Mac Pro (2010-2019)

---

## Deployment Recipes

### Data Structure (`src/core/models.py`)

```python
@dataclass
class DeploymentRecipe:
    name: str
    deployment_type: DeploymentType  # SINGLE_BOOT, MULTIBOOT, RECOVERY
    target_device: str
    partition_scheme: PartitionScheme  # GPT, MBR, HYBRID
    partitions: List[PartitionInfo]
    bootloader_config: BootloaderConfig
    os_images: List[OSImageInfo]
    tools: List[ToolInfo]
    metadata: Dict[str, Any]
```

### Example: Multi-Boot USB Recipe
```json
{
  "name": "Bobby's PhoenixDrive Multi-Boot",
  "deployment_type": "MULTIBOOT",
  "partition_scheme": "HYBRID",
  "partitions": [
    {"name": "EFI", "size_gb": 1, "filesystem": "FAT32"},
    {"name": "Data", "size_gb": 30, "filesystem": "exFAT"}
  ],
  "os_images": [
    {"name": "Windows 11", "size_gb": 5.5},
    {"name": "Ubuntu 22.04", "size_gb": 3.2},
    {"name": "ChromeOS Flex", "size_gb": 2.8}
  ],
  "tools": [
    {"name": "GParted", "size_gb": 0.8},
    {"name": "Hiren's Boot", "size_gb": 1.2}
  ],
  "bootloader_config": {
    "type": "GRUB",
    "boot_mode": "HYBRID"
  }
}
```

---

## CLI Commands

```bash
# List USB devices
python main.py list-devices

# Write image with safety validation
python main.py write-image -i windows11.iso -d \\.\PhysicalDrive1 --verify

# Dry-run (preview without executing)
python main.py write-image -i ubuntu.iso -d /dev/sdb --dry-run

# Format device
python main.py format-device -d /dev/sdb -f fat32

# Detect and repair OS
python main.py recovery repair

# Diagnose system
python main.py recovery diagnose
```

---

## What Makes PhoenixCore Special

### 1. **Safety-First Design**
- Multi-layer validation before any destructive operation
- Dry-run mode for preview
- Device health checks
- Removable device detection
- Clear error messages

### 2. **Cross-Platform**
- Windows (PowerShell/WMI for detection)
- macOS (diskutil, system profiler)
- Linux (lsblk, /proc, /sys)
- Same codebase, platform-specific implementations

### 3. **Professional Grade**
- Rust safety core for low-level operations
- Python flexibility for workflows
- PyQt6 GUI for user-friendly interaction
- CLI for automation and scripting

### 4. **Comprehensive**
- Not just USB creation — also repair, recovery, diagnostics
- Hardware auto-detection and profiling
- OCLP integration for unsupported Macs
- Multi-boot support with GRUB

### 5. **Extensible**
- Plugin system for custom diagnostics
- Provider architecture for OS images
- Workflow engine for complex deployments
- Evidence reports for auditability

---

## The Reality vs. The Dream

### What PhoenixCore CAN Do (One USB for x86-64 devices):
✅ Windows 10/11 installer  
✅ Ubuntu, Fedora, Mint, Arch Linux installers  
✅ ChromeOS Flex  
✅ macOS (Intel Macs via OCLP)  
✅ Repair tools (GParted, Hiren's, MediCat)  
✅ Multi-boot menu with GRUB  
✅ Hardware detection and auto-profiling  

### What PhoenixCore CANNOT Do (Fundamental Limitations):
❌ macOS on Apple Silicon (different CPU architecture)  
❌ ARM Chromebooks (different instruction set)  
❌ Asahi Linux on Apple Silicon (requires separate ARM build)  
❌ One USB for ALL devices (CPU architecture incompatibility)  

### The PhoenixCore Solution:
The mobile app identifies your device's CPU architecture and builds the RIGHT USB recipe for YOUR hardware. Instead of one impossible USB, it's the smartest possible USB for your specific device.

---

## Integration Opportunities for Bobby's PhoenixDrive Mobile App

### 1. **Backend API**
Create a REST API wrapper around PhoenixCore Python modules:
- `POST /api/hardware/detect` — Run hardware detection
- `POST /api/usb/build` — Start USB build with recipe
- `GET /api/usb/build/{id}/status` — Poll build progress
- `POST /api/images/download` — Download OS image
- `GET /api/recovery/diagnose` — Run diagnostics

### 2. **Recipe Export/Import**
- Mobile app builds recipe JSON
- Export to desktop via QR code or file
- Desktop BootForge reads recipe and builds USB

### 3. **Real-Time Sync**
- Mobile app sends hardware detection to desktop
- Desktop displays compatible OS/tool options
- User selects on mobile, desktop builds USB

### 4. **Embedded Tools**
- Include BootForge CLI in mobile app backend
- Call Python scripts directly from Expo backend
- Stream progress updates to mobile UI

---

## Files to Integrate

**Critical Python Modules:**
- `src/core/hardware_detector.py` — Hardware detection
- `src/core/disk_manager.py` — USB device enumeration
- `src/core/usb_builder.py` — USB building logic
- `src/core/os_image_manager.py` — Image downloading/verification
- `src/core/safety_validator.py` — Safety checks
- `src/recovery/detect.py` — OS detection and repair
- `src/core/grub_manager.py` — Multi-boot configuration

**CLI Entry Points:**
- `main.py` — Entry point
- `src/cli/cli_interface.py` — CLI commands

**Configuration:**
- `src/core/config.py` — Configuration management
- `src/core/models.py` — Data structures

---

## Next Steps for Bobby's PhoenixDrive

1. **Create Backend API** — Wrap PhoenixCore Python modules in Flask/FastAPI
2. **Recipe Format** — Define JSON schema for USB recipes
3. **Desktop Integration** — Build desktop app that reads mobile recipes
4. **Real-Time Sync** — WebSocket or polling for progress updates
5. **Hardware Profiles** — Map detected hardware to compatible OS/tool combinations
6. **Safety Validation** — Integrate PhoenixCore's multi-layer validation into mobile workflows

