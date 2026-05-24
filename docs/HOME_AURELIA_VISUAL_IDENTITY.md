# Home Aurelia Visual Identity

Canonical public name:
- `Home Aurelia OS`

Canonical tagline:
- `Four Legacies. One Throne.`

This document locks the Home-family visual direction without changing the internal edition id or build paths. The goal is to keep the Home desktop readable for daily use while aligning it to the premium Blue Phoenix / Aurelia direction used across the platform.

## Identity Rules

- Dark navy and black are the base.
- Electric blue is the primary active highlight.
- Gold is restrained and used as trim, not as the dominant field color.
- The blue phoenix emblem remains the central symbol.
- Storm energy accents are allowed, but they must stay controlled and legible.
- The desktop must remain practical for daily use, not just decorative.

## Canonical Asset Groups

### Splash Set

- Home: `editions/home/assets/home-background.png`
- Aurelia: `editions/blue-phoenix/assets/blue-horizon.png`
- ARCWYRE: `editions/arcwyre/assets/circuit-grid.png`
- Thunder God: `editions/thunder-god/assets/storm-peak.png`
- Native: research / coming-soon staging only

### Icon Set

The Home icon set is treated as a locked daily-use suite rather than a rotating art experiment:

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
- Gold borders
- Electric-blue active states
- Phoenix launcher emblem
- Glowing but restrained taskbar accents

## Engineering Integration

- The Home wallpaper is staged through the edition manifest and copied into the live image as `/usr/share/images/desktop-base/desktop-background.png`.
- The current Home wallpaper source is synchronized from `os/phoenix-os/branding/wallpaper.png` so the edition asset, the live-image asset, and the shared branding baseline stay visually aligned.
- Plasma wallpaper state is seeded through `/etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc` and mirrored into `/etc/xdg`.
- SDDM and desktop wallpaper are separate layers.
- Plymouth splash and desktop wallpaper are separate layers.
- Wallpaper selection is only considered valid after the session-start marker fires.

## Session Determinism Priority

PR39E remains the engineering priority. Visual identity only becomes canonical once the live Plasma session starts deterministically and the wallpaper marker is observed.

## Non-Goals

- No new editions.
- No renames of internal ids, package ids, or build paths.
- No branding churn outside the Home family.
- No replacement of boot/session work with style work.
