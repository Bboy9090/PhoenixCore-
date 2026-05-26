# PR39I SDDM-to-Plasma Handoff Trace

Status: first X11 handoff probe passed desktop marker for the current Home artifact. This PR does not claim release readiness because clean shutdown and repeatability remain unverified.

## Goal

Find the exact point where SDDM reaches the login/session boundary but Plasma does not start far enough to emit the desktop autostart marker.

## Current Home Baseline

Current Home artifact before this trace rebuild:

- ISO: `bwos-home.iso`
- SHA256: `f113419abc4ad8c343cedb00a667e64fd13076f3c2ed87e658b63dea8059806d`
- Classification: `BOOT_FAIL_DISPLAY`
- GRUB reached: `true`
- kernel/initramfs inferred: `true`
- SDDM/autologin prestart reached: `true`
- selected profile: `x11`
- selected session: `plasma.desktop`
- phoenix user provisioning: `true`
- desktop marker: `false`
- wallpaper marker: `false`
- clean shutdown: `false`

## Current Home Probe Result

Artifact tested after PR39I telemetry and Home Aurelia presentation-lock staging:

- ISO: `os/phoenix-os/build/bwos-home.iso`
- SHA256: `ae023f8aeac29990799b22fb7b64af1f349a89be4b947021488318eb7eba9705`
- Attempt: `PR39I-HOME-AURELIA-PRESENTATION-LOCK`
- Timestamp: `2026-05-25T06:20:57Z`
- VM tool: `qemu-system-x86_64`
- Session profile: `x11`
- Selected session file: `plasma.desktop`
- Actual session type: `x11`
- Classification: `BOOT_PASS_DESKTOP`
- Desktop marker: `true`
- Wallpaper marker: `true`
- Presentation lock marker: `true`
- Clean shutdown verified: `false`
- Evidence directory: `iso/outputs/vm-boot-evidence/home/20260525T062057Z`

Observed process chain:

- `kwin_x11`: started
- `startplasma-x11`: started
- `plasmashell`: started
- `ksmserver`: started
- user DBus: started
- systemd user session: started

This identifies the prior failure as a session determinism/configuration path that is resolved for the controlled X11 alpha profile on this artifact. It does not resolve Wayland or clean shutdown.

## Shutdown Probe Result

A follow-up VM-only shutdown probe was run against the same artifact hash:

- Attempt: `PR39J-HOME-X11-SHUTDOWN-PROBE`
- Timestamp: `2026-05-25T06:46:24Z`
- Kernel command line included: `bwos.shutdown_probe=1`
- Result stage: `BOOT_FAIL_DISPLAY`
- Desktop marker: `false`
- Wallpaper marker: `false`
- Presentation lock marker: `false`
- Clean shutdown verified: `false`
- Evidence directory: `iso/outputs/vm-boot-evidence/home/20260525T064624Z`

The serial log did include `BWOS_SHUTDOWN_TELEMETRY_STARTED`, proving the shutdown hook can execute. However, that run did not emit the desktop marker first, so it is not valid same-attempt desktop-plus-shutdown evidence. The stronger desktop-pass attempt remains canonical, and this weaker/contradictory rerun is preserved as repeatability risk evidence.

## X11 VM Alpha Policy

For VM alpha validation, X11 is the canonical session path.

Reason:

- QEMU x86_64 runs under TCG on Apple Silicon, where Wayland/KWin graphics behavior is less predictable.
- The immediate alpha blocker is deterministic desktop reachability, not proving Wayland support.
- X11 has simpler diagnostics through SDDM, Xorg logs, `DISPLAY`, `.xsession-errors`, and visible process chains.

Wayland remains experimental and can become canonical again only after X11 desktop repeatability and clean shutdown are proven and Wayland produces equal or stronger evidence across repeated VM attempts.

## Instrumentation Added

The live image now records:

- kernel command line before SDDM starts
- SDDM autologin user and selected session
- X11 and Wayland session file existence
- session `Exec=` target and whether the referenced command exists
- phoenix home ownership and mode
- SDDM active state, substate, and MainPID
- `loginctl` session list and session fields when available
- process observations for `kwin_x11`, `kwin_wayland`, `plasmashell`, `ksmserver`, `startplasma-x11`, `startplasma-wayland`, `dbus-daemon`, `dbus-broker`, and `systemd --user`
- relevant user process environment values: `XDG_SESSION_TYPE`, `DISPLAY`, `WAYLAND_DISPLAY`, `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS`
- SDDM/Xorg/user-session logs when present

## Machine-Readable Fields

`iso/outputs/vm-boot-matrix.json` now preserves process observations per boot attempt:

- `process_observations.kwin_x11`
- `process_observations.kwin_wayland`
- `process_observations.plasmashell`
- `process_observations.ksmserver`
- `process_observations.startplasma_x11`
- `process_observations.startplasma_wayland`
- `process_observations.dbus_daemon`
- `process_observations.dbus_broker`
- `process_observations.systemd_user`

## Patch Policy

No random KDE configuration changes are allowed. Fixes are allowed only after evidence identifies the failing layer.

Possible safe fixes after evidence:

- set SDDM autologin explicitly to `plasma.desktop` for VM alpha
- repair phoenix home ownership or permissions
- repair `XDG_RUNTIME_DIR` creation
- add missing DBus/user-session dependency
- repair systemd user startup
- repair invalid Plasma session/autostart path

## Current Next Step

Run repeatability and shutdown validation against the same Home artifact hash, but do not treat the shutdown probe as a pass unless the same attempt records both desktop marker and shutdown marker:

```bash
bash iso/scripts/vm-boot-checklist.sh --artifact-path os/phoenix-os/build/bwos-home.iso --session-profile x11 --shutdown-probe --attempt-label PR39J-HOME-X11-SHUTDOWN-PROBE --timeout 420 --json
```

If shutdown is observed cleanly, run three repeatability attempts. If shutdown still fails, keep `clean_shutdown_verified=false` and classify the shutdown layer separately.
