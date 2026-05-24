# Phoenix Assembly Brand Guide

Phoenix Assembly is the flagship identity for the Phoenix Core engine. It should feel
industrial, mythic, and precision-engineered.

## 1. Logos

| Asset | Description | Use |
| --- | --- | --- |
| `assets/brand/phoenix-assembly/phoenix_assembly_mark.svg` | Assembly mark (flame + anvil). | App icon, splash, boot screens. |
| `assets/brand/phoenix-assembly/phoenix_assembly_wordmark.svg` | Mark + wordmark. | Headers, landing pages, hero sections. |
| `assets/brand/phoenix-assembly/phoenix_assembly_mark_mono.svg` | Single-color mark. | Engraving, emboss, low-contrast. |
| `assets/brand/phoenix-assembly/phoenix_assembly_wordmark_mono.svg` | Single-color wordmark. | Internal docs, low-ink print. |

Minimum padding: 16px around all sides. Preserve aspect ratios.

## 2. Color Palette

| Role | Hex | Notes |
| --- | --- | --- |
| Assembly Black | `#0B0B0C` | Primary background, hardware panels. |
| Iron Gray | `#1C1E22` | Secondary surfaces, frames. |
| Ash White | `#F5F2EA` | Primary text on dark. |
| Ember Red | `#E63B2E` | Heat accents, warnings. |
| Plasma Orange | `#FF7A1A` | Action highlights, gradients. |
| Molten Gold | `#FFB020` | Signature glow and ring accents. |

Gradient: **Assembly Ember** `#E63B2E → #FF7A1A → #FFB020`

## 3. Typography

* Display: Orbitron SemiBold (fallback: Eurostile, BankGothic, Arial Black)
* Body: Inter Medium (fallback: Source Sans 3, Arial)

Keep headline tracking wide (6–12 units) for a forged, engineered feel.

## 4. Usage Guidance

1. Use the mark alone for icons or boot screens.
2. Use wordmark for docs and hero layouts.
3. Avoid thin strokes under 2px at 512px artboards.
4. Keep glow effects subtle: 4–8px blur at 60% opacity.

## 5. Tokens

Tokens live at:

```
assets/brand/phoenix-assembly/tokens.json
assets/brand/phoenix-assembly/tokens.css
```
