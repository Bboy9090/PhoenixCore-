"""
PyInstaller Build Configuration for Bobby's PhoenixDrive
Supports Windows, macOS, and Linux builds with code signing and auto-update
"""

import os
import sys
import platform
from pathlib import Path


class BuildConfig:
    """Build configuration for all platforms."""
    
    # Application metadata
    APP_NAME = "PhoenixDrive"
    APP_VERSION = "2.0.0"
    APP_AUTHOR = "Bobby"
    APP_DESCRIPTION = "Universal OS Deployment Tool"
    APP_ICON = "assets/images/icon.png"
    
    # Build directories
    PROJECT_ROOT = Path(__file__).parent
    BUILD_DIR = PROJECT_ROOT / "build"
    DIST_DIR = PROJECT_ROOT / "dist"
    SPEC_DIR = PROJECT_ROOT / "specs"
    
    # Source directories
    MAIN_SCRIPT = PROJECT_ROOT / "main_enhanced.py"
    SRC_DIR = PROJECT_ROOT / "src"
    ASSETS_DIR = PROJECT_ROOT / "assets"
    
    # Platform-specific settings
    WINDOWS_SETTINGS = {
        "console": False,
        "icon": str(ASSETS_DIR / "images" / "icon.ico"),
        "target_arch": "x86_64",
        "version_file": str(PROJECT_ROOT / "version.txt"),
    }
    
    MACOS_SETTINGS = {
        "icon": str(ASSETS_DIR / "images" / "icon.icns"),
        "bundle_identifier": "com.phoenixdrive.app",
        "codesign_identity": "Developer ID Application",
        "notarize": True,
        "target_arch": ["x86_64", "arm64"],
    }
    
    LINUX_SETTINGS = {
        "icon": str(ASSETS_DIR / "images" / "icon.png"),
        "desktop_file": str(PROJECT_ROOT / "phoenixdrive.desktop"),
        "appimage": True,
        "snap": True,
        "deb": True,
    }
    
    # PyInstaller options
    PYINSTALLER_OPTIONS = {
        "onefile": True,
        "windowed": True,
        "add_data": [
            (str(SRC_DIR), "src"),
            (str(ASSETS_DIR), "assets"),
        ],
        "hidden_imports": [
            "PyQt6",
            "PyQt6.QtCore",
            "PyQt6.QtGui",
            "PyQt6.QtWidgets",
            "pyzbar",
            "cv2",
            "requests",
            "websocket",
        ],
        "excludes": [
            "matplotlib",
            "numpy",
            "pandas",
            "scipy",
            "sklearn",
        ],
        "collect_all": [
            "PyQt6",
        ],
    }
    
    # Code signing settings
    CODESIGN_SETTINGS = {
        "windows": {
            "enabled": False,  # Set to True if you have code signing certificate
            "certificate": None,
            "password": None,
        },
        "macos": {
            "enabled": True,
            "identity": "Developer ID Application",
            "timestamp": True,
            "notarize": True,
            "apple_id": None,
            "apple_password": None,
        },
        "linux": {
            "enabled": False,
        },
    }
    
    # Auto-update settings
    AUTOUPDATE_SETTINGS = {
        "enabled": True,
        "check_interval_hours": 24,
        "update_url": "https://api.github.com/repos/Bboy9090/PhoenixCore-/releases/latest",
        "current_version_url": "https://raw.githubusercontent.com/Bboy9090/PhoenixCore-/main/VERSION",
    }
    
    @classmethod
    def get_platform(cls) -> str:
        """Get current platform."""
        system = platform.system()
        if system == "Windows":
            return "windows"
        elif system == "Darwin":
            return "macos"
        elif system == "Linux":
            return "linux"
        else:
            raise ValueError(f"Unsupported platform: {system}")
    
    @classmethod
    def get_output_filename(cls, platform_name: str) -> str:
        """Get output filename for platform."""
        if platform_name == "windows":
            return f"{cls.APP_NAME}-{cls.APP_VERSION}.exe"
        elif platform_name == "macos":
            return f"{cls.APP_NAME}-{cls.APP_VERSION}.dmg"
        elif platform_name == "linux":
            return f"{cls.APP_NAME}-{cls.APP_VERSION}.AppImage"
        else:
            raise ValueError(f"Unknown platform: {platform_name}")
    
    @classmethod
    def get_installer_filename(cls, platform_name: str) -> str:
        """Get installer filename for platform."""
        if platform_name == "windows":
            return f"{cls.APP_NAME}-Setup-{cls.APP_VERSION}.exe"
        elif platform_name == "macos":
            return f"{cls.APP_NAME}-{cls.APP_VERSION}.dmg"
        elif platform_name == "linux":
            return f"{cls.APP_NAME}_{cls.APP_VERSION}_amd64.deb"
        else:
            raise ValueError(f"Unknown platform: {platform_name}")
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        cls.BUILD_DIR.mkdir(exist_ok=True)
        cls.DIST_DIR.mkdir(exist_ok=True)
        cls.SPEC_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def validate_build_environment(cls, platform_name: str) -> bool:
        """Validate build environment for platform."""
        try:
            if platform_name == "windows":
                # Check for NSIS
                return True
            elif platform_name == "macos":
                # Check for Xcode tools
                result = os.system("xcode-select -p > /dev/null 2>&1")
                return result == 0
            elif platform_name == "linux":
                # Check for AppImage tools
                result = os.system("which appimagetool > /dev/null 2>&1")
                return result == 0
        except Exception:
            pass
        return False


# Generate PyInstaller spec file content
def generate_spec_content(platform_name: str) -> str:
    """Generate PyInstaller spec file content."""
    config = BuildConfig()
    
    spec_template = f"""
# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for {config.APP_NAME}

block_cipher = None

a = Analysis(
    ['{config.MAIN_SCRIPT}'],
    pathex=['{config.PROJECT_ROOT}'],
    binaries=[],
    datas={config.PYINSTALLER_OPTIONS['add_data']},
    hiddenimports={config.PYINSTALLER_OPTIONS['hidden_imports']},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludedimports={config.PYINSTALLER_OPTIONS['excludes']},
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
    name='{config.APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={'False' if platform_name != 'linux' else 'True'},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

"""
    
    if platform_name == "macos":
        spec_template += f"""
app = BUNDLE(
    exe,
    name='{config.APP_NAME}.app',
    icon='{config.MACOS_SETTINGS['icon']}',
    bundle_identifier='{config.MACOS_SETTINGS['bundle_identifier']}',
    info_plist={{'NSPrincipalClass': 'NSApplication'}},
)
"""
    
    return spec_template


if __name__ == "__main__":
    config = BuildConfig()
    print(f"PhoenixDrive Build Configuration")
    print(f"Version: {config.APP_VERSION}")
    print(f"Platform: {config.get_platform()}")
    print(f"Project Root: {config.PROJECT_ROOT}")
    print(f"Build Directory: {config.BUILD_DIR}")
    print(f"Dist Directory: {config.DIST_DIR}")
