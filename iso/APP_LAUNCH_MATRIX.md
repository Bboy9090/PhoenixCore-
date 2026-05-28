# PR40 App Launch Matrix Verification

This document records the formal status and results of the **PR40 App Launch Matrix** verification, ensuring that all core operating system applications boot stably inside the target desktop environment session.

## 1. Release Readiness Registry
* **Overall Release Status:** `release_blocked`
* **Blocker Reason:** USB boot validation is pending, safety validation is pending, and the final Release Candidate (RC) gate has not been run.

---

## 2. Latest Verified Validation Run
* **Artifact Path:** `os/phoenix-os/build/bwos-home.iso`
* **Artifact SHA256:** `463e8273b24ef851b64c5b7388ebaafe639f6632b62ddea64e81aff7f43f5686`
* **Verification Timestamp:** `2026-05-28T02:08:48Z`
* **Evidence Directory:** [iso/outputs/app-launch-evidence/home/20260528T020848Z/](file:///Users/bj90-m1/PhoenixCore-/iso/outputs/app-launch-evidence/home/20260528T020848Z/)
* **Serial Telemetry Stream:** [serial.log](file:///Users/bj90-m1/PhoenixCore-/iso/outputs/app-launch-evidence/home/20260528T020848Z/serial.log)
* **Outcome Class:** `APP_PROBE_COMPLETE_8of8_PASS` (100% stable execution)

---

## 3. Telemetry Signal Assertions
All crucial guest-side verification signals successfully reached the serial capture:
- [x] **`bwos.session=x11`** present on boot command line.
- [x] **`bwos.app_probe=1`** present on boot command line.
- [x] **`bwos.shutdown_probe=1`** absent (guest remains active on the desktop).
- [x] **`BWOS_DESKTOP_SESSION_STARTED`** emitted (Desktop stabilized).
- [x] **`BWOS_APP_LAUNCH_MATRIX_STARTED`** emitted (Harness active).
- [x] **`BWOS_APP_LAUNCH_MATRIX_COMPLETE`** emitted (Telemetry sequence finished).

---

## 4. Launch Results per Application
All 8 target applications successfully launched and passed their 15-second stability test under the `phoenix` user context with exit code `0`:

| App ID | Friendly Name | Execution Status | Exit Code | Desktop File |
| :--- | :--- | :--- | :---: | :--- |
| **`firefox-esr`** | Firefox Web Browser | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/firefox-esr.desktop` |
| **`dolphin`** | Dolphin File Manager | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/org.kde.dolphin.desktop` |
| **`konsole`** | Konsole Terminal Emulator | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/org.kde.konsole.desktop` |
| **`kcalc`** | KCalc Scientific Calculator | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/org.kde.kcalc.desktop` |
| **`kwrite`** | KWrite Monospace Editor | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/org.kde.kwrite.desktop` |
| **`gwenview`** | Gwenview Image Viewer | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/org.kde.gwenview.desktop` |
| **`systemsettings`** | KDE System Settings | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/systemsettings.desktop` |
| **`discover`** | Plasma Discover Software Center | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/org.kde.discover.desktop` |

---

## 5. Architectural Correctness Summary
The launch matrix succeeded by transitioning from unstable, interactive runtime workarounds to robust, standard platform configurations:
* **Service Privilege Separation:**
  The `bwos-app-launch-matrix.service` is executed as the unprivileged `User=phoenix` in the graphical session context. This successfully routes X11 and D-Bus communications through user-space pipelines (`DISPLAY=:0`, D-Bus Session Bus).
* **Systemd Standard Output Redirection:**
  Rather than attempting direct user-space `/dev/ttyS0` write commands, systemd standard output redirection (`StandardOutput=tty` + `TTYPath=/dev/ttyS0`) is used. Systemd handles opening the file descriptor as root, resolving permission issues.
* **Simplifying Telemetry Commands:**
  Redefined `serial_emit` in the chroot to write directly to standard output (`echo "$1"`), preventing shell-level redirection failures under `set -e`. Telemetry also hooks into the journal via `logger`.
* **Removing Unrecognized KDE Args:**
  Removed `--no-sandbox` from all KDE/Qt application executions, preventing immediate process exits due to unrecognized command-line parameters.
* **Static GRUB Targeting:**
  Replaced QMP interactive boot-keystroke injection with a robust, static default boot configuration in `grub.cfg`, eliminating protocol sync timing races.
