# Bobby’s Worldwide OS: Platform Edition Model

## 1. The Strategy: One Platform, Multiple Editions

Bobby’s Worldwide OS (BWOS) is no longer a collection of separate operating systems. It is a single, high-integrity operating-system platform designed for machine recovery, repair, and creator workflows.

Instead of building "Phoenix OS," "ARCWYRE OS," and "Thunder God OS" as competing entities, we now build **one core** with multiple **Editions**.

> **Bobby’s Worldwide OS is the platform. Thunder God, ARCWYRE, Forge, and future variants are editions built from the same core OS, same safety model, same recovery spine, and same development roadmap.**

---

## 2. Core vs. Edition

### The BWOS Core (The "Immutable Spine")
The Core represents the non-negotiable engineering foundation of the system.
- **BWOS Core**: Shared recovery logic, kernel track, and platform primitives.
- **BWOS Agent**: Privileged hardware bridge and safety gating.
- **BWOS Control Center**: The universal management engine.
- **BootForge Engine**: High-performance imaging and USB creation.
- **Safety Model**: Immutable disk safety rules and audit logging.

**Editions are NOT permitted to modify the Core's safety or recovery logic.**

### The Edition Layer (The "Vibe & Profile")
An Edition is a specific profile that configures the visual identity and package selection of the platform.
- **Branding**: Name, logo, color palette, wallpapers.
- **Theming**: Boot splash, lock screen, desktop/terminal themes.
- **Packages**: Pre-selected tools and app presets (e.g., Forge vs. Creator).
- **User Experience**: Welcome screens, installer branding, and dashboard skins.

---

## 3. Current Edition Lineup

| Edition | Persona | Visual Identity |
| :--- | :--- | :--- |
| **Thunder God** | The Heroic Desktop | Storm Black, Electric Cyan, Thunder Gold, Hero Red. |
| **ARCWYRE** | The Cyber-Recovery | Cyber Black, Circuit Cyan, Metallic Silver. |
| **Forge** | The Technician's Tool | Industrial Grey, Hazard Orange, Steel Blue. |
| **Blue Phoenix** | The Classic Legacy | Royal Blue, Pure White, Sky Blue (Original UI). |
| **Native Preview** | The Sovereign Track | Minimalist, Kernel-first, Debug-centric. |

---

## 4. Development Workflow

1.  **Core Development**: All logic fixes, driver support, and safety improvements happen in `core/`.
2.  **Edition Creation**: Editions are defined via a manifest file (`edition.yaml`) that references shared assets and package lists.
3.  **ISO Synthesis**: The ISO builder reads the selected edition manifest and assembles the final image using the shared BWOS Core.

---

## 5. Architectural Law

- **Shared Maintenance**: One bug fix in the Agent fixes it for every edition.
- **Safety First**: An edition cannot "opt-out" of hardware safety gates.
- **Zero Confusion**: No more "which repo am I in?". You are in the Bobby’s Worldwide OS repository.
