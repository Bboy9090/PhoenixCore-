"""
Recipe Manager - Handle recipe validation and processing
"""

import json
import logging
from typing import Dict, List, Optional
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


class RecipeManager:
    """Manages recipe validation and processing"""
    
    # Recipe schema
    RECIPE_SCHEMA = {
        "type": "object",
        "required": ["version", "id", "name", "targetDevice", "partitions"],
        "properties": {
            "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
            "id": {"type": "string"},
            "name": {"type": "string", "minLength": 1},
            "description": {"type": "string"},
            "createdAt": {"type": "string"},
            "createdBy": {"type": "string"},
            "targetDevice": {
                "type": "object",
                "required": ["size", "filesystem"],
                "properties": {
                    "type": {"type": "string"},
                    "size": {"type": "string"},
                    "sizeBytes": {"type": "integer"},
                    "filesystem": {"type": "string", "enum": ["MBR", "GPT", "HYBRID"]}
                }
            },
            "bootloader": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "timeout": {"type": "integer"},
                    "entries": {"type": "array"}
                }
            },
            "partitions": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["id", "label", "size", "filesystem", "bootable"],
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "size": {"type": "string"},
                        "sizeBytes": {"type": "integer"},
                        "filesystem": {"type": "string"},
                        "bootable": {"type": "boolean"},
                        "os": {"type": "object"}
                    }
                }
            },
            "tools": {
                "type": "array",
                "items": {"type": "object"}
            },
            "safety": {
                "type": "object",
                "properties": {
                    "requiresConfirmation": {"type": "boolean"},
                    "warningLevel": {"type": "string"},
                    "dataLossRisk": {"type": "string"},
                    "verifyAfterWrite": {"type": "boolean"}
                }
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "hardwareProfile": {"type": "string"},
                    "createdByApp": {"type": "string"},
                    "sourceDevice": {"type": "string"},
                    "estimatedBuildTime": {"type": "string"},
                    "totalSize": {"type": "string"},
                    "tags": {"type": "array"}
                }
            }
        }
    }
    
    def __init__(self):
        """Initialize recipe manager"""
        pass
    
    def validate_recipe(self, recipe: Dict) -> List[str]:
        """
        Validate recipe against schema
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        try:
            validate(instance=recipe, schema=self.RECIPE_SCHEMA)
        except ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
        
        # Additional validation checks
        if 'targetDevice' in recipe:
            device_errors = self._validate_device(recipe['targetDevice'])
            errors.extend(device_errors)
        
        if 'partitions' in recipe:
            partition_errors = self._validate_partitions(recipe['partitions'])
            errors.extend(partition_errors)
        
        if 'os' in recipe:
            os_errors = self._validate_os_images(recipe.get('partitions', []))
            errors.extend(os_errors)
        
        return errors
    
    def _validate_device(self, device: Dict) -> List[str]:
        """Validate device configuration"""
        errors = []
        
        # Check size format
        if 'size' in device:
            size_str = device['size']
            if not self._is_valid_size_format(size_str):
                errors.append(f"Invalid device size format: {size_str} (expected format: '32GB')")
        
        # Check filesystem
        if 'filesystem' in device:
            valid_fs = ['MBR', 'GPT', 'HYBRID']
            if device['filesystem'] not in valid_fs:
                errors.append(f"Invalid filesystem: {device['filesystem']} (expected: {', '.join(valid_fs)})")
        
        return errors
    
    def _validate_partitions(self, partitions: List[Dict]) -> List[str]:
        """Validate partition configuration"""
        errors = []
        
        if not partitions:
            errors.append("At least one partition is required")
            return errors
        
        total_size = 0
        
        for i, partition in enumerate(partitions):
            # Check required fields
            required = ['id', 'label', 'size', 'filesystem', 'bootable']
            for field in required:
                if field not in partition:
                    errors.append(f"Partition {i}: missing required field '{field}'")
            
            # Validate size
            if 'size' in partition:
                if not self._is_valid_size_format(partition['size']):
                    errors.append(f"Partition {i}: invalid size format '{partition['size']}'")
                else:
                    total_size += self._parse_size(partition['size'])
            
            # Validate filesystem
            if 'filesystem' in partition:
                valid_fs = ['NTFS', 'FAT32', 'ext4', 'ext3', 'btrfs', 'xfs', 'exFAT']
                if partition['filesystem'] not in valid_fs:
                    errors.append(f"Partition {i}: invalid filesystem '{partition['filesystem']}'")
        
        return errors
    
    def _validate_os_images(self, partitions: List[Dict]) -> List[str]:
        """Validate OS image configuration"""
        errors = []
        
        for i, partition in enumerate(partitions):
            if 'os' not in partition:
                continue
            
            os_info = partition['os']
            
            # Check required OS fields
            if 'name' not in os_info:
                errors.append(f"Partition {i}: OS name is required")
            
            if 'version' not in os_info:
                errors.append(f"Partition {i}: OS version is required")
            
            # Validate ISO URL if present
            if 'iso' in os_info:
                if not self._is_valid_url(os_info['iso']):
                    errors.append(f"Partition {i}: invalid ISO URL '{os_info['iso']}'")
            
            # Validate checksum if present
            if 'checksum' in os_info and 'checksumType' not in os_info:
                errors.append(f"Partition {i}: checksum type is required when checksum is provided")
        
        return errors
    
    @staticmethod
    def _is_valid_size_format(size_str: str) -> bool:
        """Check if size string is in valid format (e.g., '32GB', '1.5TB')"""
        import re
        return bool(re.match(r'^\d+\.?\d*(GB|TB|MB)$', size_str))
    
    @staticmethod
    def _parse_size(size_str: str) -> float:
        """Parse size string to GB"""
        import re
        match = re.match(r'^(\d+\.?\d*)(GB|TB|MB)$', size_str)
        if not match:
            return 0
        
        value, unit = match.groups()
        value = float(value)
        
        if unit == 'TB':
            return value * 1024
        elif unit == 'MB':
            return value / 1024
        else:  # GB
            return value
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if URL is valid"""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(url))
    
    def get_recipe_summary(self, recipe: Dict) -> str:
        """Get human-readable recipe summary"""
        parts = []
        
        if 'name' in recipe:
            parts.append(f"Name: {recipe['name']}")
        
        if 'targetDevice' in recipe:
            device = recipe['targetDevice']
            parts.append(f"Device: {device.get('size', 'Unknown')} ({device.get('filesystem', 'Unknown')})")
        
        if 'partitions' in recipe:
            parts.append(f"Partitions: {len(recipe['partitions'])}")
        
        if 'tools' in recipe:
            parts.append(f"Tools: {len(recipe['tools'])}")
        
        return " | ".join(parts) if parts else "Unknown Recipe"
    
    def estimate_build_time(self, recipe: Dict) -> str:
        """Estimate build time based on recipe"""
        # Simple estimation: 1 minute per GB + 5 minutes overhead
        total_size = 0
        
        if 'partitions' in recipe:
            for partition in recipe['partitions']:
                if 'sizeBytes' in partition:
                    total_size += partition['sizeBytes']
        
        gb = total_size / (1024**3)
        minutes = int(gb + 5)
        
        if minutes < 1:
            return "< 1 minute"
        elif minutes < 60:
            return f"{minutes} minutes"
        else:
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}h {mins}m"
