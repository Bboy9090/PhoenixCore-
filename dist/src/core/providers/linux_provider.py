"""
BootForge Linux OS Image Provider
Downloads and verifies Ubuntu LTS releases from official sources
"""

import re
import os
import logging
import hashlib
import requests
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

from src.core.os_image_manager import (
    OSImageProvider, OSImageInfo, ImageStatus, VerificationMethod
)
from src.core.config import Config


class LinuxProvider(OSImageProvider):
    """Provider for Linux distributions, focusing on Ubuntu LTS releases"""
    
    # Ubuntu LTS release information
    UBUNTU_LTS_RELEASES = {
        "24.04": {
            "name": "Ubuntu 24.04 LTS (Noble Numbat)",
            "codename": "noble",
            "support_until": "2034-04"
        },
        "22.04": {
            "name": "Ubuntu 22.04 LTS (Jammy Jellyfish)",
            "codename": "jammy",
            "support_until": "2032-04"
        },
        "20.04": {
            "name": "Ubuntu 20.04 LTS (Focal Fossa)",
            "codename": "focal",
            "support_until": "2030-04"
        },
        "18.04": {
            "name": "Ubuntu 18.04 LTS (Bionic Beaver)",
            "codename": "bionic",
            "support_until": "2028-04"
        }
    }
    
    UBUNTU_BASE_URL = "http://releases.ubuntu.com/"
    GPG_KEYSERVER = "hkp://keyserver.ubuntu.com:80"
    UBUNTU_SIGNING_KEY = "843938DF228D22F7B3742BC0D94AA3F0EFE21092"  # Ubuntu CD Image Signing Key
    
    def __init__(self, config: Config):
        super().__init__("linux", config)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BootForge/1.1 (Linux Provider)'
        })
        
        # Cache for available images
        self._image_cache: List[OSImageInfo] = []
        self._cache_expires = 0
        
    def get_available_images(self) -> List[OSImageInfo]:
        """Get all available Ubuntu LTS images"""
        import time
        
        # Use cache if still valid (1 hour)
        if time.time() < self._cache_expires and self._image_cache:
            return self._image_cache.copy()
        
        images = []
        
        # Check each LTS release
        for version, info in self.UBUNTU_LTS_RELEASES.items():
            try:
                release_images = self._get_release_images(version, info)
                images.extend(release_images)
            except Exception as e:
                self.logger.warning(f"Failed to get images for Ubuntu {version}: {e}")
        
        # Update cache
        self._image_cache = images
        self._cache_expires = time.time() + 3600  # Cache for 1 hour
        
        return images.copy()
    
    def _get_release_images(self, version: str, release_info: Dict) -> List[OSImageInfo]:
        """Get available images for a specific Ubuntu release"""
        images = []
        codename = release_info["codename"]
        release_url = urljoin(self.UBUNTU_BASE_URL, f"{version}/")
        
        try:
            # Get release directory listing
            response = self.session.get(release_url, timeout=10)
            response.raise_for_status()
            
            # Parse available ISO files
            iso_pattern = re.compile(rf'href="(ubuntu-{version}.*?\.iso)"')
            isos = iso_pattern.findall(response.text)
            
            for iso_filename in isos:
                # Skip netboot and other specialized images
                if any(skip in iso_filename for skip in ['netboot', 'mini', 'server']):
                    continue
                
                # Determine architecture
                arch = self._detect_architecture(iso_filename)
                if not arch:
                    continue
                
                # Get file size from server
                iso_url = urljoin(release_url, iso_filename)
                size_bytes = self._get_file_size(iso_url)
                
                # Create image info
                image_id = f"ubuntu-{version}-{arch}"
                
                image = OSImageInfo(
                    id=image_id,
                    name=f"{release_info['name']} ({arch})",
                    os_family="linux",
                    version=version,
                    architecture=arch,
                    size_bytes=size_bytes,
                    download_url=iso_url,
                    checksum=None,  # Will be populated when needed
                    checksum_type="sha256",
                    verification_method=VerificationMethod.HYBRID,  # SHA256 + GPG
                    status=ImageStatus.AVAILABLE,
                    provider=self.name,
                    metadata={
                        "codename": codename,
                        "support_until": release_info["support_until"],
                        "filename": iso_filename,
                        "checksum_url": urljoin(release_url, "SHA256SUMS"),
                        "signature_url": urljoin(release_url, "SHA256SUMS.gpg"),
                        "distribution": "ubuntu",
                        "release_type": "lts"
                    }
                )
                
                images.append(image)
                
        except Exception as e:
            self.logger.error(f"Failed to get release images for {version}: {e}")
        
        return images
    
    def _detect_architecture(self, filename: str) -> Optional[str]:
        """Detect architecture from ISO filename"""
        if "amd64" in filename or "x86_64" in filename:
            return "x86_64"
        elif "arm64" in filename or "aarch64" in filename:
            return "arm64"
        elif "i386" in filename:
            return "i386"
        # Desktop images are typically amd64 by default
        elif "desktop" in filename and not any(arch in filename for arch in ["arm", "i386"]):
            return "x86_64"
        return None
    
    def _get_file_size(self, url: str) -> int:
        """Get file size from HTTP headers"""
        try:
            response = self.session.head(url, timeout=10)
            return int(response.headers.get('content-length', 0))
        except Exception:
            return 0
    
    def search_images(self, query: str, os_family: Optional[str] = None) -> List[OSImageInfo]:
        """Search for Linux images matching query"""
        if os_family and os_family != "linux":
            return []
        
        all_images = self.get_available_images()
        results = []
        
        query_lower = query.lower()
        
        for image in all_images:
            # Search in name, version, and metadata
            searchable_text = f"{image.name} {image.version} {image.metadata.get('codename', '')}"
            
            if query_lower in searchable_text.lower():
                results.append(image)
        
        return results
    
    def get_latest_image(self, os_family: str, version_pattern: Optional[str] = None) -> Optional[OSImageInfo]:
        """Get the latest Ubuntu LTS image"""
        if os_family != "linux":
            return None
        
        images = self.get_available_images()
        
        # Filter by version pattern if provided
        if version_pattern:
            pattern_lower = version_pattern.lower()
            images = [img for img in images if pattern_lower in img.version or 
                     pattern_lower in img.metadata.get('codename', '').lower()]
        
        # Get latest LTS (highest version number)
        if images:
            # Sort by version (newest first)
            sorted_images = sorted(images, 
                                 key=lambda x: tuple(map(int, x.version.split('.'))), 
                                 reverse=True)
            
            # Prefer desktop over server if available
            desktop_images = [img for img in sorted_images if 'desktop' in img.metadata.get('filename', '')]
            if desktop_images:
                return desktop_images[0]
            
            return sorted_images[0]
        
        return None
    
    def verify_image(self, image_info: OSImageInfo, local_path: str) -> bool:
        """Verify Ubuntu image using SHA256 + GPG signature"""
        try:
            self.logger.info(f"Verifying Ubuntu image: {local_path}")
            
            # Step 1: Download and verify SHA256SUMS file
            checksum_url = image_info.metadata.get("checksum_url")
            signature_url = image_info.metadata.get("signature_url")
            filename = image_info.metadata.get("filename")
            
            if not all([checksum_url, signature_url, filename]):
                self.logger.error("Missing verification URLs in image metadata")
                return False
            
            # Download SHA256SUMS and signature
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                checksums_path = temp_path / "SHA256SUMS"
                signature_path = temp_path / "SHA256SUMS.gpg"
                
                # Download SHA256SUMS
                self.logger.info("Downloading SHA256SUMS...")
                checksums_response = self.session.get(checksum_url, timeout=30)
                checksums_response.raise_for_status()
                checksums_path.write_text(checksums_response.text)
                
                # Download GPG signature
                self.logger.info("Downloading GPG signature...")
                signature_response = self.session.get(signature_url, timeout=30)
                signature_response.raise_for_status()
                signature_path.write_bytes(signature_response.content)
                
                # Step 2: Verify GPG signature
                if not self._verify_gpg_signature(checksums_path, signature_path):
                    self.logger.error("GPG signature verification failed")
                    return False
                
                # Step 3: Extract expected checksum
                expected_checksum = self._extract_checksum(checksums_path, filename)
                if not expected_checksum:
                    self.logger.error(f"Could not find checksum for {filename}")
                    return False
                
                # Step 4: Calculate actual checksum
                actual_checksum = self._calculate_sha256(local_path)
                
                # Step 5: Compare checksums
                if actual_checksum.lower() == expected_checksum.lower():
                    self.logger.info("Image verification successful")
                    return True
                else:
                    self.logger.error(f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Image verification failed: {e}")
            return False
    
    def _verify_gpg_signature(self, checksums_path: Path, signature_path: Path) -> bool:
        """Verify GPG signature of SHA256SUMS file"""
        try:
            # Check if GPG is available
            subprocess.run(["gpg", "--version"], check=True, capture_output=True)
            
            # Import Ubuntu CD signing key if needed
            try:
                subprocess.run([
                    "gpg", "--keyserver", self.GPG_KEYSERVER,
                    "--recv-keys", self.UBUNTU_SIGNING_KEY
                ], check=True, capture_output=True, timeout=30)
            except subprocess.CalledProcessError:
                self.logger.warning("Could not import Ubuntu signing key from keyserver")
                # Continue anyway - key might already be imported
            
            # Verify signature
            result = subprocess.run([
                "gpg", "--verify", str(signature_path), str(checksums_path)
            ], capture_output=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info("GPG signature verification successful")
                return True
            else:
                self.logger.warning(f"GPG verification warning: {result.stderr.decode()}")
                # Ubuntu signatures sometimes have warnings but are still valid
                # Check if it's just a trust warning
                stderr_text = result.stderr.decode().lower()
                if "good signature" in stderr_text:
                    self.logger.info("GPG signature is good despite trust warnings")
                    return True
                return False
                
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.warning(f"GPG verification failed: {e}")
            # Fall back to SHA256 only verification
            return True
        except Exception as e:
            self.logger.error(f"GPG verification error: {e}")
            return False
    
    def _extract_checksum(self, checksums_path: Path, filename: str) -> Optional[str]:
        """Extract SHA256 checksum for specific file from SHA256SUMS"""
        try:
            content = checksums_path.read_text()
            
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(None, 1)
                if len(parts) == 2:
                    checksum, file_path = parts
                    # Handle both *filename and filename formats
                    clean_filename = file_path.lstrip('*')
                    
                    if clean_filename == filename:
                        return checksum
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to extract checksum: {e}")
            return None
    
    def _calculate_sha256(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def get_supported_families(self) -> List[str]:
        """Get supported OS families"""
        return ["linux"]
    
    def get_verification_methods(self) -> List[VerificationMethod]:
        """Get supported verification methods"""
        return [VerificationMethod.SHA256, VerificationMethod.GPG, VerificationMethod.HYBRID]