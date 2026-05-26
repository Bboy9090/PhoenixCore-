# PR39J Same-Attempt Clean Shutdown Verification

Status: completed as failed verification; clean shutdown remains blocked.

## Goal

Verify whether Home Aurelia can reach the live Plasma desktop, activate presentation identity markers, request shutdown, and exit QEMU cleanly in the same VM attempt.

## Artifact Under Test

The requested `iso/outputs/bwos-home.iso` path currently has SHA256 `f113419abc4ad8c343cedb00a667e64fd13076f3c2ed87e658b63dea8059806d`, not the expected PR39J hash.

The PR39J evidence target is therefore the exact current Home artifact hash:

- Artifact: `os/phoenix-os/build/bwos-home.iso`
- SHA256: `ae023f8aeac29990799b22fb7b64af1f349a89be4b947021488318eb7eba9705`
- VM profile: X11 alpha
- Host passthrough: none
- Network: disabled
- Extra disk: none

No registry output ISO is overwritten silently for this PR.

## Same-Attempt Rule

Clean shutdown can only be true when one attempt records all of the following for the same artifact hash:

- `BWOS_DESKTOP_SESSION_STARTED`
- `BWOS_PRESENTATION_LOCK_ACTIVE`
- `BWOS_WALLPAPER_APPLIED`
- `BWOS_SHUTDOWN_TELEMETRY_STARTED`
- QMP/ACPI powerdown requested when using the normal VM path
- QEMU exits normally without forced termination

A forced QEMU kill, a shutdown marker without a desktop marker, or a desktop marker without QEMU clean exit is not clean shutdown evidence.

## Evidence

PR39J normal ACPI probe:

- Attempt: `PR39J-HOME-X11-SAME-ATTEMPT-ACPI`
- Timestamp: `2026-05-25T09:20:52Z`
- Artifact: `os/phoenix-os/build/bwos-home.iso`
- SHA256: `ae023f8aeac29990799b22fb7b64af1f349a89be4b947021488318eb7eba9705`
- Evidence directory: `iso/outputs/vm-boot-evidence/home/20260525T092052Z`
- Desktop marker: `true`
- Wallpaper marker: `true`
- Presentation lock marker: `false`
- ACPI/QMP powerdown requested: `true`
- QMP powerdown sent: `true`
- Shutdown marker: `false`
- QEMU exited normally: `false`
- Forced termination: `true`
- Clean shutdown verified: `false`

## Result

PR39J does not pass. The attempt reached the live Plasma desktop and wallpaper marker, then the VM harness sent QMP `system_powerdown`. The guest/KDE session reacted by activating KDE shutdown/logout components, but systemd shutdown telemetry did not start and QEMU did not exit. The harness terminated QEMU after timeout, so this is explicitly not clean shutdown evidence.

The same attempt also failed to emit `BWOS_PRESENTATION_LOCK_ACTIVE` because the live user KDE config did not confirm `ColorScheme=HomeAurelia` or `Theme=home-aurelia` in that run. Earlier evidence for the same hash did emit the marker, so this remains repeatability risk rather than a canonical downgrade.

## Failure Classification

- Desktop path: reached
- Wallpaper path: reached
- Presentation lock path: inconsistent
- ACPI path: QMP request sent
- KDE shutdown/logout path: activated
- systemd poweroff path: not reached
- live media loopback detach: not reached, so loopback detach is not the observed blocker in this attempt
- QEMU exit: forced termination
- Clean shutdown: fail

## Next Fix Candidate

Do not mark release candidate. A rebuild is only justified if we intentionally harden the debug-only shutdown path and presentation-lock seeding. The likely safe fixes are:

- Make the Home Aurelia KDE config self-heal from `/etc/skel/.config/kdeglobals` before marker verification if the live user copy is missing.
- Add explicit shutdown-probe logging after desktop marker and before `systemctl poweroff`.
- Keep normal ACPI failure documented separately because KDE appears to intercept the virtual power button into a logout prompt rather than immediate systemd poweroff.
