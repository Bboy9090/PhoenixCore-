"""Extract the recovery `.bin` from a Chrome OS recovery `.zip` (local, no network)."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import List

from src.core.chromeos_recovery.index import ChromeosRecoveryError


def list_bin_members(zf: zipfile.ZipFile) -> List[zipfile.ZipInfo]:
    """Return non-directory zip members ending in `.bin` (any path)."""
    out: List[zipfile.ZipInfo] = []
    for info in zf.infolist():
        if info.is_dir():
            continue
        name = info.filename
        if name.lower().endswith(".bin"):
            out.append(info)
    return out


def extract_chromeos_recovery_bin(zip_path: Path, dest_dir: Path, *, safe_stem: str = "recovery") -> Path:
    """
    Extract the single recovery `.bin` from a Chrome OS recovery ZIP.

    Raises ChromeosRecoveryError if there is not exactly one `.bin` member.
    Writes to ``dest_dir / f"{safe_stem}_recovery.bin"`` (overwrites if present).
    """
    zip_path = Path(zip_path).expanduser().resolve()
    dest_dir = Path(dest_dir).expanduser().resolve()
    if not zip_path.is_file():
        raise ChromeosRecoveryError(f"Recovery ZIP not found: {zip_path}")

    dest_dir.mkdir(parents=True, exist_ok=True)
    stem = "".join(c if c.isalnum() or c in "-_" else "_" for c in safe_stem)[:120] or "recovery"
    out_path = dest_dir / f"{stem}_recovery.bin"

    with zipfile.ZipFile(zip_path, "r") as zf:
        members = list_bin_members(zf)
        if not members:
            raise ChromeosRecoveryError(f"No .bin file found inside {zip_path.name}")
        if len(members) > 1:
            names = ", ".join(m.filename for m in members[:5])
            raise ChromeosRecoveryError(
                f"Multiple .bin files in ZIP ({len(members)}); unpack manually. First entries: {names}"
            )
        member = members[0]
        with zf.open(member, "r") as src, open(out_path, "wb") as dst:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)

    return out_path
