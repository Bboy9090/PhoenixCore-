# Bobby's PhoenixDrive — Boot Camp Driver Detection & Installation System

Comprehensive system for automatic Mac model detection and Boot Camp Windows driver installation.

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Mac Model Detection](#mac-model-detection)
4. [Driver Database](#driver-database)
5. [Installation Process](#installation-process)
6. [API Specification](#api-specification)
7. [Implementation Guide](#implementation-guide)

---

## System Overview

### Problem Statement

Mac users installing Windows via Boot Camp face a critical challenge: identifying and obtaining the correct drivers for their specific Mac model. Without proper drivers, Windows cannot properly utilize Mac hardware (GPU, trackpad, audio, etc.), resulting in poor user experience.

### Solution

Bobby's PhoenixDrive provides an automated system that:

1. **Detects** the exact Mac model and hardware configuration
2. **Identifies** compatible Windows drivers from Apple's Boot Camp Support Software
3. **Downloads** drivers automatically with caching
4. **Installs** drivers to the correct locations in Windows
5. **Verifies** installation success and provides status updates

### Key Features

- **Automatic Detection:** No manual model entry required
- **Comprehensive Database:** 500+ Mac models supported (2008-2024)
- **Smart Caching:** Cached drivers prevent redundant downloads
- **Automated Installation:** One-click driver installation
- **Progress Tracking:** Real-time installation progress via WebSocket
- **Error Recovery:** Automatic retry and fallback mechanisms
- **Multi-Language Support:** Drivers for all regions

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Mobile App (iOS/Android)                 │
│  - Boot Camp Setup Wizard                                   │
│  - Mac Model Detection UI                                   │
│  - Driver Installation Progress                             │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API + WebSocket
┌────────────────────▼────────────────────────────────────────┐
│              Backend API (Flask/FastAPI)                    │
│  - Mac Detection Endpoint                                   │
│  - Driver Lookup Service                                    │
│  - Download Manager                                         │
│  - Installation Orchestrator                                │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──┐  ┌──────▼──┐  ┌─────▼──────┐
│Mac Model │  │ Driver  │  │Installation│
│Database  │  │Database │  │Engine      │
└──────────┘  └─────────┘  └────────────┘
```

### Data Flow

1. **Detection Phase**
   - User opens Boot Camp Setup Wizard
   - System detects Mac model via hardware identifiers
   - Queries driver database for compatible drivers

2. **Download Phase**
   - Checks cache for previously downloaded drivers
   - Downloads missing drivers from Apple servers
   - Verifies checksums and integrity

3. **Installation Phase**
   - Extracts driver packages
   - Installs drivers to Windows system directories
   - Registers drivers with Windows Device Manager
   - Verifies installation success

---

## Mac Model Detection

### Detection Methods

#### Method 1: Hardware Identifiers (Primary)

On macOS, retrieve model information:

```bash
# Get Mac model identifier
system_profiler SPHardwareDataType | grep "Model Identifier"
# Output: Model Identifier: MacBookPro15,1

# Get board ID
ioreg -l | grep board-id
# Output: "board-id" = <"Mac-551B86E5744E0084">

# Get serial number
system_profiler SPHardwareDataType | grep "Serial Number"
```

#### Method 2: Firmware Information

```bash
# Get firmware version
nvram -p | grep "fmk-version"

# Get EFI version
system_profiler SPHardwareDataType | grep "Boot ROM"
```

#### Method 3: Hardware Specifications

```bash
# Get CPU model
sysctl -n machdep.cpu.brand_string

# Get GPU information
system_profiler SPDisplaysDataType

# Get chipset/platform
ioreg -l | grep "AAPL,chipset-rev"
```

### Mac Model Identifier Format

Mac model identifiers follow pattern: `<Type><Year>,<Variant>`

Examples:
- `MacBookPro15,1` — MacBook Pro 15-inch (2018)
- `MacBookAir7,2` — MacBook Air 13-inch (2015)
- `iMac19,1` — iMac 27-inch (2019)
- `Mac14,7` — Mac mini (2023)

### Supported Mac Models

| Model Type | Year Range | Count | Boot Camp Support |
|------------|-----------|-------|------------------|
| MacBook Pro | 2008-2024 | 45+ | Yes (Intel only) |
| MacBook Air | 2008-2024 | 30+ | Yes (Intel only) |
| MacBook | 2006-2019 | 15+ | Yes (Intel only) |
| iMac | 2006-2024 | 40+ | Yes (Intel only) |
| Mac mini | 2006-2024 | 25+ | Yes (Intel only) |
| Mac Studio | 2022-2024 | 5+ | No (Apple Silicon) |
| Mac Pro | 2006-2023 | 20+ | Yes (Intel only) |
| **Total** | | **180+** | |

---

## Driver Database

### Database Schema

```python
@dataclass
class MacModel:
    model_id: str                    # e.g., "MacBookPro15,1"
    display_name: str                # e.g., "MacBook Pro 15-inch (2018)"
    year: int                         # 2018
    cpu_type: str                     # "Intel Core i7"
    gpu_type: str                     # "AMD Radeon Pro 555X"
    board_id: str                     # "Mac-551B86E5744E0084"
    boot_camp_support: bool           # True/False
    min_windows_version: str          # "Windows 10 1909"
    driver_package_id: str            # "BootCampESD_6.1"
    driver_url: str                   # URL to driver package
    driver_size_mb: float             # 500
    driver_checksum: str              # SHA256 hash
    release_date: str                 # "2018-07-12"
    notes: str                        # Special instructions

@dataclass
class DriverPackage:
    package_id: str                   # "BootCampESD_6.1"
    version: str                      # "6.1"
    release_date: str                 # "2018-07-12"
    compatible_models: List[str]      # ["MacBookPro15,1", ...]
    components: Dict[str, str]        # {
                                      #   "chipset": "Chipset_6.1.zip",
                                      #   "gpu": "GPU_6.1.zip",
                                      #   "audio": "Audio_6.1.zip",
                                      #   "trackpad": "Trackpad_6.1.zip",
                                      #   "keyboard": "Keyboard_6.1.zip",
                                      #   "usb": "USB_6.1.zip",
                                      #   "camera": "Camera_6.1.zip"
                                      # }
    install_order: List[str]          # Order to install components
    windows_versions: List[str]       # ["Windows 10", "Windows 11"]
    download_url: str                 # Apple CDN URL
    file_size_mb: float               # 500
    checksum_sha256: str              # Hash for verification
```

### Driver Components

Each Boot Camp driver package includes:

| Component | Purpose | Files |
|-----------|---------|-------|
| **Chipset** | Intel chipset drivers | INF, SYS |
| **GPU** | Graphics card drivers | INF, SYS, DLL |
| **Audio** | Sound card drivers | INF, SYS, DLL |
| **Trackpad** | Multi-touch trackpad | INF, SYS, DLL |
| **Keyboard** | Keyboard and function keys | INF, SYS |
| **USB** | USB controllers | INF, SYS |
| **Camera** | FaceTime HD camera | INF, SYS, DLL |
| **Bluetooth** | Bluetooth wireless | INF, SYS, DLL |
| **Ethernet** | Network adapters | INF, SYS |
| **Thunderbolt** | Thunderbolt ports | INF, SYS |

---

## Installation Process

### Step 1: Pre-Installation Checks

```python
def pre_install_checks(windows_version: str, mac_model: str) -> ValidationResult:
    """Verify system is ready for driver installation"""
    
    checks = {
        "windows_version": check_windows_version(windows_version),
        "disk_space": check_disk_space(required_mb=1000),
        "admin_privileges": check_admin_privileges(),
        "driver_compatibility": check_driver_compatibility(mac_model, windows_version),
        "existing_drivers": check_existing_drivers(),
    }
    
    return ValidationResult(all_passed=all(checks.values()), details=checks)
```

### Step 2: Download Drivers

```python
def download_drivers(mac_model: str, cache_dir: str) -> DownloadResult:
    """Download drivers with caching and verification"""
    
    # Check cache first
    cached_path = check_cache(mac_model)
    if cached_path and verify_checksum(cached_path):
        return DownloadResult(status="cached", path=cached_path)
    
    # Download from Apple CDN
    driver_package = get_driver_package(mac_model)
    download_path = download_file(
        url=driver_package.download_url,
        destination=cache_dir,
        progress_callback=on_download_progress
    )
    
    # Verify integrity
    if not verify_checksum(download_path, driver_package.checksum_sha256):
        raise DownloadError("Checksum verification failed")
    
    return DownloadResult(status="downloaded", path=download_path)
```

### Step 3: Extract Drivers

```python
def extract_drivers(package_path: str, extract_dir: str) -> ExtractResult:
    """Extract driver package to staging directory"""
    
    # Extract main package
    with zipfile.ZipFile(package_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    # Extract component packages
    components = {}
    for component_name in DRIVER_COMPONENTS:
        component_zip = os.path.join(extract_dir, f"{component_name}.zip")
        if os.path.exists(component_zip):
            component_dir = os.path.join(extract_dir, component_name)
            with zipfile.ZipFile(component_zip, 'r') as zip_ref:
                zip_ref.extractall(component_dir)
            components[component_name] = component_dir
    
    return ExtractResult(components=components)
```

### Step 4: Install Drivers

```python
def install_drivers(components: Dict[str, str], install_order: List[str]) -> InstallResult:
    """Install drivers in correct order"""
    
    results = {}
    
    for component in install_order:
        if component not in components:
            continue
        
        try:
            # Find INF file
            inf_file = find_inf_file(components[component])
            
            # Install using pnputil (Windows Device Manager)
            result = install_inf(inf_file)
            
            # Verify installation
            if verify_installation(component):
                results[component] = {"status": "success"}
            else:
                results[component] = {"status": "warning", "message": "Installation completed but verification failed"}
        
        except Exception as e:
            results[component] = {"status": "error", "message": str(e)}
    
    return InstallResult(results=results)
```

### Step 5: Post-Installation

```python
def post_installation(components: Dict[str, str]) -> PostInstallResult:
    """Verify installation and perform cleanup"""
    
    # Verify all drivers installed
    verification = verify_all_drivers(components)
    
    # Update device drivers in Device Manager
    update_device_manager()
    
    # Clean up temporary files
    cleanup_temp_files()
    
    # Restart required?
    restart_required = check_restart_required()
    
    return PostInstallResult(
        verification=verification,
        restart_required=restart_required
    )
```

---

## API Specification

### Endpoint 1: Detect Mac Model

**Request:**
```
POST /api/v1/bootcamp/detect-mac
Content-Type: application/json

{
  "system_info": {
    "model_identifier": "MacBookPro15,1",
    "board_id": "Mac-551B86E5744E0084",
    "serial_number": "C02XXXXX",
    "cpu_brand": "Intel(R) Core(TM) i7-8750H CPU @ 2.20GHz",
    "gpu_model": "AMD Radeon Pro 555X"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "mac_model": {
    "model_id": "MacBookPro15,1",
    "display_name": "MacBook Pro 15-inch (2018)",
    "year": 2018,
    "boot_camp_support": true,
    "cpu_type": "Intel Core i7-8750H",
    "gpu_type": "AMD Radeon Pro 555X"
  },
  "driver_package": {
    "package_id": "BootCampESD_6.1",
    "version": "6.1",
    "size_mb": 500,
    "components": ["chipset", "gpu", "audio", "trackpad", "keyboard"]
  }
}
```

### Endpoint 2: Get Driver Package

**Request:**
```
GET /api/v1/bootcamp/drivers/BootCampESD_6.1
```

**Response:**
```json
{
  "status": "success",
  "package": {
    "package_id": "BootCampESD_6.1",
    "version": "6.1",
    "download_url": "https://apple-cdn.example.com/BootCampESD_6.1.zip",
    "file_size_mb": 500,
    "checksum_sha256": "abc123...",
    "components": {
      "chipset": "Chipset_6.1.zip",
      "gpu": "GPU_6.1.zip",
      "audio": "Audio_6.1.zip",
      "trackpad": "Trackpad_6.1.zip"
    }
  }
}
```

### Endpoint 3: Start Driver Installation

**Request:**
```
POST /api/v1/bootcamp/install
Content-Type: application/json

{
  "mac_model": "MacBookPro15,1",
  "windows_version": "Windows 10 21H2",
  "driver_package_id": "BootCampESD_6.1"
}
```

**Response:**
```json
{
  "status": "success",
  "installation_id": "install-uuid",
  "websocket_url": "wss://api.example.com/api/v1/bootcamp/install/install-uuid/stream"
}
```

### WebSocket: Installation Progress

**Subscribe:**
```json
{
  "action": "subscribe",
  "installation_id": "install-uuid"
}
```

**Progress Updates:**
```json
{
  "event": "progress",
  "installation_id": "install-uuid",
  "stage": "downloading",
  "stage_progress": 45,
  "overall_progress": 15,
  "current_operation": "Downloading chipset drivers...",
  "speed_mbps": 25.5,
  "eta_seconds": 300
}
```

---

## Implementation Guide

### Phase 1: Mac Detection Module

Create `server/bootcamp/mac_detector.py`:

```python
import subprocess
import json
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class MacSystemInfo:
    model_identifier: str
    board_id: str
    serial_number: str
    cpu_brand: str
    gpu_model: str
    ram_gb: int
    storage_gb: int

class MacDetector:
    def detect(self) -> MacSystemInfo:
        """Detect Mac system information"""
        return MacSystemInfo(
            model_identifier=self._get_model_identifier(),
            board_id=self._get_board_id(),
            serial_number=self._get_serial_number(),
            cpu_brand=self._get_cpu_brand(),
            gpu_model=self._get_gpu_model(),
            ram_gb=self._get_ram_gb(),
            storage_gb=self._get_storage_gb()
        )
    
    def _get_model_identifier(self) -> str:
        """Get Mac model identifier"""
        result = subprocess.run(
            ['system_profiler', 'SPHardwareDataType'],
            capture_output=True,
            text=True
        )
        for line in result.stdout.split('\n'):
            if 'Model Identifier' in line:
                return line.split(':')[1].strip()
        return ""
    
    # ... additional methods for other system info
```

### Phase 2: Driver Database

Create `server/bootcamp/driver_database.py`:

```python
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class DriverDatabase:
    models: Dict[str, MacModel]
    packages: Dict[str, DriverPackage]
    
    @classmethod
    def load(cls, db_path: Path) -> 'DriverDatabase':
        """Load driver database from JSON"""
        with open(db_path, 'r') as f:
            data = json.load(f)
        
        models = {k: MacModel(**v) for k, v in data['models'].items()}
        packages = {k: DriverPackage(**v) for k, v in data['packages'].items()}
        
        return cls(models=models, packages=packages)
    
    def get_drivers_for_model(self, model_id: str) -> Optional[DriverPackage]:
        """Get driver package for Mac model"""
        if model_id not in self.models:
            return None
        
        mac_model = self.models[model_id]
        return self.packages.get(mac_model.driver_package_id)
```

### Phase 3: Installation Engine

Create `server/bootcamp/installer.py`:

```python
import os
import subprocess
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class InstallationResult:
    success: bool
    components_installed: Dict[str, bool]
    errors: List[str]
    restart_required: bool

class BootCampInstaller:
    def install(self, driver_path: str, components: List[str]) -> InstallationResult:
        """Install Boot Camp drivers"""
        
        results = {}
        errors = []
        
        for component in components:
            try:
                inf_file = self._find_inf(driver_path, component)
                self._install_inf(inf_file)
                results[component] = True
            except Exception as e:
                results[component] = False
                errors.append(f"{component}: {str(e)}")
        
        restart_required = self._check_restart_required()
        
        return InstallationResult(
            success=len(errors) == 0,
            components_installed=results,
            errors=errors,
            restart_required=restart_required
        )
    
    def _install_inf(self, inf_file: str) -> None:
        """Install INF file using pnputil"""
        subprocess.run(
            ['pnputil', '/add-driver', inf_file, '/install'],
            check=True
        )
```

---

## References

- **Apple Boot Camp Support:** https://support.apple.com/boot-camp
- **Mac Model Identifiers:** https://everymac.com/
- **Windows Device Manager:** https://docs.microsoft.com/windows/win32/devmgmt/device-management
- **pnputil Documentation:** https://docs.microsoft.com/windows-hardware/drivers/devtest/pnputil

---

**Last Updated:** April 2, 2026
**Version:** 1.0.0
