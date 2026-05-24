# Bobby's PhoenixDrive — Backend Architecture & API Specification

## Overview

Bobby's PhoenixDrive requires a backend system to bridge the mobile app with PhoenixCore's Python modules. This document defines the complete architecture, API specification, recipe format, and integration points.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Bobby's PhoenixDrive Mobile App               │
│                    (React Native + Expo)                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Device Wizard  │  USB Builder  │  Knowledge Base        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                    │
│                    REST API + WebSocket                          │
│                              ↓                                    │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│              Backend Server (Flask/FastAPI)                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Routes (REST endpoints)                             │   │
│  │  - /api/v1/hardware/detect                               │   │
│  │  - /api/v1/usb/devices                                   │   │
│  │  - /api/v1/recipe/build                                  │   │
│  │  - /api/v1/recipe/validate                               │   │
│  │  - /api/v1/safety/check                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  WebSocket Server (Real-time progress)                   │   │
│  │  - /ws/build/:build_id                                   │   │
│  │  - Streams: progress, status, errors                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Business Logic                                          │   │
│  │  - Hardware detection & mapping                          │   │
│  │  - Recipe validation & building                          │   │
│  │  - Safety validation                                     │   │
│  │  - Build execution                                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Database (SQLite/PostgreSQL)                            │   │
│  │  - Hardware profiles                                     │   │
│  │  - OS compatibility matrix                               │   │
│  │  - Build history                                         │   │
│  │  - User preferences                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│              PhoenixCore Python Modules                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Hardware Detection Module                               │   │
│  │  - Detect CPU, GPU, RAM, storage                         │   │
│  │  - Identify device type (laptop, desktop, server)        │   │
│  │  - Detect connected USB devices                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  OS Compatibility Module                                 │   │
│  │  - Map hardware to compatible OSes                       │   │
│  │  - Check OS requirements                                 │   │
│  │  - Validate tool compatibility                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  USB Builder Module                                      │   │
│  │  - Create bootable USB drives                            │   │
│  │  - Handle multi-boot scenarios                           │   │
│  │  - Manage partition tables                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Safety Validation Module (Rust)                         │   │
│  │  - Verify device safety                                  │   │
│  │  - Check partition integrity                             │   │
│  │  - Prevent data loss                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│              Desktop Recipe Consumer App                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Reads QR code or recipe JSON from mobile app            │   │
│  │  Executes USB build on desktop computer                  │   │
│  │  Provides progress feedback to mobile app                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Recipe JSON Schema

Recipes define the complete USB build configuration. They are created on mobile and executed on desktop.

```json
{
  "version": "1.0.0",
  "id": "recipe-uuid-here",
  "createdAt": "2026-04-01T12:00:00Z",
  "name": "Windows 11 + Linux Mint Multi-Boot",
  "description": "Bootable USB with Windows 11 and Linux Mint",
  "targetDevice": {
    "type": "usb_drive",
    "size": "32GB",
    "filesystem": "GPT"
  },
  "bootloader": {
    "type": "grub2",
    "timeout": 10
  },
  "partitions": [
    {
      "id": "windows-11",
      "label": "Windows 11",
      "size": "15GB",
      "filesystem": "NTFS",
      "bootable": true,
      "os": {
        "name": "Windows",
        "version": "11",
        "arch": "x86-64",
        "iso": "https://example.com/windows11.iso",
        "checksum": "sha256:abc123..."
      }
    },
    {
      "id": "linux-mint",
      "label": "Linux Mint",
      "size": "15GB",
      "filesystem": "ext4",
      "bootable": true,
      "os": {
        "name": "Linux Mint",
        "version": "21.3",
        "arch": "x86-64",
        "iso": "https://example.com/linuxmint.iso",
        "checksum": "sha256:def456..."
      }
    }
  ],
  "tools": [
    {
      "id": "gparted",
      "name": "GParted",
      "version": "1.5.0",
      "size": "500MB",
      "purpose": "Partition management"
    }
  ],
  "safety": {
    "requiresConfirmation": true,
    "warningLevel": "high",
    "dataLossRisk": "Will erase USB device"
  },
  "metadata": {
    "hardwareProfile": "laptop-x86-64",
    "createdBy": "mobile-app-v6.0",
    "sourceDevice": "iPhone 15 Pro"
  }
}
```

## API Specification

### 1. Hardware Detection Endpoint

**Endpoint:** `POST /api/v1/hardware/detect`

**Purpose:** Detect the current system's hardware and return compatible OS/tool combinations.

**Request:**
```json
{
  "includeUSBDevices": true,
  "detailed": false
}
```

