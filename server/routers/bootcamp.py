from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import json
import uuid
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/bootcamp",
    tags=["bootcamp"]
)

# --- Models ---

class MacSystemInfoModel(BaseModel):
    model_identifier: str
    board_id: str
    serial_number: Optional[str] = ""
    cpu_brand: Optional[str] = ""
    gpu_model: Optional[str] = ""

class DetectMacRequest(BaseModel):
    system_info: MacSystemInfoModel

class StartInstallationRequest(BaseModel):
    mac_model: str
    windows_version: Optional[str] = "Windows 10"
    driver_package_id: str

# --- Database Setup ---

DRIVER_DB_PATH = Path(__file__).parent.parent / 'bootcamp' / 'driver_database.json'
DRIVER_DATABASE = {}

try:
    if DRIVER_DB_PATH.exists():
        with open(DRIVER_DB_PATH, 'r') as f:
            DRIVER_DATABASE = json.load(f)
    else:
        logger.warning(f"Driver database not found at {DRIVER_DB_PATH}")
except Exception as e:
    logger.error(f"Error loading driver database: {e}")

# --- Endpoints ---

@router.get("/health")
async def health_check():
    return {
        'status': 'ok',
        'service': 'bootcamp',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }

@router.post("/detect-mac")
async def detect_mac(req: DetectMacRequest):
    # This would normally use the MacDetector class
    # For now, we simulate the response or use mock logic
    model_id = req.system_info.model_identifier
    
    mac_model = DRIVER_DATABASE.get('models', {}).get(model_id, {
        "model_id": model_id,
        "display_name": "Unknown Mac",
        "year": 2024
    })
    
    driver_package = None
    package_id = mac_model.get('driver_package_id')
    if package_id:
        driver_package = DRIVER_DATABASE.get('packages', {}).get(package_id)

    return {
        'status': 'success',
        'mac_model': mac_model,
        'driver_package': driver_package,
        'compatibility': {"status": "compatible", "reason": "System supported"},
        'timestamp': datetime.now().isoformat()
    }

@router.get("/drivers/{package_id}")
async def get_driver_package(package_id: str):
    package = DRIVER_DATABASE.get('packages', {}).get(package_id)
    if not package:
        raise HTTPException(status_code=404, detail=f"Driver package not found: {package_id}")
    
    return {
        'status': 'success',
        'package': package,
        'timestamp': datetime.now().isoformat()
    }

@router.get("/models")
async def list_mac_models(boot_camp_support: Optional[bool] = None, year: Optional[int] = None):
    models = list(DRIVER_DATABASE.get('models', {}).values())
    
    if boot_camp_support is not None:
        models = [m for m in models if m.get('boot_camp_support') == boot_camp_support]
    
    if year is not None:
        models = [m for m in models if m.get('year') == year]
        
    return {
        'status': 'success',
        'models': models,
        'total': len(models),
        'timestamp': datetime.now().isoformat()
    }

@router.post("/install")
async def start_installation(req: StartInstallationRequest):
    if req.driver_package_id not in DRIVER_DATABASE.get('packages', {}):
        raise HTTPException(status_code=400, detail=f"Invalid driver package: {req.driver_package_id}")
    
    installation_id = str(uuid.uuid4())
    return {
        'status': 'success',
        'installation_id': installation_id,
        'websocket_url': f'/ws/bootcamp/install/{installation_id}/stream',
        'timestamp': datetime.now().isoformat()
    }
