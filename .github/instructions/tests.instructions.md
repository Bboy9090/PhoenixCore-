---
applyTo: "bootable_usb/BootForge/tests/**/*.py,tests/**/*.py"
---

# Test Rules

- Keep tests deterministic (no network, no system-dependent paths unless explicitly mocked).
- Prefer unit tests for core logic and small integration tests for pipeline glue.
- If a bug is fixed, add a regression test first when practical.
