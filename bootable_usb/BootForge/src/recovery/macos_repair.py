"""macOS repair routines."""
from __future__ import annotations
from .validators import run
from .mount import mounted


def auto_repair(probe, dry_run: bool = False):
    return repair(probe, run_fsck=True, rebuild_bless=True, dry_run=dry_run)


def repair(probe, run_fsck: bool = True, rebuild_bless: bool = True, dry_run: bool = False):
    if run_fsck:
        run(["fsck_apfs", "-fy", probe.root_part.device], dry_run)
    with mounted(probe.root_part.device, rw=True) as macroot:
        if rebuild_bless:
            core_services = f"{macroot}/System/Library/CoreServices"
            run(["bless", "--folder", core_services, "--bootefi", "--create-snapshot"], dry_run)


def reinstall(probe, installer_app_or_dmg: str, erase: bool = False, dry_run: bool = False):
    if installer_app_or_dmg.endswith(".app"):
        cmd = [f"{installer_app_or_dmg}/Contents/Resources/startosinstall", "--agreetolicense"]
        if erase:
            cmd.append("--eraseinstall")
        return run(cmd, dry_run)
    args = ["asr", "restore", "--source", installer_app_or_dmg, "--target", probe.root_part.device]
    if erase:
        args.append("--erase")
    return run(args, dry_run)
