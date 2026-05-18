#!/bin/bash
# scripts/native-native0-bootproof.sh - Build and run Blue Phoenix Native NATIVE-0 UEFI boot proof.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BOOTMGR_CRATE_DIR="$REPO_ROOT/native/boot/uefi-banner"
KERNEL_CRATE_DIR="$REPO_ROOT/native/kernel/uefi-kernel-stub"

NATIVE_ARCH="${NATIVE_ARCH:-x86_64}"
QEMU_TIMEOUT_SECONDS="${QEMU_TIMEOUT_SECONDS:-10}"

BUILD_DIR="$REPO_ROOT/native/build/NATIVE-0"
ESP_DIR="$BUILD_DIR/esp"
EVIDENCE_DIR="$REPO_ROOT/native/evidence/NATIVE-0"

case "$NATIVE_ARCH" in
    x86_64)
        TARGET="x86_64-unknown-uefi"
        BOOT_FILENAME="BOOTX64.EFI"
        KERNEL_FILENAME="KERNELX64.EFI"
        QEMU_BIN_DEFAULT="qemu-system-x86_64"
        OVMF_PATTERN="edk2-x86_64-code.fd"
        ;;
    aarch64|arm64)
        TARGET="aarch64-unknown-uefi"
        BOOT_FILENAME="BOOTAA64.EFI"
        KERNEL_FILENAME="KERNELAA64.EFI"
        QEMU_BIN_DEFAULT="qemu-system-aarch64"
        OVMF_PATTERN="edk2-aarch64-code.fd"
        ;;
    *)
        echo "❌ Unsupported NATIVE_ARCH: $NATIVE_ARCH (use x86_64 or aarch64)"
        exit 1
        ;;
esac

LOG_FILE="$EVIDENCE_DIR/boot-serial-${NATIVE_ARCH}.log"
DEBUG_LOG_FILE="$EVIDENCE_DIR/boot-debugcon-${NATIVE_ARCH}.log"
COMMAND_FILE="$EVIDENCE_DIR/run-command-${NATIVE_ARCH}.txt"
STATUS_FILE="$EVIDENCE_DIR/status-${NATIVE_ARCH}.txt"
LATEST_STATUS_FILE="$EVIDENCE_DIR/status.txt"

QEMU_BIN="${QEMU_BIN:-$QEMU_BIN_DEFAULT}"
OVMF_CODE_DEFAULT="$(find /opt/homebrew/Cellar/qemu -type f -name "$OVMF_PATTERN" | head -n 1 || true)"
OVMF_CODE="${OVMF_CODE:-$OVMF_CODE_DEFAULT}"

if [ -z "$OVMF_CODE" ] || [ ! -f "$OVMF_CODE" ]; then
    echo "❌ Unable to locate OVMF firmware. Set OVMF_CODE manually."
    exit 1
fi

if ! command -v "$QEMU_BIN" >/dev/null 2>&1; then
    echo "❌ QEMU binary not found: $QEMU_BIN"
    exit 1
fi

mkdir -p "$BUILD_DIR" "$ESP_DIR/EFI/BOOT" "$EVIDENCE_DIR"

echo "🛠️ Building Native UEFI boot artifact..."
rustup target add "$TARGET" >/dev/null
cargo build --release --target "$TARGET" --manifest-path "$BOOTMGR_CRATE_DIR/Cargo.toml"
cargo build --release --target "$TARGET" --manifest-path "$KERNEL_CRATE_DIR/Cargo.toml"

BOOT_EFI_SRC="$BOOTMGR_CRATE_DIR/target/$TARGET/release/bootx64.efi"
KERNEL_EFI_SRC="$KERNEL_CRATE_DIR/target/$TARGET/release/kernelx64.efi"
BOOT_EFI_DST="$ESP_DIR/EFI/BOOT/$BOOT_FILENAME"
KERNEL_EFI_DST="$ESP_DIR/EFI/BOOT/$KERNEL_FILENAME"

