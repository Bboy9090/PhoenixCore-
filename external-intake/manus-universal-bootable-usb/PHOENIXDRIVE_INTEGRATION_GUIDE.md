# Bobby's PhoenixDrive — Complete Integration Guide

## Overview

Bobby's PhoenixDrive is a mobile companion app for your PhoenixCore USB bootable drive builder. It provides:

1. **Mobile App** — Hardware detection, recipe building, OS/tool selection
2. **Backend API** — Flask server wrapping PhoenixCore Python modules
3. **Desktop Consumer** — CLI tool that reads recipes and builds USBs using PhoenixCore
4. **QR Code Export** — Share recipes between mobile and desktop

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Bobby's PhoenixDrive                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Mobile App (React Native + Expo)                           │
│  ├─ Home Screen (stats, quick start)                        │
│  ├─ Device Wizard (hardware detection)                      │
│  ├─ USB Builder (5-step recipe builder)                     │
│  ├─ Knowledge Base (guides & troubleshooting)               │
│  └─ Recipe Export (QR code + JSON)                          │
│         ↓ (REST API + WebSocket)                            │
│  Backend API Server (Flask + SocketIO)                      │
│  ├─ /api/v1/hardware/detect                                 │
│  ├─ /api/v1/usb/devices                                     │
│  ├─ /api/v1/recipe/build                                    │
│  ├─ /api/v1/usb/build                                       │
│  ├─ /api/v1/safety/validate                                 │
│  └─ WebSocket: progress streaming                           │
│         ↓ (Python imports)                                  │
│  PhoenixCore Python Modules                                 │
│  ├─ hardware_detector.py (Windows/macOS/Linux)              │
│  ├─ disk_manager.py (USB enumeration)                       │
│  ├─ usb_builder.py (GRUB multi-boot)                        │
│  ├─ os_image_manager.py (ISO handling)                      │
│  ├─ safety_validator.py (multi-layer checks)                │
│  └─ recovery/core.py (OS recovery)                          │
│         ↓ (Rust FFI)                                        │
│  Rust Safety Core (crates/)                                 │
│  └─ Low-level disk operations with validation               │
│         ↓                                                    │
│  Actual Hardware (USB Device)                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘

Desktop Consumer (CLI)
├─ Reads recipes (JSON or QR code)
├─ Validates safety
├─ Downloads OS images
└─ Builds bootable USB using PhoenixCore
```

---

## Setup Instructions

### 1. Backend API Server

```bash
# Navigate to project
cd /home/ubuntu/phoenix-core-mobile/server

# Install dependencies
pip install -r requirements.txt

# Start the API server
python api.py
```

The API will run on `http://localhost:5000` with the following endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/hardware/detect` | POST | Detect system hardware |
| `/api/v1/usb/devices` | GET | List USB devices |
| `/api/v1/recipe/build` | POST | Build deployment recipe |
| `/api/v1/usb/build` | POST | Start USB build |
| `/api/v1/usb/build/<id>/status` | GET | Get build status |
| `/api/v1/safety/validate` | POST | Validate safety |

### 2. Mobile App

```bash
# Navigate to project
cd /home/ubuntu/phoenix-core-mobile

# Install dependencies
pnpm install

# Start dev server
pnpm dev
```

The mobile app will be available at `http://localhost:8081` with a QR code for scanning in Expo Go.

**Environment Variables:**
```bash
EXPO_PUBLIC_API_URL=http://localhost:5000/api/v1
```

### 3. Desktop Consumer

```bash
# Make script executable
chmod +x /home/ubuntu/PhoenixDrive_Desktop_Consumer.py

# List USB devices
python /home/ubuntu/PhoenixDrive_Desktop_Consumer.py --list-devices

# Show recipe summary
python /home/ubuntu/PhoenixDrive_Desktop_Consumer.py recipe.json --summary

# Build USB (dry-run)
python /home/ubuntu/PhoenixDrive_Desktop_Consumer.py recipe.json --device /dev/sdb --dry-run

# Build USB (actual)
python /home/ubuntu/PhoenixDrive_Desktop_Consumer.py recipe.json --device /dev/sdb
```

---

## Workflow: Mobile → Desktop

### Step 1: Mobile App (Hardware Detection)

1. Open Bobby's PhoenixDrive mobile app
2. Tap **Device Wizard**
3. App detects your hardware (CPU, RAM, GPU, storage)
4. Shows compatible OSes based on CPU architecture
5. Explains incompatibilities (e.g., "Apple Silicon arm64 - x86-64 ISOs not compatible")

### Step 2: Mobile App (Recipe Building)

1. Tap **USB Builder**
2. Select USB device (shows real devices with health status)
3. Select operating systems (Windows, Linux, ChromeOS, etc.)
4. Add optional tools (GParted, Clonezilla, Memtest, etc.)
5. Review recipe (total size, compatibility check)
6. Tap **Build USB**

