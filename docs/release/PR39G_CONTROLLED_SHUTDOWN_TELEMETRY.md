# PR39G Controlled Shutdown Telemetry

**Status:** partial; shutdown still blocked
**Scope:** Home Aurelia only

## Goal

Verify clean shutdown behavior without overstating normal desktop shutdown support.

PR39F proved the Home Aurelia desktop and wallpaper markers are repeatable on the rebuilt Home artifact, but ACPI/QMP shutdown did not reach the systemd shutdown hook. PR39G adds a VM-only shutdown probe that requests poweroff from inside the live Plasma session after the real desktop marker fires.

## Rules

- VM only.
- No physical USB.
- No installer.
- No formatting.
- No partitioning.
- No host disk passthrough.
- No USB passthrough.
- Do not mark release candidate.
- Do not treat shutdown probe success as proof of user-initiated GUI shutdown.

## Implementation

- Added GRUB entry: `Live system X11 shutdown probe (amd64)`.
- Kernel args include:
  - `bwos.session=x11`
  - `bwos.shutdown_probe=1`
- Added VM harness option: `--shutdown-probe`.
- The VM harness selects the shutdown-probe GRUB entry instead of sending ACPI powerdown after desktop marker.
- The live desktop marker helper only triggers guest poweroff when `bwos.shutdown_probe=1` is present.
- The shutdown systemd hook still owns the valid marker:
  - `BWOS_SHUTDOWN_TELEMETRY_STARTED`
  - `/run/bwos-shutdown-started`

## Evidence Requirements

A PR39G pass requires all of the following on the same artifact hash:

- boot menu reached
- kernel/initramfs/display chain recorded or normalized from in-guest marker
- desktop marker reached
- wallpaper marker reached
- shutdown probe requested
- shutdown marker reached
- QEMU exits after guest-initiated shutdown

## Current Known State Before PR39G Test

- PR39F hash: `fc57d42359f615fa7b5f101f3d058d6848138f739f6b201f0730a00af65246d8`
- Desktop marker: `3 / 3`
- Wallpaper marker: `3 / 3`
- Shutdown marker: `0 / 3`
- Session probe: `WAYLAND_FAIL_X11_PASS`

## PR39G Evidence

### Rebuilt Home Artifact

- Artifact: `bwos-home.iso`
- Canonical output path: `iso/outputs/bwos-home.iso`
- Build output path: `os/phoenix-os/build/bwos-home.iso`
- SHA256: `4887e18fa3a6ee6b96637569be1591c13d037612fe5f5e45441c5233b2d0c75d`
- Size: `2276362240` bytes
- VM tool: `qemu-system-x86_64`
- EFI: enabled
- Secure Boot: disabled
- RAM: `4096 MB`
- CPU cores: `2`
- Host disk passthrough: none
- USB passthrough: none

### Attempt 1: Fixed Marker Shutdown Probe

- Attempt label: `PR39G-X11-SHUTDOWN-PROBE-FIXED-MARKER`
- Evidence path: `iso/outputs/vm-boot-evidence/home/20260524T151848Z/`
- Result: `BOOT_PASS_DESKTOP`
- Desktop marker: reached
- Wallpaper marker: reached
- KWin: observed
- Plasmashell: observed
- Shutdown marker: not reached
- Clean shutdown: false
- Shutdown method: forced kill after timeout

Observed markers:

```text
BWOS_KWIN_STARTED
BWOS_PLASMASHELL_STARTED
BWOS_DESKTOP_SESSION_STARTED
BWOS_WALLPAPER_APPLIED
```

This proves the marker hang was fixed for the rebuilt Home artifact. It does not prove clean shutdown.

### Attempt 2: GRUB Hotkey Shutdown Probe

- Attempt label: `PR39G-X11-SHUTDOWN-HOTKEY-PROBE`
- Evidence path: `iso/outputs/vm-boot-evidence/home/20260524T152758Z/`
- Result: `BOOT_FAIL_DISPLAY`
- Desktop marker: not reached
- Wallpaper marker: not reached
- Shutdown marker: reached
- Clean shutdown: false
- Shutdown method: forced kill
- Canonical update: false

Observed shutdown evidence:

```text
BWOS_SHUTDOWN_TELEMETRY_STARTED
systemd-shutdown[1]: Could not detach loopback /dev/loop0: Device or resource busy
systemd-shutdown[1]: Failed to finalize file systems, loop devices, ignoring.
```

This proves the shutdown telemetry hook can fire, but it does not prove a clean shutdown and does not replace the stronger desktop-pass evidence.

## Current PR39G Classification

- Desktop reachability: `BOOT_PASS_DESKTOP` for hash `4887e18fa3a6ee6b96637569be1591c13d037612fe5f5e45441c5233b2d0c75d`
- Session path: X11 fallback proven
- Wayland path: still unproven
- Wallpaper marker: proven in desktop-pass attempt
- Shutdown telemetry: observed in a separate weaker attempt
- Clean shutdown: false
- Release candidate: blocked

The boot matrix intentionally keeps both attempts. The canonical row must not be read as "desktop marker and shutdown marker happened in the same boot"; the attempt list is the source of truth for per-run evidence.

## Remaining Blocker

Clean shutdown is not verified. The live system reaches systemd shutdown telemetry but does not exit QEMU cleanly before timeout, and systemd reports live-media/loopback finalization issues.

Recommended next debug target:

- Add explicit command-line logging for `bwos.shutdown_probe=1`.
- Add a separate shutdown-only attempt classification so shutdown-marker evidence cannot be visually merged with desktop-marker evidence.
- Investigate live media teardown:
  - `/run/live/medium`
  - `/dev/loop0`
  - services keeping the SquashFS/live medium busy
  - whether `systemctl poweroff --force --force` should exist only as a debug probe, not a normal shutdown path.

## Release State

Release remains blocked until clean shutdown is observed and app/safety validation are recorded. A shutdown-probe pass proves the guest can shut itself down from a live session; it does not prove GUI menu shutdown UX.
