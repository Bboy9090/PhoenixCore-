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

## Required Markers

- `BWOS_DESKTOP_SESSION_STARTED`
- `/run/bwos-desktop-reached`
- `BWOS_SHUTDOWN_TELEMETRY_STARTED`
- `/run/bwos-shutdown-started`

## Rules

- Stronger evidence remains canonical.
- Weaker reruns stay as separate attempts.
- Display-manager reach alone is not desktop success.
- Shutdown is only clean when telemetry proves it.

## Current Status

- Home session determinism attempts: recorded for current Home hash `fc57d42359f615fa7b5f101f3d058d6848138f739f6b201f0730a00af65246d8`
- Current repeatability result: `PASS` for the observed X11 session path
- Current desktop marker count: `3 / 3`
- Current wallpaper marker count: `3 / 3`
- Current shutdown telemetry count: `0 / 3`
- Current clean shutdown evidence: `false`
- Canonical desktop evidence: preserved from PR39C
- Session probe class: `WAYLAND_FAIL_X11_PASS`
- Wayland state: requested but not actually launched in VM evidence; SDDM selected `plasma.desktop` and `XDG_SESSION_TYPE=x11`
- Repeatability risk: `false` for desktop/wallpaper markers on the rebuilt hash; release remains blocked by shutdown evidence and unresolved Wayland canonicality
- Plasma wallpaper state is seeded in `/etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc`, mirrored into `/etc/xdg`, and re-applied by a KDE autostart helper so the session cannot silently fall back to Breeze once the desktop starts.
