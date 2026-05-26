# App Launch Matrix Data Model

This document outlines the data schema and model for tracking application launch stability across Phoenix OS / Blue Phoenix OS editions.

**Note**: This model is currently in the PLANNING phase (PR40) and is gated by the completion of PR39L.

## Schema Overview

The matrix will record the launch status of a predefined set of core applications per ISO build attempt.

### Probe Record
Each app launch probe will generate a record containing the following fields:

- `app_id`: Identifier for the application (e.g., `firefox-esr`, `dolphin`)
- `command`: The exact command launched (e.g., `/usr/bin/firefox`)
- `desktop_entry`: Path to the `.desktop` file used to launch the app
- `pid`: Process ID of the launched application
- `status`: The final classification of the launch attempt (see Status Classes)
- `exit_code`: The numeric exit code if the process terminated (optional)
- `timeout_seconds`: The configured or elapsed timeout for the probe
- `screenshot_path`: Path to the graphical capture of the app window (if available)
- `log_path`: Path to the captured stdout/stderr from the application (if available)

### Status Classes
- `APP_LAUNCH_PASS`
- `APP_LAUNCH_PARTIAL`
- `APP_LAUNCH_TIMEOUT`
- `APP_LAUNCH_CRASH`
- `APP_NOT_INSTALLED`
- `APP_DESKTOP_ENTRY_MISSING`

### Target Applications
- Firefox ESR
- Dolphin
- Konsole
- KCalc
- KWrite
- Gwenview
- System Settings
- Discover (if installed)

### Dependencies & Gating
The reliability of this model strictly depends on the host session stability. App probes MUST NOT be initiated unless the system root observer has emitted a valid `BWOS_DESKTOP_SESSION_STARTED` marker (PR39L requirement).
