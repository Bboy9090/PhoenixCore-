# ⚡ Native OS Control Center & The Theme Legacy Registry

In standard Linux, changing the system color scheme requires editing separate GTK, Kvantum, SDDM, and wallpaper registries. The Native OS completely replaces this messy paradigm with a system-wide **Legacy Theme Matrix**.

## The Theme Legacy Matrix Registry
The matrix registry resides at `/etc/native/theme_matrix.conf`. It controls HSL parameters across the entire direct-to-GPU Vulkan framebuffer canvas in real-time.

```text
[LEGACY_MATRIX_ACTIVE]
active_legacy = "NATIVE"

[THEME_COLORS]
accent_aurelia   = "#1E6BFF"
accent_arcwyre   = "#E53935"
accent_thunder   = "#FFC857"
accent_native_a  = "#FF1744"
accent_native_b  = "#1E6BFF"
```

## Control Center GUI Design Concepts
* **Direct Slider Controls**: Hardware-level contrast, brightness, and real-time HSL color temperature manipulation.
* **Fluid Transition Engine**: Activating Aurelia, Arcwyre, Thundergod, or Native dynamically sweeps a glowing HSL gradient wave from the center of the display to the edges, transitioning all application window shaders in exactly **180 milliseconds**.
