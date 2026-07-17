# BootForge aka USB Creator v1

BootForge v1 is the governed desktop application lane for USB creation, ISO verification, recovery media, driver preparation, and deployment tooling inside PhoenixCore.

## Architecture

- `main.py`: desktop application entry point
- `core/`: application contracts, plugin loading, configuration, and logging
- `services/`: safe orchestration around hardware-facing engines
- `plugins/`: manifest-declared optional tools
- `tests/`: non-destructive regression tests

## Safety rules

1. No destructive disk operation without explicit device selection and confirmation.
2. Dry-run is the default for unfinished workflows.
3. Downloads must pass the existing governed registry, detached signature, and SHA-256 validation.
4. UI code never formats or writes disks directly. It calls a service boundary.
5. Windows elevation must be detected and reported before privileged operations.

## Current integration

The v1 lane wraps the repository's existing `usb_creator.py` engine rather than replacing its security controls.

## Run on Windows 10 / Python 3.11

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r bootforge_v1/requirements.txt
python -m bootforge_v1.main
```

## Initial milestone

- Desktop shell
- Read-only removable-device discovery
- Secure engine status panel
- Manifest-based plugin discovery
- Dry-run workflow boundary
- Logging and crash isolation
