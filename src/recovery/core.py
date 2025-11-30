"""Orchestrator for auto/repair/reinstall/clone/diagnose flows."""
from __future__ import annotations
from typing import List, Optional
from .detect import probe_disks, DiskOSProbe
from .validators import guard_destructive
from . import windows_repair, macos_repair, linux_repair
from . import diagnostics, clone as clone_mod
from ..core.logger import get_logger

log = get_logger(__name__)


class RecoveryController:
    def __init__(self, dry_run: bool = False, diag: bool = False):
        self.dry_run = dry_run
        self.diag = diag

    def auto(self):
        probes = probe_disks()
        target = self._pick_primary(probes)
        log.info("AUTO target: %s", target.os_type)
        return self._dispatch(target, "repair")

    def repair(self, os_hint: Optional[str] = None):
        t = self._select_target(os_hint)
        return self._dispatch(t, "repair")

    def reinstall(self, os_hint: Optional[str] = None, image: Optional[str] = None, preserve_data: bool = True):
        t = self._select_target(os_hint)
        guard_destructive(preserve_data)
        return self._dispatch(t, "reinstall", image=image, preserve_data=preserve_data)

    def clone(self, src: str, dst: str):
        return clone_mod.cold_fuse_clone(src, dst, self.dry_run)

    def diagnose(self):
        return diagnostics.full_report()

    def _pick_primary(self, probes: List[DiskOSProbe]) -> DiskOSProbe:
        order = {"windows": 0, "macos": 1, "linux": 2, "unknown": 3}
        chosen = sorted(
            probes,
            key=lambda p: (order.get(p.os_type, 9), -(p.root_part.size_bytes or 0) if p.root_part else 0),
        )[0]
        if chosen.os_type == "unknown":
            raise RuntimeError("No supported OS found.")
        return chosen

    def _select_target(self, os_hint: Optional[str]) -> DiskOSProbe:
        probes = probe_disks()
        if os_hint:
            for p in probes:
                if p.os_type == os_hint:
                    return p
            raise RuntimeError(f"Requested OS '{os_hint}' not detected.")
        return self._pick_primary(probes)

    def _dispatch(self, probe: DiskOSProbe, action: str, **kwargs):
        if probe.os_type == "windows":
            if action == "repair":
                return windows_repair.auto_repair(probe, self.dry_run)
            if action == "reinstall":
                raise NotImplementedError("Windows reinstall is image-driven; use deployment flow.")
        if probe.os_type == "macos":
            if action == "repair":
                return macos_repair.auto_repair(probe, self.dry_run)
            if action == "reinstall":
                image = kwargs.get("image")
                erase = not kwargs.get("preserve_data", True)
                if not image:
                    raise ValueError("--image is required for macOS reinstall")
                return macos_repair.reinstall(probe, image, erase=erase, dry_run=self.dry_run)
        if probe.os_type == "linux":
            if action == "repair":
                return linux_repair.auto_repair(probe, self.dry_run)
            if action == "reinstall":
                raise NotImplementedError("Linux reinstall is distro-specific; use your imaging flow.")
        raise RuntimeError(f"Unsupported action '{action}' for OS '{probe.os_type}'")
