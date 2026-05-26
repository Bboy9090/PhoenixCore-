# Boot Repeatability Status

## Latest Record: PR39L Home (Aurelia) Edition

| Field | Value |
|---|---|
| Artifact | `os/phoenix-os/build/bwos-home.iso` |
| SHA256 | `ceb5cb1657f7b3da68eb5e9b1ef987618cc67ae167afe2f1ade03929987059db` |
| Pass Count | 3 / 3 |
| Classification | BOOT_PASS_DESKTOP |
| Repeatability Class | PASS |
| Clean Shutdown | ✅ verified (ACPI power button, all runs) |
| Forced Termination | false (all runs) |
| ROOT_OBSERVER_PASS | ✅ |

## Run Details

| Run | Timestamp | Evidence | Classification |
|---|---|---|---|
| Initial probe | 2026-05-26T15:16:48Z | `iso/outputs/vm-boot-evidence/home/20260526T151648Z/` | BOOT_PASS_DESKTOP |
| Repeatability 1 | 2026-05-26T15:49:56Z | `iso/outputs/vm-boot-evidence/home/20260526T154956Z/` | BOOT_PASS_DESKTOP |
| Repeatability 2 | 2026-05-26T15:53:45Z | `iso/outputs/vm-boot-evidence/home/20260526T155345Z/` | BOOT_PASS_DESKTOP |
| Repeatability 3 | 2026-05-26T15:58:52Z | `iso/outputs/vm-boot-evidence/home/20260526T155852Z/` | BOOT_PASS_DESKTOP |

## Release Readiness

`release_blocked` — pending:
- PR40 App Launch Matrix
- USB boot validation
- Safety validation
