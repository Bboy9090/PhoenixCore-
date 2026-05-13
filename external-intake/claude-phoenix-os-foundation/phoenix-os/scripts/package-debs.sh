#!/bin/bash
# =============================================================================
# Phoenix OS — Custom Package Builder
# File: scripts/package-debs.sh
#
# Builds all Phoenix OS custom .deb packages from source and copies them
# to live-build/config/packages.chroot/ for inclusion in the ISO.
#
# Usage:
#   ./scripts/package-debs.sh                  # Build all packages
#   ./scripts/package-debs.sh phoenix-theme     # Build a specific package
#
# Requirements: dpkg-deb, fakeroot
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PACKAGES_DIR="${REPO_ROOT}/packages"
BUILD_DIR="${REPO_ROOT}/build"
CHROOT_PACKAGES_DIR="${BUILD_DIR}/config/packages.chroot"

# ---- Color output ----
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC} $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_step()    { echo -e "\n${BOLD}${BLUE}==>${NC}${BOLD} $*${NC}"; }

# ---- Check requirements ----
for tool in dpkg-deb fakeroot; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
        log_error "Required tool not found: ${tool}"
        log_error "Install with: sudo apt install dpkg-dev fakeroot"
        exit 1
    fi
done

# ---- Prepare output directory ----
mkdir -p "${CHROOT_PACKAGES_DIR}"

# ---- Determine which packages to build ----
TARGET_PACKAGE="${1:-}"

# ---- Plain dpkg-deb package builder ----
build_deb_package() {
    local pkg_name="$1"
    local pkg_dir="${PACKAGES_DIR}/${pkg_name}"

    if [[ ! -d "${pkg_dir}" ]]; then
        log_error "Package directory not found: ${pkg_dir}"
        return 1
    fi

    if [[ ! -f "${pkg_dir}/DEBIAN/control" ]]; then
        log_error "No DEBIAN/control found in ${pkg_dir}"
        return 1
    fi

    log_step "Building .deb: ${pkg_name}"

    local pkg_version pkg_arch
    pkg_version=$(grep "^Version:" "${pkg_dir}/DEBIAN/control" | awk '{print $2}')
    pkg_arch=$(grep "^Architecture:" "${pkg_dir}/DEBIAN/control" | awk '{print $2}')

    local deb_name="${pkg_name}_${pkg_version}_${pkg_arch}.deb"
    local output_path="${CHROOT_PACKAGES_DIR}/${deb_name}"

    log_info "Package: ${deb_name}"

    # Fix DEBIAN script permissions
    for script in postinst preinst postrm prerm; do
        [[ -f "${pkg_dir}/DEBIAN/${script}" ]] && chmod 755 "${pkg_dir}/DEBIAN/${script}"
    done

    fakeroot dpkg-deb --build "${pkg_dir}" "${output_path}"
    dpkg-deb --info "${output_path}" >/dev/null

    log_success "Built: ${deb_name}"
    echo "  SHA256: $(sha256sum "${output_path}" | cut -d' ' -f1)"
}

