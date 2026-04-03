"""
Phoenix Core Enterprise - Multi-Device Management Routes
Manage multiple computers and devices from a single dashboard
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

router = APIRouter(prefix="/api", tags=["Multi-Device Management"])

# In-memory device registry (replace with database in production)
registered_devices = {}
device_groups = {}

class RegisteredDevice(BaseModel):
    device_id: str
    device_name: str
    hostname: str
    ip_address: str
    os_type: str  # windows, macos, linux
    status: str  # online, offline, busy
    last_seen: str
    cpu_cores: int
    ram_gb: int
    storage_gb: int
    connected_usb_devices: int
    group_id: Optional[str] = None

class DeviceGroup(BaseModel):
    group_id: str
    group_name: str
    description: Optional[str] = None
    device_ids: List[str]
    created_at: str

class RegisterDeviceRequest(BaseModel):
    device_name: str
    hostname: str
    ip_address: str
    os_type: str
    cpu_cores: int
    ram_gb: int
    storage_gb: int

class CreateGroupRequest(BaseModel):
    group_name: str
    description: Optional[str] = None
    device_ids: List[str] = []

class BulkOperationRequest(BaseModel):
    operation: str  # mount, unmount, scan, status
    device_ids: List[str]
    parameters: Optional[dict] = None

class BulkOperationResult(BaseModel):
    operation_id: str
    operation: str
    status: str  # pending, running, completed, failed
    total_devices: int
    completed_devices: int
    failed_devices: int
    results: dict

# Bulk operation tracking
bulk_operations = {}

@router.post("/devices/register", response_model=RegisteredDevice)
async def register_device(request: RegisterDeviceRequest):
    """Register a new device for remote management"""
    device_id = str(uuid.uuid4())
    
    device = {
        "device_id": device_id,
        "device_name": request.device_name,
        "hostname": request.hostname,
        "ip_address": request.ip_address,
        "os_type": request.os_type,
        "status": "online",
        "last_seen": datetime.now().isoformat(),
        "cpu_cores": request.cpu_cores,
        "ram_gb": request.ram_gb,
        "storage_gb": request.storage_gb,
        "connected_usb_devices": 0,
        "group_id": None,
    }
    
    registered_devices[device_id] = device
    return RegisteredDevice(**device)

@router.get("/devices/registered", response_model=dict)
async def get_registered_devices():
    """Get all registered devices"""
    return {
        "devices": list(registered_devices.values()),
        "total": len(registered_devices),
    }

@router.get("/devices/{device_id}", response_model=RegisteredDevice)
async def get_device(device_id: str):
    """Get specific device details"""
    if device_id not in registered_devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return RegisteredDevice(**registered_devices[device_id])

@router.post("/devices/{device_id}/unregister", response_model=dict)
async def unregister_device(device_id: str):
    """Unregister a device from remote management"""
    if device_id not in registered_devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    del registered_devices[device_id]
    
    # Remove from groups
    for group in device_groups.values():
        if device_id in group["device_ids"]:
            group["device_ids"].remove(device_id)
    
    return {"success": True, "message": "Device unregistered"}

@router.post("/devices/{device_id}/status", response_model=dict)
async def update_device_status(device_id: str, status: str):
    """Update device status"""
    if device_id not in registered_devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if status not in ["online", "offline", "busy"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    registered_devices[device_id]["status"] = status
    registered_devices[device_id]["last_seen"] = datetime.now().isoformat()
    
    return {"success": True, "status": status}

@router.post("/groups/create", response_model=DeviceGroup)
async def create_group(request: CreateGroupRequest):
    """Create a device group"""
    group_id = str(uuid.uuid4())
    
    # Validate devices exist
    for device_id in request.device_ids:
        if device_id not in registered_devices:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    group = {
        "group_id": group_id,
        "group_name": request.group_name,
        "description": request.description,
        "device_ids": request.device_ids,
        "created_at": datetime.now().isoformat(),
    }
    
    device_groups[group_id] = group
    
    # Update device group assignments
    for device_id in request.device_ids:
        registered_devices[device_id]["group_id"] = group_id
    
    return DeviceGroup(**group)

@router.get("/groups", response_model=dict)
async def get_groups():
    """Get all device groups"""
    return {
        "groups": list(device_groups.values()),
        "total": len(device_groups),
    }

@router.get("/groups/{group_id}", response_model=DeviceGroup)
async def get_group(group_id: str):
    """Get specific group details"""
    if group_id not in device_groups:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return DeviceGroup(**device_groups[group_id])

@router.post("/groups/{group_id}/add-device", response_model=DeviceGroup)
async def add_device_to_group(group_id: str, device_id: str):
    """Add device to group"""
    if group_id not in device_groups:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if device_id not in registered_devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    group = device_groups[group_id]
    if device_id not in group["device_ids"]:
        group["device_ids"].append(device_id)
        registered_devices[device_id]["group_id"] = group_id
    
    return DeviceGroup(**group)

@router.post("/groups/{group_id}/remove-device", response_model=DeviceGroup)
async def remove_device_from_group(group_id: str, device_id: str):
    """Remove device from group"""
    if group_id not in device_groups:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group = device_groups[group_id]
    if device_id in group["device_ids"]:
        group["device_ids"].remove(device_id)
        registered_devices[device_id]["group_id"] = None
    
    return DeviceGroup(**group)

@router.post("/bulk-operation", response_model=BulkOperationResult)
async def start_bulk_operation(request: BulkOperationRequest):
    """Start a bulk operation on multiple devices"""
    operation_id = str(uuid.uuid4())
    
    # Validate devices
    for device_id in request.device_ids:
        if device_id not in registered_devices:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    # Validate operation
    valid_operations = ["mount", "unmount", "scan", "status", "reboot", "shutdown"]
    if request.operation not in valid_operations:
        raise HTTPException(status_code=400, detail=f"Invalid operation: {request.operation}")
    
    operation = {
        "operation_id": operation_id,
        "operation": request.operation,
        "status": "running",
        "total_devices": len(request.device_ids),
        "completed_devices": 0,
        "failed_devices": 0,
        "results": {},
    }
    
    bulk_operations[operation_id] = operation
    
    # Simulate operation execution
    for device_id in request.device_ids:
        operation["results"][device_id] = {
            "status": "success",
            "message": f"{request.operation} completed on {registered_devices[device_id]['device_name']}",
        }
        operation["completed_devices"] += 1
    
    operation["status"] = "completed"
    
    return BulkOperationResult(**operation)

@router.get("/bulk-operation/{operation_id}", response_model=BulkOperationResult)
async def get_bulk_operation_status(operation_id: str):
    """Get bulk operation status"""
    if operation_id not in bulk_operations:
        raise HTTPException(status_code=404, detail="Operation not found")
    
    return BulkOperationResult(**bulk_operations[operation_id])

@router.get("/dashboard/summary", response_model=dict)
async def get_dashboard_summary():
    """Get overall dashboard summary"""
    online_devices = sum(1 for d in registered_devices.values() if d["status"] == "online")
    offline_devices = sum(1 for d in registered_devices.values() if d["status"] == "offline")
    busy_devices = sum(1 for d in registered_devices.values() if d["status"] == "busy")
    
    total_cpu_cores = sum(d["cpu_cores"] for d in registered_devices.values())
    total_ram_gb = sum(d["ram_gb"] for d in registered_devices.values())
    total_storage_gb = sum(d["storage_gb"] for d in registered_devices.values())
    total_usb_devices = sum(d["connected_usb_devices"] for d in registered_devices.values())
    
    return {
        "total_devices": len(registered_devices),
        "online_devices": online_devices,
        "offline_devices": offline_devices,
        "busy_devices": busy_devices,
        "total_groups": len(device_groups),
        "total_cpu_cores": total_cpu_cores,
        "total_ram_gb": total_ram_gb,
        "total_storage_gb": total_storage_gb,
        "total_usb_devices": total_usb_devices,
        "devices_by_os": {
            "windows": sum(1 for d in registered_devices.values() if d["os_type"] == "windows"),
            "macos": sum(1 for d in registered_devices.values() if d["os_type"] == "macos"),
            "linux": sum(1 for d in registered_devices.values() if d["os_type"] == "linux"),
        },
    }

@router.post("/devices/{device_id}/remote-command", response_model=dict)
async def send_remote_command(device_id: str, command: str, parameters: Optional[dict] = None):
    """Send a remote command to a device"""
    if device_id not in registered_devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device = registered_devices[device_id]
    
    if device["status"] != "online":
        raise HTTPException(status_code=400, detail="Device is not online")
    
    # Simulate command execution
    return {
        "success": True,
        "device_id": device_id,
        "command": command,
        "message": f"Command '{command}' sent to {device['device_name']}",
        "timestamp": datetime.now().isoformat(),
    }
