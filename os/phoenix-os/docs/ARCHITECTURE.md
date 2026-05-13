# Phoenix OS Architecture Overview

## Foundation
Phoenix OS is built upon a **Debian/Ubuntu-based Live-Build** foundation, specifically optimized for high-performance mobile device servicing and fleet management.

## Desktop Environment
- **Core**: KDE Plasma
- **Protocol**: Wayland-first
- **Aesthetic**: Phoenix Dark (Placeholder)

## Component Integration
The OS integrates three primary platform pillars:
1. **Phoenix Agent**: The system-level governor for all hardware and imaging operations.
2. **Phoenix Control Center**: The graphical interface for users and administrators.
3. **BootForge**: The localized engine for creating bootable servicing media.

## Build Philosophy
- **Reproducible**: Every ISO build is defined by declarative package manifests in `/packages`.
- **Governed**: Direct system modifications are prohibited; all changes must pass through the `overlays/` system.
- **Preview-First**: The OS itself follows the platform's preview-first doctrine for all updates and configuration changes.

## Integration Boundaries
| Component | Responsibility | Boundary |
|-----------|----------------|----------|
| Debian Base | Kernel, drivers, core OS | Immutable live-image |
| KDE Plasma | Window management, UI shell | Wayland session |
| Phoenix Agent | Hardware orchestration | Systemd service |
| Control Center | User interaction | Tauri / Webview |
