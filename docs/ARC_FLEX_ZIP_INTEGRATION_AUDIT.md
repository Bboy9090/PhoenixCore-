# Arc Flex ZIP Integration Audit

This audit evaluates the extracted contents of the **Arcwyre Flex** scaffold from the primary source ZIP files against the actual PhoenixCore build tree.

## 1. Correct Source ZIP

- **Outer ZIP Path**: `/Users/bj90-m1/Downloads/How to Use My GitHub Repos for Linux ISO Projects.zip`
- **Inner Scaffold ZIP Path**: `/Users/bj90-m1/Downloads/How to Use My GitHub Repos for Linux ISO Projects/arcwyre-flex-scaffold.zip`
- **Extracted Arc Flex Root Path**: `payload_extracted/HowToUseGithubRepos/arcwyre-flex-scaffold_extracted/arcwyre-flex/`

---

## 2. Extracted Arc Flex Inventory

The target scaffold contains the following structural components:
- [base/](file:///Users/bj90-m1/PhoenixCore-/payload_extracted/HowToUseGithubRepos/arcwyre-flex-scaffold_extracted/arcwyre-flex/base/)
  - `packages/base-packages.txt`
  - `services/disabled-services.txt`
  - `kernel-config/`
- [desktop/](file:///Users/bj90-m1/PhoenixCore-/payload_extracted/HowToUseGithubRepos/arcwyre-flex-scaffold_extracted/arcwyre-flex/desktop/)
  - `xfce/config/xfce4-panel.xml`
  - `xfce/themes/`
  - `lxqt/config/`
  - `kiosk/`
- [apps/](file:///Users/bj90-m1/PhoenixCore-/payload_extracted/HowToUseGithubRepos/arcwyre-flex-scaffold_extracted/arcwyre-flex/apps/)
  - `web-app-center/web-app-center.py`
  - `recovery-center/recovery-center.py`
  - `app-center/`
  - `device-revival/`
  - `update-system/`
- [branding/](file:///Users/bj90-m1/PhoenixCore-/payload_extracted/HowToUseGithubRepos/arcwyre-flex-scaffold_extracted/arcwyre-flex/branding/)
  - `icons/arcwyre-flex.svg`
  - `wallpapers/`
  - `themes/`
  - `plymouth/`
- [modes/](file:///Users/bj90-m1/PhoenixCore-/payload_extracted/HowToUseGithubRepos/arcwyre-flex-scaffold_extracted/arcwyre-flex/modes/)
  - `simple/profile.toml`
  - `repair/profile.toml`
  - `power/`
  - `kiosk/`
  - `live-usb/`

---

## 3. Component Meaning

- **`base/`**: Lightweight package/service policy. Dictates minimal package profiles (`base-packages.txt`) and startup performance controls via disabling non-essential services (`disabled-services.txt`).
- **`desktop/`**: XFCE/LXQt configuration candidates. Holds layout specifications and UI settings for low-resource graphical environments.
- **`apps/`**: Lightweight utility candidates. Python-driven helpers for system actions (web application shortcuts, basic rescue tools).
- **`branding/`**: Arc Flex icon/logo assets. Simple visual vectors defining the lightweight edition.
- **`modes/`**: Simple, Power, Repair, Kiosk, Live USB behavior profiles. Modular configurations applied based on deployment target or system environment.

---

## 4. Proposed PhoenixCore Destination Map

To avoid merging visual and desktop custom assets into the baseline OS source config, all files must map to profile-specific locations under the `profiles/arc-flex/` path:

| Extracted Scaffold Source | Proposed PhoenixCore Destination Path |
| :--- | :--- |
| `arcwyre-flex/base/` | `os/phoenix-os/profiles/arc-flex/base/` |
| `arcwyre-flex/base/packages/` | `os/phoenix-os/profiles/arc-flex/package-lists/` |
| `arcwyre-flex/desktop/` | `os/phoenix-os/profiles/arc-flex/includes.chroot/etc/skel/` (desktop configs) |
| `arcwyre-flex/apps/` | `os/phoenix-os/profiles/arc-flex/includes.chroot/opt/arc-flex/` |
| `arcwyre-flex/branding/` | `os/phoenix-os/profiles/arc-flex/branding/` |
| `arcwyre-flex/modes/` | `os/phoenix-os/profiles/arc-flex/modes/` |
| `arcwyre-flex/scripts/` | `os/phoenix-os/profiles/arc-flex/hooks/` |

---

## 5. Explicitly Mark Previous Payload As Out Of Scope

The following items from other payloads are **completely out of scope** for this Arc Flex implementation plan and will **not** be integrated:
- `HomeAurelia-Theme-Pack/` (all subfolders: wallpapers, cursors, sounds)
- `native-app-hub/` (Tauri React app source)
- Zenith App Hub
- Home Aurelia visual/branding assets (Aurelia, Arcwyre, Thundergod, Native visual themes)
- SDDM / GRUB / Plymouth themes derived from the Aurelia package

---

## 6. App Readiness

We audited the individual Python scripts included in the scaffold:

- **`arcwyre-flex/apps/web-app-center/web-app-center.py`**: **PARTIAL**
  - *Details*: Functionally creates local `.desktop` files using `firefox --new-window`. However, it relies on static dictionary indexes and lacks automated icon retrieval/downloading.
- **`arcwyre-flex/apps/recovery-center/recovery-center.py`**: **PARTIAL**
  - *Details*: Provides real system stats (`df -h`, `free -h`) and can execute `smartctl` and `ping` checks, but contains `NOT_RUN` mocks if system tools are missing. It acts as a basic diagnostic tool but is not a full-fledged automation suite.

Both scripts are functional but basic command-line applications and do not present mock UIs or false success indicators.

---

## 7. Integration Status

**`ARC_FLEX_PROFILE_AUDITED`**

---

## 8. Validation

Verified via `git diff --check` prior to final doc check-in.
