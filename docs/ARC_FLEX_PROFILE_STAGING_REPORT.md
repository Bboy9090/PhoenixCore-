# Arc Flex Profile Staging Report

The initial staging of the lightweight **Arc Flex** profile structure has been completed. Only the defined architecture configurations, package lists, policies, and simple vector branding assets have been staged. No app components, external binary dependencies, or visual themes were imported.

---

## 1. Staged Profile Structure

The profile structure was initialized and populated under the designated directory:
`os/phoenix-os/profiles/arc-flex/`

### File Staging Map

The following files were staged from the extracted inner scaffold:

| Extracted Scaffold Source | Staged Target Path | Status |
| :--- | :--- | :--- |
| `arcwyre-flex/branding/icons/arcwyre-flex.svg` | `os/phoenix-os/profiles/arc-flex/branding/arcwyre-flex.svg` | **STAGED** |
| `arcwyre-flex/desktop/xfce/config/xfce4-panel.xml` | `os/phoenix-os/profiles/arc-flex/includes.chroot/etc/skel/.config/xfce4/panel/xfce4-panel.xml` | **STAGED** |
| `arcwyre-flex/base/packages/base-packages.txt` | `os/phoenix-os/profiles/arc-flex/package-lists/base-packages.txt` | **STAGED** |
| `arcwyre-flex/base/services/disabled-services.txt` | `os/phoenix-os/profiles/arc-flex/base/disabled-services.txt` | **STAGED** |
| `arcwyre-flex/modes/simple/profile.toml` | `os/phoenix-os/profiles/arc-flex/modes/simple/profile.toml` | **STAGED** |
| `arcwyre-flex/modes/repair/profile.toml` | `os/phoenix-os/profiles/arc-flex/modes/repair/profile.toml` | **STAGED** |
| `arcwyre-flex/modes/power/` (empty dir) | `os/phoenix-os/profiles/arc-flex/modes/power/` | **STAGED** |
| `arcwyre-flex/modes/kiosk/` (empty dir) | `os/phoenix-os/profiles/arc-flex/modes/kiosk/` | **STAGED** |
| `arcwyre-flex/modes/live-usb/` (empty dir) | `os/phoenix-os/profiles/arc-flex/modes/live-usb/` | **STAGED** |
| `arcwyre-flex/scripts/build-iso.sh` | `os/phoenix-os/profiles/arc-flex/hooks/build-iso.sh` | **STAGED** |
| `arcwyre-flex/scripts/measure-baseline.sh` | `os/phoenix-os/profiles/arc-flex/hooks/measure-baseline.sh` | **STAGED** |

---

## 2. Excluded Components

The following directories/files were **excluded** from the staging process to keep the profile configuration-only:
- `arcwyre-flex/apps/` (Stubs: `web-app-center.py`, `recovery-center.py`)
- `arcwyre-flex/docs/`
- All visual layouts, sounds, wallpapers, and desktop themes associated with the **Home Aurelia** or **native-app-hub** payloads.

---

## 3. Verification

Staging verification completed successfully. The file structure is clean and correctly isolated from default building configurations.

**Staging Status**: `ARC_FLEX_PROFILE_STAGED`
