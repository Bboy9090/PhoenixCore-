#!/bin/bash

################################################################################
# Phoenix OS ISO Build Script
# 
# This script builds a bootable Phoenix OS ISO image using live-build
# 
# Usage:
#   ./scripts/build-iso.sh              # Full build
#   ./scripts/build-iso.sh --quick      # Quick build (skip some steps)
#   ./scripts/build-iso.sh --clean      # Clean and rebuild
#   ./scripts/build-iso.sh --help       # Show help
#
# Requirements:
#   - Ubuntu 22.04 LTS or Debian 12
#   - live-build installed
#   - 50GB free disk space
#   - 4GB RAM minimum
#   - Internet connection
#
# Output:
#   - dist/phoenix-os-2.0.0-amd64.iso
#   - dist/SHA256SUMS
#   - dist/MANIFEST
#
################################################################################

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/live-build"
DIST_DIR="$PROJECT_ROOT/dist"
LOG_DIR="$PROJECT_ROOT/logs"
VERSION="2.0.0"
ARCH="amd64"
ISO_NAME="phoenix-os-${VERSION}-${ARCH}.iso"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Print header
print_header() {
    echo "═══════════════════════════════════════════════════════════"
    echo "Phoenix OS ISO Build System"
    echo "═══════════════════════════════════════════════════════════"
    echo "Version: $VERSION"
    echo "Architecture: $ARCH"
    echo "Build Date: $(date)"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
}

# Show help
show_help() {
    cat << EOF
Phoenix OS ISO Build Script

Usage: $0 [OPTIONS]

Options:
  --quick       Skip optional steps (faster build)
  --clean       Clean and rebuild from scratch
  --verbose     Show detailed build output
  --help        Show this help message

Examples:
  $0                    # Full build
  $0 --quick            # Quick build
  $0 --clean            # Clean rebuild
  $0 --verbose          # Verbose output

Output:
  ISO Image:    $DIST_DIR/$ISO_NAME
  Checksums:    $DIST_DIR/SHA256SUMS
  Manifest:     $DIST_DIR/MANIFEST
  Build Log:    $LOG_DIR/build.log

Requirements:
  - Ubuntu 22.04 LTS or Debian 12
  - live-build installed
  - 50GB free disk space
  - 4GB RAM minimum
  - Internet connection

EOF
}

# Verify prerequisites
verify_prerequisites() {
    log_info "Verifying prerequisites..."
    
    # Check OS
    if ! grep -E "Ubuntu 22.04|Debian 12" /etc/os-release > /dev/null; then
        log_warn "This script is optimized for Ubuntu 22.04 LTS or Debian 12"
        log_warn "Other distributions may work but are not officially supported"
    fi
    
    # Check live-build
    if ! command -v lb &> /dev/null; then
        log_error "live-build not found. Install with:"
        echo "  sudo apt-get install live-build"
        exit 1
    fi
    log_success "live-build found"
    
    # Check disk space
    AVAILABLE_SPACE=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=$((50 * 1024 * 1024))  # 50GB in KB
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        log_error "Insufficient disk space. Required: 50GB, Available: $((AVAILABLE_SPACE / 1024 / 1024))GB"
        exit 1
    fi
    log_success "Disk space OK ($((AVAILABLE_SPACE / 1024 / 1024))GB available)"
    
    # Check RAM
    AVAILABLE_RAM=$(free -m | awk 'NR==2 {print $7}')
    REQUIRED_RAM=2048  # 2GB in MB
    if [ "$AVAILABLE_RAM" -lt "$REQUIRED_RAM" ]; then
        log_warn "Low RAM available. Build may be slow. Recommended: 4GB, Available: ${AVAILABLE_RAM}MB"
    fi
    log_success "RAM OK (${AVAILABLE_RAM}MB available)"
    
    # Check internet
    if ! ping -c 1 archive.ubuntu.com &> /dev/null; then
        log_error "No internet connection. Internet is required for building."
        exit 1
    fi
    log_success "Internet connection OK"
    
    # Check sudo
    if ! sudo -n true 2> /dev/null; then
        log_error "This script requires sudo privileges without password prompt"
        exit 1
    fi
    log_success "Sudo privileges OK"
    
    echo ""
}

# Create directories
create_directories() {
    log_info "Creating directories..."
    mkdir -p "$DIST_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$BUILD_DIR/config"
    log_success "Directories created"
    echo ""
}

