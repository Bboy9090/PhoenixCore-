# Repository Consolidation Plan

This document outlines the migration from the current "PhoenixCore-" structure to the unified **Bobby’s Worldwide OS (BWOS)** platform structure.

## 1. Future Directory Structure

The repository will be reorganized into the following top-level domains:

```text
/
├── core/                   # The BWOS Core (Shared Intelligence)
│   ├── agent/             # Rust-based hardware agent
│   ├── control-center/    # The consolidated UI (React/Tauri)
│   ├── bootforge/         # Imaging engine logic
│   └── shared/            # Cross-platform Rust crates & schemas
├── native/                 # ARCWYRE Native / BWOS Native
│   ├── kernel/            # Custom kernel source
│   ├── boot/              # UEFI bootloader
│   └── userland/          # Sovereign userland components
├── editions/               # Visual Profiles & Branding
│   ├── thunder-god/       # Heroic Theme
│   ├── arcwyre/           # Cyber-Recovery Theme
│   ├── forge/             # Technician Theme
│   └── blue-phoenix/      # Classic Legacy Theme
├── iso/                    # Build & Distribution
│   ├── builder/           # Python/Shell build scripts
│   ├── live-build/        # Linux ISO configuration
│   └── profiles/          # Edition-specific build targets
└── docs/                   # Unified Documentation
```

---

## 2. Component Mapping (From Phoenix -> BWOS)

| Current Path | New Domain | Note |
| :--- | :--- | :--- |
| `apps/phoenix-control-center` | `core/control-center` | Internal branding remains "Phoenix" for build stability. |
| `crates/phoenix-*` | `core/shared` | Core logic shared across all editions. |
| `os/phoenix-os/live-build` | `iso/live-build` | Base for generating BWOS ISOs. |
| `src/gui` | `core/control-center` | Merge legacy GUI features into the web-based CC. |
| `src/recovery`, `src/imaging`| `core/bootforge` | Consolidation of imaging primitives. |

---

## 3. Migration Phases

### Phase A: Strategic Documentation (Current)
- Define the Edition Model and Master PRD.
- Establish the `edition.yaml` manifest format.
- **Goal**: Unified architectural vision.

### Phase B: Structural Pre-Wiring
- Create the new directory structure.
- **Move Only** non-code assets (Docs, Templates, Manifests).
- **Goal**: Clean organization without breaking builds.

### Phase C: Logic Consolidation
- Port remaining Python-based recovery logic to the Rust Agent.
- Establish the shared `core/shared` crates as the "Source of Truth."
- **Goal**: Single execution spine for all editions.

### Phase D: Brand & Edition Synthesis
- Implement the Edition Builder scripts.
- Generate the first "Thunder God" and "Blue Phoenix" ISOs.
- **Goal**: Multi-edition production capabilities.

---

## 4. Risks & Mitigations

- **Risk**: Path breakage in CI/CD.
- **Mitigation**: Use symlinks during the transition and update paths iteratively.
- **Risk**: Identity loss for existing users.
- **Mitigation**: The "Blue Phoenix" edition preserves the original brand's look and feel while running on the modern BWOS Core.
