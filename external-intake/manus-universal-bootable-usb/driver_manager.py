"""
Boot Camp Driver Download and Caching Manager
Handles driver package downloads, caching, and verification
"""

import os
import json
import hashlib
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import zipfile

logger = logging.getLogger(__name__)


@dataclass
class DownloadProgress:
    """Download progress information"""
    total_bytes: int
    downloaded_bytes: int
    speed_mbps: float
    eta_seconds: int
    percentage: int


class DriverCacheManager:
    """Manage driver package caching"""
    
    def __init__(self, cache_dir: str = "/tmp/bootcamp_drivers", max_cache_age_days: int = 30):
        """Initialize cache manager"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_age = timedelta(days=max_cache_age_days)
        self.cache_index_file = self.cache_dir / "cache_index.json"
        self.cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict:
        """Load cache index from disk"""
        if self.cache_index_file.exists():
            try:
                with open(self.cache_index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cache index: {e}")
        return {}
    
    def _save_cache_index(self) -> None:
        """Save cache index to disk"""
        try:
            with open(self.cache_index_file, 'w') as f:
                json.dump(self.cache_index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def get_cached_driver(self, package_id: str, checksum: str) -> Optional[Path]:
        """Get cached driver package if available and valid"""
        
        cache_key = f"{package_id}_{checksum}"
        
        if cache_key not in self.cache_index:
            return None
        
        cache_entry = self.cache_index[cache_key]
        cache_path = Path(cache_entry['path'])
        
        # Check if file exists
        if not cache_path.exists():
            logger.warning(f"Cached file not found: {cache_path}")
            del self.cache_index[cache_key]
            self._save_cache_index()
            return None
        
        # Check cache age
        cached_date = datetime.fromisoformat(cache_entry['cached_date'])
        if datetime.now() - cached_date > self.max_cache_age:
            logger.info(f"Cache expired for {package_id}")
            cache_path.unlink()
            del self.cache_index[cache_key]
            self._save_cache_index()
            return None
        
        # Verify checksum
        if not self._verify_checksum(cache_path, checksum):
            logger.warning(f"Checksum mismatch for cached file: {cache_path}")
            cache_path.unlink()
            del self.cache_index[cache_key]
            self._save_cache_index()
            return None
        
        logger.info(f"Using cached driver: {cache_path}")
        return cache_path
    
    def cache_driver(self, package_id: str, file_path: Path, checksum: str) -> None:
        """Add driver package to cache"""
        
        cache_key = f"{package_id}_{checksum}"
        
        self.cache_index[cache_key] = {
            'package_id': package_id,
            'path': str(file_path),
            'checksum': checksum,
            'size_bytes': file_path.stat().st_size,
            'cached_date': datetime.now().isoformat()
        }
        
        self._save_cache_index()
        logger.info(f"Cached driver: {package_id}")
    
    def clear_cache(self) -> None:
        """Clear all cached drivers"""
        for file_path in self.cache_dir.glob("*.zip"):
            try:
                file_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete cache file: {e}")
        
        self.cache_index = {}
        self._save_cache_index()
        logger.info("Cache cleared")
    
    def get_cache_size(self) -> int:
        """Get total cache size in bytes"""
        total_size = 0
        for file_path in self.cache_dir.glob("*.zip"):
            total_size += file_path.stat().st_size
        return total_size
    
    @staticmethod
    def _verify_checksum(file_path: Path, expected_checksum: str) -> bool:
        """Verify file checksum"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest() == expected_checksum


