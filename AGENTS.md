# Repository Agent Instructions

- Never edit generated/output folders.
- Keep command documentation in `.github/copilot-instructions.md` aligned with the latest verified build/test steps.
- Prefer documenting commands with exact invocations copied from source docs or scripts; avoid guessing.

## Cursor Cloud specific instructions

### Services overview

| Service | Command | Notes |
|---------|---------|-------|
| **Python CLI** | `python3 main.py --help` | Primary CLI entry point; see README for subcommands |
| **Flask web server** | `python3 website/web_server.py` | Demo/download landing page on port 5000 |
| **PyQt6 GUI** | `python3 main.py --gui` | Requires a display (Xvfb or desktop); headless environments will error |

### Key dev commands

- **Python tests:** `python3 -m pytest tests/`
- **Rust build (compilable crates):** `cargo build -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 -p phoenix-host-linux -p phoenix-host-macos -p phoenix-bootloader-core -p phoenix-wim`
- **Rust tests (compilable crates):** `cargo test -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 -p phoenix-host-linux -p phoenix-host-macos -p phoenix-bootloader-core -p phoenix-wim`
- **Rust lint:** `cargo clippy -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 -p phoenix-host-linux -p phoenix-host-macos -p phoenix-bootloader-core -p phoenix-wim`
- **Rust format check:** `cargo fmt --check`

### Known caveats

- `cargo build --workspace` / `cargo test --workspace` **fails on Linux** due to pre-existing code issues in several crates (`phoenix-host-windows` has E0365 visibility errors on non-Windows; `phoenix-imaging`, `phoenix-report`, and `phoenix-content` have missing imports/type errors). Build and test the individual crates listed above instead.
- Rust stable toolchain must be >=1.94 because `sha2 0.11.0-rc.5` (used by `report`, `workflow-engine`, `content`) requires `edition2024`.
- The CLI `system-info` command prints a `RuntimeError: wrapped C/C++ object of type GuiLogHandler has been deleted` at shutdown — this is a known harmless atexit logging teardown race in PyQt6 and does not affect functionality.
- `$HOME/.local/bin` must be on `PATH` for pip-installed scripts (pytest, flask, etc.).
