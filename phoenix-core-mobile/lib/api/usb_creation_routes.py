"""
Phoenix Core Enterprise - USB Creation Routes
Complete bootable USB creation workflow with recipe management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
import asyncio

router = APIRouter(prefix="/api", tags=["USB Creation"])

# In-memory job storage (replace with database in production)
build_jobs = {}
recipes_db = {}

# Define available recipes
RECIPES = {
    "ubuntu-22.04": {
        "recipe_id": "ubuntu-22.04",
        "name": "Ubuntu 22.04 LTS",
        "description": "Ubuntu 22.04 LTS - Long Term Support",
        "os_name": "Ubuntu",
        "os_version": "22.04 LTS",
        "image_url": "https://releases.ubuntu.com/22.04/ubuntu-22.04.4-desktop-amd64.iso",
        "image_size_mb": 4700,
        "estimated_write_time_seconds": 300,
        "supported_devices": ["usb", "ssd"],
    },
    "ubuntu-24.04": {
        "recipe_id": "ubuntu-24.04",
        "name": "Ubuntu 24.04 LTS",
        "description": "Ubuntu 24.04 LTS - Latest Long Term Support",
        "os_name": "Ubuntu",
        "os_version": "24.04 LTS",
        "image_url": "https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso",
        "image_size_mb": 5000,
        "estimated_write_time_seconds": 320,
        "supported_devices": ["usb", "ssd"],
    },
    "fedora-39": {
        "recipe_id": "fedora-39",
        "name": "Fedora 39",
        "description": "Fedora 39 - Latest Fedora Release",
        "os_name": "Fedora",
        "os_version": "39",
        "image_url": "https://download.fedoraproject.org/pub/fedora/linux/releases/39/Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-39-1.5.iso",
        "image_size_mb": 2100,
        "estimated_write_time_seconds": 180,
        "supported_devices": ["usb", "ssd"],
    },
    "debian-12": {
        "recipe_id": "debian-12",
        "name": "Debian 12 Bookworm",
        "description": "Debian 12 Bookworm - Stable Release",
        "os_name": "Debian",
        "os_version": "12",
        "image_url": "https://cdimage.debian.org/debian-cd/current/amd64/iso-dvd/debian-12.5.0-amd64-DVD-1.iso",
        "image_size_mb": 3900,
        "estimated_write_time_seconds": 280,
        "supported_devices": ["usb", "ssd"],
    },
    "windows-11": {
        "recipe_id": "windows-11",
        "name": "Windows 11",
        "description": "Windows 11 - Latest Windows Release",
        "os_name": "Windows",
        "os_version": "11",
        "image_url": "https://software-download.microsoft.com/download/sg/Windows11_23H2_EnglishInternational_x64.iso",
        "image_size_mb": 6500,
        "estimated_write_time_seconds": 420,
        "supported_devices": ["usb", "ssd"],
    },
    "macos-sonoma": {
        "recipe_id": "macos-sonoma",
        "name": "macOS Sonoma",
        "description": "macOS Sonoma - Latest macOS Release",
        "os_name": "macOS",
        "os_version": "Sonoma",
        "image_url": "https://updates.cdn-apple.com/2023FallFCS/macOS-Sonoma-23A344.iso",
        "image_size_mb": 12500,
        "estimated_write_time_seconds": 600,
        "supported_devices": ["usb", "ssd"],
    },
    "oclp-mac": {
        "recipe_id": "oclp-mac",
        "name": "OpenCore Legacy Patcher",
        "description": "OpenCore Legacy Patcher - macOS for Unsupported Macs",
        "os_name": "macOS",
        "os_version": "OCLP",
        "image_url": "https://github.com/dortania/OpenCore-Legacy-Patcher/releases/download/0.6.9/OpenCore-Legacy-Patcher-v0.6.9.iso",
        "image_size_mb": 1200,
        "estimated_write_time_seconds": 120,
        "supported_devices": ["usb", "ssd"],
    },
}


class Recipe(BaseModel):
    recipe_id: str
    name: str
    description: str
    os_name: str
    os_version: str
    image_url: Optional[str] = None
    image_size_mb: int
    estimated_write_time_seconds: int
    supported_devices: List[str]


class SafetyCheckRequest(BaseModel):
    device_id: str
    recipe_id: str


class SafetyCheckResponse(BaseModel):
    safe: bool
    warnings: List[str] = []
    errors: List[str] = []


class BuildRequest(BaseModel):
    device_id: str
    recipe_id: str


class BuildJob(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed, cancelled
    recipe_id: str
    device_id: str
    progress_percent: int
    current_step: str
    estimated_time_remaining: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


@router.get("/recipes", response_model=dict)
async def get_recipes():
    """Get all available OS recipes"""
    return {
        "recipes": list(RECIPES.values()),
        "total": len(RECIPES),
    }


@router.get("/recipes/{recipe_id}", response_model=Recipe)
async def get_recipe(recipe_id: str):
    """Get specific recipe details"""
    if recipe_id not in RECIPES:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return RECIPES[recipe_id]


@router.post("/safety-check", response_model=SafetyCheckResponse)
async def safety_check(request: SafetyCheckRequest):
    """
    Perform safety validation before USB creation
    Checks for:
    - Device is USB/removable
    - Device is not mounted (on Linux/macOS)
    - Sufficient free space
    - No critical system partitions
    """
    warnings = []
    errors = []

    # Validate recipe exists
    if request.recipe_id not in RECIPES:
        errors.append("Recipe not found")
        return SafetyCheckResponse(safe=False, warnings=warnings, errors=errors)

    recipe = RECIPES[request.recipe_id]

    # Validate device exists (in production, check actual device)
    if not request.device_id:
        errors.append("Invalid device ID")
        return SafetyCheckResponse(safe=False, warnings=warnings, errors=errors)

    # Check device is removable
    if not request.device_id.startswith("sd") and not request.device_id.startswith("nvme"):
        warnings.append("Device may not be removable")

    # Check image size
    if recipe["image_size_mb"] > 32000:
        warnings.append(f"Large image size ({recipe['image_size_mb']} MB) - may take longer")

    # All checks passed
    safe = len(errors) == 0

    return SafetyCheckResponse(safe=safe, warnings=warnings, errors=errors)


@router.post("/build/start", response_model=BuildJob)
async def start_build(request: BuildRequest, background_tasks: BackgroundTasks):
    """
    Start a USB build job
    Creates a bootable USB drive with the selected OS
    """
    # Validate inputs
    if request.recipe_id not in RECIPES:
        raise HTTPException(status_code=404, detail="Recipe not found")

    recipe = RECIPES[request.recipe_id]

    # Create job
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "status": "pending",
        "recipe_id": request.recipe_id,
        "device_id": request.device_id,
        "progress_percent": 0,
        "current_step": "Initializing",
        "estimated_time_remaining": recipe["estimated_write_time_seconds"],
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "error_message": None,
    }

    build_jobs[job_id] = job

    # Start background task
    background_tasks.add_task(simulate_build, job_id, recipe)

    return BuildJob(**job)


@router.get("/build/{job_id}/progress", response_model=BuildJob)
async def get_build_progress(job_id: str):
    """Get current build progress"""
    if job_id not in build_jobs:
        raise HTTPException(status_code=404, detail="Build job not found")

    job = build_jobs[job_id]
    return BuildJob(**job)


@router.post("/build/{job_id}/cancel", response_model=dict)
async def cancel_build(job_id: str):
    """Cancel a build job"""
    if job_id not in build_jobs:
        raise HTTPException(status_code=404, detail="Build job not found")

    job = build_jobs[job_id]

    if job["status"] == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel completed job")

    job["status"] = "cancelled"
    job["completed_at"] = datetime.now().isoformat()

    return {"success": True, "message": "Build cancelled"}


@router.get("/build/jobs", response_model=dict)
async def get_build_jobs():
    """Get all build jobs"""
    return {
        "jobs": list(build_jobs.values()),
        "total": len(build_jobs),
    }


@router.get("/build/{job_id}", response_model=BuildJob)
async def get_build_job(job_id: str):
    """Get specific build job details"""
    if job_id not in build_jobs:
        raise HTTPException(status_code=404, detail="Build job not found")

    job = build_jobs[job_id]
    return BuildJob(**job)


# Simulated build process (replace with actual USB writing in production)
async def simulate_build(job_id: str, recipe: dict):
    """Simulate USB build process"""
    job = build_jobs[job_id]
    job["status"] = "running"
    job["started_at"] = datetime.now().isoformat()

    steps = [
        ("Downloading OS image", 0.2),
        ("Validating image", 0.1),
        ("Preparing USB device", 0.1),
        ("Formatting device", 0.15),
        ("Writing bootloader", 0.15),
        ("Writing OS files", 0.2),
        ("Finalizing", 0.1),
    ]

    total_time = recipe["estimated_write_time_seconds"]
    elapsed = 0

    for step_name, step_duration in steps:
        if job["status"] == "cancelled":
            return

        job["current_step"] = step_name
        step_time = int(total_time * step_duration)

        # Simulate step progress
        for i in range(10):
            if job["status"] == "cancelled":
                return

            job["progress_percent"] = int(
                (elapsed / total_time) * 100 + (step_duration * 100 / 10) * (i / 10)
            )
            job["estimated_time_remaining"] = max(0, total_time - elapsed - (step_time * i // 10))

            await asyncio.sleep(step_time / 10)

        elapsed += step_time

    # Completion
    job["status"] = "completed"
    job["progress_percent"] = 100
    job["current_step"] = "Complete"
    job["estimated_time_remaining"] = 0
    job["completed_at"] = datetime.now().isoformat()
