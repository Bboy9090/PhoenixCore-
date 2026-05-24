# Phoenix OS Edition Governance Policy

This policy governs the creation, synchronization, and structural boundaries of **Bobby’s Worldwide OS (BWOS)** editions to prevent divergent edition-specific codebase forks.

---

## 🗺️ Approved Edition Registry

The system officially recognizes exactly five active edition profiles. No unauthorized active editions may be added without yaml manifest registration:

1. **`Home`:** The default, clean desktop suite for basic consumer usage.
2. **`Thunder God`:** The flagship performance edition for premium desktop and ARM64 showcase builds.
3. **`Aurelia`:** The pristine creator UX profile utilizing optimized system frameworks.
4. **`ARCWYRE`:** The high-integrity, power-user edition utilizing cyber-security and recovery overlays.
5. **`Native`:** The future sovereign hardware-targeted research and compiling pipeline.

Edition variants by architecture or artifact format are not separate editions. Examples include `home-arm64`, `home-legacy-i386`, and `thunder-god-arm64`.

---

## 🗃️ Retired Edition Concepts

Archived concept names are preserved in `docs/archive/retired-editions/` and may survive only as historical references or subsystem lineage. They are not active standalone editions.

---

## 🚫 Divergent Fork Prevention Rules

To keep the platform codebase maintainable and prevent duplicate logic from degrading security audits:

1. **One Core Codebase:**
   * Editions **must not** possess custom forks of the core Rust crates (`phoenix-core`), python helpers, or the React Citadel shell.
   * All editions compiled in the mono-repo must utilize the exact same compiled package binaries.
2. **No Duplicated Safety Systems:**
   * The **Phoenix Agent Capability Matrix** and standard PolicyKit escalation actions are global. 
   * An edition must inherit the core safety constraints. Custom "bypasses" or permissive overrides in specific edition manifests are strictly blocked.
3. **Branding Isolation:**
   * Edition customizations must be strictly limited to declarative manifest parameters (`colors.css`, static wallpapers, logo SVG paths, package list mappings) staged dynamically by the synthesis engine.
