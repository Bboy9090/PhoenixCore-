# Phoenix OS — Developer Workflow

Practical guide for the most common development tasks. Assumes `setup-dev.sh` has been run.

---

## Working on the Phoenix Control Center

### Frontend only (fastest iteration loop)

```bash
cd apps/phoenix-control-center
npm run dev
# Open http://localhost:5173
# All React changes hot-reload instantly
# Tauri backend calls return stub data or error gracefully
```

### Full app with live Rust backend

```bash
cd apps/phoenix-control-center
cargo tauri dev
# Compiles Rust + launches desktop window
# Rust changes: re-run `cargo tauri dev`
# React changes: hot-reload inside the window
```

### Adding a new backend command

1. Write the function in the appropriate module (`src/disk.rs`, `src/network.rs`, etc.)
2. Annotate it with `#[tauri::command]`
3. Register it in `src/main.rs` → `invoke_handler`
4. Call it from the frontend: `invoke<ReturnType>("function_name", { args })`

---

## Working on Phoenix Recovery

```bash
cd apps/phoenix-recovery
npm install
npm run dev          # Frontend only at http://localhost:5174

# Full app:
cargo tauri dev
```

**Adding a new recovery workflow:**

1. Create `src/workflows/my_workflow.rs`
2. Add `pub mod my_workflow;` to `src/workflows/mod.rs`
3. Write the command function with `#[tauri::command]`
4. Register in `src/main.rs`
5. Create a React view in `src/views/MyWorkflowView.tsx`
6. Add it to the sidebar in `src/App.tsx`

---

## Working on live-build config

### Adding a package to the ISO

```bash
# 1. Find the package name
apt-cache search <keyword>

# 2. Add to the right list
echo "my-package  # Description of why it's included" \
  >> live-build/package-lists/020-repair-tools.list.chroot

# 3. Rebuild the ISO to test
sudo ./scripts/build-iso.sh
```

### Testing a hook change without full rebuild

After a full ISO build, hooks can be tested incrementally:

```bash
cd build/
sudo lb chroot    # Re-runs chroot stage (installs packages + hooks)
sudo lb binary    # Re-assembles the ISO
```

### Inspecting the built chroot

```bash
# Mount the chroot after lb bootstrap + lb chroot:
sudo chroot build/chroot /bin/bash

# Inside the chroot — verify your changes:
ls /usr/local/bin/
cat /etc/udev/rules.d/90-phoenix-disk-policy.rules
systemctl status ufw
```

---

## Building and testing packages

```bash
# Build all plain .deb packages (fast, no Rust compilation)
./scripts/package-debs.sh

# Build all packages including Tauri apps (slow — ~10 min first time)
BUILD_TAURI=1 ./scripts/package-debs.sh

# Build a single package
./scripts/package-debs.sh phoenix-theme

# Inspect a built .deb
dpkg-deb --contents output/packages/phoenix-theme_0.1.0_all.deb
dpkg-deb --info    output/packages/phoenix-theme_0.1.0_all.deb
```

---

## Running tests

```bash
# Shell script syntax check (fast — no ISO needed)
bash -n scripts/build-iso.sh && echo OK

# Disk safety unit tests (no disks touched)
./tests/unit/test-disk-safety.sh

# ISO validation (after build)
./tests/iso-validation/validate-iso.sh output/phoenix-os-*.iso

# QEMU boot smoke test (requires KVM)
./tests/smoke/test-boot.sh output/phoenix-os-*.iso
```

---

## Debugging a failed ISO build

```bash
# 1. Check the build log
less output/lb-build-<timestamp>.log

# 2. Common failure points:
#    - Package not found: wrong name, or not in Ubuntu 24.04
#    - Hook fails: bash syntax error or missing dependency
#    - Disk full: need 35 GB free

# 3. Build with verbose output
LB_VERBOSE=1 sudo ./scripts/build-iso.sh 2>&1 | tee build-verbose.log

# 4. Partial rebuild after fixing a hook
cd build && sudo lb chroot && sudo lb binary
```

---

## Git workflow

```bash
# Create a feature branch from develop
git checkout develop
git pull
git checkout -b feature/my-feature

# Make changes, commit with conventional commit format
git add -p                          # Stage hunks selectively
git commit -m "feat(disk): add NVMe health polling"

# Push and open PR targeting develop
git push -u origin feature/my-feature
```

**Commit message format:**

```
<type>(<scope>): <short description>

Types:  feat, fix, docs, style, refactor, test, chore, build
Scopes: disk, network, system, ui, installer, live-build, packaging, ci
```

---

## Tauri app release build

```bash
# Build release .deb for a Tauri app
cd apps/phoenix-control-center
cargo tauri build

# .deb is at:
ls target/release/bundle/deb/
```

The release binary is stripped and LTO-optimised. First build takes ~5–8 minutes. Subsequent builds ~1–2 minutes with warm Cargo cache.

---

## Environment variables reference

| Variable | Default | Description |
|----------|---------|-------------|
| `ARCH` | `amd64` | Target architecture for ISO build |
| `PHOENIX_VERSION` | From `VERSION` file | Version string in ISO filename |
| `KEEP_BUILD` | unset | If set, keep lb build directory after ISO build |
| `LB_VERBOSE` | unset | If set, pass `--verbose` to lb commands |
| `BUILD_TAURI` | `0` | If `1`, build Tauri apps in `package-debs.sh` |
| `PHOENIX_SIGNING_KEY` | unset | GPG key ID for `sign-iso.sh` |
