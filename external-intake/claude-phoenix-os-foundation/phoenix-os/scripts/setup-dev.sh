#!/bin/bash
# =============================================================================
# Phoenix OS — Developer Environment Setup
# File: scripts/setup-dev.sh
#
# Bootstraps a development environment for Phoenix OS contributions.
# Run once on a fresh Ubuntu 22.04 or 24.04 LTS workstation.
#
# Usage: ./scripts/setup-dev.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ---- Color output ----
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_step()    { echo -e "\n${BOLD}${BLUE}==>${NC}${BOLD} $*${NC}"; }

echo ""
echo -e "${BOLD}Phoenix OS — Developer Environment Setup${NC}"
echo "────────────────────────────────────────"

# ---- Detect OS ----
if ! grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
    log_warn "This script is designed for Ubuntu. Proceeding anyway."
fi

# ============================================================
log_step "System packages (build tools, live-build, QEMU)"
# ============================================================

sudo apt-get update -qq

sudo apt-get install -y \
    build-essential \
    git \
    curl \
    wget \
    pkg-config \
    libssl-dev \
    dpkg-dev \
    fakeroot \
    devscripts \
    live-build \
    debootstrap \
    squashfs-tools \
    xorriso \
    grub-pc-bin \
    grub-efi-amd64-bin \
    mtools \
    dosfstools \
    isolinux \
    imagemagick \
    qemu-system-x86 \
    ovmf \
    jq \
    shellcheck

log_success "System packages installed"

# ============================================================
log_step "Rust toolchain"
# ============================================================

if command -v rustup >/dev/null 2>&1; then
    log_info "rustup already installed — updating"
    rustup update stable
else
    log_info "Installing Rust via rustup"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
    source "${HOME}/.cargo/env"
fi

rustup component add rustfmt clippy

log_success "Rust $(rustc --version) ready"

# ============================================================
log_step "Tauri CLI"
# ============================================================

if ! command -v cargo-tauri >/dev/null 2>&1; then
    cargo install tauri-cli --version "^2"
    log_success "Tauri CLI installed"
else
    log_info "Tauri CLI already installed: $(cargo tauri --version)"
fi

# ============================================================
log_step "Tauri system dependencies (WebKit, GTK)"
# ============================================================

sudo apt-get install -y \
    libwebkit2gtk-4.1-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev \
    libssl-dev \
    libjavascriptcoregtk-4.1-dev

log_success "Tauri system dependencies installed"

# ============================================================
log_step "Node.js (via nvm)"
# ============================================================

if command -v node >/dev/null 2>&1; then
    log_info "Node.js already installed: $(node --version)"
else
    log_info "Installing Node.js 20 LTS via nvm"
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    export NVM_DIR="${HOME}/.nvm"
    source "${NVM_DIR}/nvm.sh"
    nvm install 20
    nvm use 20
    nvm alias default 20
    log_success "Node.js $(node --version) installed"
fi

# ============================================================
log_step "Frontend dependencies (phoenix-control-center)"
# ============================================================

cd "${REPO_ROOT}/apps/phoenix-control-center"
npm install
log_success "Frontend dependencies installed"

# ============================================================
log_step "Git hooks (optional — lint on commit)"
# ============================================================

cd "${REPO_ROOT}"

HOOKS_DIR=".git/hooks"
if [ -d "${HOOKS_DIR}" ]; then
    cat > "${HOOKS_DIR}/pre-commit" << 'HOOK'
#!/bin/bash
# Phoenix OS pre-commit hook
set -e

# Shell script syntax check
echo "Checking shell scripts..."
find . -name "*.sh" -o -name "*.hook.chroot" -o -name "*.hook.binary" | \
    grep -v ".git" | while read f; do
    bash -n "$f" || { echo "Syntax error in $f"; exit 1; }
done

# Rust fmt check (if Rust files changed)
if git diff --cached --name-only | grep -q "\.rs$"; then
    echo "Running cargo fmt check..."
    for app in apps/phoenix-control-center apps/phoenix-recovery apps/bootforge-launcher; do
        if [ -f "${app}/Cargo.toml" ]; then
            (cd "${app}" && cargo fmt --check) || {
                echo "Run 'cargo fmt' in ${app}/ and re-stage"
                exit 1
            }
        fi
    done
fi

echo "Pre-commit checks passed."
HOOK
    chmod +x "${HOOKS_DIR}/pre-commit"
    log_success "Git pre-commit hook installed"
fi

# ============================================================
log_step "Verify setup"
# ============================================================

"${SCRIPT_DIR}/verify-host.sh"

# ============================================================
echo ""
echo -e "${BOLD}${GREEN}Developer environment ready.${NC}"
echo ""
echo "  Build ISO:          sudo ./scripts/build-iso.sh"
echo "  Build packages:     ./scripts/package-debs.sh"
echo "  Run Control Center: cd apps/phoenix-control-center && cargo tauri dev"
echo "  Run frontend only:  cd apps/phoenix-control-center && npm run dev"
echo ""