**Response:**
```json
{
  "success": true,
  "hardware": {
    "cpu": {
      "model": "Intel Core i7-12700K",
      "cores": 12,
      "threads": 20,
      "arch": "x86-64"
    },
    "ram": {
      "total": 32,
      "unit": "GB"
    },
    "storage": {
      "drives": [
        {
          "id": "sda",
          "model": "Samsung 990 Pro",
          "size": 2000,
          "unit": "GB",
          "type": "SSD"
        }
      ]
    },
    "gpu": {
      "model": "NVIDIA RTX 4080",
      "vram": 12,
      "unit": "GB"
    },
    "deviceType": "desktop",
    "osType": "linux",
    "osVersion": "Ubuntu 22.04"
  },
  "usbDevices": [
    {
      "id": "usb-001",
      "name": "Kingston DataTraveler",
      "size": 32,
      "unit": "GB",
      "vendor": "Kingston",
      "model": "DataTraveler 3.0",
      "path": "/dev/sdb",
      "isMounted": false
    }
  ],
  "compatibleOS": [
    {
      "name": "Windows",
      "versions": ["10", "11"],
      "arch": ["x86-64"],
      "reason": "CPU supports x86-64 architecture"
    },
    {
      "name": "Linux",
      "versions": ["Ubuntu 22.04", "Fedora 37", "Debian 12"],
      "arch": ["x86-64"],
      "reason": "CPU supports x86-64 architecture"
    },
    {
      "name": "ChromeOS Flex",
      "versions": ["Latest"],
      "arch": ["x86-64"],
      "reason": "CPU supports x86-64 architecture"
    }
  ],
  "compatibleTools": [
    {
      "name": "GParted",
      "version": "1.5.0",
      "category": "Partition Management",
      "reason": "Supports x86-64 Linux"
    },
    {
      "name": "Windows Recovery Environment",
      "version": "Latest",
      "category": "Recovery",
      "reason": "Compatible with Windows installation"
    }
  ]
}
```

**Error Responses:**
```json
{
  "success": false,
  "error": "HARDWARE_DETECTION_FAILED",
  "message": "Unable to detect hardware: Permission denied",
  "code": 500
}
```

### 2. USB Devices Enumeration Endpoint

**Endpoint:** `GET /api/v1/usb/devices`

**Purpose:** List all connected USB devices with detailed information.

**Request Parameters:**
```
?includePartitions=true
?excludeMounted=false
```

**Response:**
```json
{
  "success": true,
  "devices": [
    {
      "id": "usb-001",
      "name": "Kingston DataTraveler",
      "vendor": "Kingston",
      "model": "DataTraveler 3.0",
      "path": "/dev/sdb",
      "size": 32,
      "unit": "GB",
      "sizeBytes": 34359738368,
      "filesystem": "FAT32",
      "isMounted": false,
      "mountPoint": null,
      "isBootable": false,
      "partitions": [
        {
          "id": "sdb1",
          "size": 32,
          "unit": "GB",
          "filesystem": "FAT32",
          "label": "KINGSTON"
        }
      ],
      "safeToWrite": true,
      "warnings": []
    }
  ],
  "timestamp": "2026-04-01T12:00:00Z"
}
```

### 3. Recipe Building Endpoint

**Endpoint:** `POST /api/v1/recipe/build`

**Purpose:** Create a new recipe from selected OS and tools.

**Request:**
```json
{
  "name": "Windows 11 Installation USB",
  "description": "Bootable USB for Windows 11 installation",
  "os": {
    "name": "Windows",
    "version": "11",
    "arch": "x86-64",
    "iso": "https://example.com/windows11.iso",
    "checksum": "sha256:abc123..."
  },
  "tools": [
    {
      "id": "windows-recovery",
      "name": "Windows Recovery Environment"
    }
  ],
  "targetDevice": {
    "size": "16GB",
    "filesystem": "GPT"
  },
  "hardwareProfile": "laptop-x86-64"
}
```

**Response:**
```json
{
  "success": true,
  "recipe": {
    "id": "recipe-uuid-123",
    "version": "1.0.0",
    "name": "Windows 11 Installation USB",
    "createdAt": "2026-04-01T12:00:00Z",
    "estimatedSize": "15GB",
    "partitions": [
      {
        "id": "windows-11",
        "label": "Windows 11",
        "size": "15GB",
        "filesystem": "NTFS",
        "bootable": true
      }
    ],
    "tools": [
      {
        "id": "windows-recovery",
        "name": "Windows Recovery Environment",
        "size": "500MB"
      }
    ],
    "safety": {
      "requiresConfirmation": true,
      "warningLevel": "medium",
      "dataLossRisk": "Will erase USB device"
    },
    "qrCode": "data:image/png;base64,..."
  }
}
```

### 4. Recipe Validation Endpoint

**Endpoint:** `POST /api/v1/recipe/validate`

