# ARCWYRE System Boundaries & Governance

This document defines the boundaries between the various components of the ARCWYRE ecosystem to prevent "Bloat Contagion" and maintain architectural integrity.

## 1. Domain Governance

| Component | Responsibility Domain | Must NOT Include |
| :--- | :--- | :--- |
| **ARCWYRE Core** | Logic, math, safety, imaging primitives, protocol definitions. | UI code, web server code, platform-specific GUI toolkits. |
| **ARCWYRE Agent** | Hardware execution, privilege management, telemetry stream. | Business logic, complex UI state, persistent user data. |
| **Control Center** | User interface, state management, dashboarding, visual feedback. | Raw disk I/O, low-level kext manipulation, cryptographic secrets. |
| **BootForge** | Image creation logic, bootloader configuration, ISO assembly. | User identity management, cloud synchronization. |
| **ARCWYRE Key** | Hardware identity, secret storage, recovery seeds. | Large OS images, user files, non-critical logs. |

---

## 2. Repo Distribution

- **`PhoenixCore-` Repo**: Houses the **ARCWYRE Core**, **ARCWYRE Agent**, and **ARCWYRE Control Center**. This is the primary "Platform Hub."
- **`ARCWYRE Native` Repo**: (Separate) Houses the custom kernel, native bootloader, and sovereign userland.
- **`BootForge` Repo**: (Integration) Specialized modules for imaging and media creation.

---

## 3. Communication Boundaries

- **UI -> Agent**: All UI actions must flow through the ARCWYRE Agent. No direct hardware calls from the frontend are permitted.
- **Agent -> Core**: The Agent must treat the Core as a set of stateless, high-integrity libraries.
- **Core -> Hardware**: All hardware interaction must be gated by safety checks (Capability Matrix).

---

## 4. Separation of Concerns (The "Sacred Minimal")

- **Offline-First**: The Control Center must be able to function entirely without internet connectivity.
- **Zero-Dependency Core**: Core Rust crates should aim for zero external dependencies (excluding `std` or `alloc`).
- **Minimal Surface Area**: Every service must expose only the minimum necessary API surface.

---

## 5. Naming Governance

- **Public**: All user-facing strings, logs, and docs must use **ARCWYRE**.
- **Internal**: **Phoenix** is preserved as an internal codename and crate/identifier prefix for backward compatibility and build-system stability.
- **No Mixing**: Do not introduce new Phoenix-prefixed identifiers for new features. Use ARCWYRE or generic terms.
