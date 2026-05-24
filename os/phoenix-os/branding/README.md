# Blue Phoenix OS: Brand Visual Identity & Staging System

This directory acts as the authoritative repository of branding, theme tokens, and graphics configurations representing the seven target paths of the **Blue Phoenix OS / Bobby’s Worldwide OS (BWOS)** ecosystem.

---

## 🏛️ Branding Design System & Core Principles

All custom visual themes and boot-loaders reinforce the platform as a **premium desktop operating system with advanced recovery and diagnostic superpowers**, ensuring a truth-first user experience across all editions.

The platform architecture divides branding styles into seven target paths:

### 1. 🏡 HOME Edition
* **Color:** Sky Blue (`#0EA5E9`)
* **Tagline:** `"Calm. Friendly. For Everyone."`
* **Visuals:** Royal-blue body and wings with golden/amber chest trim. Calm, sunlit clouds and bright sunburst splash background.

### 🚑 2. REVIVAL Edition
* **Color:** Teal (`#14B8A6`)
* **Tagline:** `"Recovery. Rescue. Reborn."`
* **Visuals:** Blue phoenix nested inside a circular glowing teal energy aura loop.

### 🛡️ 3. RESILIENT Edition
* **Color:** Emerald Green (`#10B981`)
* **Tagline:** `"Security. Stability. Strength."`
* **Visuals:** Blue phoenix nested inside a green protective shield.

### 👑 4. AURELIA Edition
* **Color:** Aureate Gold (`#D97706`)
* **Tagline:** `"Create. Inspire. Illuminate."`
* **Visuals:** Blue phoenix wearing a majestic golden crown with Aureate Gold tail tips.

### ⚙️ 5. FORGE Edition
* **Color:** Ember Orange (`#F97316`)
* **Tagline:** `"Tools. Workflows. Mastery."`
* **Visuals:** Blue phoenix wearing a tech shield inside a heavy industrial steel cogwheel.

### ⚡ 6. THUNDERGOD Edition
* **Color:** Electric Blue & Violet (`#8B5CF6`)
* **Tagline:** `"Speed. Power. Unleashed."`
* **Visuals:** Blue phoenix wearing a purple storm crown, with electric violet lightning behind.

### 🌌 7. NATIVE OS (Flagship)
* **Color:** Phoenix Gold (`#D97706`)
* **Tagline:** `"Sovereign. Pure. Future-Ready."`
* **Visuals:** Blue phoenix standing on a golden compass ring star.

---

## 📂 Active Edition Structures

Every compiled edition configuration resides in the `/editions/` folder:
* **Manifests (`edition.yaml`):** Register name, tagline, target ISO, and package inclusion/exclusion profiles.
* **Palette (`colors.css`):** Predefined CSS/GTK variables mapping each edition's dynamic theme colors.
* **Branding (`branding.md`):** Explanatory documentation of active color schemes, boot logos, and wallpapers.

---

## 🚀 The Synthesis & Compilation Pipeline

Dynamic staging and packaging are fully automated:
1. **Asset Mapping:** Custom wallpapers and vector logos override standard boot-splashes (Plymouth) and login interfaces (SDDM) on-the-fly.
2. **Staging Orchestration:** [`scripts/build-edition.sh`](/scripts/build-edition.sh) automates the sandboxed directory injection.
3. **Master Synthesis:** [`scripts/build-all-isos.sh`](/scripts/build-all-isos.sh) orchestrates the sequential compilation and stores all produced final ISOs in:
   `/iso/outputs/`