**Purpose:** Validate a recipe before execution.

**Request:**
```json
{
  "recipe": { /* full recipe JSON */ },
  "targetDevice": {
    "id": "usb-001",
    "path": "/dev/sdb",
    "size": "32GB"
  }
}
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "warnings": [
    {
      "level": "warning",
      "code": "DEVICE_LARGER_THAN_RECIPE",
      "message": "USB device is larger than recipe size (32GB vs 15GB). Extra space will be unused."
    }
  ],
  "errors": [],
  "estimatedTime": "15 minutes",
  "estimatedSize": "15GB"
}
```

### 5. Safety Validation Endpoint

**Endpoint:** `POST /api/v1/safety/check`

**Purpose:** Perform multi-layer safety validation before USB build.

**Request:**
```json
{
  "recipe": { /* full recipe JSON */ },
  "targetDevice": {
    "id": "usb-001",
    "path": "/dev/sdb"
  },
  "userConfirmation": true
}
```

**Response:**
```json
{
  "success": true,
  "safe": true,
  "checks": [
    {
      "name": "Device Identification",
      "status": "passed",
      "message": "Device correctly identified as Kingston DataTraveler"
    },
    {
      "name": "Partition Integrity",
      "status": "passed",
      "message": "No existing critical partitions detected"
    },
    {
      "name": "Data Loss Risk Assessment",
      "status": "passed",
      "message": "Device contains no critical system files"
    },
    {
      "name": "Bootloader Compatibility",
      "status": "passed",
      "message": "Device supports UEFI boot"
    }
  ],
  "riskLevel": "low",
  "requiresConfirmation": false
}
```

### 6. USB Build Execution Endpoint

**Endpoint:** `POST /api/v1/usb/build`

**Purpose:** Execute USB build with real-time progress streaming.

**Request:**
```json
{
  "recipe": { /* full recipe JSON */ },
  "targetDevice": {
    "id": "usb-001",
    "path": "/dev/sdb"
  },
  "buildId": "build-uuid-123"
}
```

**Response (Initial):**
```json
{
  "success": true,
  "buildId": "build-uuid-123",
  "status": "started",
  "message": "USB build started. Connect to WebSocket for progress updates.",
  "wsUrl": "wss://api.example.com/ws/build/build-uuid-123"
}
```

## WebSocket Real-Time Progress Streaming

**Connection:** `wss://api.example.com/ws/build/{buildId}`

**Messages Sent by Server:**

```json
{
  "type": "progress",
  "buildId": "build-uuid-123",
  "stage": "downloading",
  "stageNumber": 1,
  "totalStages": 5,
  "percentage": 25,
  "message": "Downloading Windows 11 ISO...",
  "timestamp": "2026-04-01T12:00:00Z"
}
```

```json
{
  "type": "status",
  "buildId": "build-uuid-123",
  "status": "writing",
  "message": "Writing to USB device...",
  "details": {
    "bytesWritten": 5368709120,
    "totalBytes": 16106127360,
    "speed": "120 MB/s",
    "timeRemaining": "90 seconds"
  },
  "timestamp": "2026-04-01T12:00:00Z"
}
```

```json
{
  "type": "completed",
  "buildId": "build-uuid-123",
  "status": "success",
  "message": "USB build completed successfully!",
  "result": {
    "totalTime": "15 minutes",
    "bytesWritten": 16106127360,
    "checksumVerified": true
  },
  "timestamp": "2026-04-01T12:00:00Z"
}
```

```json
{
  "type": "error",
  "buildId": "build-uuid-123",
  "status": "failed",
  "error": "WRITE_ERROR",
  "message": "Failed to write to USB device: I/O error",
  "recovery": "Please check USB connection and try again",
  "timestamp": "2026-04-01T12:00:00Z"
}
```

## Hardware Profile Mapping

Hardware profiles define which OSes and tools are compatible with specific hardware configurations.

