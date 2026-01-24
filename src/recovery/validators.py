"""Guardrails and subprocess helpers for recovery flows."""
from __future__ import annotations
import logging
import subprocess
import sys
from typing import Sequence

log = logging.getLogger("bootforge")


class DestructiveActionRejected(Exception):
    """Raised when a destructive action lacks explicit confirmation."""


def guard_destructive(preserve: bool) -> None:
    if preserve:
        return
    if sys.stdin.isatty():
        ans = input("⚠️  This may ERASE data. Type 'ERASE' to confirm: ")
        if ans.strip().upper() != "ERASE":
            raise DestructiveActionRejected("User did not confirm erase.")
    else:
        raise DestructiveActionRejected("Non-interactive destructive action without confirmation.")


def run(cmd: Sequence[str], dry_run: bool = False, check: bool = True, env: dict | None = None, cwd: str | None = None) -> int:
    log.info("RUN: %s%s", "(dry-run) " if dry_run else "", " ".join(cmd))
    if dry_run:
        return 0
    proc = subprocess.run(cmd, text=True, capture_output=True, env=env, cwd=cwd)
    if proc.stdout:
        log.debug("stdout: %s", proc.stdout.strip())
    if proc.stderr:
        log.debug("stderr: %s", proc.stderr.strip())
    if check and proc.returncode != 0:
        log.error("Command failed (%s): %s", proc.returncode, " ".join(cmd))
        raise RuntimeError(f"Command failed: {cmd} -> {proc.returncode}")
    return proc.returncode


def run_capture(cmd: Sequence[str], dry_run: bool = False) -> tuple[int, str, str]:
    log.info("RUN(CAP): %s%s", "(dry-run) " if dry_run else "", " ".join(cmd))
    if dry_run:
        return (0, "", "")
    proc = subprocess.run(cmd, text=True, capture_output=True)
    return (proc.returncode, proc.stdout, proc.stderr)


def run_ok(cmd: Sequence[str], dry_run: bool = False) -> bool:
    try:
        run(cmd, dry_run, check=True)
        return True
    except Exception:
        return False
