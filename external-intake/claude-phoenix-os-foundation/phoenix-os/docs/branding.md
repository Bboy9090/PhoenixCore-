# Phoenix OS — Branding Guidelines

## Identity

Phoenix OS takes its name and visual identity from the mythological phoenix: a bird reborn from ash, associated with renewal, resilience, and fire. The brand communicates **precision under pressure** — tools that professionals trust when everything else has failed.

The brand is NOT consumer-friendly pastels and rounded corners. It is the visual language of professional instruments: measured, dark, purposeful, with a signature accent of amber-orange fire.

---

## Color Palette

### Primary Palette

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| Background | Forge Black | `#0D0F12` | App backgrounds, terminal |
| Surface | Ember Dark | `#161A1F` | Cards, panels, sidebars |
| Surface Raised | Ash Grey | `#1E2329` | Elevated surfaces, dialogs |
| Border | Graphite | `#2A2F38` | Dividers, input borders |
| Text Primary | Bone White | `#E8EAF0` | Primary content text |
| Text Secondary | Slate | `#8A929E` | Labels, metadata |
| Text Disabled | Cinder | `#4A515C` | Disabled states |

### Accent Palette

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| Primary Accent | Phoenix Amber | `#F58C1F` | Primary actions, links, progress |
| Accent Warm | Ember | `#E8641A` | Hover states, secondary accent |
| Accent Hot | Flame | `#D94215` | Destructive confirmation, warnings |
| Success | Forge Green | `#3DB882` | Operation success, disk health |
| Caution | Thermal Yellow | `#F5C842` | Warnings, low battery, degraded RAID |
| Danger | Critical Red | `#E03A3A` | Errors, imminent failure, data loss risk |
| Info | Tech Blue | `#4A90D9` | Informational states, network activity |

### Gradient: Phoenix Fire

The signature gradient used in boot splash, wallpapers, and hero elements:

```css
background: linear-gradient(135deg, #0D0F12 0%, #1A0F05 40%, #F58C1F 85%, #F5C842 100%);
```

Or as a radial burst for splash screens:

```css
background: radial-gradient(ellipse at 30% 70%, #F58C1F 0%, #D94215 25%, #1A0F05 55%, #0D0F12 100%);
```

---

## Typography

### Display: Rajdhani (headings, splash, branding)
- Weights: 500 (Medium), 600 (SemiBold), 700 (Bold)
- Used for: App titles, section headers, boot splash text, dialog titles
- Character: Technical, structured, slightly condensed — evokes instrumentation

### Body: IBM Plex Mono (monospace UI, data)
- Weights: 400 (Regular), 500 (Medium)
- Used for: Device paths, disk sizes, serial numbers, log output, terminal
- Character: Technical precision, professional tooling aesthetic

### Body Alt: Inter (non-technical prose)
- Weight: 400 (Regular), 500 (Medium)
- Used for: Descriptive text, onboarding copy, documentation UI
- Character: Neutral, readable, professional

All fonts are available via Google Fonts and should be bundled locally — Phoenix OS does not make external font calls.

---

## Logo

### Phoenix Mark
The Phoenix OS logo consists of:
- A stylized phoenix/flame mark (vector, to be designed)
- Wordmark: "PHOENIX OS" in Rajdhani SemiBold, letter-spacing: 0.15em
- Submark: "PHOENIX" alone for space-constrained contexts

### Clear Space
Minimum clear space around the logo: equal to the height of the "P" glyph on all sides.

### Usage Rules
- **Do:** Use on dark backgrounds (#0D0F12 or similar)
- **Do:** Use the amber (#F58C1F) mark on dark backgrounds
- **Do not:** Distort, rotate, or recolor the logo
- **Do not:** Place on busy photographic backgrounds without a backing panel
- **Do not:** Use the wordmark smaller than 14px cap height

### File Locations

```
branding/
├── boot-logo/
│   ├── phoenix-logo.svg          # Master vector
│   ├── phoenix-logo-white.svg    # White variant for dark backgrounds
│   └── phoenix-logo-64.png       # Boot splash raster (64px height)
├── icons/
│   ├── phoenix-icon-16.png
│   ├── phoenix-icon-32.png
│   ├── phoenix-icon-64.png
│   ├── phoenix-icon-128.png
│   └── phoenix-icon-256.png
```

---

## Wallpaper

### Default Wallpaper Concept

**"Forge"** — A dark abstract composition evoking a forge or ember: deep blacks transitioning to deep amber glows. Not photographic. Geometric/procedural aesthetic. High resolution (3840×2160 minimum, 16:9 and 16:10 variants).

File: `branding/wallpapers/phoenix-forge-3840x2160.png`

### Additional Wallpapers

| Name | Concept |
|------|---------|
| Schematic | Dark grid lines, PCB trace pattern, amber accent |
| Recovery | Abstract data stream, cool blue tones |
| Ember | Close-up ember/ash texture |

---

## KDE Plasma Theme

### Color Scheme File
Location: `packages/phoenix-theme/usr/share/color-schemes/PhoenixDark.colors`

Uses the primary palette defined above. Ships as a `.colors` file in KDE format.

### Application Style
Kvantum theme (SVG-based Qt styling): `packages/phoenix-theme/usr/share/Kvantum/PhoenixOS/`

### Widget Style
Breeze Dark as base, with Phoenix color overrides.

### Icons
Based on Papirus Dark icon theme with Phoenix amber folder color override.

---

## Plymouth Boot Splash

The Plymouth theme is located at: `branding/plymouth/phoenix/`

Animation concept: A phoenix silhouette assembles from scattered embers, accompanied by a progress bar in amber. The animation is implemented as a `script` theme for maximum compatibility (no video codec dependency).

Key files:
- `phoenix.plymouth` — theme descriptor
- `phoenix.script` — animation script
- `background.png` — static fallback

---

## SDDM Login Screen

Location: `branding/sddm-theme/`

Design: Dark background with the Phoenix fire gradient subtly visible behind a centered login panel. The panel uses Forge Black background with Graphite borders. The Phoenix logo sits above the username/password fields.

---

## GRUB Boot Menu

The GRUB theme is located at: `live-build/includes.chroot/boot/grub/themes/phoenix/`

Design: Minimal dark GRUB theme. Phoenix wordmark in Bone White. Menu entries in Bone White, selected entry highlighted in Phoenix Amber. Background matches the splash aesthetic.

---

## Voice and Tone

Phoenix OS communications (UI copy, error messages, documentation) follow these principles:

- **Direct.** Not flowery. "Scan complete. 3 issues found." Not "We've finished scanning your disk and found some things you might want to look at!"
- **Precise.** Use correct technical terminology. Repair professionals know what a sector is.
- **Calm under pressure.** Error messages should de-escalate, not alarm. Explain what happened, what it means, what the user can do.
- **Respectful of expertise.** Don't over-explain. Give experts the data; give novices the guided path.