### Step 3: Recipe Export

1. After recipe is built, tap **Export**
2. Choose format:
   - **QR Code** — Scan on desktop
   - **JSON** — Download or copy to clipboard
3. Share with others or use on desktop

### Step 4: Desktop Consumer

```bash
# Option A: Import from QR code
python PhoenixDrive_Desktop_Consumer.py --scan-qr

# Option B: Import from JSON file
python PhoenixDrive_Desktop_Consumer.py recipe.json --summary

# Option C: Build USB
python PhoenixDrive_Desktop_Consumer.py recipe.json --device /dev/sdb
```

### Step 5: Desktop Consumer (Build USB)

1. Script validates recipe
2. Checks device safety (removable, not system drive, sufficient size)
3. Downloads OS images (if not cached)
4. Builds bootable USB using PhoenixCore
5. Verifies write integrity
6. Done!

---

## API Endpoints Reference

### Hardware Detection

**Request:**
```bash
POST /api/v1/hardware/detect
Content-Type: application/json

{
  "include_storage": true,
  "include_network": true,
  "timeout_seconds": 30
}
```

**Response:**
```json
{
  "status": "success",
  "device_id": "device-uuid",
  "detected_at": "2026-03-22T16:30:00Z",
  "hardware": {
    "system": {
      "manufacturer": "Dell",
      "model": "XPS 13",
      "serial_number": "ABC123"
    },
    "cpu": {
      "name": "Intel Core i7-12700H",
      "manufacturer": "Intel",
      "architecture": "x86_64",
      "cores": 14,
      "threads": 20
    },
    "memory": {
      "total_gb": 16,
      "modules": [...]
    },
    "gpu": [...],
    "storage": [...],
    "network": [...]
  },
  "platform": {
    "os": "windows",
    "version": "11",
    "architecture": "x86_64",
    "bios_mode": "uefi"
  },
  "compatible_os": ["windows_11", "ubuntu_22_04", "fedora_38", "chromeos_flex"],
  "incompatible_os": ["macos_monterey", "macos_ventura"],
  "incompatible_reason": "x86-64 architecture - ARM ISOs not compatible"
}
```

### USB Device Enumeration

**Request:**
```bash
GET /api/v1/usb/devices?min_size_gb=4&include_system_drives=false
```

**Response:**
```json
{
  "status": "success",
  "devices": [
    {
      "device_id": "usb-SanDisk_Extreme_ABC123",
      "path": "/dev/sdb",
      "name": "SanDisk Extreme",
      "size_gb": 64,
      "filesystem": "exFAT",
      "vendor": "SanDisk",
      "model": "Extreme",
      "serial": "ABC123",
      "is_removable": true,
      "health_status": "healthy",
      "write_speed_mbps": 95.5,
      "mountpoint": "/media/usb"
    }
  ],
  "total_devices": 1
}
```

### Recipe Building

**Request:**
```bash
POST /api/v1/recipe/build
Content-Type: application/json

{
  "name": "My Multi-Boot USB",
  "deployment_type": "MULTIBOOT",
  "os_selections": ["windows_11", "ubuntu_22_04"],
  "tool_selections": ["gparted", "clonezilla"],
  "target_device_id": "usb-SanDisk_Extreme_ABC123",
  "target_device_size_gb": 64,
  "partition_scheme": "HYBRID",
  "bootloader_type": "GRUB",
  "safety_level": "STANDARD"
}
```

**Response:**
```json
{
  "status": "success",
  "recipe": {
    "recipe_id": "recipe-12345",
    "name": "My Multi-Boot USB",
    "version": "1.0.0",
    "created_at": "2026-03-22T16:30:00Z",
    "created_by": "mobile-app-v1.0.0",
    "deployment_type": "MULTIBOOT",
    "target_device": {...},
    "partition_scheme": "HYBRID",
    "partitions": [...],
    "os_images": [
      {
        "image_id": "windows_11",
        "name": "Windows 11",
        "os_family": "windows",
        "version": "latest",
        "architecture": "x86_64",
        "size_gb": 5.5,
        "status": "available"
      },
      {
        "image_id": "ubuntu_22_04",
        "name": "Ubuntu 22.04 LTS",
        "os_family": "linux",
        "version": "latest",
        "architecture": "x86_64",
        "size_gb": 3.2,
        "status": "available"
      }
    ],
    "tools": ["gparted", "clonezilla"],
    "bootloader": {...},
    "safety": {...},
    "metadata": {
      "total_size_gb": 9.5,
      "estimated_write_time_minutes": 15,
      "target_platform": "x86_64",
      "tags": ["multiboot"]
    }
  }
}
```

### USB Build Execution