class DriverDownloadManager:
    """Manage driver package downloads"""
    
    def __init__(self, cache_manager: DriverCacheManager, timeout_seconds: int = 300):
        """Initialize download manager"""
        self.cache_manager = cache_manager
        self.timeout = timeout_seconds
        self.session = requests.Session()
    
    def download_driver(
        self,
        package_id: str,
        download_url: str,
        checksum: str,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None
    ) -> Optional[Path]:
        """Download driver package with caching and verification"""
        
        # Check cache first
        cached_path = self.cache_manager.get_cached_driver(package_id, checksum)
        if cached_path:
            return cached_path
        
        # Download from URL
        try:
            download_path = self._download_file(
                download_url,
                package_id,
                progress_callback
            )
            
            # Verify checksum
            if not self._verify_checksum(download_path, checksum):
                logger.error(f"Checksum verification failed for {package_id}")
                download_path.unlink()
                return None
            
            # Cache the driver
            self.cache_manager.cache_driver(package_id, download_path, checksum)
            
            return download_path
        
        except Exception as e:
            logger.error(f"Failed to download driver {package_id}: {e}")
            return None
    
    def _download_file(
        self,
        url: str,
        package_id: str,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None
    ) -> Path:
        """Download file from URL with progress tracking"""
        
        # Prepare destination
        file_name = f"{package_id}.zip"
        file_path = self.cache_manager.cache_dir / file_name
        
        # Download with streaming
        response = self.session.get(url, stream=True, timeout=self.timeout)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        start_time = datetime.now()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Calculate progress
                    if progress_callback and total_size > 0:
                        elapsed = (datetime.now() - start_time).total_seconds()
                        speed_mbps = (downloaded / (1024 * 1024)) / max(elapsed, 1)
                        eta_seconds = int((total_size - downloaded) / (downloaded / max(elapsed, 1)))
                        
                        progress = DownloadProgress(
                            total_bytes=total_size,
                            downloaded_bytes=downloaded,
                            speed_mbps=speed_mbps,
                            eta_seconds=eta_seconds,
                            percentage=int((downloaded / total_size) * 100)
                        )
                        
                        progress_callback(progress)
        
        logger.info(f"Downloaded {package_id} to {file_path}")
        return file_path
    
    @staticmethod
    def _verify_checksum(file_path: Path, expected_checksum: str) -> bool:
        """Verify file checksum"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        
        actual_checksum = sha256_hash.hexdigest()
        
        if actual_checksum != expected_checksum:
            logger.error(f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}")
            return False
        
        logger.info(f"Checksum verified: {actual_checksum}")
        return True


class DriverExtractor:
    """Extract driver packages"""
    
    def __init__(self, extract_dir: str = "/tmp/bootcamp_extract"):
        """Initialize extractor"""
        self.extract_dir = Path(extract_dir)
        self.extract_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_driver_package(self, package_path: Path) -> Optional[Dict[str, Path]]:
        """Extract driver package to components"""
        
        try:
            # Create extraction directory
            package_name = package_path.stem
            extract_path = self.extract_dir / package_name
            extract_path.mkdir(parents=True, exist_ok=True)
            
            # Extract main package
            with zipfile.ZipFile(package_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            logger.info(f"Extracted {package_path} to {extract_path}")
            
            # Extract component packages
            components = {}
            for component_zip in extract_path.glob("*.zip"):
                component_name = component_zip.stem
                component_dir = extract_path / component_name
                component_dir.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(component_zip, 'r') as zip_ref:
                    zip_ref.extractall(component_dir)
                
                components[component_name] = component_dir
                logger.info(f"Extracted component: {component_name}")
            
            return components
        
        except Exception as e:
            logger.error(f"Failed to extract driver package: {e}")
            return None
    
    def cleanup_extraction(self, package_name: str) -> None:
        """Clean up extracted files"""
        
        extract_path = self.extract_dir / package_name
        
        try:
            import shutil
            shutil.rmtree(extract_path)
            logger.info(f"Cleaned up extraction directory: {extract_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup extraction directory: {e}")


class BootCampDriverManager:
    """Main driver management orchestrator"""
    
    def __init__(
        self,
        cache_dir: str = "/tmp/bootcamp_drivers",
        extract_dir: str = "/tmp/bootcamp_extract"
    ):
        """Initialize driver manager"""
        self.cache_manager = DriverCacheManager(cache_dir)
        self.download_manager = DriverDownloadManager(self.cache_manager)
        self.extractor = DriverExtractor(extract_dir)
    
    def get_driver_package(
        self,
        package_id: str,
        download_url: str,
        checksum: str,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None
    ) -> Optional[Dict[str, Path]]:
        """Get driver package (download if needed) and extract components"""
        
        # Download driver
        package_path = self.download_manager.download_driver(
            package_id,
            download_url,
            checksum,
            progress_callback
        )
        
        if not package_path:
            return None
        
        # Extract components
        components = self.extractor.extract_driver_package(package_path)
        
        return components
    
    def cleanup(self) -> None:
        """Clean up all temporary files"""
        self.cache_manager.clear_cache()
        
        try:
            import shutil
            shutil.rmtree(self.extractor.extract_dir)
        except Exception as e:
            logger.error(f"Failed to cleanup: {e}")
