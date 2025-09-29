#!/usr/bin/env python3
"""
BootForge Build System - PyInstaller Configuration
Creates portable executables for Windows, macOS, and Linux
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

class BootForgeBuildSystem:
    """Build system for creating portable BootForge executables"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.build_dir = self.root_dir / "dist"
        self.spec_dir = self.root_dir / "build_system" / "specs"
        
        # Ensure directories exist
        self.build_dir.mkdir(exist_ok=True)
        self.spec_dir.mkdir(exist_ok=True)
        
    def create_windows_spec(self):
        """Create PyInstaller spec for Windows executable"""
        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include (only existing directories)
added_files = []
data_dirs = [
    ('src/core/data', 'src/core/data'),
    ('src/gui/icons', 'src/gui/icons'), 
    ('src/core/patches', 'src/core/patches'),
    ('config', 'config'),
]

for src_path, dest_path in data_dirs:
    full_path = self.root_dir / src_path
    if full_path.exists():
        added_files.append((str(full_path), dest_path))

# Hidden imports (modules not automatically detected)
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtWidgets', 
    'PyQt6.QtGui',
    'requests',
    'psutil',
    'cryptography',
    'yaml',
    'click',
    'colorama',
    'src.core.hardware_detector',
    'src.core.os_image_manager.macos_provider',
    'src.core.os_image_manager.windows_provider',
    'src.core.os_image_manager.linux_provider',
    'src.gui.modern_theme',
    'src.gui.stepper_wizard_widget',
]

a = Analysis(
    ['{self.root_dir}/main.py'],
    pathex=['{self.root_dir}'],
    binaries=[],
    datas=added_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BootForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{self.root_dir}/src/gui/icons/bootforge.ico'
)
'''
        spec_path = self.spec_dir / "bootforge_windows.spec"
        with open(spec_path, 'w') as f:
            f.write(spec_content)
        return spec_path

    def create_macos_spec(self):
        """Create PyInstaller spec for macOS application bundle"""
        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include (only existing directories)
added_files = []
data_dirs = [
    ('src/core/data', 'src/core/data'),
    ('src/gui/icons', 'src/gui/icons'), 
    ('src/core/patches', 'src/core/patches'),
    ('config', 'config'),
]

for src_path, dest_path in data_dirs:
    full_path = self.root_dir / src_path
    if full_path.exists():
        added_files.append((str(full_path), dest_path))

# Hidden imports
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtWidgets', 
    'PyQt6.QtGui',
    'requests',
    'psutil',
    'cryptography',
    'yaml',
    'click',
    'colorama',
    'src.core.hardware_detector',
    'src.core.os_image_manager.macos_provider',
    'src.core.os_image_manager.windows_provider',
    'src.core.os_image_manager.linux_provider',
    'src.gui.modern_theme',
    'src.gui.stepper_wizard_widget',
]

a = Analysis(
    ['{self.root_dir}/main.py'],
    pathex=['{self.root_dir}'],
    binaries=[],
    datas=added_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BootForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='BootForge.app',
    icon='{self.root_dir}/src/gui/icons/bootforge.icns',
    bundle_identifier='com.bootforge.app',
    info_plist={{
        'CFBundleName': 'BootForge',
        'CFBundleDisplayName': 'BootForge',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSMinimumSystemVersion': '10.13.0',
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False'
    }},
)
'''
        spec_path = self.spec_dir / "bootforge_macos.spec"
        with open(spec_path, 'w') as f:
            f.write(spec_content)
        return spec_path

    def create_linux_spec(self):
        """Create PyInstaller spec for Linux executable"""
        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include (only existing directories)
added_files = []
data_dirs = [
    ('src/core/data', 'src/core/data'),
    ('src/gui/icons', 'src/gui/icons'), 
    ('src/core/patches', 'src/core/patches'),
    ('config', 'config'),
]

for src_path, dest_path in data_dirs:
    full_path = self.root_dir / src_path
    if full_path.exists():
        added_files.append((str(full_path), dest_path))

# Hidden imports
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtWidgets', 
    'PyQt6.QtGui',
    'requests',
    'psutil',
    'cryptography',
    'yaml',
    'click',
    'colorama',
    'src.core.hardware_detector',
    'src.core.os_image_manager.macos_provider',
    'src.core.os_image_manager.windows_provider',
    'src.core.os_image_manager.linux_provider',
    'src.gui.modern_theme',
    'src.gui.stepper_wizard_widget',
]

a = Analysis(
    ['{self.root_dir}/main.py'],
    pathex=['{self.root_dir}'],
    binaries=[],
    datas=added_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BootForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
        spec_path = self.spec_dir / "bootforge_linux.spec"
        with open(spec_path, 'w') as f:
            f.write(spec_content)
        return spec_path

    def build_platform(self, platform):
        """Build executable for specified platform"""
        print(f"Building BootForge for {platform}...")
        
        if platform == "windows":
            spec_path = self.create_windows_spec()
            output_name = "BootForge.exe"
        elif platform == "macos":
            spec_path = self.create_macos_spec()
            output_name = "BootForge.app"
        elif platform == "linux":
            spec_path = self.create_linux_spec()
            output_name = "BootForge"
        else:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Run PyInstaller
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(spec_path)]
        result = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Build failed for {platform}:")
            print(result.stderr)
            return False
            
        print(f"Successfully built {platform} executable: {output_name}")
        return True

if __name__ == "__main__":
    builder = BootForgeBuildSystem()
    
    # Detect current platform and build
    if sys.platform.startswith("win"):
        builder.build_platform("windows")
    elif sys.platform.startswith("darwin"):
        builder.build_platform("macos")
    else:
        builder.build_platform("linux")