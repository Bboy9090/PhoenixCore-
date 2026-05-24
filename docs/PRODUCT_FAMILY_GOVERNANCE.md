# Phoenix OS Product Family Governance Policy

This document establishes the official product naming hierarchy, platform umbrellas, and structural architecture definitions of the **Bobby's Worldwide OS (BWOS)** ecosystem to prevent future naming sprawl and maintain architectural integrity.

---

## 🏛️ Platform Naming Hierarchy

To maintain complete clarity across public marketing, technical support, and structural engineering boundaries, the platform hierarchy is frozen into the following six structural tiers:

```text
├── [Public Studio]
│   └── Bobby’s World (The overarching creator space)
│
├── [Platform Umbrella]
│   └── Bobby’s Worldwide OS / BWOS (The foundational master distribution)
│
├── [Primary Consumer OS]
│   └── Blue Phoenix OS (The flagship desktop OS standard, expressed through a constrained edition lineup)
│
├── [Desktop Shell]
│   └── Citadel Desktop (The security-hardened, tailored graphical environment)
│
├── [Future Sovereign Branch]
│   └── Blue Phoenix Native (The hardware-targeted standalone build engine)
│
├── [Future Kernel]
│   └── Phoenix Prime Kernel (The audited custom execution core)
│
└── [Internal Engineering Spine]
    └── PhoenixCore- / phoenix-* crates / Phoenix Agent / BootForge (Core codebases)
```

The active BWOS / Blue Phoenix shipping edition set is intentionally constrained to:

- Home
- Thunder God
- Aurelia
- ARCWYRE
- Native as a research branch, not a shipping desktop line

Legacy concept names are archived and must not be treated as active product branches. See `docs/archive/retired-editions/` for the preserved historical notes.

---

## 🚫 Governance & Sprawl Prevention Rules

1. **No Mass Renaming:** The core internal package, build directory, and system IDs (`phoenix-core`, `phoenix-safety`, `phoenix-*` crates, and the repository root name `PhoenixCore-`) must remain locked. No branding alterations are allowed to cascade into internal codebase naming changes.
2. **No Repository Fragmentation:** Core utilities, the Tauri desktop framework, and live build packaging scripts must remain organized in a single mono-repository workspace.
3. **Truth-First App Menus:** Any application displayed in the active graphical environment menus must represent a real, fully operational utility meeting the standards of **PR33**. Placeholder/TODO launchers are blocked.
