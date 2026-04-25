"""
Boot Camp Backend API Endpoints
Exposes Mac detection and driver installation functionality
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from functools import wraps

from flask import Blueprint, request, jsonify, send_file
from flask_cors import cross_origin

from .mac_detector import MacDetector, BootCampCompatibilityChecker, MacSystemInfo
from .driver_manager import BootCampDriverManager, DownloadProgress
from .installer import BootCampDriverInstallationOrchestrator
from .installation_service import get_installation_service, InstallationConfig

logger = logging.getLogger(__name__)

# Create Blueprint
bootcamp_bp = Blueprint('bootcamp', __name__, url_prefix='/api/v1/bootcamp')

# Initialize services
mac_detector = MacDetector()
driver_manager = BootCampDriverManager()
installer_orchestrator = BootCampDriverInstallationOrchestrator()
compatibility_checker = BootCampCompatibilityChecker()
installation_service = get_installation_service()

# Load driver database
DRIVER_DB_PATH = Path(__file__).parent / 'driver_database.json'
with open(DRIVER_DB_PATH, 'r') as f:
    DRIVER_DATABASE = json.load(f)

# Active installations tracking
ACTIVE_INSTALLATIONS = {}


def require_json(f):
    """Decorator to require JSON content type"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    return decorated_function


@bootcamp_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'bootcamp',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }), 200


