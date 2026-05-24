# Desktop to Native Porting Strategy

This document establishes the official engineering architecture and code reuse patterns for porting application libraries from **Blue Phoenix Desktop (Linux)** to **Blue Phoenix Native (Sovereign OS)** without code duplication.

---

## 🎨 Layered Codebase Architecture

To prevent duplicate logic from bloating our repositories or requiring costly rebuilds whenever visual styles or targeting parameters change, all flagship applications must enforce a strict **three-layered code separation**:

```text
  ┌────────────────────────────────────────────────────────┐
  │                   GRAPHICAL SHELL                      │
  │   - Desktop UI: React / CSS / Tauri wrapper            │
  │   - Native UI: Future WorldKit UI controls             │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │                 PORTABLE SERVICES / API                │
  │   - Standard interface traits (Rust)                   │
  │   - Custom OS drivers & bridges implementation        │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │                   PORTABLE CORE LOGIC                  │
  │   - Core data structures, calculations, algorithms     │
  │   - 100% standard Rust library (no OS dependencies)    │
  └────────────────────────────────────────────────────────┘
```

---

## 🛠️ Case Study: The Ghost Writer Architecture

The minimalist, focused writing assistant **Ghost Writer** is compiled across both target platforms using standard Rust workspace target gates:

### 1. `ghostwriter-core` (Library Crate)
* **Goal:** Manages text buffer structures, markdown serialization engines, focus modes logic, and word-counts telemetry.
* **OS Independence:** Zero ties to Linux system calls or custom Native kernel headers. Fully compiled to `std` or `no_std`.

### 2. `ghostwriter-desktop` (Vite / Tauri Crate)
* **Goal:** Renders visual overlays using web-native HTML canvas and React components.
* **Target OS:** Spawns standard OS threads inside a webview window on standard Linux desktops.

### 3. `ghostwriter-native` (WorldKit / Native Crate)
* **Goal:** Binds directly to the standard sovereign input stack and draws layouts via memory-mapped buffers using the Citadel compositor.
* **Target OS:** Blue Phoenix Native.

---

## 🚫 Governance Constraints

* **No direct libc calls in Core:** System services, filesystem pathways, and thread spawns must be abstracted via unified interface traits.
* **Deny-by-default Fallbacks:** Ported systems execution code must comply fully with **PR34** rules, registering explicit confirmation structures and audit logs before triggering sector writes.
