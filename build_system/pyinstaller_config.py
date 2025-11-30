#!/usr/bin/env python3
"""
BootForge Build System – PyInstaller configuration
- Generates platform-specific .spec files from templates
- Includes folders via Tree(...)
- Conditional UPX, icon guards, persistent logs
- Optional Qt plugin bundling (set BOOTFORGE_ADD_QT_PLUGINS=1)
- Windows EXE version metadata (Properties -> Version tab)
"""
from __future__ import annotations

import os
import sys
import shutil
import subprocess
from pathlib import Path
from string import Template
from textwrap import dedent


class BootForgeBuildSystem:
    """Create Windows/macOS/Linux artifacts via PyInstaller with safe defaults."""

    def __init__(self) -> None:
        self.root_dir = Path(__file__).parent.parent.resolve()
        self.build_dir = self.root_dir / "dist"
        self.spec_dir = self.root_dir / "build_system" / "specs"
        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.spec_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # Spec generators
    # -----------------------------

    def _qt_plugins_snippet(self) -> str:
        """Optional: bundle Qt plugin trees when env flag set (avoids runtime plugin errors)."""
        # WHY: Some environments still miss Qt plugins despite hooks; opt-in to keep size lean by default.
        return dedent(
            """
            include_qt_plugins = os.environ.get('BOOTFORGE_ADD_QT_PLUGINS','0') == '1'
            if include_qt_plugins:
                try:
                    import sys as _sys
                    # Try to infer plugin root from PyQt6 install
                    try:
                        import PyQt6 as _pyqt6
                        _qbase = Path(_pyqt6.__file__).resolve().parent
                        _cands = [
                            _qbase / 'Qt6' / 'plugins',
                            _qbase / 'Qt' / 'plugins',
                        ]
                    except Exception:
                        _cands = []
                    # Fallbacks using base_prefix
                    _cands += [
                        Path(_sys.base_prefix) / 'Lib' / 'site-packages' / 'PyQt6' / 'Qt6' / 'plugins',
                        Path(_sys.base_prefix) / 'lib' / f'python{_sys.version_info.major}.{_sys.version_info.minor}' / 'site-packages' / 'PyQt6' / 'Qt6' / 'plugins',
                    ]
                    for _cand in _cands:
                        if _cand.exists():
                            added_files.append(Tree(str(_cand), prefix='qt_plugins'))
                            break
                except Exception:
                    pass
            """
        )

    def _windows_version_file(self) -> Path:
        """Emit a tiny VSVersionInfo file and return its path."""
        vf = dedent(
            r"""
            # UTF-8
            VSVersionInfo(
              ffi=FixedFileInfo(
                filevers=(1, 0, 0, 0),
                prodvers=(1, 0, 0, 0),
                mask=0x3f,
                flags=0x0,
                OS=0x40004,
                fileType=0x1,
                subtype=0x0,
                date=(0, 0)
              ),
              kids=[
                StringFileInfo([
                  StringTable('040904B0', [
                    StringStruct('CompanyName', 'BootForge'),
                    StringStruct('FileDescription', 'BootForge'),
                    StringStruct('FileVersion', '1.0.0'),
                    StringStruct('InternalName', 'BootForge'),
                    StringStruct('OriginalFilename', 'BootForge.exe'),
                    StringStruct('ProductName', 'BootForge'),
                    StringStruct('ProductVersion', '1.0.0')
                  ])
                ]),
                VarFileInfo([VarStruct('Translation', [1033, 1200])])
              ]
            )
            """
        )
        path = self.spec_dir / "bootforge_win_version.py"
        path.write_text(vf, encoding="utf-8")
        return path

    def create_windows_spec(self) -> Path:
        """Create PyInstaller spec for Windows (.exe)."""
        version_file_path = self._windows_version_file()
        spec_tpl = Template(
            dedent(
                """
                # -*- mode: python ; coding: utf-8 -*-
                import os
                from pathlib import Path
                import shutil
                from PyInstaller.building.datastruct import Tree
                # Analysis/PYZ/EXE/BUNDLE are provided by PyInstaller at spec eval time.

                block_cipher = None
                root_dir = Path(r"$root_dir")

                added_files = []
                data_dirs = [
                    ('src/core/data', 'src/core/data'),
                    ('src/gui/icons', 'src/gui/icons'),
                    ('src/core/patches', 'src/core/patches'),
                    ('config', 'config'),
                ]
                for src_path, dest_path in data_dirs:
                    full_path = root_dir / src_path
                    if full_path.exists():
                        added_files.append(Tree(str(full_path), prefix=dest_path))

                $qt_plugins

                hiddenimports = [
                    'PyQt6.QtCore','PyQt6.QtWidgets','PyQt6.QtGui',
                    'requests','psutil','cryptography','yaml','click','colorama',
                    'src.core.hardware_detector',
                    'src.core.os_image_manager.macos_provider',
                    'src.core.os_image_manager.windows_provider',
                    'src.core.os_image_manager.linux_provider',
                    'src.gui.modern_theme','src.gui.stepper_wizard_widget',
                ]

                a = Analysis(
                    [str(root_dir / 'main.py')],
                    pathex=[str(root_dir)],
                    binaries=[],
                    datas=added_files,
                    hiddenimports=hiddenimports,
                    hookspath=[],
                    hooksconfig={},
                    runtime_hooks=[],
                    excludes=['matplotlib','numpy','pandas','scipy'],
                    win_no_prefer_redirects=False,
                    win_private_assemblies=False,
                    cipher=block_cipher,
                    noarchive=False,
                )
                pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

                use_upx = shutil.which('upx') is not None
                win_icon = root_dir / 'src/gui/icons/bootforge.ico'
                icon_arg = str(win_icon) if win_icon.exists() else None

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
                    upx=use_upx,
                    upx_exclude=[],
                    runtime_tmpdir=None,
                    console=False,
                    disable_windowed_traceback=False,
                    argv_emulation=False,
                    target_arch=None,
                    codesign_identity=None,
                    entitlements_file=None,
                    icon=icon_arg,
                    version_file=str(Path(r"$version_file"))
                )
                """
            )
        )
        spec_content = spec_tpl.substitute(
            root_dir=self.root_dir,
            qt_plugins=self._qt_plugins_snippet(),
            version_file=version_file_path,
        )
        spec_path = self.spec_dir / "bootforge_windows.spec"
        spec_path.write_text(spec_content, encoding="utf-8")
        return spec_path

    def create_macos_spec(self) -> Path:
        """Create PyInstaller spec for macOS (.app bundle)."""
        spec_tpl = Template(
            dedent(
                """
                # -*- mode: python ; coding: utf-8 -*-
                import os
                from pathlib import Path
                import shutil
                from PyInstaller.building.datastruct import Tree

                block_cipher = None
                root_dir = Path(r"$root_dir")

                added_files = []
                data_dirs = [
                    ('src/core/data', 'src/core/data'),
                    ('src/gui/icons', 'src/gui/icons'),
                    ('src/core/patches', 'src/core/patches'),
                    ('config', 'config'),
                ]
                for src_path, dest_path in data_dirs:
                    full_path = root_dir / src_path
                    if full_path.exists():
                        added_files.append(Tree(str(full_path), prefix=dest_path))

                $qt_plugins

                hiddenimports = [
                    'PyQt6.QtCore','PyQt6.QtWidgets','PyQt6.QtGui',
                    'requests','psutil','cryptography','yaml','click','colorama',
                    'src.core.hardware_detector',
                    'src.core.os_image_manager.macos_provider',
                    'src.core.os_image_manager.windows_provider',
                    'src.core.os_image_manager.linux_provider',
                    'src.gui.modern_theme','src.gui.stepper_wizard_widget',
                ]

                a = Analysis(
                    [str(root_dir / 'main.py')],
                    pathex=[str(root_dir)],
                    binaries=[],
                    datas=added_files,
                    hiddenimports=hiddenimports,
                    hookspath=[],
                    hooksconfig={},
                    runtime_hooks=[],
                    excludes=['matplotlib','numpy','pandas','scipy'],
                    cipher=block_cipher,
                    noarchive=False,
                )
                pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

                use_upx = shutil.which('upx') is not None
                mac_icon = root_dir / 'src/gui/icons/bootforge.icns'
                icon_arg = str(mac_icon) if mac_icon.exists() else None

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
                    upx=use_upx,
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
                    icon=icon_arg,
                    bundle_identifier='com.bootforge.app',
                    info_plist={
                        'CFBundleName': 'BootForge',
                        'CFBundleDisplayName': 'BootForge',
                        'CFBundleVersion': '1.0.0',
                        'CFBundleShortVersionString': '1.0.0',
                        'LSMinimumSystemVersion': '10.13.0',
                        'NSHighResolutionCapable': 'True',
                        'NSRequiresAquaSystemAppearance': 'False'
                    },
                )
                """
            )
        )
        spec_content = spec_tpl.substitute(
            root_dir=self.root_dir,
            qt_plugins=self._qt_plugins_snippet(),
        )
        spec_path = self.spec_dir / "bootforge_macos.spec"
        spec_path.write_text(spec_content, encoding="utf-8")
        return spec_path

    def create_linux_spec(self) -> Path:
        """Create PyInstaller spec for Linux (ELF)."""
        spec_tpl = Template(
            dedent(
                """
                # -*- mode: python ; coding: utf-8 -*-
                import os
                from pathlib import Path
                import shutil
                from PyInstaller.building.datastruct import Tree

                block_cipher = None
                root_dir = Path(r"$root_dir")

                added_files = []
                data_dirs = [
                    ('src/core/data', 'src/core/data'),
                    ('src/gui/icons', 'src/gui/icons'),
                    ('src/core/patches', 'src/core/patches'),
                    ('config', 'config'),
                ]
                for src_path, dest_path in data_dirs:
                    full_path = root_dir / src_path
                    if full_path.exists():
                        added_files.append(Tree(str(full_path), prefix=dest_path))

                $qt_plugins

                hiddenimports = [
                    'PyQt6.QtCore','PyQt6.QtWidgets','PyQt6.QtGui',
                    'requests','psutil','cryptography','yaml','click','colorama',
                    'src.core.hardware_detector',
                    'src.core.os_image_manager.macos_provider',
                    'src.core.os_image_manager.windows_provider',
                    'src.core.os_image_manager.linux_provider',
                    'src.gui.modern_theme','src.gui.stepper_wizard_widget',
                ]

                a = Analysis(
                    [str(root_dir / 'main.py')],
                    pathex=[str(root_dir)],
                    binaries=[],
                    datas=added_files,
                    hiddenimports=hiddenimports,
                    hookspath=[],
                    hooksconfig={},
                    runtime_hooks=[],
                    excludes=['matplotlib','numpy','pandas','scipy'],
                    cipher=block_cipher,
                    noarchive=False,
                )
                pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

                use_upx = shutil.which('upx') is not None

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
                    upx=use_upx,
                    upx_exclude=[],
                    runtime_tmpdir=None,
                    console=False,
                    disable_windowed_traceback=False,
                    argv_emulation=False,
                    target_arch=None,
                    codesign_identity=None,
                    entitlements_file=None,
                )
                """
            )
        )
        spec_content = spec_tpl.substitute(
            root_dir=self.root_dir,
            qt_plugins=self._qt_plugins_snippet(),
        )
        spec_path = self.spec_dir / "bootforge_linux.spec"
        spec_path.write_text(spec_content, encoding="utf-8")
        return spec_path

    # -----------------------------
    # Build driver
    # -----------------------------

    def build_platform(self, platform: str) -> bool:
        """Run PyInstaller for a given platform and persist logs."""
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

        cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(spec_path)]
        result = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True)

        log_path = self.build_dir / f"pyinstaller_{platform}.log"
        with open(log_path, "w", encoding="utf-8") as lf:
            lf.write(result.stdout or "")
            lf.write("\n--- STDERR ---\n")
            lf.write(result.stderr or "")
        print(f"PyInstaller log -> {log_path}")

        if result.returncode != 0:
            print(f"Build failed for {platform}")
            return False

        produced = self.build_dir / output_name
        if produced.exists():
            print(f"Successfully built {platform}: {produced}")
        else:
            print(f"Build succeeded but artifact not found at {produced}. Check the log.")
        return True


if __name__ == "__main__":
    builder = BootForgeBuildSystem()
    if sys.platform.startswith("win"):
        builder.build_platform("windows")
    elif sys.platform.startswith("darwin"):
        builder.build_platform("macos")
    else:
        builder.build_platform("linux")
