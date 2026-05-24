# PR39E Session Determinism + Desktop Identity Determinism

**Status:** in progress
**Scope:** Home only

## Goal

Make the Home live session deterministic enough that unattended boots reliably:

- leave GRUB without manual input
- create the live user consistently
- request the Plasma Wayland session candidate when available
- preserve the explicit X11 fallback session for controlled debugging
- select the Home Aurelia wallpaper explicitly
- lock the Home Aurelia visual identity documented in `docs/HOME_AURELIA_VISUAL_IDENTITY.md`
- emit a desktop-session marker only after Plasma starts
- emit shutdown telemetry only when shutdown actually begins
- preserve the stronger PR39C desktop evidence as canonical
- store weaker reruns as separate attempts

## Canonical Rules

- Desktop success is valid only when `BWOS_DESKTOP_SESSION_STARTED` fires or `/run/bwos-desktop-reached` exists.
- Wallpaper identity is only considered pinned when `BWOS_WALLPAPER_APPLIED` fires or `/run/bwos-wallpaper-applied` exists.
- Display-manager reach alone does not count as desktop reach.
- Clean shutdown must be observed, not assumed.
- Stronger evidence stays canonical; weaker reruns never overwrite it.
- Contradictory reruns must mark repeatability risk truthfully.

## Current Implementation Surface

- Live user provisioning: `os/phoenix-os/live-build/config/hooks/live/0055-configure-live-user.chroot`
- Home Aurelia wallpaper pin: `os/phoenix-os/live-build/config/hooks/live/0072-pin-blue-phoenix-wallpaper.chroot`
- SDDM Wayland autologin: `os/phoenix-os/live-build/config/hooks/live/0060-set-sddm-theme.chroot`
- Plasma session token seeding: `os/phoenix-os/live-build/config/hooks/live/0065-seed-plasma-session.chroot`
- Desktop marker: `os/phoenix-os/live-build/config/hooks/live/0110-desktop-heartbeat.chroot`
- Shutdown telemetry: `os/phoenix-os/live-build/config/hooks/live/0120-shutdown-telemetry.chroot`
- Boot-matrix handling: `iso/scripts/vm-boot-checklist.sh`
- Boot-matrix validation: `iso/scripts/validate-boot-matrix.sh`
- Artifact registry propagation: `iso/scripts/scan-artifacts.sh`

## Validation Target

Run three Home VM attempts and record:

- attempt A: desktop marker + wallpaper marker + shutdown telemetry
- attempt B: desktop marker + wallpaper marker + shutdown telemetry
- attempt C: desktop marker + wallpaper marker + shutdown telemetry

Result classification:

- PASS: 3/3 attempts reach the desktop marker
- PARTIAL: 1-2/3 attempts reach the desktop marker
- FAIL: 0/3 attempts reach the desktop marker

## Current Evidence

- Current Home artifact hash under test: `fc57d42359f615fa7b5f101f3d058d6848138f739f6b201f0730a00af65246d8`
- Current repeatability run labels: `PR39F-WAYLAND`, `PR39F-WAYLAND-ACTUAL`, `PR39F-X11-CONTROLLED`
- Current repeatability class: `PASS` for the observed X11 session path
- Desktop marker count for the current hash: `3 / 3`
- Wallpaper marker count for the current hash: `3 / 3`
- Shutdown telemetry count for the current hash: `0 / 3`
- Clean shutdown verified for the current hash: `false`
- Canonical PR39C desktop evidence remains preserved on the older stronger artifact hash.
- Wayland remains unproven: Wayland-requested attempts selected `plasmawayland.desktop` in BWOS telemetry, but SDDM actually launched `plasma.desktop` with `XDG_SESSION_TYPE=x11`.

## Remaining Risk

- Clean shutdown still needs to be proven through observed shutdown telemetry.
- Wayland session launch is unresolved and must not be claimed as passing.
- If a future VM reaches login but not the desktop marker, the problem is session determinism, not payload absence.
- If the wallpaper marker is missing, the desktop identity pin is not deterministic even if Plasma itself starts.
- Plasma wallpaper state is seeded in `/etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc`, mirrored into `/etc/xdg`, and re-applied by a KDE autostart helper so the session cannot silently fall back to Breeze once the desktop starts.
