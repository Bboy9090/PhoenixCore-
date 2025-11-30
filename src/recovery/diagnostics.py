"""Lightweight diagnostics with graceful fallbacks."""
from __future__ import annotations
import platform
import shutil
import logging
from .validators import run_capture

log = logging.getLogger("bootforge")


def _has(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def smart_report(dev: str = "/dev/sda") -> str:
    if platform.system().lower() == "windows":
        if _has("smartctl"):
            rc, out, err = run_capture(["smartctl", "-a", dev])
            return out or err
        return "smartctl not available."
    if _has("smartctl"):
        rc, out, err = run_capture(["smartctl", "-a", dev])
        return out or err
    return "smartctl not installed."


def temps_report() -> str:
    if platform.system().lower() == "windows":
        return "Use WMI/OpenHardwareMonitor in full OS."
    if _has("sensors"):
        rc, out, err = run_capture(["sensors"])
        return out or err
    return "lm-sensors not installed."


def memtest_hint() -> str:
    return "Run memtest86+ from boot menu for deepest coverage."


def full_report() -> dict:
    rpt = {
        "smart": smart_report(),
        "temps": temps_report(),
        "memory": memtest_hint(),
    }
    log.info("Diagnostics summary: %s", rpt)
    return rpt
