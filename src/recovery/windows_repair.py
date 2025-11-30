"""Windows repair routines (offline)."""
from __future__ import annotations
from .mount import mounted
from .validators import run


def auto_repair(probe, dry_run: bool = False):
    return repair(probe, offline=True, rebuild_boot=True, dry_run=dry_run)


def repair(probe, offline: bool = True, rebuild_boot: bool = True, dry_run: bool = False):
    if not probe.root_part:
        raise RuntimeError("Cannot repair: no Windows root partition detected")
    with mounted(probe.root_part.device) as winroot:
        if offline:
            sfc_offline(winroot, dry_run)
            dism_offline(winroot, dry_run)
        if rebuild_boot:
            efi_dev = probe.efi_part.device if probe.efi_part else "EFI"
            with mounted(efi_dev) as efimp:
                rebuild_bcd(winroot, efimp, dry_run)


def sfc_offline(winroot: str, dry_run: bool = False):
    run(["sfc", "/scannow", f"/offbootdir={winroot}", f"/offwindir={winroot}\\Windows"], dry_run)


def dism_offline(winroot: str, dry_run: bool = False):
    run(["dism", f"/Image:{winroot}", "/Cleanup-Image", "/RestoreHealth"], dry_run)


def rebuild_bcd(winroot: str, efimp: str, dry_run: bool = False):
    for sub in (["bootrec", "/fixmbr"], ["bootrec", "/fixboot"], ["bootrec", "/rebuildbcd"]):
        run(sub, dry_run)
    run(["bcdboot", f"{winroot}\\Windows", "/s", efimp, "/f", "ALL"], dry_run)
