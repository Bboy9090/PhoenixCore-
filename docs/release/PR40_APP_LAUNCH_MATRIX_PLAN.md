# PR40: App Launch Matrix Plan

**Status**: PLANNING ONLY. PR40 is not implemented yet.
**Gating Rule**: PR40 cannot run until PR39L produces trustworthy desktop-state evidence. The root observer must provide deterministic `BWOS_DESKTOP_SESSION_STARTED` before app launch validation can begin.

## Goal
Prepare the PR40 App Launch Matrix specification so that once PR39L desktop evidence stabilizes, we can immediately validate real app behavior in the booted session.

## Required Launch Apps
The following core applications must be tested for successful launch:
- Firefox ESR
- Dolphin
- Konsole
- KCalc
- KWrite
- Gwenview
- System Settings
- Discover (if installed)

## Evidence Rules
To classify an app launch as successful or failed, the following evidence must be collected:
- The application process starts.
- A window appears or the process reaches a stable state.
- No immediate crash occurs.
- Any missing dependencies are captured.
- Timeouts are captured truthfully without faking success.

## Status Classes
The outcome of each app launch probe will be categorized into one of the following classes:
- `APP_LAUNCH_PASS`: The application launched successfully, stabilized, and produced a window.
- `APP_LAUNCH_PARTIAL`: The application launched but exhibited non-fatal issues (e.g., missing optional features).
- `APP_LAUNCH_TIMEOUT`: The application failed to reach a stable state or show a window within the allotted time.
- `APP_LAUNCH_CRASH`: The application started but terminated unexpectedly.
- `APP_NOT_INSTALLED`: The requested application is not present on the system.
- `APP_DESKTOP_ENTRY_MISSING`: The `.desktop` file for the application could not be found.

## Required Logs
For each application tested, the following telemetry must be recorded:
- Launched command
- Desktop entry path (`.desktop` file)
- Process ID (PID)
- Exit code (if any)
- Timeout duration (seconds)
- Screenshot path (if available)
- Stderr/Stdout path (if available)
