# Phoenix OS GRUB Theme — Assets

Place the following files in this directory:

| File | Description | Dimensions |
|------|-------------|------------|
| `background.png` | Full-screen GRUB background | 1920×1080 (scaled by GRUB) |
| `select_c.png` | Selected menu item highlight (center) | 1×28 px, amber fill |
| `select_l.png` | Selected menu item highlight (left cap) | 8×28 px |
| `select_r.png` | Selected menu item highlight (right cap) | 8×28 px |

## Background spec
- Color: `#0D0F12` (Forge Black) with a subtle radial amber glow bottom-left
- Format: PNG, sRGB, no transparency (GRUB ignores alpha)
- Resolution: 1920×1080 minimum; GRUB scales it

## Generating a minimal background (command-line)
```bash
# Requires ImageMagick
convert -size 1920x1080 \
  radial-gradient:"#161005"-"#0D0F12" \
  -gravity SouthWest \
  live-build/includes.chroot/boot/grub/themes/phoenix/background.png
```

## Generating select highlight PNGs
```bash
# 8×28 left/right caps + 1×28 center fill
convert -size 8x28 xc:"#F58C1F" select_l.png
convert -size 8x28 xc:"#F58C1F" select_r.png
convert -size 1x28 xc:"#F58C1F" select_c.png
```
