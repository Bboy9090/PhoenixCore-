# Arc Flex Profile Validation

Detailed validation audit of the staged lightweight **Arc Flex** profile configurations.

---

## 1. base-packages.txt Audit & Resource Impact

The base packages listed in `package-lists/base-packages.txt` are evaluated here:

### Package Classification

| Package / Group | Classification | Notes |
| :--- | :--- | :--- |
| **systemd, dbus, policykit-1, udev, sudo** | **Essential** | Core operating system runtime and security privilege infrastructure. |
| **xorg, lightdm, lightdm-gtk-greeter** | **Essential** | Graph and Display layers required for starting any visual X11 desktop environment. |
| **xfce4, xfce4-terminal, xfce4-panel, xfce4-settings, thunar, xfce4-power-manager** | **Essential** | Core XFCE desktop environment components. |
| **network-manager, wireless-tools, wpasupplicant, curl, wget** | **Essential** | Networking manager stack. Essential for local and online network connectivity. |
| **firefox-esr** | **Heavy** | ESR version saves frequent update bloat but remains the largest single runtime resource user. |
| **mousepad, ristretto, parole, file-roller, gnome-calculator** | **Optional** | Basic lightweight utility application suite. Ristretto and Mousepad are very light. |
| **flatpak, gnome-software-plugin-flatpak** | **Heavy** | Flatpak engine and Software center plugin. Impacts baseline storage and background updates. |
| **testdisk, photorec, smartmontools, hdparm, memtest86+** | **Optional** | Hardware recovery tools. Low storage impact, inactive when not explicitly launched. |
| **fonts-liberation, fonts-noto** | **Optional** | Essential for visual rendering of foreign unicode character assets. |
| **gparted, htop, neofetch, inxi** | **Optional** | GUI partition manager and terminal stats tools. |

### Resource Impact Estimates

- **Storage Impact (Installed)**:
  - *Base System + XFCE*: ~1.8 GB – 2.2 GB.
  - *Firefox-ESR*: ~180 MB.
  - *Flatpak & App plugins*: ~150 MB (increases significantly if flatpak runtimes like Flatpak GNOME Platform are pulled).
  - *Recovery & System Tools*: ~50 MB.
  - **Estimated Total**: ~2.5 GB to 3.0 GB baseline storage footprint.
- **RAM Impact (Idle / Runtime)**:
  - *Boot to XFCE desktop at idle*: ~180 MB – 240 MB.
  - *Launching Firefox-ESR (single tab)*: +200 MB to 350 MB.
  - *System Load with flatpak daemon check*: Negligible overhead unless Flatpak apps run.
  - **Estimated Total Idle RAM**: ~200 MB. Ideal for low-end 2GB/4GB targets.

---

## 2. disabled-services.txt Service Audit

Evaluating services configured to be disabled at boot in `base/disabled-services.txt`:

| Service | Audit Classification | Details / Risks |
| :--- | :--- | :--- |
| **preload** | **Safe to Disable** | Pre-caching binaries is counterproductive on low-RAM machines as it locks down active memory. |
| **tracker-miner-fs, tracker-store** | **Safe to Disable** | Indexing disk contents consumes high CPU/disk I/O cycles, which slows down aging hardware. |
| **zeitgeist-daemon** | **Safe to Disable** | Redundant telemetry tracking; reduces memory and privacy footprints when disabled. |
| **evolution-source-registry** | **Safe to Disable** | Unneeded unless active evolution GUI client mail accounts are connected. |
| **gvfs-goa-volume-monitor** | **Safe to Disable** | Not required for local file operations. |
| **gvfs-mtp-volume-monitor** | **Safe to Disable** | Disables automatic MTP mobile device mounting. Low risk, can be configured for run-time detection. |
| **bluetooth** | **Risky to Disable** | Safe to disable for absolute minimal boot, but user space Bluetooth devices (keyboards/mice) will fail to work until manually enabled. |
| **cups** | **Safe to Disable** | Printing daemon can remain disabled until a local printing task is triggered. |
| **avahi-daemon** | **Safe to Disable** | Safe to disable for basic standalone targets. Disables mDNS network share discovery by default. |

---

## 3. XFCE Panel Configuration Audit (`xfce4-panel.xml`)

We validated the staged XFCE bottom panel XML layout:
- **Panel Initialization**: Configures a single bottom panel (`panel-1` configured with `position` string `p=8`).
- **Core Elements Staged**: Contains four plugin IDs (`applicationsmenu`, `tasklist`, `systray`, `clock`).
- **Issues Found**:
  - `applicationsmenu` is defined, but no specific custom menu format is declared.
  - **Launchers missing**: The panel XML does not define shortcut launchers (quick launch buttons) for the browser (Firefox), file manager (Thunar), or system settings. Users must open the applications menu manually to locate these applications.
  - *Resolution*: This XML configures the baseline frame structure; launcher profiles (`.desktop` maps) should be added in subsequent packaging phases.

---

## 4. Mode Profiles Audit

Comparing configurations in `simple/profile.toml` and `repair/profile.toml`:

### Staged Settings

- **Simple Mode (`simple/profile.toml`)**:
  - Sets compositor to `xfwm4`, disables animations/effects, and positions the panel at the bottom.
  - Enables browser, files, and updates.
  - Restricts terminal, native package manager CLI, and developer tools (`= false`).
  - Active optimization flags: `disable_extra = true`, `zram = true`.
- **Repair Mode (`repair/profile.toml`)**:
  - Enables terminal, disk tools, boot repair, USB creator, hardware diagnostics, and network tools.
  - Maps command-line tools to boolean flags (`smartmontools`, `hdparm`, etc.).
  - Security policies: `destructive_actions_require_confirmation = true` and `no_unauthorized_bypass = true`.

### Missing Settings & Conflicts

- **Config Validation Conflicts**: The profiles define system behaviors like `zram = true` or `theme = "arcwyre-simple"`, but there are no backend scripts to bind these values to actual system environment changes during boot or runtime.
- **Missing Options**: The profiles lack target environment specifics (e.g., locking access to virtual consoles TTY1-6 when terminal access is set to false in Simple mode).

---

## 5. Empty Mode Analysis

The empty folders (`power/`, `kiosk/`, and `live-usb/`) are evaluated:
- **Status**: **Intentionally Empty / Stubs**.
- **Assessment**: The scaffold structure creates directories to define the scope of the edition modes. These are incomplete mode categories that must be populated with specific configuration overrides (`profile.toml`) during implementation phases 7, 8, and 12.

---

## 6. Staging Validation Conclusion

**Profile Validation Status**: **`ARC_FLEX_VALIDATED`**

The profile files are staged correctly and conform to the lightweight architecture footprint. No system blockers prevent integrating this profile definition in the next build design phase.
