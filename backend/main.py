"""
Phoenix Core - Real Backend API
FastAPI server exposing all Phoenix Core capabilities as REST endpoints
"""
import time
import platform
import logging
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("phoenix-core")

# Import core modules
from core.device_scanner import scan_usb_devices, get_device_by_path
from core.hardware_profiler import get_hardware_profile
from core.system_monitor import get_system_metrics, get_usb_activity
from core.usb_builder import (
    RECIPES, validate_safety, start_build, get_build_progress,
    cancel_job, list_jobs, get_job,
)
from core.oclp_integration import (
    check_oclp_compatibility, get_all_compatible_models,
    get_macos_versions, detect_current_mac_model,
)
from core.platform_caps import platform_caps
from core.platform_guard import require_destructive_usb_native, DestructiveOperationNotSupported, explain_block
from core.audit_store import read_recent, export_jsonl_path, AUDIT_SCHEMA_VERSION

# ─── App Setup ────────────────────────────────────────────────────────────────

START_TIME = time.time()
APP_VERSION = "2.0.0"

app = FastAPI(
    title="Phoenix Core API",
    description="Real backend for Phoenix Core — cross-platform OS deployment and USB creation tool",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health & Info ────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "name": "Phoenix Core API",
        "version": APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "platform": platform.system(),
    }


