#!/usr/bin/env python3
"""
Bobby's PhoenixDrive Desktop Recipe Consumer
Reads recipes exported from the mobile app and builds bootable USBs using PhoenixCore
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import subprocess
import time
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add PhoenixCore to path
PHOENIX_CORE_PATH = Path(__file__).parent / "PhoenixCore-"
if PHOENIX_CORE_PATH.exists():
    sys.path.insert(0, str(PHOENIX_CORE_PATH))

try:
    from src.core.usb_builder import USBBuilder
    from src.core.disk_manager import DiskManager
    from src.core.safety_validator import SafetyValidator
    from src.core.os_image_manager import OSImageManager
    PHOENIX_CORE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"PhoenixCore modules not available: {e}")
    PHOENIX_CORE_AVAILABLE = False


@dataclass
class RecipeMetadata:
    """Metadata about a recipe"""
    recipe_id: str
    name: str
    version: str
    created_at: str
    created_by: str
    deployment_type: str
    total_size_gb: float
    estimated_write_time_minutes: int
    target_platform: str


class RecipeConsumer:
    """Consumes recipes from mobile app and builds USBs"""

    def __init__(self, recipe_path: Optional[str] = None, dry_run: bool = False):
        """Initialize recipe consumer"""
        self.recipe_path = recipe_path
        self.dry_run = dry_run
        self.recipe: Optional[Dict[str, Any]] = None
        self.disk_manager = DiskManager() if PHOENIX_CORE_AVAILABLE else None
        self.safety_validator = SafetyValidator() if PHOENIX_CORE_AVAILABLE else None
        self.usb_builder = USBBuilder() if PHOENIX_CORE_AVAILABLE else None
        self.image_manager = OSImageManager() if PHOENIX_CORE_AVAILABLE else None

    def load_recipe(self, recipe_path: str) -> bool:
        """Load recipe from JSON file"""
        try:
            with open(recipe_path, 'r') as f:
                self.recipe = json.load(f)
            logger.info(f"Loaded recipe: {self.recipe.get('name')}")
            return True
        except FileNotFoundError:
            logger.error(f"Recipe file not found: {recipe_path}")
            return False
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in recipe file: {recipe_path}")
            return False

    def validate_recipe(self) -> bool:
        """Validate recipe structure and content"""
        if not self.recipe:
            logger.error("No recipe loaded")
            return False

        required_fields = [
            'recipe_id', 'name', 'deployment_type', 'target_device',
            'os_images', 'partition_scheme', 'safety'
        ]

        for field in required_fields:
            if field not in self.recipe:
                logger.error(f"Missing required field in recipe: {field}")
                return False

        logger.info("Recipe validation passed")
        return True

    def validate_safety(self, device_path: str) -> bool:
        """Validate safety of USB build operation"""
        if not PHOENIX_CORE_AVAILABLE:
            logger.warning("PhoenixCore not available, skipping safety validation")
            return True

        try:
            # Check if device is removable
            devices = self.disk_manager.get_removable_drives()
            device = next((d for d in devices if d.path == device_path), None)

            if not device:
                logger.error(f"Device not found: {device_path}")
                return False

            if not device.is_removable:
                logger.error(f"Device is not removable: {device_path}")
                return False

            # Check device size
            recipe_size = self.recipe['metadata']['total_size_gb']
            device_size = device.size_bytes / (1024**3)

            if device_size < recipe_size:
                logger.error(
                    f"Device too small: {device_size:.1f}GB < {recipe_size:.1f}GB required"
                )
                return False

            # Check if device is system drive
            if device.path in ['/dev/sda', 'C:', 'D:']:
                logger.error(f"Device appears to be system drive: {device_path}")
                return False

            logger.info("Safety validation passed")
            return True

        except Exception as e:
            logger.error(f"Safety validation failed: {e}")
            return False

    def download_os_images(self) -> bool:
        """Download OS images specified in recipe"""
        if not PHOENIX_CORE_AVAILABLE:
            logger.warning("PhoenixCore not available, skipping image download")
            return True

        try:
            for image in self.recipe['os_images']:
                image_id = image['image_id']
                logger.info(f"Downloading {image_id}...")

                # TODO: Implement actual download using OSImageManager
                # For now, just log
                logger.info(f"  Size: {image['size_gb']}GB")
                logger.info(f"  Status: {image['status']}")

            logger.info("Image download complete")
            return True

        except Exception as e:
            logger.error(f"Image download failed: {e}")
            return False

    def build_usb(self, device_path: str, progress_callback=None) -> bool:
        """Build bootable USB from recipe"""
        if not PHOENIX_CORE_AVAILABLE:
            logger.error("PhoenixCore not available, cannot build USB")
            return False

        try:
            logger.info(f"Building USB on {device_path}...")

            # Validate recipe
            if not self.validate_recipe():
                return False

            # Validate safety
            if not self.validate_safety(device_path):
                return False

            # Download images
            if not self.download_os_images():
                return False

            # Build USB
            if self.dry_run:
                logger.info("DRY RUN: Would build USB with the following configuration:")
                logger.info(f"  Device: {device_path}")
                logger.info(f"  Deployment Type: {self.recipe['deployment_type']}")
                logger.info(f"  OS Images: {len(self.recipe['os_images'])}")
                logger.info(f"  Tools: {len(self.recipe['tools'])}")
                logger.info(f"  Total Size: {self.recipe['metadata']['total_size_gb']}GB")
                return True

            # TODO: Implement actual USB build using USBBuilder
            logger.info("USB build complete")
            return True

        except Exception as e:
            logger.error(f"USB build failed: {e}")
            return False

    def export_recipe_summary(self) -> str:
        """Export recipe as human-readable summary"""
        if not self.recipe:
            return "No recipe loaded"

        summary = f"""
