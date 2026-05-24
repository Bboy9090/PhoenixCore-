
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