@app.get("/api/health", tags=["Health"])
async def health():
    """Comprehensive health check."""
    uptime = time.time() - START_TIME
    caps = platform_caps()
    native_usb = caps.get("destructive_usb_write_native", False)
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "uptime_seconds": round(uptime, 1),
        "platform": platform.system().lower(),
        "platform_version": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "capabilities": caps,
        "features": {
            "usb_detection": True,
            "hardware_profiling": True,
            "system_monitoring": True,
            "usb_creation": True,
            "destructive_usb_write_native": native_usb,
            "oclp_integration": platform.system() == "Darwin",
            "multiboot": True,
            "recovery_usb": True,
            "dry_run_mode": False,
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ─── Device Detection ─────────────────────────────────────────────────────────

@app.get("/api/devices", tags=["Devices"])
async def list_devices(
    removable_only: bool = Query(
        False,
        description="If true, return only OS-reported removable devices (safer for USB target pickers).",
    ),
    include_all: bool = Query(
        False,
        description="If true with removable_only, still return all devices (diagnostics override).",
    ),
):
    """
    Scan storage devices. Prefer **removable_only=true** for USB creation UIs.
    """
    try:
        result = scan_usb_devices(removable_only=removable_only, include_all=include_all)
        return result
    except Exception as e:
        logger.error(f"Device scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/devices/{device_id}", tags=["Devices"])
async def get_device(device_id: str):
    """Get detailed information about a specific device."""
    device = get_device_by_path(device_id)
    if not device:
        # Try with /dev/ prefix
        device = get_device_by_path(f"/dev/{device_id}")
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    return device


@app.post("/api/devices/refresh", tags=["Devices"])
async def refresh_devices(
    removable_only: bool = Query(False),
    include_all: bool = Query(False),
):
    """Force a fresh device scan (same query params as GET /api/devices)."""
    try:
        result = scan_usb_devices(removable_only=removable_only, include_all=include_all)
        return {"message": "Device scan complete", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Hardware Profiling ───────────────────────────────────────────────────────

@app.get("/api/hardware", tags=["Hardware"])
async def get_hardware():
    """
    Get complete hardware profile of the current system.
    Detects CPU, memory, GPU, storage, and platform information.
    """
    try:
        profile = get_hardware_profile()
        return profile
    except Exception as e:
        logger.error(f"Hardware profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hardware/profiles", tags=["Hardware"])
async def list_hardware_profiles():
    """List all known hardware profiles for USB creation targeting."""
    from core.oclp_integration import OCLP_COMPATIBILITY_DB
    profiles = []

    # Add Mac profiles from OCLP DB
    for model_id, info in OCLP_COMPATIBILITY_DB.items():
        profiles.append({
            "id": model_id,
            "name": info["name"],
            "platform": "macos",
            "architecture": "x86_64",
            "oclp_compatible": True,
        })

    # Add generic profiles
    generic = [
        {"id": "generic_x64", "name": "Generic PC (x86_64)", "platform": "windows/linux", "architecture": "x86_64", "oclp_compatible": False},
        {"id": "generic_arm64", "name": "Generic ARM (aarch64)", "platform": "linux", "architecture": "aarch64", "oclp_compatible": False},
        {"id": "windows_pc", "name": "Windows PC (UEFI)", "platform": "windows", "architecture": "x86_64", "oclp_compatible": False},
        {"id": "linux_server", "name": "Linux Server", "platform": "linux", "architecture": "x86_64", "oclp_compatible": False},
    ]
    profiles.extend(generic)

    return {"profiles": profiles, "total": len(profiles)}


# ─── System Monitoring ────────────────────────────────────────────────────────

@app.get("/api/system/metrics", tags=["Monitoring"])
async def system_metrics():
    """
    Get real-time system metrics: CPU, memory, disk, network, temperature.
    """
    try:
        metrics = get_system_metrics()
        return metrics
    except Exception as e:
        logger.error(f"System metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system/usb-activity", tags=["Monitoring"])
async def usb_activity():
    """Monitor USB device activity."""
    try:
        return get_usb_activity()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system/info", tags=["Monitoring"])
async def system_info():
    """Get comprehensive system information."""
    try:
        import psutil
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time

        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
            "uptime_seconds": round(uptime, 0),
            "boot_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(boot_time)),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── USB Build Recipes ────────────────────────────────────────────────────────

@app.get("/api/recipes", tags=["USB Creation"])
async def list_recipes():
    """List all available USB deployment recipes."""
    return {
        "recipes": list(RECIPES.values()),
        "total": len(RECIPES),
    }


@app.get("/api/recipes/{recipe_id}", tags=["USB Creation"])
async def get_recipe(recipe_id: str):
    """Get details of a specific recipe."""
    recipe = RECIPES.get(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe not found: {recipe_id}")
    return recipe


# ─── Safety Validation ────────────────────────────────────────────────────────

@app.post("/api/safety-check", tags=["USB Creation"])
async def safety_check(body: dict):
    """
    Perform safety validation before USB creation.
    Returns risk assessment and confirmation token required for build.
    """
    device_path = body.get("device_path", "")
    recipe_id = body.get("recipe_id", "")

    if not device_path or not recipe_id:
        raise HTTPException(status_code=400, detail="device_path and recipe_id are required")

    dry_run = bool(body.get("dry_run", False))
    require_removable = body.get("require_removable", True)
    if isinstance(require_removable, str):
        require_removable = require_removable.lower() in ("1", "true", "yes")
    try:
        result = validate_safety(
            device_path,
            recipe_id,
            require_removable=require_removable,
            dry_run=dry_run,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── USB Build Jobs ───────────────────────────────────────────────────────────

@app.post("/api/build/start", tags=["USB Creation"])
async def start_usb_build(body: dict):
    """
    Start a USB build job.
    Requires a confirmation token from /api/safety-check (or dry_run=true).

    Body:
    - recipe_id: string (required)
    - target_device_path: string (required)
    - os_image_path: string (optional, path to ISO)
    - dry_run: bool (default false)
    - confirmation_token: string (required unless dry_run)
    - oclp_enabled: bool (optional)
    - oclp_target_model: string (optional)
    - oclp_macos_version: string (optional)
    """
    try:
        result = start_build(body)
        if result["status"] == "failed":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/build/{job_id}/progress", tags=["USB Creation"])
async def build_progress(job_id: str):
    """Get real-time progress of a USB build job."""
    progress = get_build_progress(job_id)
    if not progress:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return progress


@app.post("/api/build/{job_id}/cancel", tags=["USB Creation"])
async def cancel_build(job_id: str):
    """Cancel an in-progress build job."""
    success = cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled (not running or not found)")
    return {"message": "Job cancelled", "job_id": job_id}


@app.get("/api/build/jobs/list", tags=["USB Creation"])
async def list_build_jobs():
    """List all build jobs (active and completed)."""
    jobs = list_jobs()
    return {
        "jobs": [
            {
                "job_id": j.job_id,
                "recipe_id": j.recipe_id,
                "target_device": j.target_device,
                "status": j.status.value,
                "progress_percent": j.progress_percent,
                "dry_run": j.dry_run,
                "elapsed_seconds": round(time.time() - j.start_time, 1),
            }
            for j in jobs
        ],
        "total": len(jobs),
    }


@app.get("/api/audit/jobs/recent", tags=["Audit"])
async def audit_recent(limit: int = Query(100, ge=1, le=500)):
    """Recent durable audit records (destructive job preflight, rejections, outcomes)."""
    return {
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "records": read_recent(limit),
        "export_path": str(export_jsonl_path()),
    }


@app.get("/api/audit/export/path", tags=["Audit"])
async def audit_export_path():
    """Absolute path to the active JSONL audit log (for operator export)."""
    return {
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "path": str(export_jsonl_path()),
        "format": "jsonl",
    }


# ─── OCLP Integration ─────────────────────────────────────────────────────────

@app.get("/api/oclp/models", tags=["OCLP"])
async def oclp_models():
    """List all OCLP-compatible Mac models."""
    models = get_all_compatible_models()
    return {"models": models, "total": len(models)}


@app.get("/api/oclp/check/{model}", tags=["OCLP"])
async def oclp_check(model: str):
    """Check OCLP compatibility for a specific Mac model."""
    return check_oclp_compatibility(model)


@app.get("/api/oclp/macos-versions", tags=["OCLP"])
async def oclp_macos_versions():
    """Get supported macOS versions for OCLP."""
    versions = get_macos_versions()
    return {
        "versions": [
            {"version": ver, "name": name}
            for ver, name in versions.items()
        ]
    }


@app.get("/api/oclp/detect", tags=["OCLP"])
async def oclp_detect_model():
    """Detect current Mac model for OCLP compatibility check."""
    model = detect_current_mac_model()
    if model:
        compat = check_oclp_compatibility(model)
        return {"detected_model": model, "compatibility": compat}
    return {
        "detected_model": None,
        "message": "Not running on macOS or model detection failed",
        "compatibility": None,
    }


# ─── OS Image Management ──────────────────────────────────────────────────────

@app.get("/api/images", tags=["OS Images"])
async def list_os_images():
    """List available OS images (local and downloadable)."""
    images = []

    # Check for local ISO files
    search_paths = [
        Path.home() / "Downloads",
        Path("/tmp"),
        Path.home(),
    ]

    for search_path in search_paths:
        if search_path.exists():
            for iso in search_path.glob("*.iso"):
                size = iso.stat().st_size
                images.append({
                    "id": iso.stem,
                    "name": iso.stem,
                    "os_type": _detect_os_type(iso.name),
                    "version": "unknown",
                    "architecture": "x86_64",
                    "size_bytes": size,
                    "size_human": _human_size(size),
                    "local_path": str(iso),
                    "verified": False,
                    "description": f"Local ISO: {iso.name}",
                })
            for img in search_path.glob("*.img"):
                size = img.stat().st_size
                images.append({
                    "id": img.stem,
                    "name": img.stem,
                    "os_type": "linux",
                    "version": "unknown",
                    "architecture": "x86_64",
                    "size_bytes": size,
                    "size_human": _human_size(size),
                    "local_path": str(img),
                    "verified": False,
                    "description": f"Local image: {img.name}",
                })

    # Add well-known downloadable images
    downloadable = [
        {
            "id": "ubuntu-22.04",
            "name": "Ubuntu 22.04.3 LTS",
            "os_type": "linux",
            "version": "22.04.3",
            "architecture": "x86_64",
            "size_bytes": 1_476_395_008,
            "size_human": "1.4 GB",
            "download_url": "https://releases.ubuntu.com/22.04/ubuntu-22.04.3-desktop-amd64.iso",
            "checksum_sha256": "a4acfda10b18da50e2ec50ccaf860d7f20b389df8765611142305c0e911d16fd",
            "local_path": None,
            "verified": False,
            "description": "Ubuntu 22.04 LTS Desktop — recommended for most users",
        },
        {
            "id": "ubuntu-24.04",
            "name": "Ubuntu 24.04 LTS",
            "os_type": "linux",
            "version": "24.04",
            "architecture": "x86_64",
            "size_bytes": 2_097_152_000,
            "size_human": "2.0 GB",
            "download_url": "https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso",
            "checksum_sha256": None,
            "local_path": None,
            "verified": False,
            "description": "Ubuntu 24.04 LTS Desktop — latest LTS release",
        },
        {
            "id": "fedora-39",
            "name": "Fedora Workstation 39",
            "os_type": "linux",
            "version": "39",
            "architecture": "x86_64",
            "size_bytes": 2_147_483_648,
            "size_human": "2.0 GB",
            "download_url": "https://download.fedoraproject.org/pub/fedora/linux/releases/39/Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-39-1.5.iso",
            "checksum_sha256": None,
            "local_path": None,
            "verified": False,
            "description": "Fedora Workstation 39 — cutting-edge Linux",
        },
    ]
    images.extend(downloadable)

    return {"images": images, "total": len(images)}


@app.get("/api/images/{image_id}", tags=["OS Images"])
async def get_image(image_id: str):
    """Get details of a specific OS image."""
    images_response = await list_os_images()
    for img in images_response["images"]:
        if img["id"] == image_id:
            return img
    raise HTTPException(status_code=404, detail=f"Image not found: {image_id}")


# ─── Workflow Engine ──────────────────────────────────────────────────────────

@app.get("/api/workflows", tags=["Workflows"])
async def list_workflows():
    """List available workflow templates."""
    workflows = [
        {
            "id": "quick-linux-usb",
            "name": "Quick Linux USB",
            "description": "Fast path for creating a bootable Linux USB",
            "steps": [
                {"id": "scan", "action": "scan_devices", "params": {}},
                {"id": "safety", "action": "safety_check", "params": {"recipe_id": "linux-automated"}},
                {"id": "build", "action": "start_build", "params": {"recipe_id": "linux-automated"}},
                {"id": "verify", "action": "verify", "params": {}},
            ],
        },
        {
            "id": "macos-oclp-workflow",
            "name": "macOS OCLP Workflow",
            "description": "Full workflow for creating a macOS USB with OCLP patches",
            "steps": [
                {"id": "detect", "action": "detect_hardware", "params": {}},
                {"id": "oclp-check", "action": "oclp_compatibility", "params": {}},
                {"id": "scan", "action": "scan_devices", "params": {}},
                {"id": "safety", "action": "safety_check", "params": {"recipe_id": "macos-oclp"}},
                {"id": "build", "action": "start_build", "params": {"recipe_id": "macos-oclp", "oclp_enabled": True}},
                {"id": "verify", "action": "verify", "params": {}},
            ],
        },
        {
            "id": "recovery-usb",
            "name": "Phoenix Recovery USB",
            "description": "Create a Phoenix recovery USB with diagnostic tools",
            "steps": [
                {"id": "scan", "action": "scan_devices", "params": {}},
                {"id": "safety", "action": "safety_check", "params": {"recipe_id": "recovery"}},
                {"id": "build", "action": "start_build", "params": {"recipe_id": "recovery"}},
            ],
        },
    ]
    return {"workflows": workflows, "total": len(workflows)}


@app.post("/api/workflows/run", tags=["Workflows"])
async def run_workflow(body: dict):
    """
    Execute a workflow — runs a complete USB creation pipeline.
    """
    workflow_id = body.get("workflow_id", "")
    device_path = body.get("device_path", "")
    dry_run = body.get("dry_run", False)

    if not device_path:
        raise HTTPException(status_code=400, detail="device_path is required")

    if not dry_run:
        try:
            require_destructive_usb_native(dry_run=False)
        except DestructiveOperationNotSupported:
            raise HTTPException(status_code=503, detail=explain_block())

    # Map workflow to recipe
    workflow_recipe_map = {
        "quick-linux-usb": "linux-automated",
        "macos-oclp-workflow": "macos-oclp",
        "recovery-usb": "recovery",
    }

    recipe_id = workflow_recipe_map.get(workflow_id, "recovery")

    # Run safety check
    safety = validate_safety(device_path, recipe_id, require_removable=True, dry_run=dry_run)

    if not safety["safe_to_proceed"] and not dry_run:
        return {
            "workflow_id": workflow_id,
            "status": "blocked",
            "message": "Safety check failed",
            "safety": safety,
        }

    token = safety.get("confirmation_token") or ""
    if not dry_run and not token:
        raise HTTPException(
            status_code=400,
            detail="Safety check did not return a confirmation token; cannot start build.",
        )

    # Start build
    build_request = {
        "recipe_id": recipe_id,
        "target_device_path": device_path,
        "dry_run": dry_run,
        "confirmation_token": token,
        "oclp_enabled": body.get("oclp_enabled", False),
        "oclp_target_model": body.get("oclp_target_model"),
        "oclp_macos_version": body.get("oclp_macos_version"),
    }

    result = start_build(build_request)

    return {
        "workflow_id": workflow_id,
        "status": "running",
        "job_id": result.get("job_id"),
        "safety": safety,
        "build": result,
    }


# ─── Diagnostics ─────────────────────────────────────────────────────────────

@app.get("/api/diagnostics", tags=["Diagnostics"])
async def run_diagnostics():
    """Run system diagnostics and return a health report."""
    import psutil

    checks = {}

    # Check psutil
    try:
        psutil.cpu_percent(interval=0.1)
        checks["psutil"] = {"status": "ok", "message": "psutil operational"}
    except Exception as e:
        checks["psutil"] = {"status": "error", "message": str(e)}

    # Check disk access
    try:
        import os
        os.listdir("/dev") if platform.system() != "Windows" else os.listdir("C:\\")
        checks["disk_access"] = {"status": "ok", "message": "Disk access available"}
    except Exception as e:
        checks["disk_access"] = {"status": "warning", "message": str(e)}

    # Check available tools
    tools = ["dd", "parted", "mkfs.fat", "mkfs.ntfs", "lsblk", "blkid"]
    tool_status = {}
    for tool in tools:
        import shutil
        available = shutil.which(tool) is not None
        tool_status[tool] = "available" if available else "not found"
    checks["tools"] = {"status": "ok", "tools": tool_status}

    from core.phoenix_paths import oclp_submodule_path, repo_root

    phoenix_path = repo_root()
    checks["phoenix_core"] = {
        "status": "ok" if phoenix_path.exists() else "not found",
        "path": str(phoenix_path),
        "exists": phoenix_path.exists(),
    }

    # Check OCLP
    oclp_path = oclp_submodule_path()
    checks["oclp"] = {
        "status": "available" if oclp_path.exists() else "not installed",
        "path": str(oclp_path),
        "note": "OCLP is macOS-only; available for macOS builds",
    }

    all_ok = all(
        v.get("status") in ("ok", "available", "not installed", "not found")
        for v in checks.values()
        if isinstance(v, dict)
    )

    return {
        "overall_status": "healthy" if all_ok else "degraded",
        "checks": checks,
        "platform": platform.system(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _detect_os_type(filename: str) -> str:
    name = filename.lower()
    if any(x in name for x in ["ubuntu", "fedora", "debian", "arch", "mint", "kali", "linux"]):
        return "linux"
    if any(x in name for x in ["windows", "win10", "win11"]):
        return "windows"
    if any(x in name for x in ["macos", "osx", "ventura", "sonoma", "monterey"]):
        return "macos"
    return "custom"


def _human_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
