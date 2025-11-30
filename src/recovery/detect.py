"""Disk and OS probing with pragmatic heuristics."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import json
import os
import re
import string
import sys

from ..core.logger import get_logger
from .validators import run_capture

log = get_logger(__name__)


@dataclass
class Partition:
    device: str
    fs_type: str
    mountpoint: Optional[str] = None
    label: Optional[str] = None
    size_bytes: Optional[int] = None


@dataclass
class DiskOSProbe:
    os_type: str  # "windows" | "macos" | "linux" | "unknown"
    root_part: Optional[Partition]
    efi_part: Optional[Partition]
    details: dict


def _looks_windows_root(mp: Path) -> bool:
    return (mp / "Windows" / "System32" / "config" / "SYSTEM").exists()


def _looks_macos_root(mp: Path) -> bool:
    return (mp / "System" / "Library" / "CoreServices" / "SystemVersion.plist").exists()


def _looks_linux_root(mp: Path) -> bool:
    return (mp / "etc" / "os-release").exists()


def _probe_from_mount(mp: Path) -> str:
    try:
        if _looks_windows_root(mp):
            return "windows"
        if _looks_macos_root(mp):
            return "macos"
        if _looks_linux_root(mp):
            return "linux"
    except Exception:
        return "unknown"
    return "unknown"


def _efi_candidate(part: Partition, mount_path: Optional[Path]) -> bool:
    if part.fs_type.lower() in ("vfat", "fat", "fat32", "msdos", "efi"):
        if part.label and part.label.lower() in ("efi", "esp", "system", "bootforge_efi"):
            return True
        if mount_path and (mount_path / "EFI").exists():
            return True
    return False


def _normalize_label(label: Optional[str]) -> Optional[str]:
    if not label:
        return None
    return re.sub(r"\s+", "_", label.strip())


def probe_disks() -> List[DiskOSProbe]:
    system = sys.platform
    log.info("Probing disks on platform: %s", system)
    probes: List[DiskOSProbe] = []

    if system.startswith("win"):
        letters = ["C"] + [c for c in string.ascii_uppercase if c != "C"]
        efi_part = Partition(device="EFI", fs_type="vfat", mountpoint=None, label="EFI", size_bytes=None)
        for L in letters:
            root = Path(f"{L}:/")
            try:
                if root.exists() and (root / "Windows").exists():
                    if _looks_windows_root(root):
                        part = Partition(device=f"{L}:", fs_type="ntfs", mountpoint=str(root), label=_normalize_label(L), size_bytes=None)
                        probes.append(DiskOSProbe("windows", part, efi_part, {"drive": f"{L}:"}))
            except Exception:
                continue
        if not probes:
            probes.append(DiskOSProbe("unknown", None, None, {}))
        return probes

    if system.startswith("darwin"):
        code, out, _ = run_capture(["/usr/sbin/diskutil", "list"])
        if code != 0:
            return [DiskOSProbe("unknown", None, None, {})]
        disks = []
        for line in out.splitlines():
            m = re.search(r"(disk\d+s\d+)\s+(\S+)\s+(.+)", line.strip())
            if m:
                dev = f"/dev/{m.group(1)}"
                fs = m.group(2).lower()
                label = m.group(3).strip().split()[-1] if m.group(3) else None
                disks.append((dev, fs, label))
        mac_root: Optional[Partition] = None
        efi: Optional[Partition] = None
        for dev, fs, label in disks:
            label_norm = _normalize_label(label)
            if not efi and ("efi" in fs or (label and "EFI" in label.upper())):
                efi = Partition(device=dev, fs_type="vfat", label=label_norm)
            tmp = Path(f"/Volumes/bf_probe_{Path(dev).name}")
            try:
                run_capture(["/usr/sbin/diskutil", "mount", "-mountPoint", str(tmp), dev])
                if tmp.exists():
                    os_type = _probe_from_mount(tmp)
                    if os_type == "macos" and not mac_root:
                        mac_root = Partition(device=dev, fs_type=fs, mountpoint=str(tmp), label=label_norm)
                run_capture(["/usr/sbin/diskutil", "unmount", str(tmp)])
            except Exception:
                pass
            finally:
                try:
                    if tmp.exists():
                        tmp.rmdir()
                except Exception:
                    pass
        if mac_root:
            probes.append(DiskOSProbe("macos", mac_root, efi, {"device": mac_root.device}))
            return probes
        for v in Path("/Volumes").iterdir():
            if v.is_dir():
                ot = _probe_from_mount(v)
                if ot in ("linux", "windows"):
                    probes.append(DiskOSProbe(ot, Partition(device=str(v), fs_type="unknown", mountpoint=str(v), label=v.name), efi, {}))
        if not probes:
            probes.append(DiskOSProbe("unknown", None, efi, {}))
        return probes

    code, out, _ = run_capture(["lsblk", "-J", "-b", "-o", "NAME,PATH,TYPE,FSTYPE,LABEL,MOUNTPOINT,SIZE"])
    if code != 0:
        return [DiskOSProbe("unknown", None, None, {})]
    data = json.loads(out)
    parts: list[Partition] = []

    def walk(node):
        t = node.get("type") or node.get("TYPE")
        if t == "part":
            p = Partition(
                device=node.get("path") or node.get("PATH"),
                fs_type=(node.get("fstype") or node.get("FSTYPE") or "unknown") or "unknown",
                mountpoint=node.get("mountpoint") or node.get("MOUNTPOINT"),
                label=_normalize_label(node.get("label") or node.get("LABEL")),
                size_bytes=int(node.get("size") or node.get("SIZE") or 0) or None,
            )
            parts.append(p)
        for ch in node.get("children", []):
            walk(ch)

    for dev in data.get("blockdevices", []):
        walk(dev)

    efi_part: Optional[Partition] = None
    best_windows: Optional[DiskOSProbe] = None
    best_macos: Optional[DiskOSProbe] = None
    best_linux: Optional[DiskOSProbe] = None

    for p in parts:
        mp: Optional[Path] = None
        tmp_mp = None
        try:
            if p.mountpoint:
                mp = Path(p.mountpoint)
            else:
                tmp_mp = Path(f"/mnt/bf_probe_{Path(p.device).name}")
                tmp_mp.mkdir(parents=True, exist_ok=True)
                rc, _, _ = run_capture(["mount", "-o", "ro,norecover", "-t", "auto", p.device, str(tmp_mp)])
                if rc == 0:
                    mp = tmp_mp

            if not efi_part and mp and _efi_candidate(p, mp):
                efi_part = p

            if mp:
                ot = _probe_from_mount(mp)
                if ot == "windows" and (not best_windows or (p.size_bytes or 0) > (best_windows.root_part.size_bytes or 0)):
                    best_windows = DiskOSProbe("windows", p, efi_part, {"device": p.device})
                elif ot == "macos" and not best_macos:
                    best_macos = DiskOSProbe("macos", p, efi_part, {"device": p.device})
                elif ot == "linux" and (not best_linux or (p.size_bytes or 0) > (best_linux.root_part.size_bytes or 0)):
                    best_linux = DiskOSProbe("linux", p, efi_part, {"device": p.device})
        except Exception:
            pass
        finally:
            if tmp_mp:
                run_capture(["umount", "-l", str(tmp_mp)])
                try:
                    tmp_mp.rmdir()
                except Exception:
                    pass

    for chosen in (best_windows, best_macos, best_linux):
        if chosen:
            probes.append(chosen)
    if not probes:
        probes.append(DiskOSProbe("unknown", None, efi_part, {}))
    return probes


def identify_os_on_partition(part: Partition) -> DiskOSProbe:
    mp = Path(part.mountpoint) if part.mountpoint else None
    if mp and mp.exists():
        ot = _probe_from_mount(mp)
        return DiskOSProbe(ot, part if ot != "unknown" else None, None, {})
    return DiskOSProbe("unknown", None, None, {})
