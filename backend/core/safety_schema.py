"""
Canonical safety result schema for API responses (versioned).

All safety-check consumers should use this shape; `safe_to_proceed` + `errors`
determine whether a confirmation token may be issued.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

SAFETY_SCHEMA_VERSION = "1.0.0"


def build_safety_payload(
    *,
    safe_to_proceed: bool,
    risk_level: str,
    warnings: List[str],
    errors: List[str],
    confirmation_token: str,
    device_info: Optional[Dict[str, Any]],
    device_risk: Optional[Dict[str, Any]] = None,
    validator_source: str = "bootforge_safety_validator",
    capability_notes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "schema_version": SAFETY_SCHEMA_VERSION,
        "safe_to_proceed": safe_to_proceed,
        "risk_level": risk_level,
        "warnings": warnings,
        "errors": errors,
        "confirmation_token": confirmation_token if safe_to_proceed else "",
        "device_info": device_info,
        "device_risk": device_risk,
        "validator_source": validator_source,
        "capability_notes": capability_notes or [],
    }