if [ ! -f "$BOOT_EFI_SRC" ]; then
    echo "❌ Expected EFI artifact not found: $BOOT_EFI_SRC"
    exit 1
fi
if [ ! -f "$KERNEL_EFI_SRC" ]; then
    echo "❌ Expected EFI artifact not found: $KERNEL_EFI_SRC"
    exit 1
fi

cp "$BOOT_EFI_SRC" "$BOOT_EFI_DST"
cp "$KERNEL_EFI_SRC" "$KERNEL_EFI_DST"

QEMU_CMD=(
    "$QEMU_BIN"
    -m 1024
    -nographic
    -serial stdio
    -monitor none
    -no-reboot
)

if [ "$TARGET" = "x86_64-unknown-uefi" ]; then
    QEMU_CMD+=(
        -machine q35
        -cpu qemu64
        -drive "if=pflash,format=raw,readonly=on,file=$OVMF_CODE"
        -debugcon "file:$DEBUG_LOG_FILE"
        -global isa-debugcon.iobase=0x402
        -drive "format=raw,file=fat:rw:$ESP_DIR"
    )
else
    QEMU_CMD+=(
        -machine virt
        -cpu cortex-a72
        -drive "if=pflash,format=raw,readonly=on,file=$OVMF_CODE"
        -drive "format=raw,file=fat:rw:$ESP_DIR"
    )
fi

printf '%s\n' "${QEMU_CMD[*]}" > "$COMMAND_FILE"
echo "Started: $(date -u +'%Y-%m-%dT%H:%M:%SZ')" >> "$COMMAND_FILE"

echo "🚀 Running QEMU proof boot (timeout: ${QEMU_TIMEOUT_SECONDS}s)..."
: > "$LOG_FILE"
: > "$DEBUG_LOG_FILE"
"${QEMU_CMD[@]}" >"$LOG_FILE" 2>&1 &
QEMU_PID=$!
sleep "$QEMU_TIMEOUT_SECONDS"
kill "$QEMU_PID" >/dev/null 2>&1 || true
wait "$QEMU_PID" >/dev/null 2>&1 || true

if rg -qi "NATIVE-0 BOOT PROOF" "$LOG_FILE" "$DEBUG_LOG_FILE" \
    && rg -qi "KERNEL STUB ACTIVE|handoff from boot manager confirmed" "$LOG_FILE" "$DEBUG_LOG_FILE"; then
    status_body="$(
        cat <<EOF
NATIVE-0: PASS
Native Arch: $NATIVE_ARCH
Target Triple: $TARGET
Evidence: $LOG_FILE
Debug Evidence: $DEBUG_LOG_FILE
Boot Manager EFI: $BOOT_EFI_DST
Kernel Stub EFI: $KERNEL_EFI_DST
Captured: $(date -u +'%Y-%m-%dT%H:%M:%SZ')
EOF
    )"
    printf '%s\n' "$status_body" > "$STATUS_FILE"
    printf '%s\n' "$status_body" > "$LATEST_STATUS_FILE"
    echo "✅ NATIVE-0 boot manager -> kernel handoff proof detected."
else
    status_body="$(
        cat <<EOF
NATIVE-0: INCONCLUSIVE
Native Arch: $NATIVE_ARCH
Target Triple: $TARGET
Evidence: $LOG_FILE
Debug Evidence: $DEBUG_LOG_FILE
Boot Manager EFI: $BOOT_EFI_DST
Kernel Stub EFI: $KERNEL_EFI_DST
Captured: $(date -u +'%Y-%m-%dT%H:%M:%SZ')
Reason: expected boot manager and kernel handoff markers not both found.
EOF
    )"
    printf '%s\n' "$status_body" > "$STATUS_FILE"
    printf '%s\n' "$status_body" > "$LATEST_STATUS_FILE"
    echo "⚠️ NATIVE-0 boot ran, but full handoff markers were not detected."
fi

echo "📁 Evidence written to: $EVIDENCE_DIR"
