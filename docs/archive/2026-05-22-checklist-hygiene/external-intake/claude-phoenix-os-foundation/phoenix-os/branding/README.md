# Phoenix OS — Branding Assets

This directory contains all visual identity assets for Phoenix OS.
See `docs/branding.md` for the full design system specification.

## Directory Contents

```
branding/
├── wallpapers/         PNG wallpapers (3840×2160 primary, 1920×1080 minimum)
├── icons/              Phoenix OS icon set (PNG, 16–256px + SVG master)
├── boot-logo/          Boot splash logo files (SVG master + raster exports)
├── plymouth/           Plymouth boot animation theme
└── sddm-theme/         SDDM login screen QML theme
```

## Asset Status

| Asset | Status | Notes |
|-------|--------|-------|
| Logo SVG (master) | ⬜ Needed | Vector source for all logo exports |
| Logo PNG (boot, 64px height) | ⬜ Needed | For Plymouth splash |
| Logo PNG (installer sidebar) | ⬜ Needed | 160px wide, for Calamares |
| Icon set (16–256px) | ⬜ Needed | App icon for all Phoenix apps |
| Wallpaper "Forge" (3840×2160) | ⬜ Needed | Primary desktop wallpaper |
| Wallpaper "Schematic" | ⬜ Needed | Alternative wallpaper |
| Plymouth script | ✅ Done | See plymouth/phoenix.script |
| Plymouth PNG assets | ⬜ Needed | Ember particle, logo rasters |
| SDDM theme QML | ✅ Done | See sddm-theme/Main.qml |
| KDE color scheme | ✅ Done | See packages/phoenix-theme/ |

## Asset Requirements

### Wallpapers
- Format: PNG (lossless)
- Primary resolution: 3840×2160 (16:9)
- Additional: 2560×1600 (16:10) for ThinkPad/Dell displays
- Color space: sRGB
- No transparency

### Icons
- Format: PNG exports + SVG master
- Sizes: 16, 22, 32, 48, 64, 128, 256 px
- Design: Flat/semi-flat, works on dark backgrounds
- The phoenix/flame mark, not the wordmark

### Boot Logo (Plymouth)
- Required files in branding/plymouth/:
  - `phoenix-logo-boot.png` — white logo, transparent background, 200px wide
  - `ember-particle.png`   — small (16×16) ember dot for particle effects
  - `background.png`       — optional static fallback (1920×1080, Forge Black)

## Exporting from Figma/Inkscape

When exporting PNG from SVG source:
```bash
# Using Inkscape CLI
inkscape --export-type=png --export-width=256 --export-filename=phoenix-icon-256.png phoenix-logo.svg

# Batch export all icon sizes
for size in 16 22 32 48 64 128 256; do
    inkscape --export-type=png --export-width=${size} \
        --export-filename=icons/phoenix-icon-${size}.png \
        boot-logo/phoenix-logo.svg
done
```
