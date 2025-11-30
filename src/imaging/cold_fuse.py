"""Cold-Fuse clone engine with adaptive retries."""
from __future__ import annotations
import hashlib
import logging
import os
from typing import List, Tuple

log = logging.getLogger("bootforge")

DEFAULT_CHUNK = 1024 * 1024
MAX_RETRIES = 3
MIN_CHUNK = 4096


def _read(src: str, offset: int, size: int) -> bytes:
    with open(src, "rb", buffering=0) as f:
        f.seek(offset)
        return f.read(size)


def _write(dst: str, offset: int, data: bytes) -> None:
    mode = "r+b" if os.path.exists(dst) else "wb"
    with open(dst, mode, buffering=0) as f:
        f.seek(offset)
        f.write(data)


def cold_fuse_clone(src_path: str, dst_path: str, dry_run: bool = False, chunk_size: int = DEFAULT_CHUNK):
    total = os.path.getsize(src_path)
    bad_map: List[Tuple[int, int]] = []
    offset = 0

    while offset < total:
        size = min(chunk_size, total - offset)
        try:
            if not dry_run:
                data = _read(src_path, offset, size)
                _ = hashlib.sha256(data).hexdigest()
                _write(dst_path, offset, data)
            log.info("cloned %d/%d", offset + size, total)
            offset += size
        except Exception as exc:
            log.warning("bad read at %d len=%d: %s", offset, size, exc)
            retried = False
            cs = size
            for _ in range(MAX_RETRIES):
                cs = max(cs // 2, MIN_CHUNK)
                try:
                    if not dry_run:
                        data = _read(src_path, offset, cs)
                        _write(dst_path, offset, data)
                    offset += cs
                    retried = True
                    break
                except Exception:
                    continue
            if not retried:
                bad_map.append((offset, size))
                offset += size
    return {"size": total, "bad_regions": bad_map}
