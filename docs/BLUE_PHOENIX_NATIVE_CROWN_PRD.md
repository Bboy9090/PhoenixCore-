# Blue Phoenix Native: Crown Edition PRD

This Product Requirement Document (PRD) defines the product vision, scope, and technical roadmap for **Blue Phoenix Native: Crown Edition**, the sovereign from-scratch operating system that owns the full Bobby's World first-party computing stack.

---

## 🎯 Product Mission & Vision

* **Mission:** Build the first non-Linux Blue Phoenix operating system that ships with Bobby’s World flagship apps and games as native, sovereign, first-party software.
* **Vision:** Blue Phoenix Native is the crown version of Bobby’s World computing—a sovereign OS with its own app model, custom GUI shell, unique package format, exclusive SDK, and private first-party ecosystem.

---

## 🚫 Core Strategy & Non-Goals

1. **The Desktop Bridge:** **Blue Phoenix Desktop** remains our Linux-based bridge product. It is *not* dead. It proves the brand, builds the user base, and runs preview, companion, and stable technician tools.
2. **The Sovereign Throne:** **Blue Phoenix Native** is where the complete, full flagship applications and exclusive games live.
3. **Strict Truthfulness (No Fake Launchers):** We will never ship "mock launchers" or dead icons in Native to look complete. The app bundle will scale dynamically as OS fundamentals (graphics, audio, window manager, SDK) mature.

---

## 📦 Revised Edition Structure

| Edition Product | Base Foundation | Primary Purpose | App & Game Inclusion Tiers |
|---|---|---|---|
| **Blue Phoenix Desktop** | Debian Linux | Public bridge, testing, user acquisition | App Previews + Selected stable utility tools |
| **Blue Phoenix Recovery Desktop** | Debian Live ISO | Technician Recovery environment | BootForge, rescue, shell |
| **Blue Phoenix Technician Desktop** | Debian Linux | Bare-metal technician workstation | Workshop, PulseCheck, diagnostic utilities |
| **Blue Phoenix Native OS** | Custom Core (No Linux) | Sovereign flagship OS standard | Full native Bobby's World app & game suite |
| **Blue Phoenix Native: Crown Edition** | Custom Core (No Linux) | Premium flagship consumer release | Complete, unrestricted apps and exclusive first-party games |

---

## 🚦 Technical Requirements for Flagship Apps Execution

Before Blue Phoenix Native can run the full, complete applications bundle, the following **twelve foundation layers** must be progressively stabilized:

```text
  [12. Update System] ➔ Secure, atomic image updates
    ▲
  [11. Graphics/Game Runtime] ➔ Accelerated 2D/3D graphics pipelines
    ▲
  [10. Permissions/Security] ➔ Sandbox containment & capabilities matrix
    ▲
  [9. SDK (WorldKit)] ➔ Unified programmatic API boundaries
    ▲
  [8. Package Format] ➔ Atomic, signature-verified package structures
    ▲
  [7. App Runtime] ➔ Native thread management & message loops
    ▲
  [6. Networking] ➔ High-performance audited TCP/IP stack
    ▲
  [5. Input Stack] ➔ Real-time event handling (keyboard, mouse, touch)
    ▲
  [4. Audio Stack] ➔ Low-latency, multi-channel sound routing
    ▲
  [3. Filesystem] ➔ Crash-resilient high-integrity storage volumes
    ▲
  [2. Window Manager/Compositor] ➔ Citadel visual compositor
    ▲
  [1. Native GUI Shell] ➔ Core GUI elements & layout engines
```

---

## 🚀 Native Milestones Roadmap

To transition Blue Phoenix Native from a bootloader to a sovereign ecosystem, the roadmap is divided into seven progressive milestones:

### `NATIVE-0: Doctrine and Kernel Boot`
* **Deliverables:** Lock product vision, compile the bootloader and custom kernel core, verify initial VGA/UART text outputs.

### `NATIVE-1: Shell and Filesystem`
* **Deliverables:** Standardize storage volume layers, establish input device drivers (keyboard/mouse), and launch the initial graphical Window Manager/Compositor shell.

### `NATIVE-2: Native App Runtime`
* **Deliverables:** Write process management, dynamic thread scheduling, permissions/security containment controls, and compile the native process lifecycles.

### `NATIVE-3: WorldKit SDK`
* **Deliverables:** Freeze public developer bindings for UI layout engines, networking, audio layers, and input device bindings.

### `NATIVE-4: Crown App Bundle MVP`
* **Deliverables:** Compile the initial sovereign utility set: Command, Market, Harbor, Ghost Writer, Soul Codex, Sonic Codex, and BootForge.

### `NATIVE-5: Native Games MVP`
* **Deliverables:** Ship the first sovereign-exclusive games: Thunder Runner, Storm Grid, Kai-Jax: Memory Hero, and Cardhouse.

### `NATIVE-6: Crown Edition Release`
* **Deliverables:** Master package assembly, cryptographic image signings, and release compilation of **Blue Phoenix Native: Crown Edition**.
