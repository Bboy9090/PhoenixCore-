"""
Swagger/OpenAPI documentation setup for PhoenixDrive API
Integrates Flask-RESTX with OpenAPI 3.0 specification
"""

from flask import Flask
from flask_restx import Api, Resource, fields, Namespace
import os

def setup_swagger(app: Flask) -> Api:
    """
    Configure Swagger/OpenAPI documentation for the Flask app
    
    Args:
        app: Flask application instance
        
    Returns:
        Flask-RESTX Api instance with Swagger configured
    """
    
    # API configuration
    api = Api(
        app,
        version='1.0.0',
        title="Bobby's PhoenixDrive API",
        description="""
        Comprehensive API for multi-boot USB creation, hardware detection, and device management.
        
        **Features:**
        - Hardware detection and compatibility analysis
        - USB device enumeration and validation
        - Multi-OS recipe building and validation
        - Real-time build progress streaming via WebSocket
        - Multi-layer safety validation
        - QR code recipe export/import
        
        **Authentication:** Bearer token in Authorization header
        
        **Rate Limiting:**
        - Standard endpoints: 10 req/s
        - Build endpoints: 2 req/s
        - WebSocket: Unlimited
        """,
        doc='/api/docs',
        prefix='/api/v1',
        contact={
            'name': "Bobby's PhoenixDrive Support",
            'url': 'https://github.com/Bboy9090/PhoenixCore-',
        },
        license={
            'name': 'MIT',
            'url': 'https://opensource.org/licenses/MIT',
        },
    )
    
    # Define namespaces
    health_ns = Namespace('health', description='API health and status')
    hardware_ns = Namespace('hardware', description='Hardware detection and compatibility')
    usb_ns = Namespace('usb', description='USB device management and building')
    recipe_ns = Namespace('recipe', description='Recipe creation, validation, and management')
    safety_ns = Namespace('safety', description='Safety validation and checks')
    build_ns = Namespace('build', description='Build execution and progress tracking')
    
    # Add namespaces to API
    api.add_namespace(health_ns, path='/health')
    api.add_namespace(hardware_ns, path='/hardware')
    api.add_namespace(usb_ns, path='/usb')
    api.add_namespace(recipe_ns, path='/recipe')
    api.add_namespace(safety_ns, path='/safety')
    api.add_namespace(build_ns, path='/build')
    
    # Define models for serialization
    error_model = api.model('Error', {
        'status': fields.String(required=True, enum=['error']),
        'error': fields.String(required=True, description='Error code'),
        'message': fields.String(required=True, description='Human-readable error message'),
        'details': fields.Raw(description='Additional error details'),
        'timestamp': fields.DateTime(),
    })
    
    health_response = api.model('HealthResponse', {
        'status': fields.String(required=True, enum=['ok']),
        'version': fields.String(required=True),
        'phoenix_core_available': fields.Boolean(),
        'timestamp': fields.DateTime(),
    })
    
    hardware_response = api.model('HardwareDetectionResponse', {
        'status': fields.String(required=True, enum=['success']),
        'device_id': fields.String(required=True),
        'detected_at': fields.DateTime(),
        'hardware': fields.Raw(required=True),
        'compatible_os': fields.List(fields.Raw()),
        'incompatible_os': fields.List(fields.Raw()),
    })
    
    usb_device = api.model('USBDevice', {
        'device_id': fields.String(required=True),
        'path': fields.String(required=True),
        'name': fields.String(required=True),
        'size_gb': fields.Float(required=True),
        'filesystem': fields.String(),
        'vendor': fields.String(),
        'model': fields.String(),
        'serial': fields.String(),
        'is_removable': fields.Boolean(),
        'is_mounted': fields.Boolean(),
        'mountpoint': fields.String(),
        'health_status': fields.String(enum=['good', 'warning', 'critical']),
        'write_speed_mbps': fields.Float(),
        'read_speed_mbps': fields.Float(),
    })
    
    usb_devices_response = api.model('USBDevicesResponse', {
        'status': fields.String(required=True, enum=['success']),
        'devices': fields.List(fields.Nested(usb_device)),
        'total_devices': fields.Integer(),
        'timestamp': fields.DateTime(),
    })
    
    recipe_response = api.model('RecipeResponse', {
        'status': fields.String(required=True, enum=['success']),
        'recipe': fields.Raw(required=True),
    })
    
    recipe_validation_response = api.model('RecipeValidationResponse', {
        'status': fields.String(required=True, enum=['success']),
        'valid': fields.Boolean(required=True),
        'warnings': fields.List(fields.String()),
        'errors': fields.List(fields.String()),
        'estimated_time': fields.String(),
        'estimated_size': fields.String(),
    })
    
    safety_check_response = api.model('SafetyCheckResponse', {
        'status': fields.String(required=True, enum=['success']),
        'safe': fields.Boolean(required=True),
        'checks': fields.List(fields.Raw()),
        'risk_level': fields.String(enum=['low', 'medium', 'high', 'critical']),
        'requires_confirmation': fields.Boolean(),
    })
    
    build_start_response = api.model('BuildStartResponse', {
        'status': fields.String(required=True, enum=['started']),
        'build_id': fields.String(required=True),
        'recipe_id': fields.String(required=True),
        'started_at': fields.DateTime(),
        'estimated_duration_minutes': fields.Float(),
        'ws_url': fields.String(),
    })
    
    build_status_response = api.model('BuildStatusResponse', {
        'build_id': fields.String(required=True),
        'recipe_id': fields.String(),
        'state': fields.String(enum=['queued', 'initializing', 'writing', 'verifying', 'complete', 'error', 'cancelled']),
        'stage': fields.String(),
        'stage_progress': fields.Float(),
        'overall_progress': fields.Float(),
        'current_operation': fields.String(),
        'speed_mbps': fields.Float(),
        'eta_seconds': fields.Integer(),
        'bytes_written': fields.Integer(),
        'timestamp': fields.DateTime(),
        'error_message': fields.String(),
    })
    
    # Store models for use in route handlers
    app.swagger_models = {
        'error': error_model,
        'health_response': health_response,
        'hardware_response': hardware_response,
        'usb_device': usb_device,
        'usb_devices_response': usb_devices_response,
        'recipe_response': recipe_response,
        'recipe_validation_response': recipe_validation_response,
        'safety_check_response': safety_check_response,
        'build_start_response': build_start_response,
        'build_status_response': build_status_response,
    }
    
    return api


