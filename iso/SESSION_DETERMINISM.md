# Session Determinism

This file tracks the Home live-session determinism pass for PR39E.
The visual identity target for that pass is documented in `docs/HOME_AURELIA_VISUAL_IDENTITY.md`.

## Canonical Evidence

- PR39C confirmed Home can reach the Plasma desktop once.
- PR39D showed the result was not yet repeatable.
- PR39E adds explicit session markers so the desktop state is observed, not inferred.
- The SDDM/Plasma session path records both the requested profile and the actual session observed in logs.
- The Home Aurelia wallpaper is seeded through the live desktop configuration and re-applied from the session-start marker.
- Wallpaper identity is only considered pinned when `BWOS_WALLPAPER_APPLIED` fires or `/run/bwos-wallpaper-applied` exists.
- The wallpaper is pinned in `/etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc`, mirrored into `/etc/xdg`, and re-applied by the login autostart helper so KDE does not silently fall back to Breeze.
- The Home Aurelia presentation layer is locked through `0066-home-aurelia-presentation-lock.chroot`; this seeds KDE colors, icon inheritance, taskbar/menu accent state, and presentation metadata without changing internal edition/build ids.

## Required Markers

- `BWOS_DESKTOP_SESSION_STARTED`
- `/run/bwos-desktop-reached`
- `BWOS_PRESENTATION_LOCK_ACTIVE`
- `/run/bwos-presentation-lock-active`
- `BWOS_SHUTDOWN_TELEMETRY_STARTED`
- `/run/bwos-shutdown-started`

## Rules

- Stronger evidence remains canonical.
- Weaker reruns stay as separate attempts.
- Display-manager reach alone is not desktop success.
- Shutdown is only clean when telemetry proves it.

## Current Status

- Latest Home artifact under test: `ae023f8aeac29990799b22fb7b64af1f349a89be4b947021488318eb7eba9705`
- Latest PR39I attempt: `PR39I-HOME-AURELIA-PRESENTATION-LOCK`
- Latest observed session profile: `x11`
- Latest desktop marker count: `1 / 2`
- Latest wallpaper marker count: `1 / 2`
- Latest presentation lock marker count: `1 / 2`
- Current shutdown telemetry count for latest hash: `0 / 2` valid same-attempt shutdown markers in the matrix
- Current clean shutdown evidence: `false`
- Canonical desktop evidence: preserved from PR39C
- Session probe class: `WAYLAND_FAIL_X11_PASS`
- Wayland state: unresolved; X11 is the controlled VM alpha path
- Repeatability risk: still open for the latest hash until three attempts are recorded
- Plasma wallpaper state is seeded in `/etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc`, mirrored into `/etc/xdg`, and re-applied by a KDE autostart helper so the session cannot silently fall back to Breeze once the desktop starts.
- Presentation lock status: active in the latest observed Plasma session for SHA256 `ae023f8aeac29990799b22fb7b64af1f349a89be4b947021488318eb7eba9705`.
- Runtime presentation lock evidence requires `BWOS_PRESENTATION_LOCK_ACTIVE`; wallpaper evidence requires `BWOS_WALLPAPER_APPLIED`.
- A separate shutdown-probe rerun emitted `BWOS_SHUTDOWN_TELEMETRY_STARTED` but did not first emit the desktop marker, so it is preserved as shutdown-hook evidence but not clean shutdown validation.