@bootcamp_bp.route('/detect-mac', methods=['POST'])
@cross_origin()
@require_json
def detect_mac():
    """
    Detect Mac system information
    
    Request:
    {
        "system_info": {
            "model_identifier": "MacBookPro15,1",
            "board_id": "Mac-551B86E5744E0084",
            "serial_number": "C02XXXXX",
            "cpu_brand": "Intel Core i7-8750H",
            "gpu_model": "AMD Radeon Pro 555X"
        }
    }
    
    Response:
    {
        "status": "success",
        "mac_model": {...},
        "driver_package": {...},
        "compatibility": {...}
    }
    """
    
    try:
        data = request.get_json()
        
        # Detect Mac system
        mac_info = mac_detector.detect()
        
        if not mac_info:
            return jsonify({
                'status': 'error',
                'message': 'Could not detect Mac system information'
            }), 400
        
        # Check compatibility
        compatibility = compatibility_checker.check_compatibility(mac_info)
        
        # Get driver package
        driver_package = None
        if mac_info.model_identifier in DRIVER_DATABASE['models']:
            model_data = DRIVER_DATABASE['models'][mac_info.model_identifier]
            if model_data.get('driver_package_id'):
                package_id = model_data['driver_package_id']
                driver_package = DRIVER_DATABASE['packages'].get(package_id)
        
        response = {
            'status': 'success',
            'mac_model': mac_info.to_dict(),
            'driver_package': driver_package,
            'compatibility': compatibility,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Mac detected: {mac_info.model_identifier}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error detecting Mac: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bootcamp_bp.route('/drivers/<package_id>', methods=['GET'])
@cross_origin()
def get_driver_package(package_id: str):
    """
    Get driver package information
    
    Response:
    {
        "status": "success",
        "package": {...}
    }
    """
    
    try:
        if package_id not in DRIVER_DATABASE['packages']:
            return jsonify({
                'status': 'error',
                'message': f'Driver package not found: {package_id}'
            }), 404
        
        package = DRIVER_DATABASE['packages'][package_id]
        
        response = {
            'status': 'success',
            'package': package,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Driver package retrieved: {package_id}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error getting driver package: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bootcamp_bp.route('/models/<model_id>', methods=['GET'])
@cross_origin()
def get_mac_model(model_id: str):
    """
    Get Mac model information
    
    Response:
    {
        "status": "success",
        "model": {...}
    }
    """
    
    try:
        if model_id not in DRIVER_DATABASE['models']:
            return jsonify({
                'status': 'error',
                'message': f'Mac model not found: {model_id}'
            }), 404
        
        model = DRIVER_DATABASE['models'][model_id]
        
        response = {
            'status': 'success',
            'model': model,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Mac model retrieved: {model_id}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error getting Mac model: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bootcamp_bp.route('/models', methods=['GET'])
@cross_origin()
def list_mac_models():
    """
    List all supported Mac models
    
    Query parameters:
    - boot_camp_support: Filter by Boot Camp support (true/false)
    - year: Filter by year
    
    Response:
    {
        "status": "success",
        "models": [...],
        "total": 180
    }
    """
    
    try:
        boot_camp_support = request.args.get('boot_camp_support')
        year = request.args.get('year')
        
        models = DRIVER_DATABASE['models'].values()
        
        # Filter
        if boot_camp_support is not None:
            support = boot_camp_support.lower() == 'true'
            models = [m for m in models if m.get('boot_camp_support') == support]
        
        if year is not None:
            try:
                year_int = int(year)
                models = [m for m in models if m.get('year') == year_int]
            except ValueError:
                pass
        
        models = list(models)
        
        response = {
            'status': 'success',
            'models': models,
            'total': len(models),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Listed {len(models)} Mac models")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error listing Mac models: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bootcamp_bp.route('/install', methods=['POST'])
@cross_origin()
@require_json
def start_installation():
    """
    Start Boot Camp driver installation
    
    Request:
    {
        "mac_model": "MacBookPro15,1",
        "windows_version": "Windows 10 21H2",
        "driver_package_id": "BootCampESD_6.1"
    }
    
    Response:
    {
        "status": "success",
        "installation_id": "install-uuid",
        "websocket_url": "wss://api.example.com/api/v1/bootcamp/install/install-uuid/stream"
    }
    """
    
    try:
        data = request.get_json()
        
        mac_model = data.get('mac_model')
        windows_version = data.get('windows_version', 'Windows 10')
        driver_package_id = data.get('driver_package_id')
        
        if not mac_model or not driver_package_id:
            return jsonify({
                'status': 'error',
                'message': 'mac_model and driver_package_id are required'
            }), 400
        
        # Validate driver package
        if driver_package_id not in DRIVER_DATABASE['packages']:
            return jsonify({
                'status': 'error',
                'message': f'Invalid driver package: {driver_package_id}'
            }), 400
        
        # Create installation ID
        installation_id = str(uuid.uuid4())
        
        # Store installation info
        ACTIVE_INSTALLATIONS[installation_id] = {
            'mac_model': mac_model,
            'windows_version': windows_version,
            'driver_package_id': driver_package_id,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'progress': 0
        }
        
        response = {
            'status': 'success',
            'installation_id': installation_id,
            'websocket_url': f'wss://api.example.com/api/v1/bootcamp/install/{installation_id}/stream',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Installation started: {installation_id}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error starting installation: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bootcamp_bp.route('/install/<installation_id>', methods=['GET'])
@cross_origin()
def get_installation_status(installation_id: str):
    """
    Get installation status
    
    Response:
    {
        "status": "success",
        "installation": {
            "id": "install-uuid",
            "status": "installing",
            "progress": 45,
            "components_installed": {...}
        }
    }
    """
    
    try:
        if installation_id not in ACTIVE_INSTALLATIONS:
            return jsonify({
                'status': 'error',
                'message': f'Installation not found: {installation_id}'
            }), 404
        
        installation = ACTIVE_INSTALLATIONS[installation_id]
        
        response = {
            'status': 'success',
            'installation': {
                'id': installation_id,
                **installation
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error getting installation status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bootcamp_bp.route('/install/<installation_id>/cancel', methods=['POST'])
@cross_origin()
def cancel_installation(installation_id: str):
    """
    Cancel installation
    
    Response:
    {
        "status": "success",
        "message": "Installation cancelled"
    }
    """
    
    try:
        if installation_id not in ACTIVE_INSTALLATIONS:
            return jsonify({
                'status': 'error',
                'message': f'Installation not found: {installation_id}'
            }), 404
        
        installation = ACTIVE_INSTALLATIONS[installation_id]
        installation['status'] = 'cancelled'
        
        response = {
            'status': 'success',
            'message': 'Installation cancelled',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Installation cancelled: {installation_id}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error cancelling installation: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bootcamp_bp.route('/compatibility/<mac_model>', methods=['GET'])
@cross_origin()
def check_compatibility(mac_model: str):
    """
    Check Boot Camp compatibility for Mac model
    
    Response:
    {
        "status": "success",
        "compatible": true,
        "reason": "System meets Boot Camp requirements"
    }
    """
    
    try:
        if mac_model not in DRIVER_DATABASE['models']:
            return jsonify({
                'status': 'error',
                'message': f'Mac model not found: {mac_model}'
            }), 404
        
        model_data = DRIVER_DATABASE['models'][mac_model]
        
        # Create MacSystemInfo from database
        mac_info = MacSystemInfo(
            model_identifier=model_data['model_id'],
            model_name=model_data['display_name'],
            mac_type=None,
            year=model_data['year'],
            board_id=model_data['board_id'],
            serial_number='',
            cpu_brand=model_data['cpu_type'],
            cpu_cores=0,
            ram_gb=0,
            storage_gb=0,
            gpu_model=model_data['gpu_type'],
            boot_camp_support=model_data['boot_camp_support']
        )
        
        compatibility = compatibility_checker.check_compatibility(mac_info)
        
        response = {
            'status': 'success',
            'mac_model': mac_model,
            'compatibility': compatibility,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error checking compatibility: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def register_bootcamp_api(app):
    """Register Boot Camp API blueprint with Flask app"""
    app.register_blueprint(bootcamp_bp)
    logger.info("Boot Camp API registered")
