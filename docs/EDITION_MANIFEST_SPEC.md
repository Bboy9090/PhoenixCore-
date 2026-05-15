# Edition Manifest Specification (edition.yaml)

This document defines the schema for the ARCWYRE/BWOS Edition Manifests. An edition manifest is a declarative configuration file that tells the build system how to skin and package a specific variant of Bobby’s Worldwide OS.

## 1. Schema Overview

```yaml
id: "unique-slug"
display_name: "The Full Human Name"
parent: "Bobby’s Worldwide OS"
version: "1.0.0"

# Visual Identity
theme:
  colors:
    primary: "#HEX"
    secondary: "#HEX"
    accent: "#HEX"
    background: "#HEX"
    surface: "#HEX"
  assets:
    logo_path: "@/assets/editions/slug/logo.svg"
    wallpaper: "@/assets/editions/slug/wallpaper.png"
    boot_splash: "@/assets/editions/slug/splash.png"

# Control Center Configuration
control_center:
  skin: "default" | "minimal" | "technician"
  default_tab: "forge" | "diagnostics" | "settings"

# Package Selection
packages:
  include:
    - "bwos-core"
    - "bootforge"
    - "custom-pkg-1"
  exclude: []

# Safety Rules (Always Inherited from Core)
safety:
  inherit_core_rules: true
  enforce_audit_logging: true

# Metadata
tagline: "Marketing short text"
description: "Long form description of this edition's purpose."
```

---

## 2. Implementation Logic

1.  **CSS Variable Injection**: The `theme.colors` are injected into `index.css` or `theme-tokens.css` during the build process, allowing the UI to adapt instantly.
2.  **Asset Linking**: The build script symlinks edition-specific assets into the distribution folder.
3.  **Package Profiling**: The ISO builder reads the `packages` list to determine which `.deb` or binary components to include in the squashfs image.

---

## 3. Example: Thunder God Edition

```yaml
id: thunder-god
display_name: "Bobby’s Worldwide OS: Thunder God Edition"
theme:
  colors:
    primary: "#62E8FF" # Electric Cyan
    secondary: "#FFD34D" # Thunder Gold
    accent: "#C8332D" # Hero Red
    background: "#080B10" # Storm Black
    surface: "#121820"
tagline: "Power the broken. Restore the world."
```

---

## 4. Location in Repository

All manifests should be stored in:
`editions/<id>/edition.yaml`
