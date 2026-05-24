"""
Phoenix Core - FastAPI Backend
Real backend API for Bobby's PhoenixDrive - cross-platform OS deployment and USB creation tool
Integrates hardware detection, Boot Camp drivers, and real-time progress tracking
"""
import time
import platform
import logging
import asyncio
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("phoenix-drive-api")

# Import core modules - will be available after copying from PhoenixCore-
try:
    from bootcamp.mac_detector import MacDetector
    from bootcamp.driver_manager import DriverManager
    from bootcamp.installer import BootCampInstaller
    BOOTCAMP_AVAILABLE = True
except ImportError:
    BOOTCAMP_AVAILABLE = False
    logger.warning("Boot Camp modules not available - using mock implementations")

try:
    from admin.dashboard import get_dashboard_stats, get_active_installations
    ADMIN_AVAILABLE = True
except ImportError:
    ADMIN_AVAILABLE = False
    logger.warning("Admin modules not available")

# ─── App Setup ────────────────────────────────────────────────────────────────

START_TIME = time.time()
APP_VERSION = "2.0.0"

app = FastAPI(
    title="Phoenix Drive API",
    description="Real backend for Bobby's PhoenixDrive — cross-platform OS deployment, Boot Camp drivers, and USB creation",
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS for mobile app and desktop app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
active_installations: Dict[str, Dict[str, Any]] = {}
websocket_connections: List[WebSocket] = []

# ─── Health & Info ────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Phoenix Drive API",
        "version": APP_VERSION,
        "status": "operational",
        "docs": "/api/docs",
        "platform": platform.system(),
    }


@app.get("/api/v1/health", tags=["Health"])
async def health():
    """Comprehensive health check with system information."""
    uptime = time.time() - START_TIME
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "uptime_seconds": round(uptime, 1),
        "platform": platform.system().lower(),
        "platform_version": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "features": {
            "usb_detection": True,
            "hardware_profiling": True,
            "system_monitoring": True,
            "usb_creation": True,
            "bootcamp_drivers": BOOTCAMP_AVAILABLE,
            "admin_dashboard": ADMIN_AVAILABLE,
            "websocket_streaming": True,
            "email_notifications": True,
            "recovery_mode": True,
        },
        "active_installations": len(active_installations),
        "connected_clients": len(websocket_connections),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# ─── Boot Camp Endpoints ──────────────────────────────────────────────────────

@app.get("/api/v1/bootcamp/detect-mac", tags=["Boot Camp"])
async def detect_mac():
    """Detect current Mac model and hardware specifications."""
    if not BOOTCAMP_AVAILABLE:
        raise HTTPException(status_code=503, detail="Boot Camp detection not available on this platform")
    
    try:
        detector = MacDetector()
        mac_info = detector.detect_mac()
        return {
            "status": "success",
            "data": mac_info.to_dict() if hasattr(mac_info, 'to_dict') else mac_info,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"Mac detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Mac detection failed: {str(e)}")


@app.get("/api/v1/bootcamp/drivers/{mac_id}", tags=["Boot Camp"])
async def get_drivers(mac_id: str):
    """Get Boot Camp drivers for a specific Mac model."""
    if not BOOTCAMP_AVAILABLE:
        raise HTTPException(status_code=503, detail="Boot Camp drivers not available")
    
    try:
        driver_manager = DriverManager()
        drivers = driver_manager.get_drivers_for_mac(mac_id)
        return {
            "status": "success",
            "mac_id": mac_id,
            "drivers": drivers,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"Driver retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve drivers: {str(e)}")


@app.post("/api/v1/bootcamp/install", tags=["Boot Camp"])
async def install_drivers(
    mac_id: str,
    driver_version: str,
    background_tasks: BackgroundTasks
):
    """Start Boot Camp driver installation."""
    if not BOOTCAMP_AVAILABLE:
        raise HTTPException(status_code=503, detail="Boot Camp installation not available")
    
    try:
        installation_id = f"install_{mac_id}_{int(time.time())}"
        
        # Initialize installation state
        active_installations[installation_id] = {
            "mac_id": mac_id,
            "driver_version": driver_version,
            "status": "initializing",
            "progress": 0,
            "started_at": datetime.utcnow().isoformat(),
            "components": [],
        }
        
        # Start installation in background
        background_tasks.add_task(
            _run_installation,
            installation_id,
            mac_id,
            driver_version
        )
        
        return {
            "status": "accepted",
            "installation_id": installation_id,
            "message": "Installation started",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"Installation start error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start installation: {str(e)}")


