"""
Multi-Boot Bridge Service
Connects the Arcwyre BootForge UI to the robust desktop/src/core/usb_builder backend.
"""
import sys
import os
from pathlib import Path

# Add the root PhoenixCore directory to sys.path so we can import desktop.src.core
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Attempt to import the backend StorageBuilder.
# If dependencies (like PyQt6.QtCore or specific core modules) fail to load,
# we fail gracefully so the UI doesn't crash.
try:
    from desktop.src.core.usb_builder import StorageBuilder
    from desktop.src.core.models import DeploymentRecipe, PartitionScheme, FileSystem, PartitionInfo, DeploymentType, HardwareProfile
    BACKEND_AVAILABLE = True
except ImportError as e:
    StorageBuilder = None
    DeploymentRecipe = None
    BACKEND_AVAILABLE = False
    _IMPORT_ERROR = str(e)


class MultiBootBridge:
    """Bridge interface to handle complex multiboot deployments."""
    
    @staticmethod
    def is_available() -> tuple[bool, str]:
        """Check if the backend StorageBuilder is available."""
        if BACKEND_AVAILABLE:
            return True, "StorageBuilder Backend Available"
        return False, f"Backend unavailable: {_IMPORT_ERROR}"

    @staticmethod
    def construct_multiboot_recipe(
        name: str, 
        payloads: list[str], 
        partition_scheme: str,
        file_system: str,
        inject_oclp: bool,
        inject_bootcamp: bool
    ) -> 'DeploymentRecipe | None':
        """
        Constructs a DeploymentRecipe for a multi-boot environment based on UI selections.
        """
        if not BACKEND_AVAILABLE:
            return None
            
        # Map strings to enums
        scheme_enum = PartitionScheme.GPT if "GPT" in partition_scheme else PartitionScheme.MBR
        
        fs_map = {
            "fat32": FileSystem.FAT32,
            "ntfs": FileSystem.NTFS,
            "exfat": FileSystem.EXFAT
        }
        fs_enum = fs_map.get(file_system.lower(), FileSystem.FAT32)
        
        # In a real multiboot scenario, we usually need two partitions:
        # 1. A small FAT32 partition for EFI/GRUB Bootloader
        # 2. A large partition for all the ISO payloads
        efi_part = PartitionInfo(
            name="EFI",
            label="BOOT",
            size_mb=512,  # 512MB for GRUB & OCLP
            filesystem=FileSystem.FAT32,
            bootable=True
        )
        
        payload_part = PartitionInfo(
            name="Payloads",
            label="ARCPAYLOADS",
            size_mb=-1,  # Use remaining space
            filesystem=fs_enum,
            bootable=False
        )
        
        # Determine target hardware profiles based on injection toggles
        hardware_profiles = ["generic_pc"]
        if inject_oclp or inject_bootcamp:
            hardware_profiles.append("generic_mac")
            
        recipe = DeploymentRecipe(
            id=f"multiboot_{len(payloads)}_payloads",
            name=name,
            description="Arcwyre Universal Multi-Boot USB",
            version="1.0.0",
            deployment_type=DeploymentType.MULTIBOOT,
            partition_scheme=scheme_enum,
            partitions=[efi_part, payload_part],
            hardware_profiles=hardware_profiles,
            required_space_mb=sum(os.path.getsize(p) for p in payloads) // (1024 * 1024) + 600,
            post_install_scripts=[]
        )
        return recipe
