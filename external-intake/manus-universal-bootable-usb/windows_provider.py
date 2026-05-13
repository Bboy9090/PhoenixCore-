BootForge Windows OS Image Provider
Handles manual Windows ISO upload and verification with checksum support
"""

import os
import re
import json
import logging
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
from urllib.parse import urlparse

from src.core.os_image_manager import (
    OSImageProvider, OSImageInfo, ImageStatus, VerificationMethod
)
from src.core.config import Config
from src.core.patch_pipeline import PatchPlanner, PatchSet, PatchAction
from src.core.hardware_detector import DetectedHardware
from src.core.models import HardwareProfile, DeploymentRecipe, DeploymentType
from src.core.safety_validator import SafetyValidator, PatchValidationMode
from src.core.win_patch_engine import WinPatchEngine, WindowsBypassType


class WindowsProvider(OSImageProvider):
    """Provider for Windows ISOs with manual upload and verification support"""
    
    # Known Windows versions and their identifiers
    WINDOWS_VERSIONS = {
        "11": {
            "name": "Windows 11",
            "editions": ["Home", "Pro", "Enterprise", "Education"],
            "min_size_gb": 4.0,
            "max_size_gb": 8.0
        },
        "10": {
            "name": "Windows 10",
            "editions": ["Home", "Pro", "Enterprise", "Education", "LTSC"],
            "min_size_gb": 3.5,
            "max_size_gb": 6.0
        },
        "server2022": {
            "name": "Windows Server 2022",
            "editions": ["Standard", "Datacenter", "Essentials"],
            "min_size_gb": 4.5,
            "max_size_gb": 8.0
        },
        "server2019": {
            "name": "Windows Server 2019",
            "editions": ["Standard", "Datacenter", "Essentials"],
            "min_size_gb": 4.0,
            "max_size_gb": 7.0
        }
    }
    
    # Common checksum sources for Windows ISOs
    CHECKSUM_SOURCES = {
        "microsoft_techbench": "https://www.microsoft.com/en-us/software-download/",