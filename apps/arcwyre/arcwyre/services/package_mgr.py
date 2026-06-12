import subprocess
import platform
import logging
from typing import List, Dict, Tuple, Optional
import shutil
import json

class PackageManager:
    """Wrapper for apt and dpkg operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_linux = platform.system().lower() == "linux"
        self.has_apt = shutil.which("apt") is not None
        self.has_dpkg = shutil.which("dpkg-query") is not None
        
    def is_supported(self) -> bool:
        """Return True if package management is supported on this system."""
        return self.is_linux and self.has_apt and self.has_dpkg
        
    def get_installed_packages(self) -> List[Dict[str, str]]:
        """Get list of installed packages via dpkg-query."""
        if not self.is_supported():
            return []
            
        try:
            # Output format: name, version, description
            cmd = ["dpkg-query", "-W", "-f=${binary:Package}\\t${Version}\\t${Description}\\n"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to get packages: {result.stderr}")
                return []
                
            packages = []
            for line in result.stdout.strip().split('\n'):
                parts = line.split('\t', 2)
                if len(parts) >= 2:
                    packages.append({
                        "name": parts[0],
                        "version": parts[1],
                        "description": parts[2] if len(parts) > 2 else ""
                    })
                    
            return packages
        except Exception as e:
            self.logger.error(f"Error querying packages: {e}")
            return []
            
    def search_packages(self, query: str) -> List[Dict[str, str]]:
        """Search for packages using apt-cache."""
        if not self.is_supported():
            return []
            
        try:
            cmd = ["apt-cache", "search", query]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return []
                
            packages = []
            for line in result.stdout.strip().split('\n'):
                parts = line.split(' - ', 1)
                if len(parts) == 2:
                    packages.append({
                        "name": parts[0],
                        "description": parts[1]
                    })
            return packages
        except Exception as e:
            self.logger.error(f"Error searching packages: {e}")
            return []
            
    def get_upgradable_packages(self) -> List[Dict[str, str]]:
        """Get list of packages that can be upgraded."""
        if not self.is_supported():
            return []
            
        try:
            cmd = ["apt", "list", "--upgradable"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            packages = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith("Listing") or not line.strip():
                    continue
                # Example line: apt/jammy-updates,now 2.4.11 amd64 [upgradable from: 2.4.9]
                parts = line.split('/')
                if parts:
                    packages.append({
                        "name": parts[0],
                        "details": line
                    })
            return packages
        except Exception as e:
            self.logger.error(f"Error checking upgradable packages: {e}")
            return []
