# Shutdown Telemetry

Status: partial. Shutdown telemetry can fire, but clean shutdown is not verified.

## Current Home Artifact

- ISO: `bwos-home.iso`
- SHA256: `f113419abc4ad8c343cedb00a667e64fd13076f3c2ed87e658b63dea8059806d`
- Size: `2276358144` bytes

## Current Evidence

For the current Home hash:

- GRUB/display-manager boundary reached: `true`
- SDDM autologin configured: `true`
- selected session: `plasma.desktop`
- live user provisioning OK: `true`
- desktop marker reached: `false`
- wallpaper marker reached: `false`
- valid shutdown marker reached: `false`
- clean shutdown verified: `false`

Older desktop evidence for hash `4887e18f...` remains preserved, but it does not apply to the current rebuilt artifact.

## Interpretation

The current Home ISO proves SDDM prestart and live-user setup, but not Plasma desktop startup. Shutdown markers emitted while QEMU is being terminated after a failed desktop attempt are not valid clean-shutdown evidence and are now ignored by the VM matrix parser.

## Evidence Rule

Do not claim clean desktop shutdown until one attempt proves all of the following for the same artifact hash:

- bootloader reached
- kernel reached
- initramfs reached
- display manager reached
- desktop marker reached
- wallpaper marker reached
- shutdown marker reached from inside the confirmed desktop path
- QEMU exits cleanly without forced kill

## Next Probe

The next controlled probe should diagnose SDDM-to-Plasma session handoff before trying shutdown again. A shutdown probe is only meaningful after the desktop and wallpaper markers are observed in the same attempt.
