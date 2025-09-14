"""
BootForge Installer Builder
Cross-platform installer creation script
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import importlib.util
from typing import Optional, List, Tuple


def find_pyinstaller() -> Optional[str]:
    """Find PyInstaller executable with robust path detection"""
    
    # Try using Python module approach first (more reliable in restricted environments)
    try:
        import PyInstaller
        print(f"✅ Found PyInstaller module at: {PyInstaller.__file__}")
        return f"{sys.executable} -m PyInstaller"
    except ImportError:
        pass
    
    # Common installation locations to check
    search_paths = [
        # Current PATH
        shutil.which('pyinstaller'),
        
        # Python scripts directory
        str(Path(sys.executable).parent / 'pyinstaller'),
        str(Path(sys.executable).parent / 'pyinstaller.exe'),
        
        # User site packages (common on Linux/macOS)
        str(Path.home() / '.local' / 'bin' / 'pyinstaller'),
        
        # macOS user Python installations
        str(Path.home() / 'Library' / 'Python' / f'{sys.version_info.major}.{sys.version_info.minor}' / 'bin' / 'pyinstaller'),
        
        # Homebrew Python on macOS
        '/opt/homebrew/bin/pyinstaller',
        '/usr/local/bin/pyinstaller',
        
        # Windows AppData
        str(Path.home() / 'AppData' / 'Roaming' / 'Python' / f'Python{sys.version_info.major}{sys.version_info.minor}' / 'Scripts' / 'pyinstaller.exe'),
        str(Path.home() / 'AppData' / 'Local' / 'Programs' / 'Python' / f'Python{sys.version_info.major}{sys.version_info.minor}' / 'Scripts' / 'pyinstaller.exe'),
        
        # Current workspace (Replit-specific)
        str(Path.cwd() / '.pythonlibs' / 'bin' / 'pyinstaller'),
        '/home/runner/workspace/.pythonlibs/bin/pyinstaller',
    ]
    
    # Check each location
    for path in search_paths:
        if path and Path(path).exists() and os.access(path, os.X_OK):
            print(f"✅ Found PyInstaller binary at: {path}")
            return path
    
    return None


def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if all required dependencies are available"""
    missing_deps = []
    
    # Check PyInstaller
    if not find_pyinstaller():
        missing_deps.append('pyinstaller')
    
    # Check optional GUI dependencies
    try:
        import PyQt6
    except ImportError:
        print("⚠️  PyQt6 not available - GUI features will be limited")
    
    return len(missing_deps) == 0, missing_deps


def get_platform_spec_file() -> Optional[str]:
    """Get the appropriate .spec file for the current platform"""
    system = platform.system()
    
    spec_files = {
        'Linux': 'BootForge-Linux-x64.spec',
        'Darwin': 'BootForge-macOS.spec',
        'Windows': 'BootForge-Windows.spec'
    }
    
    spec_file = spec_files.get(system)
    if spec_file and Path(spec_file).exists():
        return spec_file
    
    return None


