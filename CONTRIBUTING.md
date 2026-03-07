# Contributing to BootForge / Phoenix Core

Thanks for your interest in contributing! This document explains how to set up a dev environment, run tests, and submit high‑quality changes.

---

## Developer Setup

### 1. Clone the repository

```bash
git clone https://github.com/Bboy9090/PhoenixCore-.git
cd PhoenixCore-
```

### 2. Install prerequisites

- **Python**: 3.8 or newer
- **Rust**: stable toolchain via `rustup`
- **pip** and **virtualenv** (optional but recommended)

On all platforms:

```bash
pip install -r requirements.txt
```

On macOS (for OCLP integration and tests):

```bash
git submodule update --init third_party/OpenCore-Legacy-Patcher
pip install wxpython pyobjc
```

---

## Running Tests

### Python tests

```bash
python -m pytest tests/
```

Make sure tests pass before opening a PR if you touched Python code.

### Rust tests

```bash
cargo test --workspace
```

This runs all Rust tests across the workspace (Phoenix Core and CLI).

---

## Code Style & Linting

- **Python**
  - Follow PEP 8 style where practical.
  - Prefer type hints where they improve clarity.
  - Keep GUI logic separate from core logic where possible.

- **Rust**
  - Run `cargo fmt` before committing.
  - Use `cargo clippy` for lints when possible.

---

## Making Changes

1. Create a feature branch:

   ```bash
   git checkout -b feature/my-change
   ```

2. Make your changes in small, focused commits.
3. Add or update tests where it makes sense.
4. Update documentation:
   - `README.md`
   - `WINDOWS-README.txt`
   - `QUICK_START.txt`
   - `docs/oclp_integration.md`

---

## Pull Requests

Before opening a PR:

1. **Tests pass**

   ```bash
   cargo test --workspace
   python -m pytest tests/
   ```

2. **Docs updated** for any user‑facing changes.
3. **Clear description**:
   - What problem it solves
   - How it solves it
   - Any trade‑offs or limitations

---

## Reporting Bugs

When filing an issue, please include:

- OS and version (Windows/macOS/Linux)
- Python and Rust versions
- Exact command or GUI action
- Logs or stack traces when available
- Whether you are using a release build or running from source

There are dedicated issue templates for **bug reports** and **feature requests** in `.github/ISSUE_TEMPLATE/`.

---

## Security

For any security‑sensitive issues, please avoid filing public issues and instead contact the maintainer directly if contact information is available in the repo profile.

---

Thanks again for contributing!

