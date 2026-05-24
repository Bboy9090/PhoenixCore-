# PR39F Session Failure Telemetry + Controlled X11 Fallback Probe

**Status:** evidence recorded
**Scope:** Home Aurelia only

## Goal

Determine why the current Home Aurelia artifact reaches the display-manager boundary but does not reach the real Plasma desktop marker, then test whether the explicit X11 fallback profile restores desktop startup.

## Current Baseline

- Current Home hash before PR39F rebuild: `149ec4c728d8c02b3017a48a2e7533133b1db2175036a2c740145d53ef0f2bc6`
- PR39E current-hash result: `BOOT_FAIL_DISPLAY`
- Boot menu, kernel, initramfs, and display-manager boundary were observed.
- Desktop marker, wallpaper marker, shutdown marker, and clean shutdown were not observed.
- The older PR39C desktop evidence remains preserved on hash `8f5e094ca9164d8b117a07ea2371816c8afdd0e4ad8d7e6a47d00195b93f5f32`.

## Implementation

- Added explicit GRUB entries for:
  - `bwos.session=wayland`
  - `bwos.session=x11`
- Added boot-time session profile selection before `sddm.service`.
- Added session diagnostics emitted to serial logs.
- Added live-user/config verification before SDDM starts.
- Added Plasma-session marker telemetry for:
  - session launch attempted
  - Wayland or X11 profile attempted
  - selected session file
  - KWin observed or missing
  - plasmashell observed or missing
  - wallpaper marker
  - desktop marker
- Added extracted session log files beside each VM attempt.

## Classification Model

- `WAYLAND_PASS`
- `WAYLAND_FAIL_X11_PASS`
- `BOTH_FAIL`
- `SESSION_CONFIG_FAIL`
- `DISPLAY_MANAGER_FAIL`
- `USER_PROVISIONING_FAIL`
- `MARKER_HOOK_FAIL`

## Required Probe

1. Rebuild Home only.
2. Run one Wayland attempt with `--session-profile wayland`.
3. If Wayland still fails, run one X11 attempt with `--session-profile x11`.
4. Record profile, selected session file, session markers, serial log, console log, and extracted session log.

## PR39F Evidence

- Rebuilt Home hash: `fc57d42359f615fa7b5f101f3d058d6848138f739f6b201f0730a00af65246d8`
- Artifact: `iso/outputs/bwos-home.iso`
- VM tool: `qemu-system-x86_64`
- EFI: enabled
- Secure Boot: disabled
- RAM: 4096 MB
- CPU cores: 2
- Disk attached: none

| Attempt | Requested Profile | Selected Session | Actual Session Type | Actual SDDM Session | Desktop Marker | Wallpaper Marker | Clean Shutdown | Probe Class |
|---|---|---|---|---|---|---|---|---|
| `PR39F-WAYLAND` | `wayland` | `plasmawayland.desktop` | `x11` | `plasma.desktop` | true | true | false | `WAYLAND_FAIL_X11_PASS` |
| `PR39F-WAYLAND-ACTUAL` | `wayland` | `plasmawayland.desktop` | `x11` | `plasma.desktop` | true | true | false | `WAYLAND_FAIL_X11_PASS` |
| `PR39F-X11-CONTROLLED` | `x11` | `plasma.desktop` | `x11` | `plasma.desktop` | true | true | false | `WAYLAND_FAIL_X11_PASS` |

## Findings

- The Home live image now reaches the real Plasma desktop marker repeatably on the rebuilt artifact hash.
- The Home Aurelia wallpaper marker fires repeatably on the rebuilt artifact hash.
- Kernel/initramfs/display stage booleans are normalized from the in-guest display/desktop marker when normal boot output does not expose early kernel text.
- The Wayland-requested profile does not actually launch a Wayland session in the current VM path.
- SDDM selects `/usr/share/xsessions/plasma.desktop` and starts `/usr/bin/startplasma-x11`.
- The actual session environment is `XDG_SESSION_TYPE=x11`.
- The controlled X11 fallback profile reaches KWin, plasmashell, desktop marker, and wallpaper marker.
- Clean shutdown remains unverified; ACPI powerdown was sent, but the VM attempts ended by timeout/forced kill.

## Current Classification

- Session probe classification: `WAYLAND_FAIL_X11_PASS`
- Desktop classification: `BOOT_PASS_DESKTOP`
- Session determinism class: `PASS` for the observed X11 desktop marker path
- Release readiness: still `release_blocked`

## Release State

No artifact is release-candidate eligible from PR39F. The remaining release blocker is clean shutdown evidence, and Wayland remains unresolved as a canonical session target.
