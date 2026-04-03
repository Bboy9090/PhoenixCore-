"""
BootForge OCLP Launcher
Launches the embedded OpenCore Legacy Patcher when on macOS.
OCLP is vendored at third_party/OpenCore-Legacy-Patcher.
"""

import logging
import os
import platform
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to vendored OCLP (relative to workspace root)
OCLP_SUBMODULE_PATH = Path(__file__).resolve().parent.parent / "third_party" / "OpenCore-Legacy-Patcher"


def is_oclp_available() -> bool:
    """Check if OCLP is present and runnable."""
    oclp_init = OCLP_SUBMODULE_PATH / "opencore_legacy_patcher" / "__init__.py"
    return oclp_init.exists()


def is_macos() -> bool:
    """Check if running on macOS (OCLP is macOS-only)."""
    return platform.system() == "Darwin"


def launch_oclp() -> bool:
    """
    Launch OpenCore Legacy Patcher in a subprocess.
    Returns True if launched successfully, False otherwise.
    """
    if not is_macos():
        logger.warning("OCLP requires macOS to run")
        return False

    if not is_oclp_available():
        logger.warning("OCLP not found. Run: git submodule update --init third_party/OpenCore-Legacy-Patcher")
        return False

    oclp_root = OCLP_SUBMODULE_PATH.resolve()
    if not oclp_root.exists():
        logger.error(f"OCLP path does not exist: {oclp_root}")
        return False

    try:
        cmd = [sys.executable, "-m", "opencore_legacy_patcher"]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(oclp_root) + (os.pathsep + env.get("PYTHONPATH", ""))
        subprocess.Popen(
            cmd,
            cwd=str(oclp_root),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        logger.info("OCLP launched successfully")
        return True
    except FileNotFoundError as e:
        logger.error(f"Failed to launch OCLP: {e}")
        return False
    except Exception as e:
        logger.exception(f"Failed to launch OCLP: {e}")
        return False
