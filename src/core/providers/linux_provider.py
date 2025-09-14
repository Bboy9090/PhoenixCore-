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
    """Provider for Linux distributions, supporting Ubuntu LTS and Kali Linux releases"""
    
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
    
    # Kali Linux release information
    KALI_RELEASES = {
        "2024.1": {
            "name": "Kali Linux 2024.1",
            "codename": "kali-rolling",
            "release_date": "2024-03-05",
            "type": "quarterly"
        },
        "2023.4": {
            "name": "Kali Linux 2023.4",
            "codename": "kali-rolling",
            "release_date": "2023-12-05",
            "type": "quarterly"
        },
        "2023.3": {
            "name": "Kali Linux 2023.3",
            "codename": "kali-rolling",
            "release_date": "2023-08-15",
            "type": "quarterly"
        },
        "2023.2": {
            "name": "Kali Linux 2023.2",
            "codename": "kali-rolling",
            "release_date": "2023-05-15",
            "type": "quarterly"
        },
        "2023.1": {
            "name": "Kali Linux 2023.1",
            "codename": "kali-rolling",
            "release_date": "2023-03-13",
            "type": "quarterly"
        }
    }
    
    # Kali Linux editions and their use cases
    KALI_EDITIONS = {
        "live": {
            "name": "Live",
            "description": "Bootable live environment with persistence support",
            "use_case": "security_testing",
            "toolset": "full"
        },
        "installer": {
            "name": "Installer",
            "description": "Full installation image with complete toolset",
            "use_case": "security_testing",
            "toolset": "full"
        },
        "netinst": {
            "name": "Net Installer",
            "description": "Minimal installer that downloads packages during installation",
            "use_case": "security_testing",
            "toolset": "minimal"
        },
        "rpi": {
            "name": "Raspberry Pi",
            "description": "Specialized images for Raspberry Pi devices",
            "use_case": "portable_security_testing",
            "toolset": "full"
        }
    }
    
    UBUNTU_BASE_URL = "http://releases.ubuntu.com/"
    KALI_BASE_URL = "https://cdimage.kali.org/"
    KALI_CURRENT_URL = "https://cdimage.kali.org/current/"
    GPG_KEYSERVER = "hkp://keyserver.ubuntu.com:80"
    UBUNTU_SIGNING_KEY = "843938DF228D22F7B3742BC0D94AA3F0EFE21092"  # Ubuntu CD Image Signing Key
    KALI_SIGNING_KEY = "44C6513A8E4FB3D30875F758ED444FF07D8D0BF6"  # Kali Linux Official Signing Key
    
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
        """Get all available Ubuntu LTS and Kali Linux images"""
        import time
        
        # Use cache if still valid (1 hour)
        if time.time() < self._cache_expires and self._image_cache:
            return self._image_cache.copy()
        
        images = []
        
        # Check each Ubuntu LTS release
        for version, info in self.UBUNTU_LTS_RELEASES.items():
            try:
                release_images = self._get_ubuntu_release_images(version, info)
                images.extend(release_images)
            except Exception as e:
                self.logger.warning(f"Failed to get images for Ubuntu {version}: {e}")
        
        # Check Kali Linux releases
        try:
            kali_images = self._get_kali_images()
            images.extend(kali_images)
        except Exception as e:
            self.logger.warning(f"Failed to get Kali Linux images: {e}")
        
        # Update cache
        self._image_cache = images
        self._cache_expires = time.time() + 3600  # Cache for 1 hour
        
        return images.copy()
    
    def _get_ubuntu_release_images(self, version: str, release_info: Dict) -> List[OSImageInfo]:
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
    
    def _get_kali_images(self) -> List[OSImageInfo]:
        """Get available Kali Linux images from current and archive releases"""
        images = []
        
        # Get current release images
        try:
            current_images = self._get_kali_current_images()
            images.extend(current_images)
        except Exception as e:
            self.logger.warning(f"Failed to get current Kali images: {e}")
        
        # Get archived release images for older versions
        for version, info in self.KALI_RELEASES.items():
            # Skip 2024.1 since it's likely the current
            if version == "2024.1":
                continue
                
            try:
                archived_images = self._get_kali_archived_images(version, info)
                images.extend(archived_images)
            except Exception as e:
                self.logger.warning(f"Failed to get Kali {version} images: {e}")
        
        return images
    
    def _get_kali_current_images(self) -> List[OSImageInfo]:
        """Get current Kali Linux release images"""
        images = []
        
        try:
            # Get current directory listing
            response = self.session.get(self.KALI_CURRENT_URL, timeout=15)
            response.raise_for_status()
            
            # Parse available ISO files
            iso_patterns = [
                r'href="(kali-linux-.*?\.iso)"',  # Standard ISOs
                r'href="(kali-linux-.*?\.img\.xz)"',  # ARM images
            ]
            
            isos = []
            for pattern in iso_patterns:
                matches = re.findall(pattern, response.text)
                isos.extend(matches)
            
            # Process each ISO
            for iso_filename in isos:
                # Parse version from filename instead of hardcoding
                version = self._parse_kali_version_from_filename(iso_filename) or "2024.1"
                image_info = self._process_kali_iso(iso_filename, self.KALI_CURRENT_URL, version)
                if image_info:
                    images.append(image_info)
                    
        except Exception as e:
            self.logger.error(f"Failed to get current Kali images: {e}")
        
        return images
    
    def _get_kali_archived_images(self, version: str, release_info: Dict) -> List[OSImageInfo]:
        """Get archived Kali Linux release images"""
        images = []
        
        try:
            # Construct archive URL
            archive_url = urljoin(self.KALI_BASE_URL, f"kali-{version}/")
            
            # Try to get archive directory listing
            response = self.session.get(archive_url, timeout=15)
            response.raise_for_status()
            
            # Parse available ISO files
            iso_patterns = [
                r'href="(kali-linux-.*?\.iso)"',
                r'href="(kali-linux-.*?\.img\.xz)"',
            ]
            
            isos = []
            for pattern in iso_patterns:
                matches = re.findall(pattern, response.text)
                isos.extend(matches)
            
            # Process each ISO
            for iso_filename in isos:
                image_info = self._process_kali_iso(iso_filename, archive_url, version)
                if image_info:
                    images.append(image_info)
                    
        except Exception as e:
            self.logger.warning(f"Failed to get archived Kali {version} images: {e}")
        
        return images
    
    def _process_kali_iso(self, iso_filename: str, base_url: str, version: str) -> Optional[OSImageInfo]:
        """Process a Kali ISO filename and create OSImageInfo"""
        try:
            # Determine architecture
            arch = self._detect_kali_architecture(iso_filename)
            if not arch:
                return None
            
            # Determine edition and variant
            edition, variant_info = self._detect_kali_edition(iso_filename)
            
            # Get file size
            iso_url = urljoin(base_url, iso_filename)
            size_bytes = self._get_file_size(iso_url)
            
            # Create truly unique image ID using sanitized filename stem
            sanitized_stem = self._sanitize_filename_for_id(iso_filename)
            image_id = f"kali-{sanitized_stem}"
            
            # Build display name
            kali_info = self.KALI_RELEASES.get(version, {"name": f"Kali Linux {version}"})
            display_name = f"{kali_info['name']} {variant_info['name']} ({arch})"
            
            # Create metadata
            metadata = {
                "distribution": "kali",
                "release_type": "quarterly",
                "codename": "kali-rolling",
                "filename": iso_filename,
                "edition": edition,
                "variant_info": variant_info,
                "use_case": variant_info.get("use_case", "security_testing"),
                "toolset": variant_info.get("toolset", "full"),
                "checksum_url": urljoin(base_url, "SHA256SUMS"),
                "signature_url": urljoin(base_url, "SHA256SUMS.gpg"),
                "target_hardware": self._get_target_hardware(arch, iso_filename)
            }
            
            # Add release date if available
            if "release_date" in kali_info:
                metadata["release_date"] = kali_info["release_date"]
            
            # Create image info
            image = OSImageInfo(
                id=image_id,
                name=display_name,
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
                metadata=metadata
            )
            
            return image
            
        except Exception as e:
            self.logger.warning(f"Failed to process Kali ISO {iso_filename}: {e}")
            return None
    
    def _sanitize_filename_for_id(self, filename: str) -> str:
        """Sanitize filename for use in image IDs
        
        Takes full filename and creates a clean, unique identifier by:
        1. Removing file extensions (.iso, .img.xz, etc.)
        2. Removing common prefix "kali-linux-" to avoid redundancy  
        3. Replacing problematic characters with dashes
        4. Ensuring uniqueness across all variants
        
        Examples:
        - kali-linux-2024.1-rpi4-arm64.img.xz → 2024.1-rpi4-arm64
        - kali-linux-2024.1-pinebook-pro-arm64.img.xz → 2024.1-pinebook-pro-arm64
        - kali-linux-2024.1-live-amd64.iso → 2024.1-live-amd64
        """
        # Remove known extensions properly (handle .img.xz, .iso, etc.)
        stem = filename
        for ext in ['.img.xz', '.iso', '.img', '.xz']:
            if stem.endswith(ext):
                stem = stem[:-len(ext)]
                break
        
        # Remove common kali-linux prefix to avoid redundancy
        if stem.startswith('kali-linux-'):
            stem = stem[11:]  # Remove "kali-linux-"
        elif stem.startswith('kali-'):
            stem = stem[5:]   # Remove "kali-"
        
        # Sanitize problematic characters - replace with dashes
        sanitized = re.sub(r'[^a-zA-Z0-9.-]', '-', stem)
        
        # Clean up multiple consecutive dashes
        sanitized = re.sub(r'-+', '-', sanitized)
        
        # Remove leading/trailing dashes
        sanitized = sanitized.strip('-')
        
        return sanitized
    
    def _detect_kali_architecture(self, filename: str) -> Optional[str]:
        """Detect architecture from Kali ISO filename"""
        filename_lower = filename.lower()
        
        # ARM variants (most specific first)
        if "raspberry-pi" in filename_lower or "rpi" in filename_lower:
            if "arm64" in filename_lower or "aarch64" in filename_lower:
                return "arm64"  # Pi 3/4/5 64-bit
            else:
                return "armhf"  # Pi 2/3/4 32-bit
        elif "pinebook" in filename_lower:
            return "arm64"  # Pinebook Pro
        elif "banana" in filename_lower or "orange" in filename_lower:
            return "armhf"  # Banana Pi, Orange Pi
        elif "arm64" in filename_lower or "aarch64" in filename_lower:
            return "arm64"  # Generic ARM64
        elif "armhf" in filename_lower or "armv7" in filename_lower:
            return "armhf"  # Generic ARM 32-bit
        
        # x86 variants
        elif "amd64" in filename_lower or "x86_64" in filename_lower:
            return "x86_64"
        elif "i386" in filename_lower:
            return "i386"
        
        # Default assumption for Kali (most images are x86_64)
        elif not any(arch in filename_lower for arch in ["arm", "i386", "i686"]):
            return "x86_64"
        
        return None
    
    def _detect_kali_edition(self, filename: str) -> Tuple[str, Dict[str, str]]:
        """Detect Kali edition and return edition key with variant info"""
        filename_lower = filename.lower()
        
        # Check for specific editions
        if "live" in filename_lower:
            return "live", self.KALI_EDITIONS["live"]
        elif "installer" in filename_lower:
            return "installer", self.KALI_EDITIONS["installer"]
        elif "netinst" in filename_lower:
            return "netinst", self.KALI_EDITIONS["netinst"]
        elif any(rpi in filename_lower for rpi in ["rpi", "raspberry", "pinebook", "banana", "orange"]):
            return "rpi", self.KALI_EDITIONS["rpi"]
        
        # Default to live for most Kali images
        return "live", self.KALI_EDITIONS["live"]
    
    def _parse_kali_version_from_filename(self, filename: str) -> Optional[str]:
        """Parse Kali Linux version from ISO filename"""
        # Pattern to match kali-linux-YYYY.X format
        version_pattern = r'kali-linux-(20\d{2}\.\d+)'
        match = re.search(version_pattern, filename, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        # Try alternative patterns like kali-YYYY.X
        alt_pattern = r'kali-(20\d{2}\.\d+)'
        alt_match = re.search(alt_pattern, filename, re.IGNORECASE)
        
        if alt_match:
            return alt_match.group(1)
            
        return None
    
    def _get_target_hardware(self, arch: str, filename: str) -> str:
        """Determine target hardware from architecture and filename"""
        filename_lower = filename.lower()
        
        if arch == "x86_64":
            return "desktop_laptop"
        elif arch == "i386":
            return "legacy_desktop"
        elif "raspberry-pi" in filename_lower or "rpi" in filename_lower:
            if "4" in filename_lower:
                return "raspberry_pi_4"
            elif "3" in filename_lower:
                return "raspberry_pi_3"
            elif "2" in filename_lower:
                return "raspberry_pi_2"
            else:
                return "raspberry_pi"
        elif "pinebook" in filename_lower:
            return "pinebook_pro"
        elif arch in ["arm64", "armhf"]:
            return "single_board_computer"
        
        return "generic"
    
    def _detect_architecture(self, filename: str) -> Optional[str]:
        """Detect architecture from ISO filename (Ubuntu-focused)"""
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
        """Search for Linux images matching query across Ubuntu and Kali distributions"""
        if os_family and os_family != "linux":
            return []
        
        all_images = self.get_available_images()
        results = []
        
        query_lower = query.lower()
        
        for image in all_images:
            # Enhanced search across multiple fields
            searchable_fields = [
                image.name,
                image.version,
                image.metadata.get('codename', ''),
                image.metadata.get('distribution', ''),
                image.metadata.get('edition', ''),
                image.metadata.get('use_case', ''),
                image.metadata.get('target_hardware', ''),
            ]
            
            # Also search in variant info if available
            variant_info = image.metadata.get('variant_info', {})
            if isinstance(variant_info, dict):
                searchable_fields.extend([
                    variant_info.get('name', ''),
                    variant_info.get('description', ''),
                    variant_info.get('use_case', ''),
                ])
            
            searchable_text = ' '.join(str(field) for field in searchable_fields if field)
            
            if query_lower in searchable_text.lower():
                results.append(image)
        
        return results
    
    def get_latest_image(self, os_family: str, version_pattern: Optional[str] = None) -> Optional[OSImageInfo]:
        """Get the latest Linux image (Ubuntu LTS or Kali)"""
        if os_family != "linux":
            return None
        
        images = self.get_available_images()
        
        # Filter by version pattern if provided
        if version_pattern:
            pattern_lower = version_pattern.lower()
            images = [img for img in images if pattern_lower in img.version or 
                     pattern_lower in img.metadata.get('codename', '').lower() or
                     pattern_lower in img.metadata.get('distribution', '').lower()]
        
        if images:
            # Separate Ubuntu and Kali images
            ubuntu_images = [img for img in images if img.metadata.get('distribution') == 'ubuntu']
            kali_images = [img for img in images if img.metadata.get('distribution') == 'kali']
            
            latest_images = []
            
            # Get latest Ubuntu image (highest version number)
            if ubuntu_images:
                sorted_ubuntu = sorted(ubuntu_images, 
                                     key=lambda x: tuple(map(int, x.version.split('.'))), 
                                     reverse=True)
                
                # Prefer desktop over server for Ubuntu
                desktop_ubuntu = [img for img in sorted_ubuntu if 'desktop' in img.metadata.get('filename', '')]
                if desktop_ubuntu:
                    latest_images.append(desktop_ubuntu[0])
                else:
                    latest_images.append(sorted_ubuntu[0])
            
            # Get latest Kali image (newest by version)
            if kali_images:
                sorted_kali = sorted(kali_images, 
                                   key=lambda x: tuple(map(int, x.version.split('.'))), 
                                   reverse=True)
                
                # Prefer live edition for Kali
                live_kali = [img for img in sorted_kali if img.metadata.get('edition') == 'live']
                if live_kali:
                    latest_images.append(live_kali[0])
                else:
                    latest_images.append(sorted_kali[0])
            
            # Return the most recent overall (preserve Ubuntu-first behavior unless explicitly requested)
            if latest_images:
                if len(latest_images) == 2:  # Both Ubuntu and Kali available
                    # Check if user specifically requested Kali via version pattern
                    if version_pattern:
                        pattern_lower = version_pattern.lower()
                        if any(kali_term in pattern_lower for kali_term in ['kali', 'security', 'penetration', 'pentest']):
                            # User wants Kali - return it
                            kali_img = next((img for img in latest_images if img.metadata.get('distribution') == 'kali'), None)
                            if kali_img:
                                return kali_img
                    
                    # Default behavior: prefer Ubuntu for backward compatibility
                    ubuntu_img = next((img for img in latest_images if img.metadata.get('distribution') == 'ubuntu'), None)
                    if ubuntu_img:
                        return ubuntu_img
                
                return latest_images[0]
        
        return None
    
    def verify_image(self, image_info: OSImageInfo, local_path: str) -> bool:
        """Verify Linux image (Ubuntu/Kali) using SHA256 + GPG signature"""
        try:
            distribution = image_info.metadata.get("distribution", "ubuntu")
            self.logger.info(f"Verifying {distribution} image: {local_path}")
            
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
                if not self._verify_gpg_signature(checksums_path, signature_path, distribution):
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
    
    def _verify_gpg_signature(self, checksums_path: Path, signature_path: Path, distribution: str) -> bool:
        """Verify GPG signature of SHA256SUMS file"""
        try:
            # Check if GPG is available
            subprocess.run(["gpg", "--version"], check=True, capture_output=True)
            
            # Import the appropriate signing key based on distribution
            if distribution == "kali":
                signing_key = self.KALI_SIGNING_KEY
                key_name = "Kali"
            else:
                signing_key = self.UBUNTU_SIGNING_KEY
                key_name = "Ubuntu"
            
            try:
                subprocess.run([
                    "gpg", "--keyserver", self.GPG_KEYSERVER,
                    "--recv-keys", signing_key
                ], check=True, capture_output=True, timeout=30)
            except subprocess.CalledProcessError:
                self.logger.warning(f"Could not import {key_name} signing key from keyserver")
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