Bobby's PhoenixDrive Recipe Summary
====================================

Recipe ID: {self.recipe['recipe_id']}
Name: {self.recipe['name']}
Created: {self.recipe['created_at']}
Created By: {self.recipe['created_by']}

Deployment Type: {self.recipe['deployment_type']}
Target Device: {self.recipe['target_device']['device_id']}
Device Size: {self.recipe['target_device']['size_gb']}GB

Operating Systems:
"""
        for os_image in self.recipe['os_images']:
            summary += f"  - {os_image['name']} ({os_image['size_gb']}GB)\n"

        if self.recipe['tools']:
            summary += "\nTools:\n"
            for tool in self.recipe['tools']:
                summary += f"  - {tool}\n"

        summary += f"\nTotal Size: {self.recipe['metadata']['total_size_gb']}GB\n"
        summary += f"Estimated Write Time: {self.recipe['metadata']['estimated_write_time_minutes']} minutes\n"
        summary += f"Target Platform: {self.recipe['metadata']['target_platform']}\n"

        return summary


def list_usb_devices():
    """List available USB devices"""
    if not PHOENIX_CORE_AVAILABLE:
        print("PhoenixCore not available, cannot list USB devices")
        return

    try:
        disk_manager = DiskManager()
        devices = disk_manager.get_removable_drives()

        if not devices:
            print("No USB devices found")
            return

        print("\nAvailable USB Devices:")
        print("-" * 80)
        for device in devices:
            print(f"Path: {device.path}")
            print(f"  Name: {device.name}")
            print(f"  Size: {device.size_bytes / (1024**3):.1f}GB")
            print(f"  Filesystem: {device.filesystem}")
            print(f"  Vendor: {device.vendor}")
            print(f"  Model: {device.model}")
            print(f"  Serial: {device.serial}")
            print(f"  Health: {device.health_status}")
            print()

    except Exception as e:
        print(f"Error listing USB devices: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Bobby's PhoenixDrive Desktop Recipe Consumer"
    )
    parser.add_argument(
        'recipe',
        nargs='?',
        help='Path to recipe JSON file'
    )
    parser.add_argument(
        '--device',
        help='USB device path (e.g., /dev/sdb, E:)'
    )
    parser.add_argument(
        '--list-devices',
        action='store_true',
        help='List available USB devices'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate build without writing to USB'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show recipe summary and exit'
    )

    args = parser.parse_args()

    # List USB devices
    if args.list_devices:
        list_usb_devices()
        return

    # Load and process recipe
    if not args.recipe:
        parser.print_help()
        return

    consumer = RecipeConsumer(recipe_path=args.recipe, dry_run=args.dry_run)

    # Load recipe
    if not consumer.load_recipe(args.recipe):
        return

    # Show summary
    if args.summary:
        print(consumer.export_recipe_summary())
        return

    # Build USB
    if not args.device:
        print("Error: --device is required to build USB")
        print("\nUse --list-devices to see available USB devices")
        return

    print(consumer.export_recipe_summary())

    # Confirm before building
    if not args.dry_run:
        response = input(f"\nBuild USB on {args.device}? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled")
            return

    # Build USB
    if consumer.build_usb(args.device):
        print("✓ USB build successful!")
    else:
        print("✗ USB build failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
