# Phoenix Core Enterprise - Complete API Documentation

**Version:** 2.0  
**Last Updated:** 2026-04-02  
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Storage Device Management](#storage-device-management)
4. [USB Creation Workflow](#usb-creation-workflow)
5. [Multi-Device Management](#multi-device-management)
6. [System Monitoring](#system-monitoring)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [Code Examples](#code-examples)

---

## Overview

Phoenix Core Enterprise provides a comprehensive REST API for managing storage devices, creating bootable USB drives, and controlling multiple computers remotely. All endpoints return JSON responses and support both HTTP and HTTPS protocols.

### Base URL

```
http://localhost:8000/api
https://your-domain.com/api
```

### API Features

- **30+ REST Endpoints** for complete device and system management
- **Real-time WebSocket Support** for live updates and monitoring
- **Multi-Device Management** for enterprise-scale deployments
- **Comprehensive Error Handling** with detailed error messages
- **Rate Limiting** to prevent abuse
- **Authentication** via JWT tokens (optional)

---

## Authentication

### Optional JWT Authentication

For production deployments, enable JWT authentication:

```bash
Authorization: Bearer <jwt_token>
```

### Getting an Auth Token

```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Storage Device Management

### Get All Devices

Returns all connected storage devices (USB, SSD, HDD, NVMe, virtual disks).

```
GET /api/storage/devices
```

**Response:**
```json
{
  "devices": [
    {
      "device_id": "sda",
      "device_name": "/dev/sda",
      "device_type": "ssd",
      "vendor": "Samsung",
      "model": "970 EVO Plus",
      "serial_number": "S123456789",
      "size_bytes": 1099511627776,
      "used_bytes": 549755813888,
      "free_bytes": 549755813888,
      "status": "mounted",
      "mount_point": "/mnt/sda1",
      "removable": false,
      "read_only": false,
      "health_status": "healthy",
      "temperature": 42
    }
  ],
  "total": 1
}
```

### Get USB Devices Only

```
GET /api/storage/devices/usb
```

### Get SSD Devices Only

```
GET /api/storage/devices/ssd
```

### Get HDD Devices Only

```
GET /api/storage/devices/hdd
```

### Get Virtual Devices Only

```
GET /api/storage/devices/vdd
```

### Get Storage Summary

Returns aggregated storage information across all devices.

```
GET /api/storage/summary
```

**Response:**
```json
{
  "total_devices": 5,
  "usb_devices": 2,
  "ssd_devices": 1,
  "hdd_devices": 1,
  "nvme_devices": 1,
  "vdd_devices": 0,
  "capacity": {
    "total_bytes": 5497558138880,
    "used_bytes": 2748779069440,
    "free_bytes": 2748779069440
  },
  "devices": [...]
}
```

### Mount Device

```
POST /api/storage/devices/{device_id}/mount
```

**Response:**
```json
{
  "success": true,
  "mount_point": "/mnt/usb1"
}
```

### Unmount Device

```
POST /api/storage/devices/{device_id}/unmount
```

**Response:**
```json
{
  "success": true
}
```

### Erase Device

Formats and erases a device.

```
POST /api/storage/devices/{device_id}/erase
Content-Type: application/json

{
  "filesystem": "ext4"
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "job-12345"
}
```

---

## USB Creation Workflow

### Get Available Recipes

Returns all available operating system recipes for bootable USB creation.

```
GET /api/recipes
```

**Response:**
```json
{
  "recipes": [
    {
      "recipe_id": "ubuntu-22.04",
      "name": "Ubuntu 22.04 LTS",
      "description": "Ubuntu 22.04 LTS - Long Term Support",
      "os_name": "Ubuntu",
      "os_version": "22.04 LTS",
      "image_url": "https://releases.ubuntu.com/22.04/ubuntu-22.04.4-desktop-amd64.iso",
      "image_size_mb": 4700,
      "estimated_write_time_seconds": 300,
      "supported_devices": ["usb", "ssd"]
    },
    {
      "recipe_id": "windows-11",
      "name": "Windows 11",
      "description": "Windows 11 - Latest Windows Release",
      "os_name": "Windows",
      "os_version": "11",
      "image_size_mb": 6500,
      "estimated_write_time_seconds": 420,
      "supported_devices": ["usb", "ssd"]
    }
  ],
  "total": 7
}
```

### Get Specific Recipe

```
GET /api/recipes/{recipe_id}
```

### Safety Check

Validates device and recipe compatibility before starting a build.

```
POST /api/safety-check
Content-Type: application/json

{
  "device_id": "sdb",
  "recipe_id": "ubuntu-22.04"
}
```

**Response:**
```json
{
  "safe": true,
  "warnings": [],
  "errors": []
}
```

### Start Build

Initiates a bootable USB creation job.

```
POST /api/build/start
Content-Type: application/json

{
  "device_id": "sdb",
  "recipe_id": "ubuntu-22.04"
}
```

**Response:**
```json
{
  "job_id": "job-abc123def456",
  "status": "pending",
  "recipe_id": "ubuntu-22.04",
  "device_id": "sdb",
  "progress_percent": 0,
  "current_step": "Initializing",
  "estimated_time_remaining": 300,
  "created_at": "2026-04-02T10:30:00Z"
}
```

### Get Build Progress

Monitors the progress of an ongoing build job.

```
GET /api/build/{job_id}/progress
```

**Response:**
```json
{
  "job_id": "job-abc123def456",
  "status": "running",
  "progress_percent": 45,
  "current_step": "Writing OS files",
  "estimated_time_remaining": 165
}
```

### Cancel Build

Stops an ongoing build job.

```
POST /api/build/{job_id}/cancel
```

**Response:**
```json
{
  "success": true,
  "message": "Build cancelled"
}
```

### Get All Build Jobs

```
GET /api/build/jobs
```

**Response:**
```json
{
  "jobs": [...],
  "total": 5
}
```

---

## Multi-Device Management

### Register Device

Registers a new computer for remote management.

```
POST /api/devices/register
Content-Type: application/json

{
  "device_name": "Office Desktop",
  "hostname": "office-pc-01",
  "ip_address": "192.168.1.100",
  "os_type": "windows",
  "cpu_cores": 8,
  "ram_gb": 16,
  "storage_gb": 512
}
```

**Response:**
```json
{
  "device_id": "dev-xyz789",
  "device_name": "Office Desktop",
  "hostname": "office-pc-01",
  "ip_address": "192.168.1.100",
  "os_type": "windows",
  "status": "online",
  "last_seen": "2026-04-02T10:35:00Z",
  "cpu_cores": 8,
  "ram_gb": 16,
  "storage_gb": 512,
  "connected_usb_devices": 2
}
```

### Get Registered Devices

```
GET /api/devices/registered
```

### Get Device Details

```
GET /api/devices/{device_id}
```

### Unregister Device

```
POST /api/devices/{device_id}/unregister
```

### Update Device Status

```
POST /api/devices/{device_id}/status?status=online
```

### Create Device Group

Groups multiple devices for bulk operations.

```
POST /api/groups/create
Content-Type: application/json

{
  "group_name": "Office Workstations",
  "description": "All office desktop computers",
  "device_ids": ["dev-xyz789", "dev-abc123"]
}
```

**Response:**
```json
{
  "group_id": "grp-office-01",
  "group_name": "Office Workstations",
  "description": "All office desktop computers",
  "device_ids": ["dev-xyz789", "dev-abc123"],
  "created_at": "2026-04-02T10:40:00Z"
}
```

### Get All Groups

```
GET /api/groups
```

### Add Device to Group

```
POST /api/groups/{group_id}/add-device?device_id={device_id}
```

### Remove Device from Group

```
POST /api/groups/{group_id}/remove-device?device_id={device_id}
```

### Start Bulk Operation

Execute an operation on multiple devices simultaneously.

```
POST /api/bulk-operation
Content-Type: application/json

{
  "operation": "scan",
  "device_ids": ["dev-xyz789", "dev-abc123"],
  "parameters": {}
}
```

**Supported Operations:**
- `mount` - Mount all USB devices
- `unmount` - Unmount all USB devices
- `scan` - Scan for new devices
- `status` - Get device status
- `reboot` - Reboot device
- `shutdown` - Shutdown device

**Response:**
```json
{
  "operation_id": "op-bulk-001",
  "operation": "scan",
  "status": "completed",
  "total_devices": 2,
  "completed_devices": 2,
  "failed_devices": 0,
  "results": {
    "dev-xyz789": {
      "status": "success",
      "message": "Scan completed on Office Desktop"
    },
    "dev-abc123": {
      "status": "success",
      "message": "Scan completed on Laptop"
    }
  }
}
```

### Get Dashboard Summary

```
GET /api/dashboard/summary
```

**Response:**
```json
{
  "total_devices": 5,
  "online_devices": 4,
  "offline_devices": 1,
  "busy_devices": 0,
  "total_groups": 2,
  "total_cpu_cores": 32,
  "total_ram_gb": 64,
  "total_storage_gb": 2048,
  "total_usb_devices": 8,
  "devices_by_os": {
    "windows": 3,
    "macos": 1,
    "linux": 1
  }
}
```

### Send Remote Command

```
POST /api/devices/{device_id}/remote-command?command=scan
Content-Type: application/json

{
  "parameters": {}
}
```

---

## System Monitoring

### Get System Metrics

Returns real-time CPU, memory, and disk metrics.

```
GET /api/system/metrics
```

**Response:**
```json
{
  "cpu_percent": 42.5,
  "memory_percent": 68.2,
  "memory_available_mb": 8192,
  "memory_total_mb": 16384,
  "disk_percent": 55.3,
  "disk_free_gb": 256,
  "disk_total_gb": 512,
  "uptime_seconds": 864000,
  "timestamp": "2026-04-02T10:45:00Z"
}
```

### Get Hardware Profile

```
GET /api/hardware
```

**Response:**
```json
{
  "cpu_model": "Intel Core i7-10700K",
  "cpu_cores": 8,
  "cpu_threads": 16,
  "cpu_frequency_ghz": 3.8,
  "ram_gb": 32,
  "disk_total_gb": 1024,
  "gpu_model": "NVIDIA RTX 3080",
  "os_name": "Windows",
  "os_version": "11",
  "hostname": "workstation-01",
  "architecture": "x86_64"
}
```

### Get System Information

```
GET /api/system/info
```

### Health Check

```
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime_seconds": 864000
}
```

---

## Error Handling

All errors return a consistent JSON format:

```json
{
  "error": "Device not found",
  "detail": "Device with ID 'sdc' does not exist",
  "status_code": 404,
  "timestamp": "2026-04-02T10:50:00Z"
}
```

### Common Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 400 | Bad Request | Invalid parameters or malformed request |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Operation conflicts with current state |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

---

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Default:** 1000 requests per hour per IP
- **Burst:** 100 requests per minute

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1648901400
```

---

## Code Examples

### Python Example

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

# Get all devices
response = requests.get(f"{BASE_URL}/storage/devices")
devices = response.json()["devices"]

# Start USB build
build_data = {
    "device_id": "sdb",
    "recipe_id": "ubuntu-22.04"
}
response = requests.post(f"{BASE_URL}/build/start", json=build_data)
job = response.json()

# Monitor progress
job_id = job["job_id"]
while True:
    response = requests.get(f"{BASE_URL}/build/{job_id}/progress")
    progress = response.json()
    print(f"Progress: {progress['progress_percent']}% - {progress['current_step']}")
    
    if progress["status"] == "completed":
        break
    
    time.sleep(1)
```

### JavaScript Example

```javascript
const BASE_URL = "http://localhost:8000/api";

// Get all devices
async function getAllDevices() {
  const response = await fetch(`${BASE_URL}/storage/devices`);
  const data = await response.json();
  return data.devices;
}

// Start USB build
async function startBuild(deviceId, recipeId) {
  const response = await fetch(`${BASE_URL}/build/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      device_id: deviceId,
      recipe_id: recipeId
    })
  });
  return await response.json();
}

// Monitor progress
async function monitorBuild(jobId) {
  while (true) {
    const response = await fetch(`${BASE_URL}/build/${jobId}/progress`);
    const progress = await response.json();
    console.log(`${progress.progress_percent}% - ${progress.current_step}`);
    
    if (progress.status === "completed") break;
    
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
}
```

### cURL Examples

```bash
# Get all devices
curl -X GET http://localhost:8000/api/storage/devices

# Start USB build
curl -X POST http://localhost:8000/api/build/start \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "sdb",
    "recipe_id": "ubuntu-22.04"
  }'

# Get build progress
curl -X GET http://localhost:8000/api/build/job-abc123/progress

# Register device
curl -X POST http://localhost:8000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "Office Desktop",
    "hostname": "office-pc-01",
    "ip_address": "192.168.1.100",
    "os_type": "windows",
    "cpu_cores": 8,
    "ram_gb": 16,
    "storage_gb": 512
  }'
```

---

## WebSocket Real-Time Updates

Connect to the WebSocket endpoint for real-time device and build updates:

```javascript
const ws = new WebSocket("ws://localhost:8000/api/ws");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Update:", data);
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};
```

---

## Support & Documentation

For additional help:
- **GitHub:** https://github.com/Bboy9090/PhoenixCore-
- **Issues:** Report bugs and request features
- **Discussions:** Community support and discussions

---

**Phoenix Core Enterprise v2.0** - Professional OS Deployment & Storage Management