```json
{
  "profiles": [
    {
      "id": "laptop-x86-64",
      "name": "Laptop (x86-64)",
      "description": "Intel/AMD 64-bit laptop",
      "hardware": {
        "cpu": {
          "arch": "x86-64",
          "minCores": 2
        },
        "ram": {
          "min": 4,
          "unit": "GB"
        }
      },
      "compatibleOS": [
        {
          "name": "Windows",
          "versions": ["10", "11"],
          "notes": "Requires UEFI firmware"
        },
        {
          "name": "Linux",
          "versions": ["Ubuntu 22.04+", "Fedora 37+", "Debian 12+"],
          "notes": "Most distributions supported"
        },
        {
          "name": "ChromeOS Flex",
          "versions": ["Latest"],
          "notes": "Good for older laptops"
        }
      ],
      "compatibleTools": [
        "GParted",
        "Windows Recovery Environment",
        "Linux Live Systems",
        "Disk Repair Utilities"
      ]
    },
    {
      "id": "desktop-x86-64",
      "name": "Desktop (x86-64)",
      "description": "Intel/AMD 64-bit desktop",
      "hardware": {
        "cpu": {
          "arch": "x86-64",
          "minCores": 4
        },
        "ram": {
          "min": 8,
          "unit": "GB"
        }
      },
      "compatibleOS": [
        {
          "name": "Windows",
          "versions": ["10", "11", "Server 2022"],
          "notes": "Full support for all editions"
        },
        {
          "name": "Linux",
          "versions": ["Ubuntu 22.04+", "Fedora 37+", "Debian 12+"],
          "notes": "All distributions supported"
        }
      ],
      "compatibleTools": [
        "GParted",
        "Windows Recovery Environment",
        "Linux Live Systems",
        "Server Installation Tools"
      ]
    },
    {
      "id": "mac-arm64",
      "name": "Mac (Apple Silicon)",
      "description": "Apple Silicon (M1/M2/M3) Mac",
      "hardware": {
        "cpu": {
          "arch": "arm64",
          "minCores": 8
        },
        "ram": {
          "min": 8,
          "unit": "GB"
        }
      },
      "compatibleOS": [
        {
          "name": "macOS",
          "versions": ["12+", "13+", "14+"],
          "notes": "Native Apple Silicon support"
        },
        {
          "name": "Linux",
          "versions": ["Ubuntu 22.04+ ARM64", "Fedora 37+ ARM64"],
          "notes": "ARM64 distributions only"
        }
      ],
      "compatibleTools": [
        "Disk Utility",
        "Linux Live Systems (ARM64)"
      ]
    }
  ]
}
```

## Safety Validation Layers

The backend implements multi-layer safety validation to prevent data loss:

### Layer 1: Device Identification
- Verify USB device is actually a removable storage device
- Check device vendor and model
- Confirm device is not a system drive

### Layer 2: Partition Integrity
- Scan for critical system partitions
- Check for EFI/UEFI partitions on system drive
- Verify no mounted filesystems on target device

### Layer 3: Data Loss Risk Assessment
- Analyze existing data on USB device
- Check for recoverable user files
- Warn about data that will be lost

### Layer 4: Bootloader Compatibility
- Verify target device supports required bootloader
- Check UEFI vs BIOS compatibility
- Validate partition table type (MBR vs GPT)

### Layer 5: Post-Build Verification
- Verify written data matches source
- Check bootloader integrity
- Validate partition table after write

## Database Schema

```sql
-- Hardware Profiles
CREATE TABLE hardware_profiles (
  id VARCHAR(255) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  cpu_arch VARCHAR(50) NOT NULL,
  min_cores INT,
  min_ram_gb INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OS Compatibility
CREATE TABLE os_compatibility (
  id INT PRIMARY KEY AUTO_INCREMENT,
  profile_id VARCHAR(255) NOT NULL,
  os_name VARCHAR(100) NOT NULL,
  os_version VARCHAR(50) NOT NULL,
  notes TEXT,
  FOREIGN KEY (profile_id) REFERENCES hardware_profiles(id)
);

-- Build History
CREATE TABLE build_history (
  id VARCHAR(255) PRIMARY KEY,
  recipe_id VARCHAR(255) NOT NULL,
  device_id VARCHAR(255),
  status VARCHAR(50) NOT NULL,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  error_message TEXT,
  total_time_seconds INT,
  bytes_written BIGINT
);

-- User Preferences
CREATE TABLE user_preferences (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id VARCHAR(255),
  preferred_os VARCHAR(100),
  preferred_tools JSON,
  saved_recipes JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Error Handling & Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Hardware detected successfully |
| 400 | Bad Request | Invalid recipe format |
| 401 | Unauthorized | User not authenticated |
| 403 | Forbidden | User lacks permission |
| 404 | Not Found | Recipe not found |
| 409 | Conflict | USB device already in use |
| 500 | Server Error | Hardware detection failed |
| 503 | Service Unavailable | Backend service down |

## Implementation Roadmap

1. **Phase 1:** Set up Flask/FastAPI backend with basic endpoints
2. **Phase 2:** Implement hardware detection and USB enumeration
3. **Phase 3:** Build recipe creation and validation
4. **Phase 4:** Implement WebSocket progress streaming
5. **Phase 5:** Integrate safety validation layers
6. **Phase 6:** Build desktop recipe consumer application
7. **Phase 7:** End-to-end testing and optimization

## Next Steps

- Review this architecture with the development team
- Confirm hardware profile definitions with PhoenixCore team
- Set up development environment for backend
- Begin Phase 1 implementation
