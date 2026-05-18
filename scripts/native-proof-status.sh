#!/bin/bash
# scripts/native-proof-status.sh - Show Native proof-track status without touching ISO pipelines.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROADMAP="$REPO_ROOT/native/roadmap.yaml"

if [ ! -f "$ROADMAP" ]; then
    echo "❌ Missing roadmap file: $ROADMAP"
    exit 1
fi

value_of() {
    local key="$1"
    sed -n "s/^[[:space:]]*${key}:[[:space:]]*\"\\{0,1\\}\\([^\"#]*\\)\"\\{0,1\\}[[:space:]]*$/\\1/p" "$ROADMAP" | head -n 1
}

channel="$(value_of channel)"
maturity="$(value_of maturity)"
boot_status="$(value_of boot_status)"

echo "=========================================================="
echo "🔥 Blue Phoenix Native Proof Track"
echo "=========================================================="
echo "Roadmap: $ROADMAP"
echo "Channel: ${channel:-unknown}"
echo "Maturity: ${maturity:-unknown}"
echo "Boot Status: ${boot_status:-unknown}"
echo ""
echo "Milestones:"
printf "%-10s %-12s %-8s %s\n" "ID" "State" "Proof" "Title"
printf "%-10s %-12s %-8s %s\n" "----------" "------------" "--------" "----------------------------------------------"

id=""
state=""
title=""
evidence_path=""

emit_row() {
    if [ -n "$id" ]; then
        local proof_state="MISSING"
        if [ -n "$evidence_path" ] && [ -e "$REPO_ROOT/$evidence_path" ]; then
            proof_state="READY"
        fi
        printf "%-10s %-12s %-8s %s\n" "$id" "${state:-unknown}" "$proof_state" "${title:-untitled}"
    fi
}

while IFS= read -r line; do
    case "$line" in
        "  - id:"*)
            emit_row
            id="${line#*id: }"
            state=""
            title=""
            evidence_path=""
            ;;
        "    state:"*)
            state="${line#*state: }"
            ;;
        "    title:"*)
            title="${line#*title: }"
            title="${title#\"}"
            title="${title%\"}"
            ;;
        "    evidence_path:"*)
            evidence_path="${line#*evidence_path: }"
            evidence_path="${evidence_path#\"}"
            evidence_path="${evidence_path%\"}"
            ;;
    esac
done < "$ROADMAP"

emit_row

echo ""
echo "Legend: READY = evidence path exists, MISSING = evidence path not found"

NATIVE0_EVIDENCE="$REPO_ROOT/native/evidence/NATIVE-0"
if [ -d "$NATIVE0_EVIDENCE" ]; then
    echo ""
    echo "NATIVE-0 Architecture Evidence:"
    for arch in x86_64 aarch64; do
        status_file="$NATIVE0_EVIDENCE/status-${arch}.txt"
        if [ -f "$status_file" ]; then
            result="$(sed -n 's/^NATIVE-0:[[:space:]]*//p' "$status_file" | head -n 1)"
            captured="$(sed -n 's/^Captured:[[:space:]]*//p' "$status_file" | head -n 1)"
            echo "  - $arch: ${result:-UNKNOWN} (${captured:-no timestamp})"
        else
            echo "  - $arch: no evidence file yet"
        fi
    done
fi
