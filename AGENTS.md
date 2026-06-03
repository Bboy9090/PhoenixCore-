# Repository Agent Instructions

# AGENTS.md

You are working in this repository as a fast senior coding agent.

Primary rule:
Do the requested task only. Do not perform broad audits, redesigns, rewrites, dependency upgrades, or unrelated cleanup unless explicitly asked.

Workflow:

1. Read the user request carefully.
2. Inspect only the files most likely related to the request.
3. Make the smallest complete fix.
4. Run the most relevant check available.
5. Summarize changed files, commands run, and any remaining risks.

Do not:

* Rewrite working systems.
* Change unrelated files.
* Install packages unless required.
* Use browser, Chrome, Google Drive, Canva, presentations, documents, or spreadsheets unless the task explicitly needs them.
* Spend time on cosmetic cleanup unless requested.
* Create placeholder features and call them finished.

Project priorities:

* Working buttons and routes.
* Complete screen flow.
* Clean mobile/iOS/macOS behavior.
* Stable builds.
* Readable code.
* Fast iteration.

When fixing navigation:

* Verify the button handler.
* Verify the route/screen exists.
* Verify the target component renders.
* Verify state/data needed by the screen is available.
* Avoid blank-screen failures.

Completion format:

* What changed
* Files changed
* Commands run
* What was verified
* What still needs manual testing

* Never edit generated/output folders.
* Keep command documentation in `.github/copilot-instructions.md` aligned with the latest verified build/test steps.
* Prefer documenting commands with exact invocations copied from source docs or scripts; avoid guessing.

## Cursor Cloud specific instructions

### Services overview

| Service | Command | Notes |
|---------|---------|-------|
| **Python CLI** | `python3 main.py --help` | Primary CLI entry point; see README for subcommands |
| **Flask web server** | `python3 web_server.py` | Demo/download landing page on port 5000 |
| **PyQt6 GUI** | `python3 main.py --gui` | Requires a display (Xvfb or desktop); headless environments will error |

### Key dev commands

* **Python tests:** `python3 -m pytest tests/`
* **Rust build (compilable crates):** `cargo build -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 -p phoenix-host-linux -p phoenix-host-macos -p phoenix-bootloader-core -p phoenix-wim`
* **Rust tests (compilable crates):** `cargo test -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 -p phoenix-host-linux -p phoenix-host-macos -p phoenix-bootloader-core -p phoenix-wim`
* **Rust lint:** `cargo clippy -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 -p phoenix-host-linux -p phoenix-host-macos -p phoenix-bootloader-core -p phoenix-wim`
* **Rust format check:** `cargo fmt --check`

### Known caveats

* `cargo build --workspace` / `cargo test --workspace` **fails on Linux** due to pre-existing code issues in several crates (`phoenix-host-windows` has E0365 visibility errors on non-Windows; `phoenix-imaging`, `phoenix-report`, and `phoenix-content` have missing imports/type errors). Build and test the individual crates listed above instead.
* Rust stable toolchain must be >=1.94 because `sha2 0.11.0-rc.5` (used by `report`, `workflow-engine`, `content`) requires `edition2024`.
* The CLI `system-info` command prints a `RuntimeError: wrapped C/C++ object of type GuiLogHandler has been deleted` at shutdown — this is a known harmless atexit logging teardown race in PyQt6 and does not affect functionality.
* `$HOME/.local/bin` must be on `PATH` for pip-installed scripts (pytest, flask, etc.).
