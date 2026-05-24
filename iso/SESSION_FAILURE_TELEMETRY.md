# Session Failure Telemetry

PR39F records where Home Aurelia session startup dies after the display-manager boundary.

## Markers

- `BWOS_SDDM_SERVICE_PRESTART`
- `BWOS_SDDM_AUTOLOGIN_CONFIGURED`
- `BWOS_SELECTED_SESSION_FILE=...`
- `BWOS_USER_PROVISIONING_OK`
- `BWOS_USER_PROVISIONING_FAIL`
- `BWOS_PLASMA_CONFIG_READABLE`
- `BWOS_AUTOSTART_MARKER_PRESENT`
- `BWOS_SESSION_LAUNCH_ATTEMPTED`
- `BWOS_WAYLAND_SESSION_ATTEMPTED`
- `BWOS_X11_SESSION_ATTEMPTED`
- `BWOS_KWIN_STARTED`
- `BWOS_KWIN_NOT_OBSERVED`
- `BWOS_PLASMASHELL_STARTED`
- `BWOS_PLASMASHELL_NOT_OBSERVED`
- `BWOS_WALLPAPER_APPLIED`
- `BWOS_DESKTOP_SESSION_STARTED`
- `BWOS_SHUTDOWN_TELEMETRY_STARTED`

## Profiles

- `wayland`: canonical Home Aurelia path.
- `x11`: controlled fallback probe only.

Wayland remains present even when X11 is tested. X11 success does not hide a Wayland failure; it records `WAYLAND_FAIL_X11_PASS` when that exact sequence is observed.

## Evidence

Each PR39F attempt records:

- exact artifact hash
- requested session profile
- selected SDDM session file
- actual session type from `XDG_SESSION_TYPE`
- actual SDDM session file observed in logs
- boot chain stages
- session launch markers
- wallpaper marker
- desktop marker
- shutdown marker
- console log
- serial log
- extracted session log

## PR39F Result

- Artifact hash: `fc57d42359f615fa7b5f101f3d058d6848138f739f6b201f0730a00af65246d8`
- Wayland-requested attempts selected `plasmawayland.desktop` in BWOS profile telemetry, but SDDM actually launched `plasma.desktop`.
- Actual session type observed: `x11`
- Controlled X11 fallback also reached the desktop marker.
- Desktop marker result: `3 / 3`
- Wallpaper marker result: `3 / 3`
- Shutdown marker result: `0 / 3`
- Probe class: `WAYLAND_FAIL_X11_PASS`

## Interpretation

Home Aurelia desktop startup is now deterministic for the observed X11 path, but Wayland is not proven. The next fix should either install/enable the missing Wayland session path correctly or temporarily promote X11 to the declared Home alpha session while keeping Wayland as a tracked blocker.

When normal boot output does not expose early kernel/initramfs text, the matrix records earlier boot stages from the later in-guest display/desktop marker. That is not a separate kernel log; it is a stage-chain normalization from direct in-guest evidence.

## Quality Rule

Display-manager reach is not desktop reach. Desktop success requires the real Plasma-session marker or `/run/bwos-desktop-reached`.
