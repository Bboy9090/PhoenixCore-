"""
Tests for backend/core/safety_schema.py (new in this PR).

Covers: SAFETY_SCHEMA_VERSION constant, build_safety_payload() all fields and
edge cases (token blanked when not safe, optional fields, capability_notes default).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


class TestSafetySchemaVersion:
    def test_is_string(self):
        from core.safety_schema import SAFETY_SCHEMA_VERSION
        assert isinstance(SAFETY_SCHEMA_VERSION, str)

    def test_semver_format(self):
        from core.safety_schema import SAFETY_SCHEMA_VERSION
        parts = SAFETY_SCHEMA_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


class TestBuildSafetyPayload:
    def _make_payload(self, **overrides):
        from core.safety_schema import build_safety_payload
        defaults = dict(
            safe_to_proceed=True,
            risk_level="low",
            warnings=[],
            errors=[],
            confirmation_token="PHX-some-token",
            device_info={"path": "/dev/sdb"},
        )
        defaults.update(overrides)
        return build_safety_payload(**defaults)

    def test_returns_dict(self):
        result = self._make_payload()
        assert isinstance(result, dict)

    def test_schema_version_is_present(self):
        from core.safety_schema import SAFETY_SCHEMA_VERSION
        result = self._make_payload()
        assert result["schema_version"] == SAFETY_SCHEMA_VERSION

    def test_safe_to_proceed_true(self):
        result = self._make_payload(safe_to_proceed=True)
        assert result["safe_to_proceed"] is True

    def test_safe_to_proceed_false(self):
        result = self._make_payload(safe_to_proceed=False, errors=["blocking error"])
        assert result["safe_to_proceed"] is False

    def test_confirmation_token_present_when_safe(self):
        result = self._make_payload(safe_to_proceed=True, confirmation_token="PHX-abc123")
        assert result["confirmation_token"] == "PHX-abc123"

    def test_confirmation_token_blanked_when_not_safe(self):
        """Confirmation token must be empty string when safe_to_proceed is False."""
        result = self._make_payload(
            safe_to_proceed=False,
            confirmation_token="PHX-should-be-cleared",
            errors=["error"]
        )
        assert result["confirmation_token"] == ""

    def test_risk_level_passed_through(self):
        for level in ("low", "medium", "high", "critical"):
            result = self._make_payload(risk_level=level)
            assert result["risk_level"] == level

    def test_warnings_list_passed_through(self):
        warnings = ["disk is large", "close to minimum size"]
        result = self._make_payload(warnings=warnings)
        assert result["warnings"] == warnings

    def test_errors_list_passed_through(self):
        errors = ["system disk detected"]
        result = self._make_payload(errors=errors)
        assert result["errors"] == errors

    def test_device_info_passed_through(self):
        info = {"path": "/dev/sdc", "size_gb": 64.0, "removable": True}
        result = self._make_payload(device_info=info)
        assert result["device_info"] == info

    def test_device_info_none_allowed(self):
        result = self._make_payload(device_info=None)
        assert result["device_info"] is None

    def test_device_risk_defaults_to_none(self):
        result = self._make_payload()
        assert result.get("device_risk") is None

    def test_device_risk_passed_through(self):
        risk = {"overall_risk": "safe", "is_system_disk": False}
        result = self._make_payload(device_risk=risk)
        assert result["device_risk"] == risk

    def test_validator_source_default(self):
        result = self._make_payload()
        assert result["validator_source"] == "phoenix_safety"

    def test_validator_source_custom(self):
        result = self._make_payload(validator_source="legacy_scanner")
        assert result["validator_source"] == "legacy_scanner"

    def test_capability_notes_defaults_to_empty_list(self):
        result = self._make_payload()
        assert result["capability_notes"] == []

    def test_capability_notes_passed_through(self):
        notes = ["destructive_usb_write_native=false", "install required"]
        result = self._make_payload(capability_notes=notes)
        assert result["capability_notes"] == notes

    def test_capability_notes_none_becomes_empty_list(self):
        result = self._make_payload(capability_notes=None)
        assert result["capability_notes"] == []

    def test_all_required_keys_present(self):
        required = {
            "schema_version", "safe_to_proceed", "risk_level",
            "warnings", "errors", "confirmation_token",
            "device_info", "device_risk", "validator_source", "capability_notes"
        }
        result = self._make_payload()
        assert required.issubset(set(result.keys()))

    def test_empty_warnings_and_errors_preserved(self):
        result = self._make_payload(warnings=[], errors=[])
        assert result["warnings"] == []
        assert result["errors"] == []

    def test_token_blank_even_if_nonempty_but_not_safe(self):
        """Edge case: token provided but safe_to_proceed=False — must return empty."""
        result = self._make_payload(safe_to_proceed=False, confirmation_token="PHX-ghost-token")
        assert result["confirmation_token"] == ""