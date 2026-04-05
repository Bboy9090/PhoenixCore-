"""
Bridge to canonical **phoenix_safety** package (shared with BootForge desktop).

Install: `pip install -e packages/phoenix_safety` (see root `requirements.txt`).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

try:
    from phoenix_safety.safety_validator import (
        SafetyValidator,
        SafetyLevel,
        ValidationResult,
    )

    _VALIDATOR_AVAILABLE = True
except ImportError:
    _VALIDATOR_AVAILABLE = False
    SafetyValidator = None  # type: ignore
    SafetyLevel = None  # type: ignore
    ValidationResult = None  # type: ignore


def validator_available() -> bool:
    return _VALIDATOR_AVAILABLE


def run_device_safety(device_path: str) -> Tuple[bool, Dict[str, Any], List[str], List[str]]:
    """
    Returns (ok_to_consider, device_risk_dict, errors, warnings).
    ok_to_consider False means BLOCKED for API token purposes.
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not _VALIDATOR_AVAILABLE:
        errors.append(
            "phoenix_safety package not installed. Run: pip install -e packages/phoenix_safety"
        )
        return False, {}, errors, warnings

    v = SafetyValidator(SafetyLevel.STANDARD)
    dr = v.validate_device_safety(device_path)

    risk_dict = {
        "device_path": dr.device_path,
        "is_system_disk": dr.is_system_disk,
        "is_boot_disk": dr.is_boot_disk,
        "is_removable": dr.is_removable,
        "size_gb": dr.size_gb,
        "mount_points": dr.mount_points,
        "risk_factors": list(dr.risk_factors),
        "overall_risk": dr.overall_risk.value,
    }

    for factor in dr.risk_factors:
        if factor not in warnings:
            warnings.append(factor)

    ov = dr.overall_risk
    if ov == ValidationResult.BLOCKED:
        errors.append(
            f"Safety blocked: {', '.join(dr.risk_factors) if dr.risk_factors else 'policy BLOCKED'}"
        )
        return False, risk_dict, errors, warnings

    if ov == ValidationResult.DANGEROUS:
        errors.append(
            "Target risk is DANGEROUS; API token refused. Use BootForge desktop for this target or resolve risk factors."
        )
        return False, risk_dict, errors, warnings

    if ov == ValidationResult.WARNING:
        warnings.append(
            f"Overall risk: WARNING ({', '.join(dr.risk_factors) if dr.risk_factors else 'see risk_factors'})"
        )

    return True, risk_dict, errors, warnings


def map_risk_level_from_validator(device_risk: Dict[str, Any]) -> str:
    overall = device_risk.get("overall_risk", "safe")
    mapping = {
        "safe": "low",
        "warning": "medium",
        "dangerous": "high",
        "blocked": "critical",
    }
    return mapping.get(str(overall).lower(), "medium")
