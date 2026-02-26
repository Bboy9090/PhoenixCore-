# BootForge

Professional cross-platform OS deployment tool for creating bootable USB drives. Supports Windows, Linux, and macOS (including OpenCore Legacy Patcher for unsupported Macs).

## Features

- **Universal USB creation**: Windows, Linux, macOS installers
- **OCLP integration**: Boot unsupported Macs on newer macOS via embedded OpenCore Legacy Patcher
- **Target & Kext config**: Select Mac model, kexts (Graphics, Audio, WiFi/Bluetooth, USB), and OpenCore settings
- **Phoenix Core**: Rust-based device graph, safety gates, imaging primitives
- **PyQt6 GUI**: Modern wizard workflow and one-click profiles

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Optional: OCLP (for Mac patching)
git submodule update --init third_party/OpenCore-Legacy-Patcher

# Run GUI
python main.py --gui

# Or CLI
python main.py --help
```

## OCLP (OpenCore Legacy Patcher)

BootForge embeds [OpenCore Legacy Patcher](https://github.com/dortania/OpenCore-Legacy-Patcher) to run unsupported Macs on macOS 11–15.

**Setup (macOS only):**
```bash
git submodule update --init third_party/OpenCore-Legacy-Patcher
pip install wxpython pyobjc
```

**Usage:**
- **Tools → OpenCore Legacy Patcher** – Launch full OCLP GUI
- **Tools → OCLP Target & Kext Config** – Configure target Mac, kexts, SIP, SecureBootModel
- OCLP wizard – Step-by-step detection → config → build

See [docs/oclp_integration.md](docs/oclp_integration.md) for details.

## Build & Test

```bash
# Python build
python src/installers/build_installer.py

# Run tests
python -m pytest tests/

# Rust (Phoenix Core)
cargo build --workspace
cargo test --workspace
```

## Phoenix Core

Windows-first core engine providing:
- Device graph (disks + volumes)
- Safety gates
- Read-only imaging primitives (chunk plan + SHA-256)
- Evidence reports

```bash
# Workflow runner
phoenix-cli workflow-run --file workflow.json --report-base .

# Pack export
phoenix-cli pack-export --manifest pack.json --out phoenix-pack.zip
```

## Layout

```
.
├── main.py                 # BootForge entry point
├── src/                    # Python application
│   ├── gui/               # PyQt6 GUI, wizards, OCLP config
│   ├── core/              # Config, safety, OCLP integration
│   └── cli/               # CLI interface
├── third_party/
│   └── OpenCore-Legacy-Patcher/  # OCLP submodule
├── docs/
│   └── oclp_integration.md
├── crates/                 # Phoenix Core (Rust)
└── apps/cli/               # phoenix-cli
```

## License

OCLP is BSD 2-Clause. See `third_party/OpenCore-Legacy-Patcher/LICENSE`.