**Request:**
```bash
POST /api/v1/usb/build
Content-Type: application/json

{
  "recipe_id": "recipe-12345",
  "device_path": "/dev/sdb",
  "dry_run": false,
  "verify_after_write": true
}
```

**Response:**
```json
{
  "status": "started",
  "build_id": "build-67890",
  "recipe_id": "recipe-12345",
  "started_at": "2026-03-22T16:30:00Z",
  "estimated_duration_minutes": 15
}
```

### Build Progress (WebSocket)

**Subscribe:**
```javascript
socket.emit('subscribe_build', { build_id: 'build-67890' });
```

**Progress Update:**
```json
{
  "build_id": "build-67890",
  "state": "writing",
  "stage": "writing",
  "stage_progress": 45,
  "overall_progress": 45,
  "current_operation": "Writing image: 45%",
  "speed_mbps": 95.5,
  "eta_seconds": 540,
  "timestamp": "2026-03-22T16:30:30Z"
}
```

---

## Recipe JSON Format

```json
{
  "recipe_id": "recipe-12345",
  "name": "My Multi-Boot USB",
  "version": "1.0.0",
  "created_at": "2026-03-22T16:30:00Z",
  "created_by": "mobile-app-v1.0.0",
  "deployment_type": "MULTIBOOT",
  "target_device": {
    "device_id": "usb-SanDisk_Extreme_ABC123",
    "size_gb": 64,
    "confirm_erase": true
  },
  "partition_scheme": "HYBRID",
  "partitions": [
    {
      "name": "EFI",
      "size_gb": 1.0,
      "filesystem": "FAT32",
      "label": "PHOENIX_EFI",
      "boot": true
    },
    {
      "name": "Data",
      "size_gb": 63.0,
      "filesystem": "exFAT",
      "label": "PHOENIX_DATA"
    }
  ],
  "os_images": [
    {
      "image_id": "windows_11",
      "name": "Windows 11",
      "os_family": "windows",
      "version": "latest",
      "architecture": "x86_64",
      "size_gb": 5.5,
      "status": "available"
    }
  ],
  "tools": ["gparted", "clonezilla"],
  "bootloader": {
    "type": "GRUB",
    "boot_mode": "HYBRID",
    "timeout_seconds": 10,
    "entries": []
  },
  "safety": {
    "dry_run": false,
    "verify_after_write": true,
    "safety_level": "STANDARD",
    "confirmations_required": 2
  },
  "metadata": {
    "total_size_gb": 9.5,
    "estimated_write_time_minutes": 15,
    "target_platform": "x86_64",
    "tags": ["multiboot"]
  }
}
```

---

## QR Code Format

Recipes can be exported as QR codes for easy sharing. The QR code contains a compressed JSON:

```json
{
  "v": "1",
  "id": "recipe-12345",
  "n": "My Multi-Boot USB",
  "t": "MULTIBOOT",
  "os": ["windows_11", "ubuntu_22_04"],
  "tl": ["gparted", "clonezilla"],
  "d": 64,
  "s": 9.5
}
```

**Scanning:** Use the desktop consumer with `--scan-qr` flag to import from QR code.

---

## Troubleshooting

### Backend API not responding

```bash
# Check if API is running
curl http://localhost:5000/api/v1/health

# Check logs
tail -f /home/ubuntu/phoenix-core-mobile/server/api.log
```

### PhoenixCore modules not found

```bash
# Verify PhoenixCore path
ls -la /home/ubuntu/PhoenixCore-/src/core/

# Add to PYTHONPATH
export PYTHONPATH=/home/ubuntu/PhoenixCore-:$PYTHONPATH
```

### USB device not detected

```bash
# List all devices
lsblk

# Check permissions
sudo ls -la /dev/sd*

# Run with sudo if needed
sudo python PhoenixDrive_Desktop_Consumer.py --list-devices
```

### Recipe too large for QR code

Use JSON export instead:
```bash
python PhoenixDrive_Desktop_Consumer.py recipe.json --device /dev/sdb
```

---

## Next Steps

1. **Test end-to-end workflow** — Mobile app → Backend API → Desktop consumer
2. **Implement WebSocket progress** — Real-time USB build updates
3. **Add QR code scanning** — Mobile app can scan desktop recipes
4. **Add recipe caching** — Save recipes locally for offline use
5. **Add cloud sync** — Optional Manus backend for recipe sharing
6. **Build desktop GUI** — Optional Electron app for desktop consumer

---

## Support

For issues or questions:
1. Check the Knowledge Base in the mobile app
2. Review PhoenixCore documentation at `/home/ubuntu/PhoenixCore-/README.md`
3. Check API logs at `/home/ubuntu/phoenix-core-mobile/server/api.log`
4. Submit issues on GitHub: https://github.com/Bboy9090/PhoenixCore-

---

**Bobby's PhoenixDrive** — Your universal bootable USB companion
