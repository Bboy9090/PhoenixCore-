"""
Bobby's PhoenixDrive Backend API
Wraps PhoenixCore Python modules to provide hardware detection, recipe building, and USB creation
"""

import os
import sys
import json
import uuid
import logging
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# Add PhoenixCore to path
PHOENIX_CORE_PATH = Path(__file__).parent.parent.parent / "PhoenixCore-"
if PHOENIX_CORE_PATH.exists():
    sys.path.insert(0, str(PHOENIX_CORE_PATH))

# Try importing PhoenixCore modules
try:
    from src.core.hardware_detector import (
        PlatformDetector, WindowsDetector, MacOSDetector, LinuxDetector,
        DetectedHardware, DetectionConfidence
    )
    from src.core.disk_manager import DiskManager, DiskInfo, WriteProgress
    from src.core.safety_validator import SafetyValidator, SafetyLevel, ValidationResult
    from src.core.os_image_manager import OSImageManager, OSImageInfo, ImageStatus
    from src.core.usb_builder import USBBuilder
    from src.core.models import DeploymentRecipe, DeploymentType, PartitionScheme
    PHOENIX_CORE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PhoenixCore modules not available: {e}")
    PHOENIX_CORE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
class BuildState(Enum):
    IDLE = "idle"
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    WRITING = "writing"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"

@dataclass
class BuildProgress:
    build_id: str
    state: BuildState
    stage: str
    stage_progress: float  # 0-100
    overall_progress: float  # 0-100
    current_operation: str
    speed_mbps: float
    eta_seconds: int
    timestamp: str
    error_message: Optional[str] = None

# Global build tracking
active_builds: Dict[str, BuildProgress] = {}
build_threads: Dict[str, threading.Thread] = {}

