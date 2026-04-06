"""
Chrome OS recovery image resolution and download.

Uses the chromeos-releases-data JSON index (CC-BY) which maps board names to
official Google-hosted recovery ZIP URLs (dl.google.com). See docs/CHROMEOS_RECOVERY.md.
"""

from src.core.chromeos_recovery.extract import extract_chromeos_recovery_bin
from src.core.chromeos_recovery.index import (
    DEFAULT_INDEX_URL,
    ChromeosRecoveryError,
    RecoverySelection,
    download_recovery_zip,
    fetch_index,
    list_board_names,
    pick_latest_stable_image,
    resolve_board,
    select_recovery_for_board,
)

__all__ = [
    "DEFAULT_INDEX_URL",
    "ChromeosRecoveryError",
    "RecoverySelection",
    "download_recovery_zip",
    "extract_chromeos_recovery_bin",
    "fetch_index",
    "list_board_names",
    "pick_latest_stable_image",
    "resolve_board",
    "select_recovery_for_board",
]
