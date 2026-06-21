# Arc Flex ZIP Integration Audit

This audit evaluates the extracted contents of `payload.zip` against the actual PhoenixCore build tree structure at [os/phoenix-os/live-build/config/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/).

## Extracted File Inventory

The extracted zip structure contains two main components:
1. **`os/phoenix-os/live-build/config/includes.chroot/opt/`**: Contains the source/packages for the flagship application **Zenith App Hub** (`native-app-hub`), which is a Tauri/React app.
2. **`HomeAurelia-Theme-Pack/`**: Contains visual design system blueprints, wallpapers, color schemes, Kvantum configurations, Plymouth themes, icons, cursor files, sounds, and terminal themes across the 4 legacies (Aurelia, Arcwyre, Thundergod, Native).

---

## Usable Assets & Target Paths

The following visual and configuration assets are approved for integration into the PhoenixCore build system:

| Source Path (Extracted) | Destination Path in PhoenixCore | Type | Description |
| :--- | :--- | :--- | :--- |
| `HomeAurelia-Theme-Pack/02-Wallpapers/FHD/` | [os/phoenix-os/live-build/config/includes.chroot/usr/share/backgrounds/arcwyre/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/usr/share/backgrounds/arcwyre/) | Wallpaper | Desktop Wallpapers (main visual identity) |
| `HomeAurelia-Theme-Pack/09-Icons/` | [os/phoenix-os/live-build/config/includes.chroot/usr/share/icons/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/usr/share/icons/) | Icons | Home Aurelia icon index and sizes |
| `HomeAurelia-Theme-Pack/10-Cursors/` | [os/phoenix-os/live-build/config/includes.chroot/usr/share/icons/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/usr/share/icons/) | Cursors | Cursor themes |
| `HomeAurelia-Theme-Pack/06-Color-Schemes/` | [os/phoenix-os/live-build/config/includes.chroot/usr/share/color-schemes/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/usr/share/color-schemes/) | Theme | Plasma desktop color schemes |
| `HomeAurelia-Theme-Pack/07-Kvantum/` | [os/phoenix-os/live-build/config/includes.chroot/usr/share/Kvantum/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/usr/share/Kvantum/) | Theme | Kvantum widget style files |
| `HomeAurelia-Theme-Pack/08-Window-Decorations/Aurorae/` | [os/phoenix-os/live-build/config/includes.chroot/usr/share/aurorae/themes/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/usr/share/aurorae/themes/) | Theme | Aurorae window border decorations |
| `HomeAurelia-Theme-Pack/11-SDDM-Login/HomeAurelia/` | [os/phoenix-os/live-build/config/includes.chroot/usr/share/sddm/themes/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/usr/share/sddm/themes/) | Login | SDDM Login theme |
| `HomeAurelia-Theme-Pack/12-GRUB/HomeAurelia/` | [os/phoenix-os/live-build/config/includes.binary/boot/grub/themes/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.binary/boot/grub/themes/) | GRUB | GRUB Bootloader theme |
| `HomeAurelia-Theme-Pack/04-Plymouth/home-aurelia/` | [os/phoenix-os/live-build/config/includes.chroot/usr/share/plymouth/themes/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/usr/share/plymouth/themes/) | Boot | Plymouth boot screen theme |
| `HomeAurelia-Theme-Pack/13-Sounds/` | [os/phoenix-os/live-build/config/includes.chroot/usr/share/sounds/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/usr/share/sounds/) | Sounds | Custom OS sound effects |
| `HomeAurelia-Theme-Pack/17-Terminal/` | [os/phoenix-os/live-build/config/includes.chroot/usr/share/konsole/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/usr/share/konsole/) | Terminal | Konsole terminal profiles |
| `HomeAurelia-Theme-Pack/18-Browser-Startpage/` | [os/phoenix-os/live-build/config/includes.chroot/usr/share/browser-startpage/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/usr/share/browser-startpage/) | Browser | Offline-ready browser homepage |

---

## Usable App Source

- **`os/phoenix-os/live-build/config/includes.chroot/opt/native-app-hub/`**: Should be integrated into the actual PhoenixCore tree under [os/phoenix-os/live-build/config/includes.chroot/opt/native-app-hub/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/opt/native-app-hub/).

---

## Docs-Only Material

These items are for designer or developer reference and should **not** be staged to the ISO build directories:
- `HomeAurelia-Theme-Pack/00-Reference-Boards/` (design mocks)
- `HomeAurelia-Theme-Pack/01-Style-Guide/` (brand style specs)
- `HomeAurelia-Theme-Pack/Docs/` (implementation docs)
- `HomeAurelia-Theme-Pack/Preview-Sheets/` (visual mock grids)
- `HomeAurelia-Theme-Pack/20-QA-Testing/` (validation scripts/reports)

---

## Cautions & Prohibited Scripts (NOT to Import)

The following scripts are either legacy, system-destructive, or redundant/conflicting for standard builds and **must not be copied or automated**:
- **`HomeAurelia-Theme-Pack/apply-theme.sh`**: For user local machine testing. Modifies active configuration and database values locally using DBus commands; not suitable for chroot baking.
- **`HomeAurelia-Theme-Pack/install.sh`**: Installs files to `$HOME/.local/share` or system `/usr/share` on the host machine. The ISO build stages them directly via live-build overlays.
- **`HomeAurelia-Theme-Pack/build-package.sh` & `19-Package-Build/`**: Legacy Debian/Arch packager logic.
- **`HomeAurelia-Theme-Pack/generate_variant_themes.py`**: Developer color regeneration helper script.
- **Cursed/Destructive scripts (e.g., legacy MacBook 4,1 installer logic, `diskutil partitionDisk`, `dd`)** found elsewhere: Treat strictly as offline reference.

---

## Conflicts & Duplications

1. **`os/phoenix-os/live-build/config/includes.chroot/opt/native-app-hub`**:
   The `native-app-hub` has source files, Node modules, and Tauri structures. We must verify if `zenith-app-hub` (which maps to [os/phoenix-os/live-build/config/includes.chroot/opt/zenith-apps/](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/opt/zenith-apps/)) or existing configurations have conflicting naming or startup logic.
2. **`HomeAurelia-Theme-Pack/Plymouth` vs. Existing Plymouth**:
   The theme pack contains `04-Plymouth/home-aurelia` while our existing tree already has `os/phoenix-os/branding/plymouth/phoenix`. We must ensure they do not overwrite each other but are configured cleanly.
