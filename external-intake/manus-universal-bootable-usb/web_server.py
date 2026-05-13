"""
BootForge Web Demo Server
Simple web interface to showcase BootForge capabilities and serve downloads
"""

from flask import Flask, render_template, jsonify, send_from_directory, Response, request
import os
import sys
import hashlib
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

app = Flask(__name__)

# Configuration
BASE_URL = os.environ.get('BASE_URL', 'https://bootforge.dev')
DIST_DIR = 'dist'

# Supported architectures
SUPPORTED_ARCHITECTURES = {
    'linux': ['x64', 'arm64'],
    'windows': ['x64', 'arm64'],
    'macos': ['x64', 'arm64']
}

def get_base_url():
    """Get the base URL for the current request"""
    if 'X-Forwarded-Host' in request.headers:
        protocol = request.headers.get('X-Forwarded-Proto', 'https')
        host = request.headers.get('X-Forwarded-Host')
        return f"{protocol}://{host}"
    elif request.host:
        return f"{request.scheme}://{request.host}"
    else:
        return BASE_URL

def verify_file_integrity(file_path, expected_checksum=None):
    """Verify file integrity using SHA256"""
    try:
        with open(file_path, 'rb') as f:
            sha256_hash = hashlib.sha256()
            for chunk in iter(lambda: f.read(65536), b""):
                sha256_hash.update(chunk)
            actual_checksum = sha256_hash.hexdigest()
            
        if expected_checksum:
            return actual_checksum == expected_checksum
        return actual_checksum
    except Exception:
        return None

@app.route('/')
def index():
    """Main landing page"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BootForge - Professional OS Deployment Tool</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e1e, #2d2d2d);
            color: #ffffff;
            min-height: 100vh;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 2rem;
        }
        .header {
            text-align: center;
            margin-bottom: 3rem;
        }
        .logo {
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(45deg, #00d4ff, #0099cc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }
        .subtitle {
            font-size: 1.2rem;
            color: #cccccc;
            margin-bottom: 2rem;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin: 3rem 0;
        }