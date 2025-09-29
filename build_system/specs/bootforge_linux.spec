
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include
added_files = [
    ('/home/runner/workspace/src/core/data', 'src/core/data'),
    ('/home/runner/workspace/src/gui/icons', 'src/gui/icons'),
    ('/home/runner/workspace/src/core/patches', 'src/core/patches'),
    ('/home/runner/workspace/config', 'config'),
]

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
    ['/home/runner/workspace/main.py'],
    pathex=['/home/runner/workspace'],
    binaries=[],
    datas=added_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
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
