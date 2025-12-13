---
applyTo: "bootable_usb/BootForge/src/core/patch_pipeline.py"
---

# Patch Pipeline Rules

- Keep patch stages deterministic (prepare ➜ apply ➜ verify ➜ cleanup) and document any ordering changes in code comments.
- Surface actionable errors that name the failing patch step and target device; avoid silent fallbacks.
- Guard platform-specific operations and never assume write access without explicit checks.
- Keep logging concise but include patch identifiers and device paths for traceability.
- Add or update targeted tests in `bootable_usb/BootForge/tests/` when changing pipeline flow or validation logic.
