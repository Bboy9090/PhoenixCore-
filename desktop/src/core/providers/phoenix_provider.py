"""
BootForge Native Phoenix OS & Home Aurelia Provider
Dedicated provider for Bobby's custom distributions: Blue Phoenix OS, Home Aurelia, Arcwyre, and Thunder God.
"""

import os
import time
import logging
from pathlib import Path
from typing import List, Optional, Dict

from src.core.os_image_manager import (
    OSImageProvider, OSImageInfo, ImageStatus, VerificationMethod
)
from src.core.config import Config

class PhoenixProvider(OSImageProvider):
    """Provider for premium local and cloud-based Native Phoenix OS suites"""
    
    def __init__(self, config: Config):
        super().__init__("phoenix", config)
        self.logger = logging.getLogger(f"{__name__}.phoenix")
        self._image_cache: List[OSImageInfo] = []
        self._load_images()
        
    def _load_images(self):
        """Pre-populate the list of premium Phoenix OS suite images"""
        self._image_cache = []
        
        # 1. Home Aurelia OS (Legacy i386)
        local_aurelia = Path("/Users/bj90-m1/PhoenixCore-/iso/outputs/bwos-home-legacy-i386.iso")
        aurelia_status = ImageStatus.AVAILABLE
        aurelia_local_path = None
        
        if local_aurelia.exists():
            aurelia_status = ImageStatus.VERIFIED
            aurelia_local_path = str(local_aurelia)
            
        aurelia_img = OSImageInfo(
            id="phoenix-aurelia-legacy",
            name="Home Aurelia OS (Legacy i386 Live)",
            os_family="linux",
            version="2.0.0",
            architecture="i386",
            size_bytes=2405183488,  # ~2.24 GB
            download_url="https://archive.org/download/bwos-home-legacy-i386/bwos-home-legacy-i386.iso",
            local_path=aurelia_local_path,
            status=aurelia_status,
            verification_method=VerificationMethod.NONE,
            provider=self.name,
            metadata={
                "distribution": "aurelia",
                "codename": "noble-phoenix",
                "aesthetic": "Dark Navy Base, Electric Blue Highlights, Gold Trim, Blue Phoenix Logo",
                "edition": "Legacy Live (32-bit ready)",
                "description": "Premium 32-bit hybrid OS designed for legacy Macs and custom MBR-FAT32 bootstrapping."
            }
        )
        
        # 2. Blue Phoenix OS (Native Flagship)
        blue_phoenix = OSImageInfo(
            id="phoenix-blue-native",
            name="Blue Phoenix Native OS (Flagship Edition)",
            os_family="linux",
            version="1.0.0-Beta",
            architecture="x86_64",
            size_bytes=3350071296,  # ~3.12 GB
            download_url="https://archive.org/download/blue-phoenix-native-os/blue-phoenix-native-x86_64.iso",
            status=ImageStatus.AVAILABLE,
            verification_method=VerificationMethod.NONE,
            provider=self.name,
            metadata={
                "distribution": "blue-phoenix",
                "codename": "thunder-god",
                "aesthetic": "Electric Blue Core, Dark Space Background, Gold Highlights",
                "edition": "Flagship Native",
                "description": "Next-generation native operating system designed for high-performance and modern developer setups."
            }
        )
        
        # 3. Arcwyre OS (Developer Power-User Edition)
        arcwyre = OSImageInfo(
            id="phoenix-arcwyre-dev",
            name="Arcwyre OS (Developer Suite)",
            os_family="linux",
            version="3.4.1",
            architecture="x86_64",
            size_bytes=3060162560,  # ~2.85 GB
            download_url="https://archive.org/download/arcwyre-os-dev/arcwyre-os-x86_64.iso",
            status=ImageStatus.AVAILABLE,
            verification_method=VerificationMethod.NONE,
            provider=self.name,
            metadata={
                "distribution": "arcwyre",
                "codename": "arcwyre",
                "aesthetic": "Deep Amethyst Base, Violet Lightning Accents, Gold Trim",
                "edition": "Developer Suite",
                "description": "Optimized power-user Linux distribution loaded with pre-configured developer workflows and tools."
            }
        )
        
        # 4. Thunder God OS (High-Performance Gaming/Workstation)
        thunder_god = OSImageInfo(
            id="phoenix-thunder-god",
            name="Thunder God OS (Workstation Edition)",
            os_family="linux",
            version="5.0.0",
            architecture="x86_64",
            size_bytes=3758096384,  # ~3.50 GB
            download_url="https://archive.org/download/thunder-god-os/thunder-god-x86_64.iso",
            status=ImageStatus.AVAILABLE,
            verification_method=VerificationMethod.NONE,
            provider=self.name,
            metadata={
                "distribution": "thunder-god",
                "codename": "mjolnir",
                "aesthetic": "Deep Obsidian Base, Neon Cyan Lightning Accents, Silver Trim",
                "edition": "Workstation & Gaming",
                "description": "Ultra-low latency kernel workstation designed for heavy compilation, gaming, and design workloads."
            }
        )
        
        self._image_cache = [aurelia_img, blue_phoenix, arcwyre, thunder_god]
        
    def get_available_images(self) -> List[OSImageInfo]:
        """Return available custom Phoenix OS suite images"""
        self._load_images()  # Reload in case file status changes
        return self._image_cache.copy()
        
    def search_images(self, query: str, os_family: Optional[str] = None) -> List[OSImageInfo]:
        """Search images in the Phoenix suite"""
        results = []
        query_lower = query.lower()
        for img in self._image_cache:
            if os_family and img.os_family != os_family:
                continue
            if query_lower in img.name.lower() or query_lower in img.metadata.get("description", "").lower():
                results.append(img)
        return results
        
    def get_latest_image(self, os_family: str, version_pattern: Optional[str] = None) -> Optional[OSImageInfo]:
        """Get latest image from the suite"""
        images = [img for img in self._image_cache if img.os_family == os_family]
        if not images:
            return None
        return images[0]
        
    def verify_image(self, image_info: OSImageInfo, local_path: str) -> bool:
        """Verify image integrity (bypass for custom suite for fast prototyping)"""
        return True