# ---- Tauri app builder ----
# Builds a Tauri app via `cargo tauri build` and copies the resulting .deb
# from target/release/bundle/deb/ to the chroot packages directory.
build_tauri_app() {
    local app_name="$1"
    local app_dir="${REPO_ROOT}/apps/${app_name}"

    if [[ ! -d "${app_dir}" ]]; then
        log_error "App directory not found: ${app_dir}"
        return 1
    fi

    if [[ ! -f "${app_dir}/tauri.conf.json" ]]; then
        log_error "No tauri.conf.json in ${app_dir} — skipping"
        return 1
    fi

    # Check Rust and Tauri CLI are available
    if ! command -v cargo >/dev/null 2>&1; then
        log_error "cargo not found. Run ./scripts/setup-dev.sh first."
        return 1
    fi

    if ! cargo tauri --version >/dev/null 2>&1; then
        log_error "cargo-tauri not found. Run: cargo install tauri-cli --version '^2'"
        return 1
    fi

    log_step "Building Tauri app: ${app_name}"

    # Install npm dependencies if package.json exists in the app root
    if [[ -f "${app_dir}/package.json" ]]; then
        log_info "Installing npm dependencies..."
        (cd "${app_dir}" && npm install --silent)
    fi

    # Build the Tauri application
    log_info "Running cargo tauri build..."
    (cd "${app_dir}" && cargo tauri build 2>&1)

    # Find the generated .deb
    local deb_path
    deb_path=$(find "${app_dir}/target/release/bundle/deb" -name "*.deb" 2>/dev/null | head -1)

    if [[ -z "${deb_path}" ]]; then
        log_error "No .deb found in ${app_dir}/target/release/bundle/deb/"
        log_error "Check that bundle.linux.deb is configured in tauri.conf.json"
        return 1
    fi

    local deb_name
    deb_name=$(basename "${deb_path}")
    cp "${deb_path}" "${CHROOT_PACKAGES_DIR}/${deb_name}"

    log_success "Built Tauri app: ${deb_name}"
    echo "  SHA256: $(sha256sum "${CHROOT_PACKAGES_DIR}/${deb_name}" | cut -d' ' -f1)"
}

# ---- Build packages ----
echo ""
echo -e "${BOLD}Phoenix OS — Custom Package Builder${NC}"
echo "────────────────────────────────────"
echo ""
echo "Mode: plain .deb packages (Tauri apps require --tauri flag)"
echo ""

BUILT=0
FAILED=0

# Set BUILD_TAURI=1 to also build Tauri apps (slow — requires Rust + Node)
BUILD_TAURI="${BUILD_TAURI:-0}"

if [[ -n "${TARGET_PACKAGE}" ]]; then
    build_deb_package "${TARGET_PACKAGE}" && (( BUILT++ )) || (( FAILED++ ))
else
    # Plain .deb packages (fast — no compilation)
    PLAIN_PACKAGES=(
        phoenix-theme
        phoenix-tools
        phoenix-welcome
    )

    for pkg in "${PLAIN_PACKAGES[@]}"; do
        build_deb_package "${pkg}" && (( BUILT++ )) || {
            (( FAILED++ )) || true
            log_warn "Package ${pkg} failed. Continuing."
        }
    done

    # Tauri apps (slow — opt-in with BUILD_TAURI=1)
    if [[ "${BUILD_TAURI}" == "1" ]]; then
        log_info "BUILD_TAURI=1: building Tauri applications"
        TAURI_APPS=(
            phoenix-control-center
            phoenix-recovery
            bootforge-launcher
        )
        for app in "${TAURI_APPS[@]}"; do
            build_tauri_app "${app}" && (( BUILT++ )) || {
                (( FAILED++ )) || true
                log_warn "Tauri app ${app} failed. Continuing."
            }
        done
    else
        log_warn "Skipping Tauri app builds (set BUILD_TAURI=1 to include them)"
        log_warn "The ISO will use stub .deb packages for Phoenix apps"
        # Create stub .deb for phoenix-control-center so package list 080 installs cleanly
        build_deb_package "phoenix-control-center" && (( BUILT++ )) || (( FAILED++ ))
    fi
fi

# ---- Summary ----
echo ""
echo "────────────────────────────────────"
echo -e "${BOLD}Results:${NC} ${GREEN}${BUILT} built${NC}  $([ "${FAILED}" -gt 0 ] && echo "${RED}${FAILED} failed${NC}" || echo "0 failed")"

if [[ "${FAILED}" -gt 0 ]]; then
    log_error "Some packages failed to build. Check output above."
    exit 1
fi

echo ""
log_success "All packages built. Files in: ${CHROOT_PACKAGES_DIR}"
echo ""
ls -lh "${CHROOT_PACKAGES_DIR}"/*.deb 2>/dev/null || true
echo ""
