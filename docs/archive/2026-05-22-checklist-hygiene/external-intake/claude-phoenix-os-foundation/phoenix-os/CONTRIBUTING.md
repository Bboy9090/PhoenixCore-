# Contributing to Phoenix OS

Thank you for your interest in contributing. Phoenix OS is a professional-grade project. Contributions are expected to meet the same standards as the rest of the codebase.

---

## Where to Start

Check the [ROADMAP.md](ROADMAP.md) for current phase priorities. The highest-value contributions right now are:

1. **Getting the first ISO to build** — validating `live-build` config, fixing package list issues
2. **Phoenix Control Center** — completing the lsblk parser in `disk.rs`, wiring up SMART data
3. **Plymouth assets** — designing and exporting the logo PNG and ember particle PNG
4. **SDDM theme testing** — verifying `Main.qml` renders correctly on target hardware
5. **ARM64 testing** — validating the build structure on Raspberry Pi 4/5

---

## Development Environment Setup

```bash
# 1. Clone the repo
git clone https://github.com/your-org/phoenix-os.git
cd phoenix-os

# 2. Set up the dev environment (installs all required tools)
./scripts/setup-dev.sh

# 3. Build custom packages
./scripts/package-debs.sh

# 4. Verify host before building the ISO
./scripts/verify-host.sh
```

For working on the React frontend only (no ISO build required):

```bash
cd apps/phoenix-control-center
npm install
npm run dev          # Starts Vite dev server at http://localhost:5173
```

For working on the Rust backend:

```bash
cd apps/phoenix-control-center
cargo build          # Build backend
cargo clippy         # Lint
cargo test           # Run tests
```

---

## Branching

| Branch | Purpose |
|--------|---------|
| `main` | Stable — tagged releases only |
| `develop` | Integration branch — all PRs target here |
| `feature/*` | Feature branches |
| `fix/*` | Bug fix branches |
| `docs/*` | Documentation-only changes |

---

## Pull Request Rules

1. **All PRs target `develop`**, not `main`
2. **CI must pass** — validate, Rust build, React build
3. **No new TODOs without a linked issue**
4. **Security-relevant changes** (disk safety model, polkit rules, udev) require a second review
5. **Package list changes** must be tested on a real Ubuntu 24.04 host (virtual machine is acceptable)

---

## Code Standards

### Shell scripts
- `set -euo pipefail` at the top of every script
- Comments explaining non-obvious logic
- Color-coded output using the established pattern (`log_info`, `log_success`, etc.)
- No hardcoded paths that differ between live session and installed system without guards

### Rust
- `cargo fmt` must pass (enforced by CI)
- `cargo clippy -- -D warnings` must pass (enforced by CI)
- All `pub fn` must have a doc comment (`///`)
- Error types must implement `std::error::Error`
- No `unwrap()` in production paths — use `?` or explicit error handling

### TypeScript / React
- Strict TypeScript (`"strict": true` in tsconfig)
- Inline styles using the Phoenix design token CSS variables
- No external UI libraries (no MUI, no Chakra) — Phoenix has its own design system
- Components under 150 lines; split otherwise

### Package lists
- One package name per line
- Group packages by purpose with section comments
- Comment out packages that are not yet verified on Ubuntu 24.04

---

## Disk Safety — Mandatory Review

Any contribution that touches the following **must** include a security review note in the PR description:

- `live-build/hooks/live/0300-disk-safety.hook.chroot`
- `packages/phoenix-tools/etc/udev/rules.d/`
- `packages/phoenix-tools/etc/polkit-1/rules.d/`
- `apps/phoenix-recovery/src/safety.rs`
- Any new disk write, format, or wipe operation

The safety model is documented in [`docs/security-model.md`](docs/security-model.md). Submissions that violate it will not be merged.

---

## Reporting Bugs

File an issue with:
- Phoenix OS version (from `VERSION` file or ISO filename)
- Host hardware (`inxi -Faz` output)
- Steps to reproduce
- Expected vs. actual behavior
- Relevant log output (`/var/log/phoenix/`, `dmesg`, `journalctl -b`)

**Security vulnerabilities**: email `security@phoenix-os.io` — do not file public issues.

---

## License

By contributing, you agree that your contributions are licensed under the MIT License. Upstream components retain their original licenses.
