# Phoenix OS Branding Boundary Policy

This policy establishes strict boundaries separating mutable visual assets from dangerous programmatic identifiers to prevent renaming cascades from breaking build, security, or packaging scripts.

---

## 🟢 Safe-to-Change Parameters (Visual Assets Only)

Technicians and artists may freely modify the following properties in custom edition manifests to customize product experiences:
* **Desktop Wallpapers:** PNG/JPG visual assets staged under `/usr/share/images/desktop-base/`.
* **System Colorways:** Standard CSS color tokens compiled inside `colors.css`.
* **Emblem Icons & Splash Logos:** Plymouth vector shapes (`phoenix-logo-boot.png`) or application menu icons.
* **Declarative Display Names:** The `display_name` and `tagline` fields inside `edition.yaml`.
* **Display Hooks & Static Strings:** Text labels in HTML/React user interfaces (e.g. system dashboard titles).

---

## 🔴 Dangerous-to-Change Parameters (Programmatic Identifiers)

The following identifiers must remain **strictly locked**. Programmers must never rename or mutate them, as they govern active package resolution, Polkit escalation routes, or dbus communication pipelines:

1. **Crate Names & Rust Targets:**
   * Crates such as `phoenix-core`, `phoenix-safety`, and `phoenix-bootloader-core` must retain their exact namespace bounds.
2. **Package & Binary IDs:**
   * Package naming schemas (`bwos-core`, `bootforge`) must not be changed, as this breaks dependency resolution in package-lists profiles.
3. **Tauri & App IDs:**
   * Structural desktop shell namespaces (e.g. `com.aurelia.citadel`) must remain locked to prevent system state files and config dirs from breaking.
4. **Governance Identifiers:**
   * Polkit Action IDs (`org.aurelia.phoenix.core.read_smart`) must match policy keys exactly. Any mutation will break authentication paths, resulting in system failures.
5. **Runtime System Paths:**
   * Standard directory locations (e.g. `/usr/libexec/phoenix/`, `/etc/aurelia/`) must not be altered.