def create_standalone_script() -> bool:
    """Create a standalone script as fallback when PyInstaller doesn't work"""
    print("🔄 Creating standalone script (PyInstaller fallback)...")
    
    try:
        # Create dist directory
        Path('dist').mkdir(exist_ok=True)
        
        # Create a portable script that bundles everything
        standalone_content = '''#!/usr/bin/env python3
"""
BootForge Standalone Script
Generated portable version of BootForge
"""

import sys
import os
from pathlib import Path

# Add src directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / "src"))

def main():
    """Main entry point"""
    # Import after path setup
    try:
        from main import main as bootforge_main
        bootforge_main()
    except Exception as e:
        print(f"Error running BootForge: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        # Write standalone script
        standalone_file = Path('dist/bootforge-standalone.py')
        standalone_file.write_text(standalone_content)
        standalone_file.chmod(0o755)
        
        # Copy source files to dist
        src_dist = Path('dist/src')
        if src_dist.exists():
            shutil.rmtree(src_dist)
        shutil.copytree('src', src_dist)
        
        # Copy main.py
        shutil.copy2('main.py', 'dist/main.py')
        
        # Copy requirements
        if Path('requirements.txt').exists():
            shutil.copy2('requirements.txt', 'dist/requirements.txt')
        
        print("✅ Standalone script created successfully")
        print("📝 Usage: python3 dist/bootforge-standalone.py")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create standalone script: {e}")
        return False


def build_executable() -> bool:
    """Build standalone executable with PyInstaller"""
    print("🔨 Building BootForge executable...")
    
    # Find PyInstaller
    pyinstaller_cmd = find_pyinstaller()
    if not pyinstaller_cmd:
        print("❌ PyInstaller not found!")
        print("\n📦 Installation options:")
        print("   • pip install pyinstaller")
        print("   • pip3 install --user pyinstaller")
        print("   • python -m pip install pyinstaller")
        return False
    
    # Check if we should use existing spec file
    spec_file = get_platform_spec_file()
    
    if spec_file:
        print(f"📋 Using existing spec file: {spec_file}")
        if 'python' in pyinstaller_cmd.lower():
            cmd = pyinstaller_cmd.split() + [spec_file]
        else:
            cmd = [pyinstaller_cmd, spec_file]
    else:
        print("📋 Creating new build configuration")
        
        # Build command dynamically
        if 'python' in pyinstaller_cmd.lower():
            cmd = pyinstaller_cmd.split()
        else:
            cmd = [pyinstaller_cmd]
        
        cmd.extend([
            '--onefile',
            '--name=BootForge',
            '--add-data=src:src',
            '--hidden-import=src.core',
            '--hidden-import=src.plugins',
            '--hidden-import=src.cli',
            '--console',  # Console application
            'main.py'
        ])
        
        # Add GUI support if available
        try:
            import PyQt6
            cmd.extend([
                '--hidden-import=PyQt6.QtWidgets',
                '--hidden-import=PyQt6.QtCore', 
                '--hidden-import=PyQt6.QtGui',
                '--hidden-import=src.gui'
            ])
            print("🖥️  Including GUI support (PyQt6 detected)")
        except ImportError:
            print("📟 Building CLI-only version (PyQt6 not available)")
    
    print(f"🚀 Running: {' '.join(cmd)}")
    
    try:
        # Create dist directory
        Path('dist').mkdir(exist_ok=True)
        
        # Run PyInstaller with environment restrictions check
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            cwd=Path.cwd(),
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print("✅ Executable built successfully")
            
            # Show build artifacts
            dist_dir = Path('dist')
            if dist_dir.exists():
                artifacts = list(dist_dir.glob('*'))
                if artifacts:
                    print("\n📦 Build artifacts:")
                    for artifact in artifacts:
                        size = artifact.stat().st_size if artifact.is_file() else 0
                        size_mb = size / (1024 * 1024) if size > 0 else 0
                        print(f"   • {artifact.name} ({size_mb:.1f}MB)")
            
            return True
        else:
            print("❌ PyInstaller build failed!")
            
            # Check for specific environment issues
            error_output = result.stderr.lower() if result.stderr else ""
            if "ptrace" in error_output or "esrch" in error_output:
                print("\n⚠️  Environment Limitation Detected:")
                print("   This appears to be a restricted environment that doesn't support")
                print("   PyInstaller's process monitoring features (ptrace restrictions).")
                print("\n🔄 Switching to fallback method...")
                return create_standalone_script()
            else:
                print(f"\n🔍 Error details:")
                print(f"Exit code: {result.returncode}")
                if result.stdout:
                    print(f"STDOUT: {result.stdout}")
                if result.stderr:
                    print(f"STDERR: {result.stderr}")
                
                print("\n🔄 Trying fallback method...")
                return create_standalone_script()
            
    except subprocess.TimeoutExpired:
        print("❌ Build timed out (5 minutes)")
        print("🔄 Switching to fallback method...")
        return create_standalone_script()
    except Exception as e:
        print(f"❌ Build failed with exception: {e}")
        print("🔄 Switching to fallback method...")
        return create_standalone_script()


def create_windows_installer():
    """Create Windows installer with Inno Setup"""
    print("Creating Windows installer...")
    
    # Inno Setup script
    iss_content = """
[Setup]
AppName=BootForge
AppVersion=1.0.0
AppPublisher=BootForge Team
AppPublisherURL=https://bootforge.dev
DefaultDirName={pf}\\BootForge
DefaultGroupName=BootForge
UninstallDisplayIcon={app}\\BootForge.exe
Compression=lzma2
SolidCompression=yes
OutputDir=dist\\windows
OutputBaseFilename=BootForge-Setup

[Files]
Source: "dist\\BootForge.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "docs\\*"; DestDir: "{app}\\docs"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\\BootForge"; Filename: "{app}\\BootForge.exe"
Name: "{group}\\Uninstall BootForge"; Filename: "{uninstallexe}"
Name: "{commondesktop}\\BootForge"; Filename: "{app}\\BootForge.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\\BootForge.exe"; Description: "Launch BootForge"; Flags: nowait postinstall skipifsilent
"""
    
    # Write Inno Setup script
    iss_file = Path("BootForge.iss")
    iss_file.write_text(iss_content)
    
    # Run Inno Setup compiler
    try:
        result = subprocess.run(['iscc', 'BootForge.iss'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Windows installer created")
            return True
        else:
            print(f"❌ Installer creation failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Inno Setup not found - install from https://jrsoftware.org/isinfo.php")
        return False


def create_macos_installer():
    """Create macOS installer"""
    print("Creating macOS installer...")
    
    app_name = "BootForge.app"
    app_dir = Path("dist/macos") / app_name
    
    # Create app bundle structure
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "Contents").mkdir(exist_ok=True)
    (app_dir / "Contents/MacOS").mkdir(exist_ok=True)
    (app_dir / "Contents/Resources").mkdir(exist_ok=True)
    
    # Copy executable
    shutil.copy2("dist/BootForge", app_dir / "Contents/MacOS/BootForge")
    
    # Create Info.plist
    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>BootForge</string>
    <key>CFBundleIdentifier</key>
    <string>dev.bootforge.BootForge</string>
    <key>CFBundleName</key>
    <string>BootForge</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
</dict>
</plist>"""
    
    (app_dir / "Contents/Info.plist").write_text(plist_content)
    
    # Create DMG
    try:
        result = subprocess.run([
            'hdiutil', 'create', '-volname', 'BootForge',
            '-srcfolder', str(app_dir.parent),
            '-ov', '-format', 'UDZO',
            'dist/BootForge-1.0.0.dmg'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ macOS DMG created")
            return True
        else:
            print(f"❌ DMG creation failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ hdiutil not found - macOS required for DMG creation")
        return False


def create_linux_package():
    """Create Linux package (AppImage)"""
    print("Creating Linux package...")
    
    # Find the executable in dist directory
    dist_dir = Path("dist")
    executable_candidates = [
        "BootForge",
        "BootForge-Linux-x64", 
        "bootforge",
        "bootforge-linux-x64"
    ]
    
    executable_path = None
    for candidate in executable_candidates:
        candidate_path = dist_dir / candidate
        if candidate_path.exists() and candidate_path.is_file():
            executable_path = candidate_path
            break
    
    if not executable_path:
        print("❌ Could not find executable in dist directory")
        print("Available files:")
        for item in dist_dir.iterdir():
            if item.is_file():
                print(f"   • {item.name}")
        return False
    
    print(f"✅ Found executable: {executable_path}")
    
    # Create AppDir structure
    appdir = Path("dist/linux/BootForge.AppDir")
    appdir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    shutil.copy2(executable_path, appdir / "BootForge")
    
    # Create desktop file
    desktop_content = """[Desktop Entry]
Type=Application
Name=BootForge
Comment=Professional OS Deployment Tool
Exec=BootForge
Icon=bootforge
Categories=System;
"""
    
    (appdir / "BootForge.desktop").write_text(desktop_content)
    
    # Create AppRun script
    apprun_content = """#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/BootForge" "$@"
"""
    
    apprun_file = appdir / "AppRun"
    apprun_file.write_text(apprun_content)
    apprun_file.chmod(0o755)
    
    # Try to create AppImage
    try:
        result = subprocess.run([
            'appimagetool', str(appdir), 'dist/BootForge-1.0.0-x86_64.AppImage'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Linux AppImage created")
            return True
        else:
            print(f"❌ AppImage creation failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ appimagetool not found - install AppImageKit")
        return False


def main() -> bool:
    """Main installer build function"""
    print("🚀 BootForge Installer Builder")
    print("═" * 50)
    
    # Check system info
    system = platform.system()
    arch = platform.machine()
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    print(f"🖥️  Platform: {system} {arch}")
    print(f"🐍 Python: {python_version}")
    print(f"📁 Working directory: {Path.cwd()}")
    print()
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    deps_ok, missing_deps = check_dependencies()
    
    if not deps_ok:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print("\n📦 Please install missing dependencies and try again.")
        return False
    
    print("✅ All dependencies available")
    print()
    
    # Create dist directory
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    
    # Build executable
    success = build_executable()
    
    if not success:
        print("\n❌ Failed to build executable")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Check that all dependencies are properly installed")
        print("   2. Ensure you have enough disk space")
        print("   3. Check file permissions in the project directory")
        print("   4. Try running with verbose output: python -c 'import PyInstaller; print(PyInstaller.__file__)'")
        return False
    
    # Create platform-specific installers
    print("\n📦 Creating platform-specific installer...")
    
    installer_created = False
    if system == "Windows":
        installer_created = create_windows_installer()
    elif system == "Darwin":
        installer_created = create_macos_installer()
    elif system == "Linux":
        installer_created = create_linux_package()
    else:
        print(f"⚠️  Platform {system} not directly supported for packaging")
        print("   Executable is available in dist/ directory")
        installer_created = True  # Executable exists
    
    print("\n" + "═" * 50)
    if success and installer_created:
        print("✅ Build completed successfully!")
        print(f"📁 Installers available in: {dist_dir.absolute()}")
        
        # List all build artifacts
        artifacts = list(dist_dir.rglob('*'))
        if artifacts:
            print("\n📦 Available artifacts:")
            for artifact in sorted(artifacts):
                if artifact.is_file():
                    size = artifact.stat().st_size
                    size_mb = size / (1024 * 1024)
                    rel_path = artifact.relative_to(dist_dir)
                    print(f"   • {rel_path} ({size_mb:.1f}MB)")
        
        print("\n🎉 Ready for distribution!")
        return True
    else:
        print("❌ Build completed with errors")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        print("\n🔍 Full traceback:")
        traceback.print_exc()
        sys.exit(1)