def create_swagger_routes(api: Api, namespaces: dict):
    """
    Create Swagger-documented routes
    
    Args:
        api: Flask-RESTX Api instance
        namespaces: Dictionary of namespace instances
    """
    
    health_ns = namespaces.get('health')
    hardware_ns = namespaces.get('hardware')
    usb_ns = namespaces.get('usb')
    recipe_ns = namespaces.get('recipe')
    safety_ns = namespaces.get('safety')
    build_ns = namespaces.get('build')
    
    if not health_ns:
        return
    
    # Health check endpoint
    @health_ns.route('/check')
    class HealthCheck(Resource):
        """API health check endpoint"""
        
        @health_ns.doc('get_health')
        @health_ns.marshal_with(api.models.get('health_response', {}))
        @health_ns.response(200, 'API is healthy')
        @health_ns.response(503, 'API is unhealthy')
        def get(self):
            """Returns API health status and version information"""
            return {
                'status': 'ok',
                'version': '1.0.0',
                'phoenix_core_available': True,
                'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
            }
    
    # Hardware detection endpoint
    if hardware_ns:
        @hardware_ns.route('/detect')
        class HardwareDetect(Resource):
            """Hardware detection endpoint"""
            
            @hardware_ns.doc('detect_hardware', security='bearerAuth')
            @hardware_ns.expect(api.parser().add_argument('include_gpu', type=bool, default=True))
            @hardware_ns.marshal_with(api.models.get('hardware_response', {}))
            @hardware_ns.response(200, 'Hardware detected successfully')
            @hardware_ns.response(400, 'Invalid request parameters')
            @hardware_ns.response(500, 'Hardware detection failed')
            def post(self):
                """Analyzes system hardware and returns compatible operating systems"""
                # Implementation handled by actual route handler
                pass
    
    # USB devices endpoint
    if usb_ns:
        @usb_ns.route('/devices')
        class USBDevices(Resource):
            """USB devices listing endpoint"""
            
            @usb_ns.doc('list_usb_devices', security='bearerAuth')
            @usb_ns.expect(
                api.parser()
                .add_argument('include_internal', type=bool, default=False)
                .add_argument('min_size_gb', type=float, default=1)
            )
            @usb_ns.marshal_with(api.models.get('usb_devices_response', {}))
            @usb_ns.response(200, 'USB devices listed successfully')
            @usb_ns.response(401, 'Unauthorized')
            @usb_ns.response(500, 'Failed to list USB devices')
            def get(self):
                """Returns list of connected USB devices with detailed information"""
                pass
    
    # Recipe building endpoint
    if recipe_ns:
        @recipe_ns.route('/build')
        class RecipeBuild(Resource):
            """Recipe building endpoint"""
            
            @recipe_ns.doc('build_recipe', security='bearerAuth')
            @recipe_ns.marshal_with(api.models.get('recipe_response', {}))
            @recipe_ns.response(200, 'Recipe built successfully')
            @recipe_ns.response(400, 'Invalid recipe parameters')
            @recipe_ns.response(422, 'Recipe validation failed')
            @recipe_ns.response(500, 'Recipe building failed')
            def post(self):
                """Creates a multi-boot USB recipe based on specifications"""
                pass
    
    # Safety check endpoint
    if safety_ns:
        @safety_ns.route('/check')
        class SafetyCheck(Resource):
            """Safety validation endpoint"""
            
            @safety_ns.doc('run_safety_check', security='bearerAuth')
            @safety_ns.marshal_with(api.models.get('safety_check_response', {}))
            @safety_ns.response(200, 'Safety checks completed')
            @safety_ns.response(400, 'Invalid safety check parameters')
            @safety_ns.response(422, 'Safety check failed')
            @safety_ns.response(500, 'Safety check error')
            def post(self):
                """Performs multi-layer safety validation before build execution"""
                pass
    
    # Build execution endpoint
    if build_ns:
        @build_ns.route('/start')
        class BuildStart(Resource):
            """Build start endpoint"""
            
            @build_ns.doc('start_usb_build', security='bearerAuth')
            @build_ns.marshal_with(api.models.get('build_start_response', {}))
            @build_ns.response(202, 'Build started successfully')
            @build_ns.response(400, 'Invalid build parameters')
            @build_ns.response(409, 'Device already in use')
            @build_ns.response(500, 'Build start failed')
            def post(self):
                """Initiates USB build process with real-time progress tracking"""
                pass
        
        @build_ns.route('/status/<string:build_id>')
        class BuildStatus(Resource):
            """Build status endpoint"""
            
            @build_ns.doc('get_build_status', security='bearerAuth')
            @build_ns.marshal_with(api.models.get('build_status_response', {}))
            @build_ns.response(200, 'Build status retrieved')
            @build_ns.response(404, 'Build not found')
            @build_ns.response(500, 'Failed to retrieve build status')
            def get(self, build_id):
                """Returns current build progress and status"""
                pass


def get_swagger_json_url(app: Flask) -> str:
    """
    Get the URL for the Swagger JSON specification
    
    Args:
        app: Flask application instance
        
    Returns:
        URL to the Swagger JSON file
    """
    return f"{app.config.get('SERVER_NAME', 'localhost')}/api/v1/swagger.json"


def get_swagger_ui_url(app: Flask) -> str:
    """
    Get the URL for the Swagger UI
    
    Args:
        app: Flask application instance
        
    Returns:
        URL to the Swagger UI
    """
    return f"{app.config.get('SERVER_NAME', 'localhost')}/api/docs"
