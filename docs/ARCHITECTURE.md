# PhoenixCore Architecture

This document describes how PhoenixCore and BootForge fit together, and the major pieces inside the project.

At a high level:

- **PhoenixCore** is the recovery environment and core engine.
- **BootForge** is the USB creation and deployment layer that builds media embedding PhoenixCore (and, on macOS, OCLP).

---

## High-Level Shape

### PhoenixCore = recovery environment

PhoenixCore is the code that runs *on* the target machine when you boot from Phoenix media:

- presents a minimal UI / CLI for recovery tasks
- talks directly to disks and hardware via the Rust core
- executes recovery workflows (diagnostics, backup, reinstall, logging)

Artifacts:

- Rust crates under `crates/` (device graph, imaging, safety gates)
- CLI under `apps/cli/` (`phoenix-cli` workflows, pack management)
- Any runtime tooling packaged into the bootable environment

### BootForge = USB creation / deployment layer

BootForge runs *on a healthy host* (Windows/macOS/Linux) and is responsible for:

- building PhoenixCore + supporting bits into bootable images
- writing those images safely to USB or other removable media
- embedding extras like OpenCore Legacy Patcher for unsupported Macs

Artifacts:

- Python app under `src/` (`gui/`, `cli/`, `core/`)
- `main.py` entry point (GUI + CLI)
- platform‑specific packaging / installers (e.g. Windows `.exe`)

---

## Core Components

### Host-side builder

The **host-side builder** is everything that runs on the operator’s existing system before boot:

- BootForge Python CLI and GUI (`src/cli`, `src/gui`)
- Image assembly and packaging scripts (e.g. `src/installers`, build scripts)
- Integration with Rust crates to:
  - generate PhoenixCore runtime artifacts
  - produce bootable images and packs
  - verify artifacts (hashes, signatures where applicable)

Responsibilities:

- build and validate bootable media
- ensure images include the right PhoenixCore components and tools
- expose “safe write” flows to disks (dry‑runs, confirmations, checks)

### Bootable runtime

The **bootable runtime** is what runs after the machine is started from Phoenix media:

- PhoenixCore Rust services (device graph, imaging)
- thin shells / UIs that orchestrate workflows:
  - interactive CLI (`phoenix-cli workflow-run ...`)
  - potential TUI/GUI components on top of core services

Responsibilities:

- discover hardware and OS installations
- enforce safety rules for destructive actions
- expose well‑defined operations that higher‑level workflows can compose

### Tool modules

**Tool modules** are focused pieces of functionality layered on top of the runtime:

- device and filesystem inspection
- imaging and verification
- partition/volume management (where supported)
- OS reinstall helpers
- integration points for third‑party tools (e.g. OCLP on macOS)

They should:

- be composable from the CLI (`phoenix-cli` commands, Python wrappers)
- avoid duplicating low‑level logic already in the core
- have clear boundaries and inputs/outputs

### Recovery workflows

**Recovery workflows** orchestrate multiple tool modules into end‑to‑end flows, for example:

- “Safely back up user data from a failing disk”
- “Reinstall OS while preserving a specific partition”
- “Diagnose boot failures and export a support bundle”

They may be defined as:

- structured workflow descriptions (e.g. JSON/YAML consumed by `phoenix-cli`)
- Python‑side wizards in the BootForge GUI that call into CLI/core primitives

Goals:

- clear, explainable steps with checkpoints and confirmations
- repeatable behavior across hardware where possible
- easy to log, replay, or audit

### Logging and export

Logging and export glue together the host builder and bootable runtime:

- **Runtime logs**
  - per‑operation logs with timestamps and outcomes
  - device/volume/OS discovery results
  - errors and warnings with enough context for support

- **Evidence / export**
  - support bundles that include logs, hardware snapshot, and workflow history
  - optional anonymization where appropriate

Artifacts and locations:

- CLI options like `--report-base` in `phoenix-cli` to control where reports land
- structured outputs (JSON, text summaries) suitable for attaching to tickets or automation

---

## How It Fits Together

1. **On the host**
   - Operator runs BootForge GUI/CLI.
   - BootForge uses PhoenixCore crates and tooling to build a bootable image.
   - BootForge writes the image to USB with safety gates and verification.

2. **On the target machine**
   - Machine boots from Phoenix media into the PhoenixCore runtime.
   - Runtime discovers hardware and OS state.
   - Operator selects or triggers a recovery workflow.

3. **Workflows and logging**
   - The workflow calls into tool modules and low‑level PhoenixCore primitives.
   - All steps produce logs and (optionally) evidence bundles.
   - Operator can export results and, if needed, reboot into the recovered OS.

