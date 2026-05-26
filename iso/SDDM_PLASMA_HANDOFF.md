# SDDM to Plasma Handoff

Status: X11 handoff proven for the current Home hash. Clean shutdown and repeatability remain unproven.

## Problem

Home reaches SDDM/autologin prestart but does not emit the real Plasma desktop marker. Display-manager reachability is not desktop reachability.

## Required Evidence

A successful handoff requires observing the same artifact hash reach:

- SDDM service active
- autologin configured for `phoenix`
- selected session file exists
- session `Exec=` target exists
- `loginctl` session for `phoenix`
- user DBus/session runtime is present
- `startplasma-x11` or `startplasma-wayland` attempts to run
- KWin starts
- `plasmashell` starts
- `BWOS_DESKTOP_SESSION_STARTED` fires
- `BWOS_WALLPAPER_APPLIED` fires

## Current Evidence

The current Home artifact has reached the required X11 desktop-session evidence once:

- Artifact: `os/phoenix-os/build/bwos-home.iso`
- SHA256: `ae023f8aeac29990799b22fb7b64af1f349a89be4b947021488318eb7eba9705`
- Attempt: `PR39I-HOME-AURELIA-PRESENTATION-LOCK`
- Evidence: `iso/outputs/vm-boot-evidence/home/20260525T062057Z`
- Session: `x11`
- Selected session file: `plasma.desktop`
- KWin: `kwin_x11`
- Plasma shell: started
- Desktop marker: reached
- Wallpaper marker: reached
- Home Aurelia presentation lock marker: reached
- Clean shutdown: not verified

This is a desktop reachability pass for the exact hash above, not a release-candidate pass.

## Shutdown Probe Note

The follow-up shutdown probe for the same hash recorded `bwos.shutdown_probe=1` and emitted `BWOS_SHUTDOWN_TELEMETRY_STARTED` in the serial log, but it did not emit the desktop marker in that same attempt.

- Attempt: `PR39J-HOME-X11-SHUTDOWN-PROBE`
- Evidence: `iso/outputs/vm-boot-evidence/home/20260525T064624Z`
- Same-attempt desktop plus shutdown proof: `false`

This is useful shutdown-hook evidence, but it is not clean shutdown validation.

## VM Alpha Policy

X11 is canonical for VM alpha until Home desktop repeatability and clean shutdown are proven. Wayland remains available as an experimental profile.

## Failure Classification

Use the trace to classify the failing layer:

- `DISPLAY_MANAGER_FAIL`: SDDM does not become active or cannot autologin.
- `SESSION_CONFIG_FAIL`: session file or session executable is missing.
- `USER_PROVISIONING_FAIL`: `phoenix` user or home is invalid.
- `PAM_OR_LOGINCTL_FAIL`: no `phoenix` session appears in `loginctl`.
- `XDG_RUNTIME_FAIL`: session exists but `XDG_RUNTIME_DIR` or user runtime is missing.
- `DBUS_SESSION_FAIL`: user session exists but DBus is missing.
- `STARTPLASMA_FAIL`: SDDM starts the session but `startplasma-*` does not persist.
- `KWIN_FAIL`: KWin never starts.
- `PLASMASHELL_FAIL`: KWin starts but `plasmashell` does not.
- `MARKER_HOOK_FAIL`: Plasma starts but marker/autostart does not run.

## Evidence Rule

Do not update canonical boot status to desktop pass unless the actual desktop marker fires. Login prompt, SDDM boundary, or graphical target markers are insufficient.