# Clean previous build
clean_build() {
    log_info "Cleaning previous build..."
    cd "$BUILD_DIR"
    
    if [ -f "config/auto/config" ]; then
        sudo lb clean --purge 2>&1 | tee -a "$LOG_DIR/clean.log"
        log_success "Previous build cleaned"
    else
        log_warn "No previous build found"
    fi
    
    echo ""
}

# Configure live-build
configure_livebuild() {
    log_info "Configuring live-build..."
    cd "$BUILD_DIR"
    
    # Run the configuration script
    if [ -x "config/auto/config" ]; then
        bash config/auto/config 2>&1 | tee -a "$LOG_DIR/config.log"
        log_success "Live-build configured"
    else
        log_error "Configuration script not found or not executable"
        exit 1
    fi
    
    echo ""
}

# Build ISO
build_iso() {
    log_info "Building ISO image..."
    log_info "This may take 30-60 minutes depending on your system..."
    echo ""
    
    cd "$BUILD_DIR"
    
    # Run live-build
    if sudo lb build 2>&1 | tee -a "$LOG_DIR/build.log"; then
        log_success "ISO build completed"
    else
        log_error "ISO build failed. Check $LOG_DIR/build.log for details"
        exit 1
    fi
    
    echo ""
}

# Move ISO to dist directory
move_iso() {
    log_info "Moving ISO to distribution directory..."
    
    if [ -f "$BUILD_DIR/$ISO_NAME" ]; then
        sudo mv "$BUILD_DIR/$ISO_NAME" "$DIST_DIR/$ISO_NAME"
        sudo chown "$(whoami):$(whoami)" "$DIST_DIR/$ISO_NAME"
        log_success "ISO moved to $DIST_DIR/$ISO_NAME"
    else
        log_error "ISO file not found in $BUILD_DIR"
        exit 1
    fi
    
    echo ""
}

# Generate checksums
generate_checksums() {
    log_info "Generating checksums..."
    cd "$DIST_DIR"
    
    if sha256sum "$ISO_NAME" > SHA256SUMS; then
        log_success "Checksums generated"
        cat SHA256SUMS
    else
        log_error "Failed to generate checksums"
        exit 1
    fi
    
    echo ""
}

# Generate manifest
generate_manifest() {
    log_info "Generating package manifest..."
    cd "$BUILD_DIR"
    
    if [ -f "binary/live/filesystem.packages" ]; then
        cp binary/live/filesystem.packages "$DIST_DIR/MANIFEST"
        log_success "Manifest generated"
    else
        log_warn "Manifest file not found"
    fi
    
    echo ""
}

# Verify ISO
verify_iso() {
    log_info "Verifying ISO integrity..."
    cd "$DIST_DIR"
    
    if sha256sum -c SHA256SUMS; then
        log_success "ISO integrity verified"
    else
        log_error "ISO integrity check failed"
        exit 1
    fi
    
    echo ""
}

# Print build summary
print_summary() {
    echo "═══════════════════════════════════════════════════════════"
    echo "Build Complete!"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    log_success "ISO Image: $DIST_DIR/$ISO_NAME"
    log_success "Size: $(du -h "$DIST_DIR/$ISO_NAME" | cut -f1)"
    log_success "Checksums: $DIST_DIR/SHA256SUMS"
    log_success "Manifest: $DIST_DIR/MANIFEST"
    log_success "Build Log: $LOG_DIR/build.log"
    echo ""
    echo "Next steps:"
    echo "  1. Test the ISO:"
    echo "     qemu-system-x86_64 -m 2048 -cdrom $DIST_DIR/$ISO_NAME"
    echo ""
    echo "  2. Write to USB:"
    echo "     sudo dd if=$DIST_DIR/$ISO_NAME of=/dev/sdX bs=4M status=progress"
    echo ""
    echo "  3. Verify checksums:"
    echo "     sha256sum -c $DIST_DIR/SHA256SUMS"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
}

# Main build process
main() {
    print_header
    
    # Parse arguments
    QUICK_BUILD=false
    CLEAN_BUILD=false
    VERBOSE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick)
                QUICK_BUILD=true
                shift
                ;;
            --clean)
                CLEAN_BUILD=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Run build steps
    verify_prerequisites
    create_directories
    
    if [ "$CLEAN_BUILD" = true ]; then
        clean_build
    fi
    
    configure_livebuild
    build_iso
    move_iso
    generate_checksums
    generate_manifest
    verify_iso
    print_summary
}

# Run main function
main "$@"
