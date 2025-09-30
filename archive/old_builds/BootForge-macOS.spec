
# -*- mode: python ; coding: utf-8 -*-
import os

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('assets', 'assets'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtWidgets',
        'PyQt6.QtCore', 
        'PyQt6.QtGui',
        'src.gui.main_window',
        'src.core.config',
        'src.core.logger',
        'click',
        'colorama',
        'psutil',
        'cryptography'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BootForge-macOS-x64',
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
    icon='assets/icons/app_icon_premium.png',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'CFBundleIdentifier': 'dev.bootforge.BootForge',
        'LSMinimumSystemVersion': '10.15',
        'NSHighResolutionCapable': True,
        'LSApplicationCategoryType': 'public.app-category.utilities',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Disk Image',
                'CFBundleTypeExtensions': ['iso', 'dmg', 'img'],
                'CFBundleTypeRole': 'Editor'
            }
        ]
    },
    bundle_identifier='com.bootforge.app',
    version='1.0.0',
)
