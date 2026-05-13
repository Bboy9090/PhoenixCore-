#!/bin/bash
# =============================================================================
# Phoenix OS — Unit Tests: Disk Safety Validation
# File: tests/unit/test-disk-safety.sh
#
# Tests the shell-level device path validation rules used across Phoenix tools.
# These tests do NOT touch any real disks.
# =============================================================================

set -euo pipefail

PASS=0; FAIL=0

GREEN='\033[0;32m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'

assert_valid() {
    local path="$1"
    local desc="${2:-${path}}"
    if is_valid_device_path "${path}"; then
        echo -e "  ${GREEN}✓${NC} VALID   ${desc}"
        (( PASS++ )) || true
    else
        echo -e "  ${RED}✗${NC} INVALID ${desc} (expected VALID)"
        (( FAIL++ )) || true
    fi
}

assert_invalid() {
    local path="$1"
    local desc="${2:-${path}}"
    if ! is_valid_device_path "${path}"; then
        echo -e "  ${GREEN}✓${NC} REJECTED ${desc}"
        (( PASS++ )) || true
    else
        echo -e "  ${RED}✗${NC} ACCEPTED ${desc} (expected REJECTED)"
        (( FAIL++ )) || true
    fi
}

# Mirrors the validation logic in apps/phoenix-recovery/src/safety.rs
is_valid_device_path() {
    local path="$1"
    # Must start with /dev/
    [[ "${path}" == /dev/* ]] || return 1
    # Must not contain path traversal
    [[ "${path}" != *..* ]] || return 1
    [[ "${path}" != *//* ]] || return 1
    # Must not be too long
    [[ ${#path} -le 25 ]] || return 1
    # Must match known patterns
    local dev="${path#/dev/}"
    [[ "${dev}" == sd[a-z]   ]] && return 0
    [[ "${dev}" == sd[a-z][0-9]* ]] && return 0
    [[ "${dev}" == nvme[0-9]n[0-9] ]] && return 0
    [[ "${dev}" == nvme[0-9]n[0-9]p[0-9]* ]] && return 0
    [[ "${dev}" == mmcblk[0-9] ]] && return 0
    [[ "${dev}" == mmcblk[0-9]p[0-9]* ]] && return 0
    [[ "${dev}" == vd[a-z] ]] && return 0
    return 1
}

echo ""
echo -e "${BOLD}Phoenix OS — Disk Safety Validation Tests${NC}"
echo "──────────────────────────────────────────"

echo ""
echo "Valid device paths:"
assert_valid "/dev/sda"      "SATA disk"
assert_valid "/dev/sdb"      "SATA disk 2"
assert_valid "/dev/sda1"     "SATA partition"
assert_valid "/dev/sdb2"     "SATA partition 2"
assert_valid "/dev/nvme0n1"  "NVMe disk"
assert_valid "/dev/nvme0n1p1" "NVMe partition"
assert_valid "/dev/mmcblk0"  "eMMC disk"
assert_valid "/dev/mmcblk0p1" "eMMC partition"
assert_valid "/dev/vda"      "VirtIO disk"

echo ""
echo "Invalid device paths (must be rejected):"
assert_invalid ""                        "Empty string"
assert_invalid "/etc/passwd"             "Not a device"
assert_invalid "/dev/../etc/shadow"      "Path traversal"
assert_invalid "/dev//sda"               "Double slash"
assert_invalid "sda"                     "No /dev/ prefix"
assert_invalid "/dev/sda; rm -rf /"      "Shell injection"
assert_invalid "/dev/$(echo sda)"        "Command substitution"
assert_invalid "/dev/xxxxxxxxxxxxxxxxxxx" "Too long"

echo ""
echo "──────────────────────────────────────────"
echo -e "${BOLD}Results:${NC} ${GREEN}${PASS} passed${NC}  ${RED}${FAIL} failed${NC}"
echo ""

[[ "${FAIL}" -gt 0 ]] && exit 1 || exit 0