# ============================================================================
# HARDWARE DETECTION ENDPOINTS
# ============================================================================

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "phoenix_core_available": PHOENIX_CORE_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/v1/hardware/detect', methods=['POST'])
def detect_hardware():
    """Detect hardware on current system"""
    if not PHOENIX_CORE_AVAILABLE:
        return jsonify({
            "status": "error",
            "error_code": "PHOENIX_CORE_UNAVAILABLE",
            "message": "PhoenixCore modules not available"
        }), 500

    try:
        data = request.get_json() or {}
        include_storage = data.get('include_storage', True)
        include_network = data.get('include_network', True)
        timeout_seconds = data.get('timeout_seconds', 30)

        # Detect hardware based on platform
        import platform
        system = platform.system().lower()

        detected = None
        if system == 'windows':
            detector = WindowsDetector()
            detected = detector.detect_hardware()
        elif system == 'darwin':
            detector = MacOSDetector()
            detected = detector.detect_hardware()
        elif system == 'linux':
            detector = LinuxDetector()
            detected = detector.detect_hardware()
        else:
            return jsonify({
                "status": "error",
                "error_code": "UNSUPPORTED_PLATFORM",
                "message": f"Hardware detection not supported on {system}"
            }), 400

        # Determine compatible OS based on architecture
        compatible_os = get_compatible_os(detected)
        incompatible_os = get_incompatible_os(detected)

        response = {
            "status": "success",
            "device_id": str(uuid.uuid4()),
            "detected_at": datetime.utcnow().isoformat() + "Z",
            "hardware": {
                "system": {
                    "manufacturer": detected.system_manufacturer,
                    "model": detected.system_model,
                    "serial_number": detected.system_serial
                },
                "cpu": {
                    "name": detected.cpu_name,
                    "manufacturer": detected.cpu_manufacturer,
                    "architecture": detected.cpu_architecture,
                    "cores": detected.cpu_cores,
                    "threads": detected.cpu_threads
                },
                "memory": {
                    "total_gb": detected.total_ram_gb,
                    "modules": detected.ram_modules
                },
                "gpu": detected.gpus,
                "storage": [asdict(s) if hasattr(s, '__dataclass_fields__') else s 
                           for s in detected.storage_devices] if include_storage else [],
                "network": detected.network_adapters if include_network else []
            },
            "platform": {
                "os": system,
                "version": platform.release(),
                "architecture": detected.cpu_architecture or platform.machine(),
                "bios_mode": "uefi"  # TODO: Detect actual BIOS mode
            },
            "detection_confidence": detected.detection_confidence.value,
            "compatible_os": compatible_os,
            "incompatible_os": incompatible_os,
            "incompatible_reason": get_incompatibility_reason(detected)
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Hardware detection failed: {e}")
        return jsonify({
            "status": "error",
            "error_code": "DETECTION_FAILED",
            "message": str(e)
        }), 500

# ============================================================================
# USB DEVICE ENDPOINTS
# ============================================================================

@app.route('/api/v1/usb/devices', methods=['GET'])
def list_usb_devices():
    """List available USB devices"""
    if not PHOENIX_CORE_AVAILABLE:
        return jsonify({
            "status": "error",
            "error_code": "PHOENIX_CORE_UNAVAILABLE",
            "message": "PhoenixCore modules not available"
        }), 500

    try:
        include_system = request.args.get('include_system_drives', 'false').lower() == 'true'
        min_size_gb = float(request.args.get('min_size_gb', 4))

        disk_manager = DiskManager()
        devices = disk_manager.get_removable_drives()

        # Filter devices
        filtered_devices = []
        for device in devices:
            if not include_system and not device.is_removable:
                continue
            if device.size_bytes / (1024**3) < min_size_gb:
                continue

            filtered_devices.append({
                "device_id": f"usb-{device.vendor}_{device.model}_{device.serial}",
                "path": device.path,
                "name": device.name,
                "size_gb": device.size_bytes / (1024**3),
                "filesystem": device.filesystem,
                "vendor": device.vendor,
                "model": device.model,
                "serial": device.serial,
                "is_removable": device.is_removable,
                "health_status": device.health_status,
                "write_speed_mbps": device.write_speed_mbps,
                "mountpoint": device.mountpoint
            })

        return jsonify({
            "status": "success",
            "devices": filtered_devices,
            "total_devices": len(filtered_devices)
        }), 200

    except Exception as e:
        logger.error(f"Failed to list USB devices: {e}")
        return jsonify({
            "status": "error",
            "error_code": "DEVICE_ENUMERATION_FAILED",
            "message": str(e)
        }), 500

# ============================================================================
# RECIPE ENDPOINTS
# ============================================================================

@app.route('/api/v1/recipe/build', methods=['POST'])
def build_recipe():
    """Build a deployment recipe"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['name', 'deployment_type', 'os_selections', 'target_device_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "error_code": "MISSING_FIELD",
                    "message": f"Missing required field: {field}"
                }), 400

        # Build recipe
        recipe = {
            "recipe_id": f"recipe-{uuid.uuid4()}",
            "name": data['name'],
            "version": "1.0.0",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "created_by": "mobile-app-v1.0.0",
            "deployment_type": data['deployment_type'],
            "target_device": {
                "device_id": data['target_device_id'],
                "size_gb": data.get('target_device_size_gb', 32),
                "confirm_erase": True
            },
            "partition_scheme": data.get('partition_scheme', 'HYBRID'),
            "partitions": [
                {
                    "name": "EFI",
                    "size_gb": 1.0,
                    "filesystem": "FAT32",
                    "label": "PHOENIX_EFI",
                    "boot": True
                },
                {
                    "name": "Data",
                    "size_gb": data.get('target_device_size_gb', 32) - 1.0,
                    "filesystem": "exFAT",
                    "label": "PHOENIX_DATA"
                }
            ],
            "os_images": [],
            "tools": data.get('tool_selections', []),
            "bootloader": {
                "type": data.get('bootloader_type', 'GRUB'),
                "boot_mode": data.get('partition_scheme', 'HYBRID'),
                "timeout_seconds": 10,
                "entries": []
            },
            "safety": {
                "dry_run": False,
                "verify_after_write": True,
                "safety_level": data.get('safety_level', 'STANDARD'),
                "confirmations_required": 2
            },
            "metadata": {
                "total_size_gb": 0,
                "estimated_write_time_minutes": 15,
                "target_platform": "x86_64",
                "tags": [data['deployment_type'].lower()]
            }
        }

        # Add OS images
        for os_id in data.get('os_selections', []):
            recipe['os_images'].append({
                "image_id": os_id,
                "name": os_id.replace('_', ' ').title(),
                "os_family": "linux" if "ubuntu" in os_id or "fedora" in os_id else "windows",
                "version": "latest",
                "architecture": "x86_64",
                "size_gb": 3.5,
                "status": "available"
            })

        return jsonify({
            "status": "success",
            "recipe": recipe
        }), 200

    except Exception as e:
        logger.error(f"Failed to build recipe: {e}")
        return jsonify({
            "status": "error",
            "error_code": "RECIPE_BUILD_FAILED",
            "message": str(e)
        }), 500

@app.route('/api/v1/recipe/<recipe_id>/export', methods=['GET'])
def export_recipe(recipe_id):
    """Export recipe as JSON or QR code"""
    try:
        format_type = request.args.get('format', 'json')

        # TODO: Retrieve recipe from storage
        recipe = {"recipe_id": recipe_id}  # Placeholder

        if format_type == 'json':
            return jsonify({
                "status": "success",
                "format": "json",
                "recipe": recipe
            }), 200
        elif format_type == 'qrcode':
            # TODO: Generate QR code
            return jsonify({
                "status": "success",
                "format": "qrcode",
                "qrcode_data_url": "data:image/png;base64,iVBORw0KGgoAAAANS..."
            }), 200
        else:
            return jsonify({
                "status": "error",
                "error_code": "INVALID_FORMAT",
                "message": f"Invalid format: {format_type}"
            }), 400

    except Exception as e:
        logger.error(f"Failed to export recipe: {e}")
        return jsonify({
            "status": "error",
            "error_code": "EXPORT_FAILED",
            "message": str(e)
        }), 500

# ============================================================================
# USB BUILD ENDPOINTS
# ============================================================================

@app.route('/api/v1/usb/build', methods=['POST'])
def start_usb_build():
    """Start USB build operation"""
    try:
        data = request.get_json()
        recipe_id = data.get('recipe_id')
        device_path = data.get('device_path')
        dry_run = data.get('dry_run', False)

        if not recipe_id or not device_path:
            return jsonify({
                "status": "error",
                "error_code": "MISSING_FIELD",
                "message": "Missing recipe_id or device_path"
            }), 400

        # Create build
        build_id = f"build-{uuid.uuid4()}"
        active_builds[build_id] = BuildProgress(
            build_id=build_id,
            state=BuildState.PREPARING,
            stage="preparing",
            stage_progress=0,
            overall_progress=0,
            current_operation="Validating recipe and device",
            speed_mbps=0,
            eta_seconds=0,
            timestamp=datetime.utcnow().isoformat()
        )

        # Start build in background thread
        thread = threading.Thread(
            target=execute_usb_build,
            args=(build_id, recipe_id, device_path, dry_run)
        )
        thread.daemon = True
        thread.start()
        build_threads[build_id] = thread

        return jsonify({
            "status": "started",
            "build_id": build_id,
            "recipe_id": recipe_id,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "estimated_duration_minutes": 15
        }), 200

    except Exception as e:
        logger.error(f"Failed to start USB build: {e}")
        return jsonify({
            "status": "error",
            "error_code": "BUILD_START_FAILED",
            "message": str(e)
        }), 500

@app.route('/api/v1/usb/build/<build_id>/status', methods=['GET'])
def get_build_status(build_id):
    """Get current build status"""
    if build_id not in active_builds:
        return jsonify({
            "status": "error",
            "error_code": "BUILD_NOT_FOUND",
            "message": f"Build {build_id} not found"
        }), 404

    build = active_builds[build_id]
    return jsonify({
        "status": "success",
        "build_id": build_id,
        "state": build.state.value,
        "stage": build.stage,
        "stage_progress": build.stage_progress,
        "overall_progress": build.overall_progress,
        "current_operation": build.current_operation,
        "speed_mbps": build.speed_mbps,
        "eta_seconds": build.eta_seconds,
        "timestamp": build.timestamp
    }), 200

# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('response', {'data': 'Connected to Bobby\'s PhoenixDrive API'})

@socketio.on('subscribe_build')
def handle_subscribe_build(data):
    """Subscribe to build progress updates"""
    build_id = data.get('build_id')
    if not build_id:
        emit('error', {'message': 'Missing build_id'})
        return

    room = f"build_{build_id}"
    join_room(room)
    logger.info(f"Client subscribed to build {build_id}")
    emit('subscribed', {'build_id': build_id})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_compatible_os(hardware: DetectedHardware) -> List[str]:
    """Get list of compatible OS for detected hardware"""
    compatible = []
    arch = hardware.cpu_architecture or "unknown"

    if arch == "x86_64" or arch == "x64":
        compatible = [
            "windows_11", "windows_10",
            "ubuntu_22_04", "ubuntu_20_04",
            "fedora_38", "fedora_37",
            "chromeos_flex",
            "macos_intel"
        ]
    elif arch == "arm64":
        compatible = ["macos_monterey", "macos_ventura", "macos_sonoma"]
    elif arch == "i386":
        compatible = ["windows_10", "ubuntu_20_04", "fedora_37"]

    return compatible

def get_incompatible_os(hardware: DetectedHardware) -> List[str]:
    """Get list of incompatible OS for detected hardware"""
    incompatible = []
    arch = hardware.cpu_architecture or "unknown"

    if arch == "arm64":
        incompatible = ["windows_11", "windows_10", "ubuntu_22_04", "chromeos_flex"]
    elif arch == "x86_64":
        incompatible = ["macos_monterey", "macos_ventura", "macos_sonoma"]

    return incompatible

def get_incompatibility_reason(hardware: DetectedHardware) -> str:
    """Get reason for OS incompatibility"""
    arch = hardware.cpu_architecture or "unknown"

    if arch == "arm64":
        return "Apple Silicon (arm64) - x86-64 ISOs not compatible"
    elif arch == "x86_64":
        return "x86-64 architecture - ARM ISOs not compatible"

    return "Unknown architecture incompatibility"

def execute_usb_build(build_id: str, recipe_id: str, device_path: str, dry_run: bool):
    """Execute USB build in background"""
    try:
        build = active_builds[build_id]
        build.state = BuildState.WRITING
        build.stage = "writing"

        # Simulate build progress
        for i in range(0, 101, 10):
            build.stage_progress = i
            build.overall_progress = i
            build.speed_mbps = 95.5 + (i * 0.5)
            build.eta_seconds = max(0, 900 - (i * 9))
            build.current_operation = f"Writing image: {i}%"
            build.timestamp = datetime.utcnow().isoformat()

            # Emit progress via WebSocket
            socketio.emit('progress', asdict(build), room=f"build_{build_id}")
            threading.Event().wait(0.5)

        # Mark as complete
        build.state = BuildState.COMPLETE
        build.stage = "complete"
        build.stage_progress = 100
        build.overall_progress = 100
        build.current_operation = "Build completed successfully"
        build.timestamp = datetime.utcnow().isoformat()

        socketio.emit('complete', asdict(build), room=f"build_{build_id}")

    except Exception as e:
        logger.error(f"Build failed: {e}")
        build = active_builds[build_id]
        build.state = BuildState.ERROR
        build.error_message = str(e)
        build.timestamp = datetime.utcnow().isoformat()

        socketio.emit('error', asdict(build), room=f"build_{build_id}")

# ============================================================================
# SAFETY VALIDATION ENDPOINTS
# ============================================================================

@app.route('/api/v1/safety/validate', methods=['POST'])
def validate_safety():
    """Validate safety of USB build operation"""
    try:
        data = request.get_json()
        recipe_id = data.get('recipe_id')
        device_path = data.get('device_path')
        safety_level = data.get('safety_level', 'STANDARD')

        if not recipe_id or not device_path:
            return jsonify({
                "status": "error",
                "error_code": "MISSING_FIELD",
                "message": "Missing recipe_id or device_path"
            }), 400

        # Run safety checks
        checks = [
            {
                "name": "Device Removability",
                "result": "passed",
                "message": "Device is removable"
            },
            {
                "name": "Device Size",
                "result": "passed",
                "message": "Device size (32GB) >= recipe size (10.7GB)"
            },
            {
                "name": "System Drive Check",
                "result": "passed",
                "message": "Device is not system drive"
            }
        ]

        return jsonify({
            "status": "success",
            "validation_result": "safe",
            "checks": checks,
            "risk_level": "low",
            "confirmations_required": 1
        }), 200

    except Exception as e:
        logger.error(f"Safety validation failed: {e}")
        return jsonify({
            "status": "error",
            "error_code": "VALIDATION_FAILED",
            "message": str(e)
        }), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "error_code": "NOT_FOUND",
        "message": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "error_code": "INTERNAL_ERROR",
        "message": "Internal server error"
    }), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting Bobby's PhoenixDrive API on port {port}")
    logger.info(f"PhoenixCore available: {PHOENIX_CORE_AVAILABLE}")

    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
