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
- Home Aurelia presentation lock: `os/phoenix-os/live-build/config/hooks/live/0066-home-aurelia-presentation-lock.chroot`
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

- Current Home artifact hash under test: `ae023f8aeac29990799b22fb7b64af1f349a89be4b947021488318eb7eba9705`
- Current probe label: `PR39I-HOME-AURELIA-PRESENTATION-LOCK`
- Current probe class: `BOOT_PASS_DESKTOP` for the controlled X11 alpha session path
- Desktop marker count for the current hash: `1 / 2`
- Wallpaper marker count for the current hash: `1 / 2`
- Presentation lock marker count for the current hash: `1 / 2`
- Valid same-attempt shutdown marker count for the current hash: `0 / 2`
- Clean shutdown verified for the current hash: `false`
- Canonical PR39C desktop evidence remains preserved on the older stronger artifact hash.
- Wayland remains unproven. X11 is the current VM alpha session path until repeatability and shutdown are stable.
- The `PR39J-HOME-X11-SHUTDOWN-PROBE` rerun emitted shutdown telemetry, but without a prior desktop marker in the same attempt; it is not clean shutdown proof.

## Remaining Risk

- Clean shutdown still needs to be proven through observed shutdown telemetry.
- Wayland session launch is unresolved and must not be claimed as passing.
- If a future VM reaches login but not the desktop marker, the problem is session determinism, not payload absence.
- If the wallpaper marker is missing, the desktop identity pin is not deterministic even if Plasma itself starts.
- Plasma wallpaper state is seeded in `/etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc`, mirrored into `/etc/xdg`, and re-applied by a KDE autostart helper so the session cannot silently fall back to Breeze once the desktop starts.

## Home Aurelia Presentation Lock

- Canonical alpha presentation identity: `Home Aurelia OS`
- Canonical tagline: `Four Legacies. One Throne.`
- The lock is presentation-layer only and does not rename `home`, build targets, service ids, package ids, or artifact paths.
- Controlled layers: KDE color scheme, inherited icon theme, Plymouth theme, SDDM theme, wallpaper, splash assets, and taskbar/menu accent colors.
- The lock is not release evidence by itself. It becomes valid only when the rebuilt live Plasma session reaches the desktop marker and the wallpaper marker for the exact artifact hash under test.
- Runtime confirmation is emitted as `BWOS_PRESENTATION_LOCK_ACTIVE` only after Plasma reaches the desktop marker and the session observes the seeded metadata, KDE color scheme, and inherited icon theme.
- The latest Home rebuild completed with SHA256 `ae023f8aeac29990799b22fb7b64af1f349a89be4b947021488318eb7eba9705`; PR39I VM evidence observed `BWOS_PRESENTATION_LOCK_ACTIVE`, `BWOS_WALLPAPER_APPLIED`, and `BWOS_DESKTOP_SESSION_STARTED` for that exact hash.
