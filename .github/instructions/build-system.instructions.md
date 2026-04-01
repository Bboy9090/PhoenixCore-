---
applyTo: "bootable_usb/BootForge/src/**/*.py"
---

# BootForge Runtime Rules (Python)

- Never return success unless the real action happened (disk/USB write, mount, imaging, patch application, device scan).
- OS-specific code must be guarded; avoid assuming bash tools exist on Windows.
- Prefer pathlib; avoid hardcoded absolute paths.
- Errors must be explicit and actionable (what failed, what to check next).
- Keep core logic in `src/core` and treat CLI/GUI as thin wrappers.

## Validation
- Prefer running tests in `bootable_usb/BootForge/tests/`.
- If a change affects patching/imaging pipelines, add or update a test case.
