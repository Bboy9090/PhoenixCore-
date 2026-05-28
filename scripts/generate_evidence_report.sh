#!/usr/bin/env bash
# ==============================================================================
# PR41E - Release Candidate Evidence Report Generator
# Aggregates test metrics, safety gate logs, and hardware validation results.
# Outputs the formal evidence report for Release Engineering sign-off.
# ==============================================================================

set -eo pipefail

REPORT_FILE="evidence_report.txt"
SAFETY_REPORT="safety_report.json"

echo "======================================================================"
echo "      PHOENIX OS RELEASE ENGINEERING - PR41 EVIDENCE PACKAGE"
echo "======================================================================"
echo "Timestamp: $(date -u)"
echo "Target Branch: fix/edition-branding-fallbacks-20260518"
echo "System Host: $(uname -a)"
echo "----------------------------------------------------------------------"

# Track overall status
OVERALL_PASS=true

run_validation_suite() {
    local suite_name="$1"
    local test_file="$2"
    echo -n "Running $suite_name tests ($test_file)... "

    if python3 -m pytest "$test_file" -q > /dev/null 2>&1; then
        echo "✅ PASS"
        return 0
    else
        echo "❌ FAIL"
        OVERALL_PASS=false
        return 1
    fi
}

# 1. Run PR41A - Physical Boot log check
run_validation_suite "PR41A: Physical USB Boot" "tests/test_bootforge_physical.py"

# 2. Run PR41B - Safety enforcement check
run_validation_suite "PR41B: Safety Gating" "tests/test_safety_gating.py"

# 3. Run PR41C - Transactional dry-run
run_validation_suite "PR41C: Transactional Dry-Run" "tests/test_transactional_dryrun.py"

# 4. Run PR41D - Apple EFI T2
run_validation_suite "PR41D: Apple EFI & T2 Boot" "tests/test_apple_efi.py"

echo "----------------------------------------------------------------------"
echo "AUDIT LOGS & REPORTS STATUS:"

if [ -f "$SAFETY_REPORT" ]; then
    echo "✅ safety_report.json found"
    cat "$SAFETY_REPORT" | grep -E "status|milestone|policy"
else
    # Run the specific test that generates the safety report if not present
    python3 -m pytest tests/test_safety_gating.py -k test_export_safety_report -q > /dev/null 2>&1 || true
    if [ -f "$SAFETY_REPORT" ]; then
        echo "✅ safety_report.json generated successfully"
        cat "$SAFETY_REPORT" | grep -E "status|milestone|policy"
    else
        echo "❌ safety_report.json is MISSING"
        OVERALL_PASS=false
    fi
fi

echo "----------------------------------------------------------------------"
echo "FINAL RECOMMENDATION FOR RELEASE CANDIDATE (RC) GO/NO-GO:"
if [ "$OVERALL_PASS" = true ]; then
    echo "██████╗  █████╗ ███████╗███████╗"
    echo "██╔══██╗██╔══██╗██╔════╝██╔════╝"
    echo "██████╔╝███████║███████╗███████╗"
    echo "██╔═══╝ ██╔══██║╚════██║╚════██║"
    echo "██║     ██║  ██║███████║███████║"
    echo "╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝"
    echo "RECOMMENDATION: GO (All PR41 gates verified and passed)"
else
    echo "███████╗ █████╗ ██╗██╗     ███████╗██████╗ "
    echo "██╔════╝██╔══██╗██║██║     ██╔════╝██╔══██╗"
    echo "█████╗  ███████║██║██║     █████╗  ██║  ██║"
    echo "██╔══╝  ██╔══██║██║██║     ██╔══╝  ██║  ██║"
    echo "██║     ██║  ██║██║███████╗███████╗██████╔╝"
    echo "╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═════╝ "
    echo "RECOMMENDATION: NO-GO (One or more safety gates/tests failed)"
fi
echo "======================================================================"
