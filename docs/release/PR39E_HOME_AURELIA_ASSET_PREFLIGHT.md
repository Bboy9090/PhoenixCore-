# PR39E-A Home Aurelia Asset Tracking + Session Determinism Preflight

**Status:** in progress
**Scope:** Home family only

## Purpose

Confirm that the Home Aurelia visual identity is reproducible from tracked repository files and remains tied to the PR39E session determinism path.

This preflight does not replace PR39E. It proves the visual identity inputs are real build inputs, not local-only files.

## Tracked Home-Family Assets

The following Home-family visual assets are tracked in Git and consumed by the build:

- `editions/home/assets/home-background.png`
- `editions/home/assets/home-logo.png`
- `editions/home-arm64/assets/home-background.png`
- `editions/home-arm64/assets/home-logo.png`
- `editions/home-legacy-i386/assets/home-background.png`
- `editions/home-legacy-i386/assets/home-logo.png`

The Home-family declarative branding files are also part of the tracked build surface:

- `editions/home/edition.yaml`
- `editions/home/branding.md`
- `editions/home/colors.css`
- `editions/home/package-profile.txt`
- `editions/home-arm64/edition.yaml`
- `editions/home-arm64/branding.md`
- `editions/home-arm64/colors.css`
- `editions/home-arm64/package-profile.txt`
- `editions/home-legacy-i386/edition.yaml`
- `editions/home-legacy-i386/branding.md`
- `editions/home-legacy-i386/colors.css`
- `editions/home-legacy-i386/package-profile.txt`

## Manifest References

The Home-family manifests still point at stable internal paths:

- `editions/home/edition.yaml`
- `editions/home-arm64/edition.yaml`
- `editions/home-legacy-i386/edition.yaml`

These manifests continue to reference:

- `assets/home-logo.png`
- `assets/home-background.png`

No internal edition id or build path was renamed.

## Hooks Checked

The wallpaper/session path remains tied to the same stable internal build path:

- `os/phoenix-os/live-build/config/hooks/live/0072-pin-blue-phoenix-wallpaper.chroot`

Validation expectations:

- the hook names the Home Aurelia wallpaper helper in its user-facing marker strings
- the helper still stages and applies `/usr/share/images/desktop-base/desktop-background.png`
- the live session still relies on PR39E markers:
  - `BWOS_WALLPAPER_APPLIED`
  - `BWOS_DESKTOP_SESSION_STARTED`
  - `/run/bwos-wallpaper-applied`
  - `/run/bwos-desktop-reached`

## Intentionally Untracked Files

- None for the Home family asset set.

If a file remains untracked, it is a preflight failure unless it is explicitly documented as generated output.

## Remaining PR39E Tasks

- Rebuild Home only through the telemetry-aware pipeline.
- Run three VM attempts for Home Aurelia determinism.
- Record:
  - desktop reached
  - desktop marker reached
  - wallpaper marker reached
  - clean shutdown observed
  - screenshot path
  - serial log path
  - console log path
- Keep stronger desktop evidence canonical and preserve weaker reruns separately.

## Validation Commands

```bash
git status --short
bash -n os/phoenix-os/live-build/config/hooks/live/0072-pin-blue-phoenix-wallpaper.chroot
git diff --check
rg -n "Blue Phoenix: Home Edition|Calm\\. Friendly\\. For Everyone\\.|Sky Blue" editions/home editions/home-arm64 editions/home-legacy-i386 docs/HOME_AURELIA_VISUAL_IDENTITY.md docs/release/PR39E_SESSION_DETERMINISM.md iso/SESSION_DETERMINISM.md
```

## Quality Rule

A visual identity is not locked until its assets are tracked and reproducible from a clean checkout.
