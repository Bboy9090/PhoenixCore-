# PR42 Package Baking Audit

## Executive Summary
This audit traces the integration state of custom applications and the Windows gaming compatibility layer across the Phoenix OS live-build artifacts.

### Audit Findings Matrix

| Component Name | Expected Path / Inclusion | Actual Path | Baked into SquashFS? | Installed via APT? | First-Run Download? | Recommended Fix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Zenith App Hub (8 Flagship Apps)** | `/opt/native-app-hub` | `/opt/native-app-hub` | Yes (Source Only) | **No** | **Yes** | Requires `npm run tauri dev` and Rust/Node toolchain downloads on first run via `build-zenith-ui.sh`. Needs to be pre-compiled into a `.deb` package. |
| **Wine Compatibility Layer** | `gaming.list.chroot` | Integrated | **Yes** | **Yes** | No | None - Wine32/64 and Winetricks are cleanly baked into the OS via `apt`. |
| **Vulkan Drivers** | `gaming.list.chroot` | Integrated | **Yes** | **Yes** | No | None - Mesa-vulkan-drivers and tools are cleanly baked. |
| **Proton / Lutris / Heroic** | System Packages | N/A | **No** | **No** | No | Missing entirely from the build configuration. Need to add to a custom package list or stage `.deb` files in `packages.chroot/`. |
| **Phoenix Gamemode Script** | `/usr/local/bin/phoenix-gamemode` | `/usr/local/bin/phoenix-gamemode` | **Yes** | **Yes** | No | None - Script is present and executable, though currently basic (CPU governor / RAM drop). |

## Next Steps for PR42
1. Create a CI/CD pipeline to pre-compile the Tauri Zenith UI into a Debian package (`.deb`).
2. Include the pre-compiled `.deb` inside `packages.chroot/` so that it is installed natively during the live-build execution phase.
3. Identify and package Lutris and Proton into the `gaming.list.chroot`.
