# Home Aurelia Visual Identity

Canonical public name:
- `Home Aurelia OS`

Canonical tagline:
- `Four Legacies. One Throne.`

This document locks the Home-family alpha presentation layer without changing internal edition ids, package ids, service ids, build ids, or build paths. The lock is intentionally narrow: it governs KDE presentation, Plymouth, SDDM, wallpaper, icon inheritance, splash assets, and taskbar/menu accents while PR39E/PR39I session determinism remains the engineering gate.

## Identity Rules

- Dark navy and black are the base.
- Electric blue is the primary active highlight.
- Gold is restrained trim, not the dominant field color.
- The blue phoenix / Aurelia crest is the central symbol.
- Storm energy accents are allowed only where they stay readable.
- The desktop must remain practical for daily use.
- Native remains research-only and must not become a shipping identity through this lock.

## Controlled Integration Paths

| Layer | Canonical Path | Status | Evidence Rule |
| --- | --- | --- | --- |
| KDE shell | `/usr/share/color-schemes/HomeAurelia.colors`, `/etc/skel/.config/kdeglobals` | staged by hook | Valid only after Plasma starts and keeps the seeded state |
| Plymouth | `/usr/share/plymouth/themes/phoenix` | staged by build overlay | Valid only when the built ISO contains the staged theme |
| SDDM | `/usr/share/sddm/themes/phoenix` | staged by build overlay | Display-manager reach is not desktop success |
| Wallpaper | `/usr/share/images/desktop-base/desktop-background.png` | staged and pinned | Valid only when `BWOS_WALLPAPER_APPLIED` fires |
| Icon pack | `/usr/share/icons/home-aurelia` | inherited Breeze coverage with Home Aurelia crest overrides | Valid only as controlled alpha layer, not a complete custom icon suite |
| Splash assets | Plymouth and SDDM phoenix theme assets | staged by build overlay | Must not be confused with desktop wallpaper state |
| Taskbar/menu accents | HomeAurelia KDE color scheme | seeded through `/etc/skel` and `/etc/xdg` | Valid only after session marker evidence |

## Canonical Asset Groups

### Splash Set

- Home: `editions/home/assets/home-background.png`
- Aurelia: `editions/blue-phoenix/assets/blue-horizon.png`
- ARCWYRE: `editions/arcwyre/assets/circuit-grid.png`
- Thunder God: `editions/thunder-god/assets/storm-peak.png`
- Native: research / coming-soon presentation only

### Icon Set

The Home icon set is treated as a locked daily-use target, not an active promise that every icon has bespoke artwork yet. Until every icon asset exists, the `home-aurelia` icon theme inherits Breeze/Hicolor and only overrides controlled crest targets.

- Home
- Documents
- Downloads
- Music
- Pictures
- Videos
- Trash
- Settings
- System
- Terminal
- Software
- Files
- Browser
- Mail
- Calendar
- Calculator
- Text Editor
- Help
- Drive
- Network
- Bluetooth
- Firewall
- User
- Power

### Plymouth Set

- Home Aurelia main blue phoenix
- ARCWYRE red-blue storm variant
- Thunder God white-blue storm variant
- Native locked / research variant

### Wallpaper Set

- Home Aurelia royal blue sky guardian
- ARCWYRE dark storm rebellion
- Thunder God divine stormbringer
- Native ancestral research variant

### KDE Shell

- Dark navy / black base
- Gold borders and separators
- Electric-blue active/focus/selection states
- Phoenix launcher/menu emblem via controlled icon-theme override
- Restrained taskbar/menu accents through the HomeAurelia color scheme

## Engineering Integration

- The presentation lock is staged by `os/phoenix-os/live-build/config/hooks/live/0066-home-aurelia-presentation-lock.chroot`.
- The Home wallpaper is staged through the edition manifest and copied into the live image as `/usr/share/images/desktop-base/desktop-background.png`.
- The current Home wallpaper source is synchronized from `os/phoenix-os/branding/wallpaper.png` so the edition asset, live-image asset, and shared branding baseline stay visually aligned.
- Plasma wallpaper state is seeded through `/etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc`, mirrored into `/etc/xdg`, and re-applied by the session helper.
- SDDM and desktop wallpaper are separate layers.
- Plymouth splash and desktop wallpaper are separate layers.
- KDE shell colors and icon inheritance are seeded separately from wallpaper state.
- Wallpaper selection is only considered valid after the session-start marker and wallpaper marker fire.

## Evidence Gates

- `BWOS_DESKTOP_SESSION_STARTED` or `/run/bwos-desktop-reached` proves a real desktop session marker.
- `BWOS_PRESENTATION_LOCK_ACTIVE` or `/run/bwos-presentation-lock-active` proves the session saw the seeded presentation lock metadata, KDE color scheme, and inherited icon theme.
- `BWOS_WALLPAPER_APPLIED` or `/run/bwos-wallpaper-applied` proves the wallpaper helper ran.
- Display-manager reach alone does not prove the Home Aurelia desktop.
- Asset existence alone does not prove the theme is active.
- No artifact is release candidate until boot repeatability and shutdown evidence pass.

## Non-Goals

- No new editions.
- No internal id, package id, service id, Tauri id, or build path renames.
- No branding redesign outside this locked direction.
- No replacement of boot/session determinism work with style work.
- No claim that the icon pack is complete until individual icon assets are tracked and boot evidence confirms they load.
