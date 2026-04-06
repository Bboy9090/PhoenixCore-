"""
Chrome OS recovery: fetch metadata index, resolve board, download from Google CDN.

Data source: https://github.com/MercuryWorkshop/chromeos-releases-data (CC-BY).
Image files: https://dl.google.com/dl/edgedl/chromeos/recovery/ (Google).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

DEFAULT_INDEX_URL = os.environ.get(
    "CHROMEOS_RECOVERY_INDEX_URL",
    "https://cdn.jsdelivr.net/gh/MercuryWorkshop/chromeos-releases-data@main/data.json",
)


class ChromeosRecoveryError(RuntimeError):
    """Failed to resolve or download a Chrome OS recovery image."""


def fetch_index(url: str = DEFAULT_INDEX_URL, timeout: int = 120) -> Dict[str, Any]:
    """Download and parse the chromeos-releases-data JSON object."""
    req = urllib.request.Request(url, headers={"User-Agent": "PhoenixCore-BootForge/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.URLError as e:
        raise ChromeosRecoveryError(f"Failed to fetch recovery index: {e}") from e
    try:
        data = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise ChromeosRecoveryError("Recovery index is not valid JSON") from e
    if not isinstance(data, dict):
        raise ChromeosRecoveryError("Recovery index root must be an object")
    return data


def _is_real_image_entry(entry: Dict[str, Any]) -> bool:
    if not entry.get("url"):
        return False
    u = str(entry["url"])
    if "github.com/MercuryWorkshop/chromeos-releases-data" in u:
        return False
    if "dl.google.com" not in u and "edgedl/chromeos/recovery" not in u:
        return False
    pv = str(entry.get("platform_version", ""))
    if pv in ("", "0.0.0"):
        return False
    ch = str(entry.get("channel", ""))
    if "stable" not in ch.lower():
        return False
    return True


def _platform_version_sort_key(pv: str) -> tuple:
    """Parse e.g. 13982.70.16 into a tuple for correct numeric ordering (not lexical string order)."""
    parts = str(pv).split(".")
    out: List[int] = []
    for p in parts:
        if p.isdigit():
            out.append(int(p))
        else:
            # Non-numeric segment: sort after pure numeric
            return (0,)
    return tuple(out)


def pick_latest_stable_image(images: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Choose the newest stable-channel image by platform_version (numeric component order)."""
    candidates = [img for img in images if isinstance(img, dict) and _is_real_image_entry(img)]
    if not candidates:
        return None
    candidates.sort(
        key=lambda x: _platform_version_sort_key(str(x.get("platform_version", ""))),
        reverse=True,
    )
    return candidates[0]


def resolve_board(index: Dict[str, Any], board: str) -> Optional[Dict[str, Any]]:
    """Return board payload (images, brand_names, hwid_matches) or None."""
    key = board.strip().lower()
    for k, v in index.items():
        if k.lower() == key and isinstance(v, dict):
            return v
    return None


def list_board_names(index: Dict[str, Any]) -> List[str]:
    return sorted(k for k in index if k and not k.startswith("_"))


def download_recovery_zip(
    url: str,
    dest_path: Path,
    *,
    progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
    chunk_size: int = 1024 * 1024,
    timeout: int = 600,
) -> Path:
    """
    Stream-download a recovery ZIP to dest_path (atomic rename on success).
    """
    dest_path = Path(dest_path).expanduser().resolve()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest_path.with_suffix(dest_path.suffix + ".part")

    host = urlparse(url).netloc or "unknown"
    req = urllib.request.Request(url, headers={"User-Agent": f"PhoenixCore-BootForge/1.0 ({host})"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            total = resp.length if hasattr(resp, "length") and resp.length else None
            received = 0
            with open(tmp, "wb") as out:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    out.write(chunk)
                    received += len(chunk)
                    if progress_callback:
                        progress_callback(received, total)
    except urllib.error.HTTPError as e:
        raise ChromeosRecoveryError(f"HTTP {e.code} downloading recovery image") from e
    except urllib.error.URLError as e:
        raise ChromeosRecoveryError(f"Download failed: {e}") from e

    tmp.replace(dest_path)
    return dest_path


@dataclass(frozen=True)
class RecoverySelection:
    board: str
    platform_version: str
    chrome_version: str
    channel: str
    url: str
    brand_names: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "board": self.board,
            "platform_version": self.platform_version,
            "chrome_version": self.chrome_version,
            "channel": self.channel,
            "url": self.url,
            "brand_names": list(self.brand_names),
        }


def select_recovery_for_board(index: Dict[str, Any], board: str) -> RecoverySelection:
    payload = resolve_board(index, board)
    if not payload:
        raise ChromeosRecoveryError(f"Unknown board: {board!r}. Use --list-boards or check spelling.")

    images = payload.get("images") or []
    if not isinstance(images, list):
        raise ChromeosRecoveryError(f"Invalid images list for board {board!r}")

    picked = pick_latest_stable_image([i for i in images if isinstance(i, dict)])
    if not picked:
        raise ChromeosRecoveryError(f"No stable recovery image found for board {board!r}")

    brands = payload.get("brand_names") or []
    if not isinstance(brands, list):
        brands = []

    return RecoverySelection(
        board=board.strip(),
        platform_version=str(picked.get("platform_version", "")),
        chrome_version=str(picked.get("chrome_version", "")),
        channel=str(picked.get("channel", "")),
        url=str(picked["url"]),
        brand_names=[str(b) for b in brands],
    )
