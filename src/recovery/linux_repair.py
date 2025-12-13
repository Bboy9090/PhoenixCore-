"""Linux repair routines."""
from __future__ import annotations
from .validators import run
from .mount import mounted


def auto_repair(probe, dry_run: bool = False):
    return repair(probe, fsck_all=True, grub=True, dry_run=dry_run)


def repair(probe, fsck_all: bool = True, grub: bool = True, dry_run: bool = False):
    if fsck_all:
        run(["fsck", "-Af", "-V"], dry_run)
    if grub and probe.root_part:
        root_dev = probe.root_part.device
        disk = _disk_from_part(root_dev)
        with mounted(root_dev, rw=True) as rootmp:
            run(["grub-install", "--root-directory", rootmp, disk], dry_run)
            try:
                run(["chroot", rootmp, "update-grub"], dry_run)
            except Exception:
                run(["chroot", rootmp, "grub-mkconfig", "-o", "/boot/grub/grub.cfg"], dry_run)


def _disk_from_part(part: str) -> str:
    if "nvme" in part:
        import re
        m = re.match(r"(.+n\d+)p\d+$", part)
        if m:
            return m.group(1)
    return _strip_digits(part)


def _strip_digits(dev: str) -> str:
    import re
    return re.sub(r"\d+$", "", dev)
