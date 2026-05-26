# PR39I Home Aurelia Presentation Lock

**Status:** VM evidence captured, shutdown still unverified  
**Scope:** Home presentation layer only

## Goal

Lock Home Aurelia as the canonical alpha presentation layer without changing internal edition ids, build ids, service ids, package ids, artifact names, or active edition scope.

## Canonical Identity

- Public name: `Home Aurelia OS`
- Tagline: `Four Legacies. One Throne.`
- Base: dark navy / black
- Primary highlight: electric blue
- Trim: restrained royal gold
- Symbol: blue phoenix / Aurelia crest
- Tone: premium fantasy-tech, readable for daily desktop use

## Controlled Infrastructure Paths

| Layer | Path | Implementation Status |
| --- | --- | --- |
| KDE shell | `/usr/share/color-schemes/HomeAurelia.colors` and `/etc/skel/.config/kdeglobals` | staged by `0066-home-aurelia-presentation-lock.chroot` |
| Plymouth | `/usr/share/plymouth/themes/phoenix` | staged by edition overlay and selected by `0050-set-plymouth-theme.chroot` |
| SDDM | `/usr/share/sddm/themes/phoenix` | staged by edition overlay and selected by `0060-set-sddm-theme.chroot` |
| Wallpaper | `/usr/share/images/desktop-base/desktop-background.png` | staged from the Home manifest and pinned by Plasma hooks |
| Icon pack | `/usr/share/icons/home-aurelia` | inherited Breeze/Hicolor coverage with crest overrides |
| Splash assets | Plymouth and SDDM phoenix assets | controlled by the existing build overlay path |
| Taskbar/menu accents | HomeAurelia KDE color scheme | seeded through `/etc/skel` and `/etc/xdg` |

## Files Changed

- `docs/HOME_AURELIA_VISUAL_IDENTITY.md`
- `docs/release/PR39E_SESSION_DETERMINISM.md`
- `iso/SESSION_DETERMINISM.md`
- `os/phoenix-os/live-build/config/hooks/live/0066-home-aurelia-presentation-lock.chroot`
- `os/phoenix-os/branding/plymouth/phoenix/phoenix.plymouth`
- `os/phoenix-os/branding/sddm/phoenix/metadata.desktop`

## Evidence Policy

This lock is not a boot pass and not a release candidate signal.

The Home Aurelia desktop is considered active only when a tested artifact records:

- `BWOS_DESKTOP_SESSION_STARTED` or `/run/bwos-desktop-reached`
- `BWOS_PRESENTATION_LOCK_ACTIVE` or `/run/bwos-presentation-lock-active`
- `BWOS_WALLPAPER_APPLIED` or `/run/bwos-wallpaper-applied`
- matching artifact SHA256 in the boot matrix
- no weaker rerun overwriting stronger prior evidence

## Current Artifact Evidence

A Home ISO rebuild completed after staging `0066-home-aurelia-presentation-lock.chroot`:

- Artifact: `os/phoenix-os/build/bwos-home.iso`
- SHA256: `ae023f8aeac29990799b22fb7b64af1f349a89be4b947021488318eb7eba9705`
- Size: `2276372480` bytes
- Build result: completed

PR39I probe evidence:

- Attempt: `PR39I-HOME-AURELIA-PRESENTATION-LOCK`
- Timestamp: `2026-05-25T06:20:57Z`
- VM tool: `qemu-system-x86_64`
- EFI: enabled
- Secure Boot: disabled
- Session profile: `x11`
- Selected session: `plasma.desktop`
- Result stage: `BOOT_PASS_DESKTOP`
- Desktop marker: `true`
- Wallpaper marker: `true`
- Presentation lock marker: `true`
- Clean shutdown verified: `false`
- Evidence directory: `iso/outputs/vm-boot-evidence/home/20260525T062057Z`

Observed markers:

- `BWOS_DESKTOP_SESSION_STARTED`
- `BWOS_PRESENTATION_LOCK_ACTIVE`
- `BWOS_WALLPAPER_APPLIED`

This proves the Home Aurelia presentation layer can load in the live Plasma session for this exact artifact hash. It does not prove release readiness because clean shutdown is still unverified and repeatability has not yet been established for this new hash.

## Remaining Risks

- The inherited icon theme is an alpha presentation path, not a complete custom icon suite.
- Clean shutdown remains a separate release blocker.
- Repeatability remains unproven for SHA256 `ae023f8aeac29990799b22fb7b64af1f349a89be4b947021488318eb7eba9705`.
- Wayland remains unresolved; X11 is the controlled VM alpha session path until evidence changes.
