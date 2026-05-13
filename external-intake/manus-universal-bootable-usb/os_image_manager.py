BootForge OS Image Manager
Intelligent cloud-based OS image downloading, verification, and caching system
"""

import os
import json
import time
import uuid
import sqlite3
import hashlib
import logging
import requests
import tempfile
import threading
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from enum import Enum
from typing import Dict, List, Optional, Tuple, Callable, Any, Union
from dataclasses import dataclass, asdict, field
from urllib.parse import urlparse
# Qt dependencies removed for CLI compatibility

from src.core.config import Config


class ImageStatus(Enum):
    """OS Image status tracking"""
    UNKNOWN = "unknown"
    AVAILABLE = "available"          # Can be downloaded
    DOWNLOADING = "downloading"       # Currently downloading
    PAUSED = "paused"                # Download paused
    DOWNLOADED = "downloaded"        # Download complete
    VERIFYING = "verifying"          # Checking checksums/signatures
    VERIFIED = "verified"            # Ready to use
    FAILED = "failed"                # Download or verification failed
    CACHED = "cached"                # Available offline


class VerificationMethod(Enum):
    """Verification methods for OS images"""
    NONE = "none"
    SHA256 = "sha256"
    SHA512 = "sha512"
    MD5 = "md5"
    GPG = "gpg"
    HYBRID = "hybrid"  # Multiple methods


@dataclass
class OSImageInfo:
    """OS Image metadata and tracking"""
    id: str                          # Unique identifier
    name: str                        # Display name (e.g., "Ubuntu 22.04.3 LTS")
    os_family: str                   # "linux", "windows", "macos"
    version: str                     # Version string
    architecture: str                # "x86_64", "arm64", "i386"
    size_bytes: int                  # File size in bytes
    download_url: str                # Source URL
    local_path: Optional[str] = None # Local file path if cached
    checksum: Optional[str] = None   # Expected checksum
    checksum_type: str = "sha256"    # Checksum algorithm
    signature_url: Optional[str] = None  # GPG signature URL
    verification_method: VerificationMethod = VerificationMethod.SHA256
    status: ImageStatus = ImageStatus.UNKNOWN
    download_progress: float = 0.0   # Progress percentage (0-100)
    download_speed: float = 0.0      # Speed in MB/s
    eta_seconds: int = 0             # Estimated time remaining
    created_at: Optional[str] = None # ISO timestamp
    updated_at: Optional[str] = None # ISO timestamp
    provider: str = "unknown"        # Provider name
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extra data
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not self.updated_at:
            self.updated_at = self.created_at


@dataclass
class DownloadProgress:
    """Download progress information"""
    image_id: str
    status: ImageStatus
    progress_percent: float
    speed_mbps: float
    eta_seconds: int
    downloaded_bytes: int
    total_bytes: int
    error_message: Optional[str] = None


class OSImageProvider(ABC):
    """Abstract base class for OS image providers"""
    
    def __init__(self, name: str, config: Config):
        self.name = name
        self.config = config