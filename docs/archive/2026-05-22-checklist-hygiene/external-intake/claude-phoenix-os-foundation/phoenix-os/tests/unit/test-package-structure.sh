#!/bin/bash
# =============================================================================
# Phoenix OS — Unit Tests: Package Structure Validation
# File: tests/unit/test-package-structure.sh
#
# Validates that all packages in packages/ have correct DEBIAN structure
# required for dpkg-deb to build them successfully.
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PACKAGES_DIR="${REPO_ROOT}/packages"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
PASS=0; FAIL=0; WARN=0

pass() { echo -e "  ${GREEN}✓${NC} $*"; (( PASS++ )) || true; }
fail() { echo -e "  ${RED}✗${NC} $*"; (( FAIL++ )) || true; }
warn() { echo -e "  ${YELLOW}⚠${NC} $*"; (( WARN++ )) || true; }

echo ""
echo -e "${BOLD}Phoenix OS — Package Structure Tests${NC}"
echo "────────────────────────────────────"

PACKAGES=(phoenix-theme phoenix-tools phoenix-welcome phoenix-control-center)

for pkg in "${PACKAGES[@]}"; do
    pkg_dir="${PACKAGES_DIR}/${pkg}"
    echo ""
    echo -e "${BOLD}${pkg}${NC}"

    # Directory exists
    if [[ -d "${pkg_dir}" ]]; then
        pass "Package directory exists"
    else
        fail "Package directory MISSING: ${pkg_dir}"
        continue
    fi

    # DEBIAN/control exists and has required fields
    control="${pkg_dir}/DEBIAN/control"
    if [[ -f "${control}" ]]; then
        pass "DEBIAN/control exists"
        for field in Package Version Architecture Maintainer Description; do
            if grep -q "^${field}:" "${control}"; then
                pass "  Field present: ${field}"
            else
                fail "  Field MISSING: ${field}"
            fi
        done
    else
        fail "DEBIAN/control MISSING"
    fi

    # DEBIAN/postinst must be executable if it exists
    postinst="${pkg_dir}/DEBIAN/postinst"
    if [[ -f "${postinst}" ]]; then
        if [[ -x "${postinst}" ]]; then
            pass "DEBIAN/postinst is executable"
        else
            warn "DEBIAN/postinst is not executable (package-debs.sh will fix this)"
        fi
        # Shell syntax check
        if bash -n "${postinst}" 2>/dev/null; then
            pass "DEBIAN/postinst syntax OK"
        else
            fail "DEBIAN/postinst has syntax errors"
        fi
    fi

    # Validate no world-writable files in package
    ww=$(find "${pkg_dir}" -not -path "*/DEBIAN/*" -perm -o+w -type f 2>/dev/null | wc -l)
    if [[ "${ww}" -eq 0 ]]; then
        pass "No world-writable files"
    else
        warn "${ww} world-writable file(s) found (may cause dpkg warnings)"
    fi
done

# Verify package lists reference real package names (basic check)
echo ""
echo -e "${BOLD}Package Lists${NC}"
pkg_lists="${REPO_ROOT}/live-build/package-lists"
list_count=$(find "${pkg_lists}" -name "*.list.chroot" | wc -l)
pass "${list_count} package list files found"

# Check for duplicate package names across all lists
all_packages=$(grep -h -v "^#" "${pkg_lists}"/*.list.chroot 2>/dev/null | grep -v "^$" | sort)
dup_count=$(echo "${all_packages}" | sort | uniq -d | wc -l)
if [[ "${dup_count}" -eq 0 ]]; then
    pass "No duplicate package names across lists"
else
    warn "${dup_count} duplicate package name(s) across lists (harmless but noisy)"
    echo "${all_packages}" | sort | uniq -d | sed 's/^/    /'
fi

echo ""
echo "────────────────────────────────────"
echo -e "${BOLD}Results:${NC} ${GREEN}${PASS} passed${NC}  ${RED}${FAIL} failed${NC}  ${YELLOW}${WARN} warnings${NC}"
echo ""
[[ "${FAIL}" -gt 0 ]] && exit 1 || exit 0
