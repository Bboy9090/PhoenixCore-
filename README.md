# BootForge (Phoenix Core)

BootForge is a professional, cross‑platform OS deployment tool for creating safe, bootable USB drives. It supports Windows, Linux, and macOS, with first‑class integration for OpenCore Legacy Patcher (OCLP) so you can boot unsupported Macs on newer macOS versions.

Under the hood, Phoenix Core (Rust) provides a safety‑focused device graph and imaging engine; the Python app (with a PyQt6 GUI and CLI) provides a modern workflow on top.

---

## Features

- **Universal USB creation**
  - Create installers for **Windows**, **Linux**, and **macOS**
  - Cross‑platform: runs on Windows, macOS, and Linux

- **OCLP (OpenCore Legacy Patcher) integration**
  - Embedded [OpenCore Legacy Patcher](https://github.com/dortania/OpenCore-Legacy-Patcher) via git submodule
  - One‑click access to full OCLP GUI from BootForge
  - Target & kext configuration wizard for unsupported Macs

- **Phoenix Core (Rust engine)**
  - Device graph for disks and volumes
  - Safety gates to avoid destructive operations
  - Read‑only imaging primitives (chunk plan + SHA‑256)
  - Evidence reports for auditability

- **PyQt6 GUI**
  - Wizard‑style workflow
  - Hardware detection and model selection
  - Profiles and presets for common setups (e.g. iMac 18,1)

- **CLI tools**
  - Python CLI (`python main.py …`) for scripting and automation
  - Rust CLI (`phoenix-cli`) for low‑level workflows and pack management

---

## Supported Platforms & Requirements

| Component       | Windows                          | macOS                            | Linux                                 |
| -------------- | -------------------------------- | -------------------------------- | ------------------------------------- |
| Python         | 3.8+                             | 3.8+                             | 3.8+                                  |
| Rust           | Stable toolchain (`rustup`)      | Stable toolchain                 | Stable toolchain                      |
| GUI            | PyQt6                            | PyQt6                            | PyQt6                                 |
| OCLP           | n/a                              | Required for unsupported Macs    | n/a                                   |
| Extras (OCLP)  | –                                | `wxpython`, `pyobjc`             | –                                     |

> Exact versions may evolve; see `requirements.txt` and `Cargo.toml` for authoritative details.

---

## Project Layout

```text
.
├── main.py                 # BootForge entry point
├── src/                    # Python application
│   ├── gui/                # PyQt6 GUI, wizards, OCLP config
│   ├── core/               # Config, safety, OCLP integration
│   └── cli/                # CLI interface
├── crates/                 # Phoenix Core (Rust workspace)
├── apps/cli/               # phoenix-cli (Rust CLI)
├── docs/
│   └── oclp_integration.md # Detailed OCLP integration docs
├── third_party/
│   └── OpenCore-Legacy-Patcher/  # OCLP as git submodule
├── QUICK_START.txt         # Guided macOS USB quick start (iMac 18,1 example)
├── WINDOWS-README.txt      # Windows‑specific setup and usage
└── …
```

---

## Quick Start (Source Code)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Optional: OCLP (for Mac patching; macOS only)
git submodule update --init third_party/OpenCore-Legacy-Patcher

# Run GUI
python main.py --gui

# Or CLI
python main.py --help
```

---

## Platform-Specific Guides

### Windows

See `WINDOWS-README.txt` for full details. In short:

- Extract the BootForge Windows package (e.g. `bootforge-windows.zip`) to a folder, then run `windows-setup.bat` as Administrator to install dependencies.
- Use an elevated Command Prompt or PowerShell for USB operations.

Example commands:

```powershell
# List devices
python main.py list-devices

# Dry‑run image write
python main.py write-image -i windows10.iso -d \\.\PhysicalDrive1 --dry-run

# Format a device
python main.py format-device -d \\.\PhysicalDrive1 -f fat32
```

Safety features include:

- Multi‑step confirmations before destructive operations
- `--dry-run` mode to preview what will happen
- Device health checks and clear device path display

> **Note:** The standalone `BootForge.exe` GUI build is in progress. For now, running via Python is the supported path on Windows.

### macOS + OCLP

BootForge vendors [OpenCore Legacy Patcher](https://github.com/dortania/OpenCore-Legacy-Patcher) via a git submodule and exposes it through the GUI.

**Setup (macOS only):**

```bash
git submodule update --init third_party/OpenCore-Legacy-Patcher
pip install wxpython pyobjc
```

**From within BootForge:**

- `Tools → OpenCore Legacy Patcher` – Launches the full OCLP GUI
- `Tools → OCLP Target & Kext Config` – Configure:
  - Target Mac model (searchable list)
  - Target macOS version (11.0–15.0)
  - Kexts: Graphics, Audio, WiFi/Bluetooth, USB
  - SIP, `SecureBootModel`, verbose boot, etc.

See `docs/oclp_integration.md` for full details.

### Example: iMac 18,1 macOS USB

`QUICK_START.txt` walks through a full end‑to‑end flow for an iMac 18,1, including:

- Running the GUI (`python3 main.py --gui` on Mac/Linux; `BootForge.exe` planned for Windows)
- Selecting the iMac 18,1 model
- Choosing a macOS installer (Ventura recommended, Sonoma supported with caveats)
- Building and booting from the USB
- Running OCLP post‑install patches

---

## Phoenix Core (Rust)

Phoenix Core is a Windows‑first Rust engine for safe imaging and device management.

```bash
# Build and test the Rust workspace
cargo build --workspace
cargo test --workspace
```

Key capabilities:

- Device graph representation (disks, partitions, volumes)
- Safety gates around destructive operations
- Read‑only imaging with SHA‑256 verification
- Workflow runner and pack export via `phoenix-cli`:

```bash
# Workflow runner
phoenix-cli workflow-run --file workflow.json --report-base .

# Pack export
phoenix-cli pack-export --manifest pack.json --out phoenix-pack.zip
```

---

## Build & Test

Python side:

```bash
# Build Python installer/package
python src/installers/build_installer.py

# Run Python tests
python -m pytest tests/
```

Rust side:

```bash
cargo build --workspace
cargo test --workspace
```

> GitHub Actions run Rust build + tests on Windows (`.github/workflows/ci-windows.yml`). See below for extended CI plans.

---

## Status, Known Issues & Roadmap

**What works (per docs and CI):**

- Rust core builds/tests on Windows  
- Windows CLI USB operations with safety checks and `--dry-run`  
- PyQt6 GUI and CLI flows  
- OCLP integration on macOS  
- Guided flows such as the iMac 18,1 quick‑start  

**Known rough edges:**

- GUI **Manual Selection** path can crash in some scenarios (see `QUICK_START.txt`).  
- Windows standalone GUI (`BootForge.exe`) is still “coming soon”.  
- Python tests are not yet wired into CI across all platforms.  
- OCLP is macOS‑only by design (disabled on other platforms).  

**Near‑term roadmap:**

- Add full cross‑platform CI for Python and Rust (Windows/macOS/Linux).  
- Publish release artifacts (Windows `.exe`, macOS app bundle, Linux AppImage) on GitHub Releases.  
- Improve GUI error messages around device selection and OCLP failures.  
- Document and stabilize the Windows packaging pipeline.  

---

## Contributing

Pull requests and issues are welcome.

Before opening a PR:

1. Make sure `cargo test --workspace` passes.
2. Run Python tests with `python -m pytest tests/` (if applicable to your changes).
3. Update docs (`README.md`, `WINDOWS-README.txt`, `QUICK_START.txt`, `docs/oclp_integration.md`) where relevant.
4. Follow the guidelines in `CONTRIBUTING.md`.

See `CONTRIBUTING.md` for full details.

---

## License

- **BootForge / Phoenix Core** – Licensed under the MIT License, see `LICENSE`.
- **OpenCore Legacy Patcher** – BSD 2‑Clause, see `third_party/OpenCore-Legacy-Patcher/LICENSE`.

