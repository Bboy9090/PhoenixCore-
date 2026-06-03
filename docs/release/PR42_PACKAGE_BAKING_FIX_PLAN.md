# PR42 Package Baking Fix Plan

## Objective
Remediate the package integration flaws identified in the PR42 Audit. Specifically, transition custom flagship applications (Zenith UI) from source-code/first-run downloads into fully compiled, offline-ready Debian packages (`.deb`) baked into the SquashFS at boot.

## Component Baking Analysis Table

| Component Name | Source Path | Package / Build Command | Expected Binary Path | Current Binary Exists? | Copied into `includes.chroot`? | Installed via `package-list`? | Installed via Hook? | Visible After Boot? | Fix Required |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Zenith App Hub** | `apps/native-app-hub` | `npm install && npm run tauri build` | `/usr/bin/zenith-app-hub` (or similar) | **No** | **Yes** (Source code only in `/opt/`) | **No** | **No** | **No** (Only a desktop shortcut downloading compilers) | **Compile before live-build**, stage `.deb` into `packages.chroot/`, and let live-build natively install it. Remove source copy from `includes.chroot/opt/`. |
| **Lutris / Proton** | Debian / External Repos | N/A | `/usr/games/lutris` | **No** | **No** | **No** | **No** | **No** | **Add to package-list** (`gaming.list.chroot`). |
| **Phoenix Gamemode** | `includes.chroot/.../phoenix-gamemode` | N/A (Bash Script) | `/usr/local/bin/phoenix-gamemode` | **Yes** | **Yes** | **No** | **No** | **Yes** | **Preserve as copied binary** via `includes.chroot`. No action needed. |
| **Wine Layer** | Debian Repos | N/A | `/usr/bin/wine` | **Yes** | **No** | **Yes** | **No** | **Yes** | **None**. Safely baked via `gaming.list.chroot`. |
| **Vulkan Drivers** | Debian Repos | N/A | `/usr/bin/vulkaninfo` | **Yes** | **No** | **Yes** | **No** | **Yes** | **None**. Safely baked via `gaming.list.chroot`. |

## Recommended Implementation Order

To safely transition the architecture to a fully baked offline ISO without breaking existing validation:

1.  **Stage 1: Pre-Compilation Pipeline**
    *   Create a local build script (e.g., `scripts/build-native-app-hub.sh`) that runs on the host *before* ISO generation.
    *   This script will run `npm run tauri build` inside `apps/native-app-hub` to generate a native `.deb` package.
2.  **Stage 2: Staging the Package**
    *   Create the `os/phoenix-os/live-build/config/packages.chroot/` directory if it does not exist.
    *   Copy the newly compiled Zenith UI `.deb` into `packages.chroot/`. Debian `live-build` automatically installs any `.deb` files placed here during the `chroot` phase.
3.  **Stage 3: Cleanup Source Overlays**
    *   Remove the raw source code injection from `includes.chroot/opt/native-app-hub`.
    *   Remove the first-run downloader script (`build-zenith-ui.sh`) and its desktop launcher. The Tauri `.deb` will automatically provide a clean `.desktop` file pointing directly to the compiled binary.
4.  **Stage 4: Gaming List Expansion**
    *   Modify `os/phoenix-os/live-build/config/package-lists/gaming.list.chroot` to explicitly include `lutris` (and any related Proton dependencies available in Debian bullseye).
5.  **Stage 5: Verification & Rebuild**
    *   Execute `build-all-isos.sh` and verify that the `.deb` correctly installs during the chroot log output.

*Execution is pending operator approval. No fixes or rebuilds have been run.*
