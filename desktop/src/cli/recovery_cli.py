"""BootForge Recovery CLI entrypoint."""
from __future__ import annotations
import argparse
from ..recovery.core import RecoveryController
from ..core.logger import get_logger

log = get_logger(__name__)


def main(argv=None):
    p = argparse.ArgumentParser(prog="bootforge-recovery", description="BootForge Recovery CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    c_auto = sub.add_parser("auto", help="Detect OS and attempt automatic repair")
    c_auto.add_argument("--dry-run", action="store_true")
    c_auto.add_argument("--diag", action="store_true")

    c_rep = sub.add_parser("repair", help="Repair installed OS")
    c_rep.add_argument("--os", choices=["windows", "macos", "linux"], help="If you know the OS")
    c_rep.add_argument("--dry-run", action="store_true")
    c_rep.add_argument("--diag", action="store_true")

    c_rei = sub.add_parser("reinstall", help="Reinstall OS from image/installer")
    c_rei.add_argument("--os", choices=["macos"], required=True)
    c_rei.add_argument("--image", required=True, help="Path to DMG/APP (macOS)")
    c_rei.add_argument("--erase", action="store_true")
    c_rei.add_argument("--dry-run", action="store_true")
    c_rei.add_argument("--diag", action="store_true")

    c_cln = sub.add_parser("clone", help="Cold-fuse clone (adaptive read retry)")
    c_cln.add_argument("--src", required=True)
    c_cln.add_argument("--dst", required=True)
    c_cln.add_argument("--dry-run", action="store_true")

    c_diag = sub.add_parser("diagnose", help="SMART/temps/memory hints")

    args = p.parse_args(argv)
    rc = RecoveryController(dry_run=getattr(args, "dry_run", False), diag=getattr(args, "diag", False))

    if args.cmd == "auto":
        return rc.auto()
    if args.cmd == "repair":
        return rc.repair(os_hint=args.os)
    if args.cmd == "reinstall":
        return rc.reinstall(os_hint=args.os, image=args.image, preserve_data=not args.erase)
    if args.cmd == "clone":
        rep = rc.clone(args.src, args.dst)
        print(rep)
        return 0
    if args.cmd == "diagnose":
        rep = rc.diagnose()
        print(rep)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
