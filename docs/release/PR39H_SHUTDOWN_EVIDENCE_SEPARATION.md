# PR39H Shutdown Evidence Separation

Status: PASS for evidence-model hardening. Home clean shutdown remains unverified.

## Goal

Prevent boot matrix rows from implying that desktop reachability, wallpaper activation, and shutdown telemetry occurred in the same VM boot attempt when they were observed in separate attempts or during forced VM termination.

## Scope

This PR hardened the evidence model and ran one Home-only guarded shutdown probe after a Home rebuild. It does not mark any artifact release-ready.

## Active Home Artifact

Current Home artifact:

- ISO: `bwos-home.iso`
- SHA256: `f113419abc4ad8c343cedb00a667e64fd13076f3c2ed87e658b63dea8059806d`
- Size: `2276358144` bytes
- Build result: successful
- Canonical class for this hash: `BOOT_FAIL_DISPLAY`

Previous stronger desktop evidence remains preserved for older hash `4887e18fa3a6ee6b96637569be1591c13d037612fe5f5e45441c5233b2d0c75d`, but it is not transferred to the new hash.

## New Probe Result

Attempt: `PR39H-X11-GUARDED-SHUTDOWN-PROBE`

Observed for `f113419a...`:

- GRUB reached: `true`
- kernel inferred reachable: `true`
- initramfs inferred reachable: `true`
- SDDM/autologin prestart reached: `true`
- selected session: `plasma.desktop`
- X11 profile selected: `true`
- live user provisioning OK: `true`
- Plasma desktop marker: `false`
- wallpaper marker: `false`
- clean shutdown verified: `false`

Interpretation: SDDM reaches the graphical/login boundary, but the KDE session does not start far enough to execute the desktop autostart marker.

## Change Summary

- Added canonical-attempt reconstruction from attempt logs.
- Added attempt-count fields for desktop, wallpaper, shutdown marker, and clean shutdown evidence.
- Added same-attempt fields so clean desktop shutdown evidence cannot be inferred from separate runs.
- Stopped merging row-level marker booleans across unrelated attempts.
- Preserved the older Home output ISO under `iso/outputs/archive/` before promoting the new Home ISO.
- Added `BWOS_KERNEL_CMDLINE` logging to the pre-SDDM session profile service for future rebuilds.
- Hardened VM parsing so shutdown markers emitted during forced QEMU termination are not counted as valid shutdown evidence.
- Regenerated boot matrix and artifact registry from current artifacts and existing evidence.

## Evidence Policy

Canonical fields describe the strongest observed attempt for the exact artifact hash.

Aggregate fields describe all attempts for that exact artifact hash:

- `desktop_marker_attempt_count`
- `wallpaper_marker_attempt_count`
- `shutdown_marker_attempt_count`
- `clean_shutdown_attempt_count`
- `desktop_shutdown_same_attempt`
- `desktop_wallpaper_shutdown_same_attempt`

A row must not be interpreted as clean desktop shutdown unless same-attempt evidence is true and clean shutdown is verified.

## Current Result

For the Home hash `f113419a...`:

- SDDM/autologin prestart is proven.
- X11 profile selection is proven.
- User provisioning is proven.
- Plasma desktop marker is not proven.
- Home Aurelia wallpaper marker is not proven.
- Shutdown marker from forced VM termination is ignored.
- Clean shutdown is not verified.
- Release-candidate status remains blocked.

## Remaining Risk

The active blocker is no longer GRUB, kernel, initramfs, or asset staging. The blocker is KDE session startup after SDDM/autologin. The next pass must inspect why the Plasma autostart marker never runs.

## Recommended Next Move

PR39I should focus on SDDM to Plasma session handoff:

1. Extract SDDM and Xorg logs earlier, before shutdown timeout.
2. Verify whether SDDM actually starts `plasma.desktop` for user `phoenix`.
3. Capture `/home/phoenix/.local/share/sddm/` and `.xsession-errors` reliably.
4. Test a minimal X11 session marker outside Plasma to separate SDDM autologin failure from Plasma startup failure.
5. Rebuild Home only after the pre-SDDM cmdline logger is included.
6. Preserve all evidence by exact artifact hash.
