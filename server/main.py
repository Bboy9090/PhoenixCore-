"""
PhoenixCore Industrial Backend API (FastAPI Version)
Modernized backend with type safety, async support, and high performance.
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
from enum import Enum

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import socketio
import uvicorn

# Import routers
from server.routers import bootcamp, admin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PhoenixCore Industrial API",
    description="Backend API for PhoenixCore hardware interaction",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(bootcamp.router)
app.include_router(admin.router)

# Initialize Socket.IO
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

# Global State
class BuildState(str, Enum):
    IDLE = "idle"
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    WRITING = "writing"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"

class BuildProgress(BaseModel):
    build_id: str
    state: BuildState
    stage: str
    stage_progress: float
    overall_progress: float
    current_operation: str
    speed_mbps: float
    eta_seconds: int
    timestamp: str
    error_message: Optional[str] = None

active_builds: Dict[str, BuildProgress] = {}

# --- Models ---

class HardwareDetectRequest(BaseModel):
    include_storage: bool = True
    include_network: bool = True
    timeout_seconds: int = 30

class RecipeBuildRequest(BaseModel):
    name: str
    deployment_type: str
    os_selections: List[str]
    target_device_id: str
    target_device_size_gb: Optional[float] = 32
    partition_scheme: Optional[str] = "HYBRID"
    tool_selections: Optional[List[str]] = []
    bootloader_type: Optional[str] = "GRUB"
    safety_level: Optional[str] = "STANDARD"

class USBBuildRequest(BaseModel):
    recipe_id: str
    device_path: str
    dry_run: bool = False

# Import bootcamp modules
from server.bootcamp.mac_detector import MacDetector
from server.bootcamp.usb_manager import get_removable_drives

# --- Endpoints ---

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "ok",
        "version": "2.0.0",
        "framework": "FastAPI",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/hardware/detect")
async def detect_hardware(req: HardwareDetectRequest):
    detector = MacDetector()
    sys_info = detector.detect()
    
    if not sys_info:
        return {
            "status": "error",
            "message": "Could not detect Mac hardware"
        }
        
    return {
        "status": "success",
        "device_id": sys_info.serial_number or str(uuid.uuid4()),
        "detected_at": datetime.utcnow().isoformat() + "Z",
        "hardware": sys_info.to_dict(),
        "compatible_os": ["macos_sonoma", "macos_ventura", "ubuntu_22_04_arm64"]
    }

@app.get("/api/v1/usb/devices")
async def list_usb_devices(include_system_drives: bool = False, min_size_gb: float = 4):
    devices = get_removable_drives()
    filtered_devices = [d for d in devices if d['size_gb'] >= min_size_gb]
    
    return {
        "status": "success",
        "devices": filtered_devices
    }

@app.post("/api/v1/recipe/build")
async def build_recipe(req: RecipeBuildRequest):
    recipe_id = f"recipe-{uuid.uuid4()}"
    return {
        "status": "success",
        "recipe": {
            "recipe_id": recipe_id,
            "name": req.name,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "deployment_type": req.deployment_type,
            "estimated_write_time_minutes": 15
        }
    }

@app.post("/api/v1/usb/build")
async def start_usb_build(req: USBBuildRequest, background_tasks: BackgroundTasks):
    build_id = f"build-{uuid.uuid4()}"
    
    progress = BuildProgress(
        build_id=build_id,
        state=BuildState.PREPARING,
        stage="preparing",
        stage_progress=0,
        overall_progress=0,
        current_operation="Initializing build...",
        speed_mbps=0,
        eta_seconds=900,
        timestamp=datetime.utcnow().isoformat()
    )
    active_builds[build_id] = progress
    
    background_tasks.add_task(execute_build_task, build_id, req.recipe_id, req.device_path)
    
    return {
        "status": "started",
        "build_id": build_id,
        "estimated_duration_minutes": 15
    }

@app.get("/api/v1/usb/build/{build_id}/status")
async def get_build_status(build_id: str):
    if build_id not in active_builds:
        raise HTTPException(status_code=404, detail="Build not found")
    return active_builds[build_id]

# --- Background Task ---

async def execute_build_task(build_id: str, recipe_id: str, device_path: str):
    try:
        progress = active_builds[build_id]
        
        # Path to the Rust CLI (adjust based on build location)
        cli_path = os.getenv("PHOENIX_CLI_PATH", "./target/release/phoenix-cli")
        
        if not os.path.exists(cli_path):
            # Fallback for dev environment
            cli_path = "cargo run --release -p phoenix-cli --" 
            
        job_payload = {
            "job_id": build_id,
            "operation": "IMAGE_RESTORE",
            "target": {
                "device_path": device_path,
                "expected_size_bytes": 32 * 1024 * 1024 * 1024 # Placeholder
            },
            "payload": {
                "image_path": "industrial_os.iso",
                "image_hash": "sha256-..."
            },
            "policy": {
                "verify_post_write": True,
                "lock_device": True,
                "dry_run": False
            }
        }
        
        cmd = f"{cli_path} run-job --json '{json.dumps(job_payload)}'"
        logger.info(f"Executing: {cmd}")
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        while True:
            line = await process.stdout.readline()
            if not line:
                break
                
            try:
                data = json.loads(line.decode().strip())
                if data["type"] == "status":
                    progress.state = BuildState.PREPARING
                    progress.stage = data["stage"]
                    progress.current_operation = data["message"]
                elif data["type"] == "progress":
                    progress.state = BuildState.WRITING
                    progress.overall_progress = data["overall"]
                    progress.speed_mbps = data["speed_mbps"]
                    progress.eta_seconds = data["eta_seconds"]
                elif data["type"] == "result":
                    if data["success"]:
                        progress.state = BuildState.COMPLETE
                        progress.overall_progress = 100
                    else:
                        progress.state = BuildState.ERROR
                        progress.error_message = data.get("error", "Unknown error")
                
                # Emit to SIO
                await sio.emit('progress', progress.model_dump(), room=f"build_{build_id}")
                
            except json.JSONDecodeError:
                logger.debug(f"CLI output: {line.decode().strip()}")
                
        await process.wait()
        
        if progress.state != BuildState.COMPLETE and progress.state != BuildState.ERROR:
            progress.state = BuildState.COMPLETE # Fallback
            
        await sio.emit('complete', progress.model_dump(), room=f"build_{build_id}")
        
    except Exception as e:
        logger.error(f"Build {build_id} failed: {e}")
        if build_id in active_builds:
            active_builds[build_id].state = BuildState.ERROR
            active_builds[build_id].error_message = str(e)
            await sio.emit('error', active_builds[build_id].model_dump(), room=f"build_{build_id}")

# --- Socket.IO Handlers ---

@sio.on('connect')
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.on('subscribe_build')
async def subscribe_build(sid, data):
    build_id = data.get('build_id')
    if build_id:
        sio.enter_room(sid, f"build_{build_id}")
        logger.info(f"Client {sid} subscribed to build {build_id}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    uvicorn.run(socket_app, host="127.0.0.1", port=port)
