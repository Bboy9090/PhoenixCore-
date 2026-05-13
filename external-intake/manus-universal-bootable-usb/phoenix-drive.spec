# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Bobby's PhoenixDrive Desktop App
Builds standalone executables for Windows, macOS, and Linux
"""

import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Collect data files
datas = [
    ('src/ui/resources', 'resources'),
    ('src/ui/icons', 'icons'),
]

# Collect hidden imports
hiddenimports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'requests',
    'websocket',
    'cv2',
    'pyzbar',
    'psutil',
    'jsonschema',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
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
    name='PhoenixDrive',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/ui/icons/app.ico' if sys.platform == 'win32' else None,
)

# For macOS
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='PhoenixDrive.app',
        icon='src/ui/icons/app.icns',
        bundle_identifier='com.phoenixdrive.app',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
        },
    )
