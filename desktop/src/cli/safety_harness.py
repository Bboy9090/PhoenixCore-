#!/usr/bin/env python3
"""
Phoenix Core — Safety Validator CLI Integration Harness
A safe, 100% read-only diagnostic utility that queries real host block storage devices,
runs them through the safety classifier, and registers forensic audit records.
"""

import sys
import platform
from pathlib import Path

# Ensure we can import the core safety validator module
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.core.safety_validator import (
    enumerate_host_devices,
    validate_target_safety,
    persist_audit_record,
    get_audit_log_path,
    SafetyVerdict,
    SafetySeverity
)


def print_styled_verdict(verdict: SafetyVerdict):
    """Print standard color-coded, block-structured output to the console"""
    # ANSI color codes
    RED = "\033[1;31m"
    YELLOW = "\033[1;33m"
    GREEN = "\033[1;32m"
    BLUE = "\033[1;34m"
    RESET = "\033[0m"

    is_safe = (verdict.confidence_score >= 90 and 
               verdict.severity not in (SafetySeverity.SAFETY_CRITICAL_BLOCK, SafetySeverity.SAFETY_BLOCK))

    print("=" * 80)
    if is_safe:
        print(f"{GREEN}✅ Phoenix Safety Clearance Granted {RESET}")
    elif verdict.severity == SafetySeverity.SAFETY_CRITICAL_BLOCK:
        print(f"{RED}🛑 Phoenix Safety Lockout Enforced (CRITICAL) {RESET}")
    else:
        print(f"{RED}🛑 Phoenix Safety Lockout Enforced {RESET}")
    print("=" * 80)

    print(f"Target Device:        {BLUE}{verdict.device_path}{RESET}")
    print(f"Severity Class:       {RED if not is_safe else GREEN}{verdict.severity.value}{RESET}")
    print(f"Confidence Score:     {GREEN if is_safe else RED}{verdict.confidence_score}{RESET} / 90 (Pass Threshold: 90)")
    print(f"Timestamp:            {verdict.timestamp}")

    if not is_safe:
        print("\nReason for Lockout:")
        print(f"{RED}{verdict.hardlock_reason or 'Confidence score below threshold'}{RESET}")
        print("\nOperator Guidance:")
        print(f"{YELLOW}{verdict.operator_message}{RESET}")
    else:
        print("\nClassification Outcome:")
        print(f"{GREEN}{verdict.operator_message}{RESET}")

    if verdict.factors:
        print("\nAttributed Confidence Factors:")
        for factor in verdict.factors:
            color = GREEN if factor.score_delta > 0 else RED
            print(f"  • [{color}{factor.score_delta:+d}{RESET}] {factor.name}: {factor.description}")

    print("\nForensic Registry Audit Trail:")
    audit_persist = getattr(verdict, "audit_persistence", "SUCCESS")
    if audit_persist == "FAILED":
        print(f"  Audit Persistence:  {RED}FAILED (Forensic evidence was NOT successfully persisted!){RESET}")
    else:
        print(f"  Audit Log Location:  {BLUE}{get_audit_log_path()}{RESET}")
    print("=" * 80)


def run_live_enumeration():
    """Discover and classify all storage devices plugged into the host OS"""
    print("================================================================================")
    print("PHOENIX CORE SAFETY VALIDATOR - LIVE STORAGE DISCOVERY HARNESS")
    print("================================================================================")
    print(f"Host OS Architecture: {platform.system()} ({platform.release()})")
    print(f"Forensic Audit Log:  {get_audit_log_path()}\n")

    try:
        probes = enumerate_host_devices()
    except Exception as e:
        print(f"ERROR: Central device enumeration failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not probes:
        print("No block storage devices discovered on host storage bus.")
        return

    for p in probes:
        try:
            # Route target through centralized validation middleware
            verdict = validate_target_safety(p.device_path)
            print_styled_verdict(verdict)
        except Exception as ve:
            print(f"ERROR: Failed safety validation targeting {p.device_path}: {ve}", file=sys.stderr)


def validate_single_target(target_path: str):
    """Diagnose and classify a single targeted path on the live system"""
    print(f"Executing read-only target validation on path: {target_path}...")
    try:
        verdict = validate_target_safety(target_path)
        print_styled_verdict(verdict)
    except Exception as e:
        print(f"ERROR: Safety validation failed for target {target_path}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """CLI Entrypoint for the Integration Harness"""
    import argparse
    parser = argparse.ArgumentParser(
        description="Safe, read-only physical storage validation integration harness."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--enumerate", action="store_true",
        help="Enumerate and validate all connected storage devices."
    )
    group.add_argument(
        "--validate-target", type=str, metavar="BLOCK_PATH",
        help="Validate a specific target device block path (read-only check)."
    )

    args = parser.parse_args()

    if args.enumerate:
        run_live_enumeration()
    elif args.validate_target:
        validate_single_target(args.validate_target)


if __name__ == "__main__":
    main()
