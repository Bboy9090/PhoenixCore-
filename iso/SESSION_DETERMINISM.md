# Session Determinism Status

## Latest Record: PR39L

| Field | Value |
|---|---|
| Artifact | `os/phoenix-os/build/bwos-home.iso` |
| SHA256 | `ceb5cb1657f7b3da68eb5e9b1ef987618cc67ae167afe2f1ade03929987059db` |
| Session Profile | x11 |
| session_determinism_class | PASS |
| Repeatability Pass Count | 3 / 3 |
| Desktop Marker | ✅ all 3 runs |
| Wallpaper Marker | ✅ all 3 runs |
| Presentation Lock Marker | ✅ all 3 runs |
| Shutdown Marker | ✅ all 3 runs |
| Clean Shutdown | ✅ all 3 runs |
| Repeatability Risk | false |

## Evidence

| Run | Evidence Folder |
|---|---|
| Initial probe | `iso/outputs/vm-boot-evidence/home/20260526T151648Z/` |
| Repeatability 1 | `iso/outputs/vm-boot-evidence/home/20260526T154956Z/` |
| Repeatability 2 | `iso/outputs/vm-boot-evidence/home/20260526T155345Z/` |
| Repeatability 3 | `iso/outputs/vm-boot-evidence/home/20260526T155852Z/` |

## Notes

- The root-level `bwos-desktop-observer` systemd service (PR39L) correctly emits all session markers without any user-level race conditions.
- Wayland session was attempted and correctly fell back to X11 (`WAYLAND_FAIL_X11_PASS`), which is the expected behaviour for this ISO configuration.
- PR40 App Launch Matrix is now unblocked pending explicit user approval.