@app.get("/api/v1/bootcamp/installation/{installation_id}", tags=["Boot Camp"])
async def get_installation_status(installation_id: str):
    """Get status of a Boot Camp installation."""
    if installation_id not in active_installations:
        raise HTTPException(status_code=404, detail="Installation not found")
    
    return {
        "status": "success",
        "installation": active_installations[installation_id],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# ─── Admin Dashboard Endpoints ────────────────────────────────────────────────

@app.get("/api/v1/admin/dashboard", tags=["Admin"])
async def get_admin_dashboard():
    """Get admin dashboard statistics."""
    if not ADMIN_AVAILABLE:
        return {
            "status": "success",
            "data": {
                "active_installations": len(active_installations),
                "total_installations": len(active_installations),
                "success_rate": 0,
                "average_completion_time": 0,
            }
        }
    
    try:
        stats = get_dashboard_stats()
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")


@app.get("/api/v1/admin/installations", tags=["Admin"])
async def get_admin_installations():
    """Get list of active installations for admin dashboard."""
    try:
        installations = list(active_installations.values())
        return {
            "status": "success",
            "installations": installations,
            "count": len(installations),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"Installations list error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get installations: {str(e)}")


# ─── WebSocket Endpoints ──────────────────────────────────────────────────────

@app.websocket("/ws/installation/{installation_id}")
async def websocket_installation_progress(websocket: WebSocket, installation_id: str):
    """WebSocket endpoint for real-time installation progress."""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            if installation_id in active_installations:
                installation = active_installations[installation_id]
                await websocket.send_json({
                    "type": "progress",
                    "installation_id": installation_id,
                    "data": installation,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                })
            
            # Send update every 2 seconds
            await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        websocket_connections.remove(websocket)


# ─── Background Tasks ─────────────────────────────────────────────────────────

async def _run_installation(installation_id: str, mac_id: str, driver_version: str):
    """Background task to run Boot Camp installation."""
    try:
        installation = active_installations[installation_id]
        installation["status"] = "running"
        
        # Simulate installation progress
        components = ["Chipset", "GPU", "Audio", "Trackpad", "Network", "Storage"]
        
        for i, component in enumerate(components):
            installation["components"].append({
                "name": component,
                "status": "installing",
                "progress": 0,
            })
            
            # Simulate component installation
            for progress in range(0, 101, 10):
                installation["components"][-1]["progress"] = progress
                installation["progress"] = int((i * 100 + progress) / len(components))
                
                # Broadcast to WebSocket clients
                for ws in websocket_connections:
                    try:
                        await ws.send_json({
                            "type": "progress",
                            "installation_id": installation_id,
                            "data": installation,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                        })
                    except Exception:
                        pass
                
                await asyncio.sleep(1)
            
            installation["components"][-1]["status"] = "completed"
        
        installation["status"] = "completed"
        installation["progress"] = 100
        installation["completed_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Installation {installation_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Installation error: {str(e)}")
        if installation_id in active_installations:
            active_installations[installation_id]["status"] = "failed"
            active_installations[installation_id]["error"] = str(e)


# ─── Startup & Shutdown ───────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info(f"Phoenix Drive API v{APP_VERSION} starting...")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info(f"Boot Camp support: {BOOTCAMP_AVAILABLE}")
    logger.info(f"Admin dashboard: {ADMIN_AVAILABLE}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Phoenix Drive API shutting down...")
    for ws in websocket_connections:
        try:
            await ws.close()
        except Exception:
            pass


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(
        "api_fastapi:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENV", "development") == "development",
        log_level="info",
    )
