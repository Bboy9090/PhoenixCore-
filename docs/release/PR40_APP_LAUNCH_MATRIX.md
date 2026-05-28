# PR40 App Launch Matrix Release Record

## 1. Overview
* **Status:** `release_blocked`
* **Reason:** USB boot validation is pending, safety validation is pending, and the final Release Candidate (RC) gate has not been run.
* **Edition:** Home Aurelia
* **Target Architecture:** `amd64`
* **Verification Status:** `APP_PROBE_COMPLETE_8of8_PASS` (100% Launch Pass Rate)

---

## 2. Provenance and Artifact Metadata
* **Artifact Path:** `os/phoenix-os/build/bwos-home.iso`
* **Artifact SHA256:** `463e8273b24ef851b64c5b7388ebaafe639f6632b62ddea64e81aff7f43f5686`
* **Evidence Directory:** `iso/outputs/app-launch-evidence/home/20260528T020848Z/`
* **Serial Telemetry Log:** `iso/outputs/app-launch-evidence/home/20260528T020848Z/serial.log`
* **QEMU Execution Mode:** Headless UEFI x86_64, `qemu-system-x86_64`

---

## 3. Telemetry Verification Milestones
All major telemetry markers were verified in the serial log stream:
- [x] **`bwos.session=x11`** present on kernel command line.
- [x] **`bwos.app_probe=1`** present on kernel command line.
- [x] **`bwos.shutdown_probe=1`** absent from kernel command line.
- [x] **`BWOS_DESKTOP_SESSION_STARTED`** emitted (Plasma/X11 fully stabilized).
- [x] **`BWOS_APP_LAUNCH_MATRIX_STARTED`** emitted (App launch sequence triggered).
- [x] **`BWOS_APP_LAUNCH_MATRIX_COMPLETE`** emitted (All 8 app checks completed).

---

## 4. App Launch Matrix Outcomes
Each of the 8 target suite applications successfully initialized and completed its 15-second stability check with exit code `0` (no crashes):

| Application | Command | Result | Exit Code | Desktop Entry File |
| :--- | :--- | :--- | :---: | :--- |
| **`firefox-esr`** | `/usr/bin/firefox-esr` | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/firefox-esr.desktop` |
| **`dolphin`** | `/usr/bin/dolphin` | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/org.kde.dolphin.desktop` |
| **`konsole`** | `/usr/bin/konsole` | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/org.kde.konsole.desktop` |
| **`kcalc`** | `/usr/bin/kcalc` | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/org.kde.kcalc.desktop` |
| **`kwrite`** | `/usr/bin/kwrite` | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/org.kde.kwrite.desktop` |
| **`gwenview`** | `/usr/bin/gwenview` | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/org.kde.gwenview.desktop` |
| **`systemsettings`** | `/usr/bin/systemsettings5` | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/systemsettings.desktop` |
| **`discover`** | `/usr/bin/plasma-discover` | `APP_LAUNCH_PASS` | `0` | `/usr/share/applications/org.kde.discover.desktop` |

---

## 5. Architectural & Implementation Fixes
To achieve this clean sweep, the validation harness and guest telemetry strategy were refactored to eliminate permission hurdles and process-level crash loops:
1. **User Session Context (`User=phoenix`):**
   The `bwos-app-launch-matrix.service` was ported to run in the `phoenix` graphical user context rather than as root. We exported all essential session parameters (`DISPLAY=:0`, `XAUTHORITY=/home/phoenix/.Xauthority`, `XDG_RUNTIME_DIR=/run/user/1000`, `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus`) directly inside the systemd service definition.
2. **Systemd Telemetry Redirection (`StandardOutput=tty`):**
   Rather than writing directly to `/dev/ttyS0` from user-space (which triggered permission blocks and shell-level aborts under `set -e` redirection constraints), the service redirects standard output at the systemd layer:
   ```ini
   StandardOutput=tty
   TTYPath=/dev/ttyS0
   ```
   This allows systemd to open the device file as root before dropping privileges, passing an already-opened write-only file descriptor to the guest probe.
3. **Robust Script Telemetry:**
   Guest `serial_emit` functions were simplified to output to `stdout` (`echo "$1"`) and write to `logger -t bwos-app-matrix` for systemd journal synchronization.
4. **Qt / KDE App Parameter Fix:**
   Unrecognized command-line parameters (like `--no-sandbox`) were removed for native KDE applications. KDE apps strictly reject invalid CLI flags and exit immediately with exit code 1; since they are now executed as non-root user `phoenix`, sandboxing is automatically handled safely.
5. **Deterministic Boot Menu Targeting:**
   Runtime interactive boot-menu hotkey injections (via QMP socket keystrokes) were replaced with a static, deterministic boot parameter configuration in `grub.cfg`. The PR40 app-launch entry is set as the default target with a short timeout, guaranteeing a reliable boot path without runtime human-monitor protocol races.
