GRUB Bootloader Configuration Manager
Handles GRUB installation and configuration for multi-boot systems
"""

import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from .models import DeploymentRecipe, PartitionInfo, FileSystem


class GRUBBootMode(Enum):
    """GRUB boot modes"""
    UEFI = "uefi"
    LEGACY_BIOS = "bios"
    HYBRID = "hybrid"


@dataclass
class OSEntry:
    """Operating system entry for GRUB menu"""
    name: str
    os_type: str  # "windows", "macos", "linux", "custom"
    partition_uuid: str
    kernel_path: Optional[str] = None
    initrd_path: Optional[str] = None
    boot_params: List[str] = field(default_factory=list)
    chainload_path: Optional[str] = None
    icon_path: Optional[str] = None
    description: str = ""
    
    def to_grub_entry(self) -> str:
        """Generate GRUB menu entry"""
        entry_lines = [
            f'menuentry "{self.name}" {{',
        ]
        
        if self.description:
            entry_lines.append(f'    # {self.description}')
        
        # Set partition
        entry_lines.append(f'    set root=(hd0,gpt{self._get_partition_number()})')
        
        if self.os_type == "windows":
            # Windows chainload entry (correct path for installer media)
            entry_lines.extend([
                f'    insmod part_gpt',
                f'    insmod fat',
                f'    insmod ntfs',
                f'    insmod chain',
                f'    search --fs-uuid --set=root {self.partition_uuid}',
                f'    chainloader /EFI/BOOT/BOOTX64.EFI'
            ])
        elif self.os_type == "macos":
            # macOS chainload entry with APFS support
            entry_lines.extend([
                f'    insmod part_gpt',
                f'    insmod hfsplus',
                f'    insmod apfs',
                f'    insmod chain',
                f'    search --fs-uuid --set=root {self.partition_uuid}',
                f'    chainloader /System/Library/CoreServices/boot.efi'
            ])
        elif self.os_type == "linux":
            # Linux chainload to installer EFI (more reliable than direct boot)
            entry_lines.extend([
                f'    insmod part_gpt',
                f'    insmod ext2',
                f'    insmod fat',
                f'    search --fs-uuid --set=root {self.partition_uuid}',
                f'    chainloader /EFI/BOOT/BOOTX64.EFI'
            ])
        else:
            # Custom chainload
            if self.chainload_path: