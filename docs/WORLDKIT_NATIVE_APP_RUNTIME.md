# WorldKit Native App Runtime Spec

This document specifies the custom application runtime, package formats, and developer SDK bindings (WorldKit) governing software execution inside **Blue Phoenix Native**.

---

## 📦 The Native Package Format (`.wpk`)

Applications compiled for Blue Phoenix Native are bundled into a single, high-integrity cryptographically signed file structure: **WorldKit Package (`.wpk`)**.

### Package Schema Structure:
```text
[app-name].wpk
├── metadata.yaml        # Manifest declaring ID, version, permissions, and entry point
├── signature.bin        # Cryptographic signature matching the developer's public key
└── payload.bin          # Statically compiled binary payload or compressed system assets
```

---

## 🛡️ WorldKit App Sandbox permissions Model

To guarantee bare-metal integrity without relying on massive Linux kernel namespaces, every `.wpk` package runs within a sandboxed virtual interface governed by the **Permissions Manifest**:

* `sys.disk.read`: Allows read-only access to partition geometries and SMART metadata.
* `sys.disk.write`: **Strictly Gated.** Allows disk mutations; requires Polkit authentication.
* `sys.net.client`: Permits outgoing client socket TCP connections.
* `sys.net.server`: Permits incoming socket bindings.
* `sys.hw.audio`: Permits raw access to system audio buffers.
* `sys.hw.graphics`: Permits raw memory-mapped buffer access for 2D/3D hardware rendering.

---

## ⚙️ Application Lifecycle Contract

Applications must register and respond to standard lifecycle signals broadcasted by the **Citadel Compositor**:

```text
  [INIT] ➔ Application parses metadata, validates permissions, registers entry points.
    │
    ▼
  [LAUNCH] ➔ Allocates graphics buffers, binds input threads, registers draw handlers.
    │
    ▼
  [RUNNING] ➔ Primary execution thread loop.
    │
  ┌─┴────────────────────────┐
  ▼                          ▼
[SUSPEND] ➔ (Low-memory)   [FOCUS_LOST] ➔ (Background)
  │                          │
  ▼                          ▼
[RESUME] ➔ (Re-bind paths) [FOCUS_GAIN] ➔ (Restore state)
  │
  ▼
[TERMINATE] ➔ De-allocates threads, frees buffers, writes exit status code.
```

---

## 📝 WorldKit SDK UI Scaffold (Rust Example)

The unified interface bindings target standard compiled structures:

```rust
use worldkit::prelude::*;

#[app_entry]
fn main(ctx: AppContext) -> AppResult {
    // 1. Request permissions and build graphical layout
    let mut window = Window::new("Command Native")
        .with_size(1024, 768)
        .with_theme(Theme::Aurelia)
        .build(ctx)?;

    // 2. Register draw/event handlers
    window.on_draw(|canvas| {
        canvas.clear(Color::RGB(10, 25, 47)); // Flat royal-blue background
        canvas.draw_text("Blue Phoenix Sovereign Shell", 50, 50);
    });

    // 3. Spawns application thread loop
    window.exec()
}
```
