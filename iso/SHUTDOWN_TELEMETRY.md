# Shutdown Telemetry

This file defines the BWOS / Blue Phoenix OS clean shutdown evidence rule for VM validation.

## Clean Shutdown Requirements

Clean shutdown is valid only when all required events occur in the same VM attempt and on the same artifact hash:

- Desktop session marker: `BWOS_DESKTOP_SESSION_STARTED`
- Presentation identity marker: `BWOS_PRESENTATION_LOCK_ACTIVE`
- Wallpaper marker: `BWOS_WALLPAPER_APPLIED`
- Shutdown marker: `BWOS_SHUTDOWN_TELEMETRY_STARTED`
- QEMU exits normally
- The VM harness does not terminate or kill QEMU

## Non-Pass Conditions

The following are not clean shutdown passes:

- Shutdown marker appears in a separate attempt from the desktop marker.
- QEMU is terminated by the harness after timeout.
- QEMU is killed after failed graceful termination.
- The guest begins shutdown but live media loopback detach stalls indefinitely.
- The desktop reaches Plasma but ACPI/QMP powerdown is ignored.

## Current Home Status

Current Home artifact under PR39J:

- Artifact: `os/phoenix-os/build/bwos-home.iso`
- SHA256: `ae023f8aeac29990799b22fb7b64af1f349a89be4b947021488318eb7eba9705`
- Clean shutdown: not yet verified

PR39J normal ACPI probe result:

- Attempt: `PR39J-HOME-X11-SAME-ATTEMPT-ACPI`
- Evidence: `iso/outputs/vm-boot-evidence/home/20260525T092052Z`
- Desktop marker: `true`
- Wallpaper marker: `true`
- Presentation lock marker: `false`
- ACPI/QMP powerdown requested: `true`
- QMP powerdown sent: `true`
- Shutdown marker: `false`
- QEMU exited normally: `false`
- Forced termination: `true`
- Clean shutdown: `false`

The guest showed KDE shutdown/logout activity after the ACPI request, but `BWOS_SHUTDOWN_TELEMETRY_STARTED` did not appear and QEMU did not exit normally. No `/dev/loop0` or `/run/live/medium` teardown failure was observed in this attempt because systemd shutdown did not begin. This is not a clean shutdown pass.
