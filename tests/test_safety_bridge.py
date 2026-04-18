"""
Tests for backend/core/safety_bridge.py (new in this PR).

Covers: validator_available(), run_device_safety() when package unavailable,
map_risk_level_from_validator() all mappings including unknown values.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock
from types import SimpleNamespace

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


class TestValidatorAvailable:
    def test_returns_bool(self):
        from core.safety_bridge import validator_available
        result = validator_available()
        assert isinstance(result, bool)

    def test_false_when_import_fails(self):
        """When phoenix_safety is not installed, validator_available() must return False."""
        # Patch _VALIDATOR_AVAILABLE directly in the module
        with mock.patch("core.safety_bridge._VALIDATOR_AVAILABLE", False):
            from core.safety_bridge import validator_available
            assert validator_available() is False

    def test_true_when_package_available(self):
        with mock.patch("core.safety_bridge._VALIDATOR_AVAILABLE", True):
            from core.safety_bridge import validator_available
            assert validator_available() is True


class TestRunDeviceSafety:
    def test_returns_tuple_of_four(self):
        from core.safety_bridge import run_device_safety
        with mock.patch("core.safety_bridge._VALIDATOR_AVAILABLE", False):
            result = run_device_safety("/dev/sdb")
        assert isinstance(result, tuple)
        assert len(result) == 4

    def test_false_and_error_when_package_unavailable(self):
        from core.safety_bridge import run_device_safety
        with mock.patch("core.safety_bridge._VALIDATOR_AVAILABLE", False):
            ok, risk, errors, warnings = run_device_safety("/dev/sdb")
        assert ok is False
        assert risk == {}
        assert len(errors) == 1
        assert "phoenix_safety" in errors[0].lower() or "not installed" in errors[0].lower()
        assert warnings == []

    def _make_mock_result(self, overall_risk_value, risk_factors=None, **kwargs):
        """Build a mock DeviceRisk result object."""
        from enum import Enum

        class FakeValidationResult(Enum):
            SAFE = "safe"
            WARNING = "warning"
            DANGEROUS = "dangerous"
            BLOCKED = "blocked"

        risk_factors = risk_factors or []
        overall = FakeValidationResult(overall_risk_value)
        return SimpleNamespace(
            device_path=kwargs.get("device_path", "/dev/sdb"),
            is_system_disk=kwargs.get("is_system_disk", False),
            is_boot_disk=kwargs.get("is_boot_disk", False),
            is_removable=kwargs.get("is_removable", True),
            size_gb=kwargs.get("size_gb", 32.0),
            mount_points=kwargs.get("mount_points", []),
            risk_factors=risk_factors,
            overall_risk=overall,
        )

    def _setup_mock_validator(self, device_result):
        """Context manager: mock SafetyValidator + related enums."""
        from enum import Enum

        class FakeSafetyLevel(Enum):
            STANDARD = "standard"

        class FakeValidationResult(Enum):
            SAFE = "safe"
            WARNING = "warning"
            DANGEROUS = "dangerous"
            BLOCKED = "blocked"

        class FakeValidator:
            def __init__(self, level):
                pass
            def validate_device_safety(self, path):
                return device_result

        return (
            mock.patch("core.safety_bridge._VALIDATOR_AVAILABLE", True),
            mock.patch("core.safety_bridge.SafetyValidator", FakeValidator),
            mock.patch("core.safety_bridge.SafetyLevel", FakeSafetyLevel),
            mock.patch("core.safety_bridge.ValidationResult", FakeValidationResult),
        )

    def test_safe_result_returns_ok_true(self):
        from core.safety_bridge import run_device_safety

        from enum import Enum
        class FakeValidationResult(Enum):
            SAFE = "safe"
            WARNING = "warning"
            DANGEROUS = "dangerous"
            BLOCKED = "blocked"

        dr = self._make_mock_result("safe")
        # Patch overall_risk to be FakeValidationResult.SAFE
        dr.overall_risk = FakeValidationResult.SAFE

        class FakeSafetyLevel(Enum):
            STANDARD = "standard"

        class FakeValidator:
            def __init__(self, level):
                pass
            def validate_device_safety(self, path):
                return dr

        with mock.patch("core.safety_bridge._VALIDATOR_AVAILABLE", True):
            with mock.patch("core.safety_bridge.SafetyValidator", FakeValidator):
                with mock.patch("core.safety_bridge.SafetyLevel", FakeSafetyLevel):
                    with mock.patch("core.safety_bridge.ValidationResult", FakeValidationResult):
                        ok, risk_dict, errors, warnings = run_device_safety("/dev/sdb")

        assert ok is True
        assert errors == []

    def test_blocked_result_returns_ok_false(self):
        from core.safety_bridge import run_device_safety
        from enum import Enum

        class FakeValidationResult(Enum):
            SAFE = "safe"
            WARNING = "warning"
            DANGEROUS = "dangerous"
            BLOCKED = "blocked"

        dr = self._make_mock_result("blocked", risk_factors=["system_disk"])
        dr.overall_risk = FakeValidationResult.BLOCKED

        class FakeSafetyLevel(Enum):
            STANDARD = "standard"

        class FakeValidator:
            def __init__(self, level):
                pass
            def validate_device_safety(self, path):
                return dr

        with mock.patch("core.safety_bridge._VALIDATOR_AVAILABLE", True):
            with mock.patch("core.safety_bridge.SafetyValidator", FakeValidator):
                with mock.patch("core.safety_bridge.SafetyLevel", FakeSafetyLevel):
                    with mock.patch("core.safety_bridge.ValidationResult", FakeValidationResult):
                        ok, risk_dict, errors, warnings = run_device_safety("/dev/sdb")

        assert ok is False
        assert len(errors) > 0

    def test_dangerous_result_returns_ok_false(self):
        from core.safety_bridge import run_device_safety
        from enum import Enum

        class FakeValidationResult(Enum):
            SAFE = "safe"
            WARNING = "warning"
            DANGEROUS = "dangerous"
            BLOCKED = "blocked"

        dr = self._make_mock_result("dangerous", risk_factors=["large_drive"])
        dr.overall_risk = FakeValidationResult.DANGEROUS

        class FakeSafetyLevel(Enum):
            STANDARD = "standard"

        class FakeValidator:
            def __init__(self, level):
                pass
            def validate_device_safety(self, path):
                return dr

        with mock.patch("core.safety_bridge._VALIDATOR_AVAILABLE", True):
            with mock.patch("core.safety_bridge.SafetyValidator", FakeValidator):
                with mock.patch("core.safety_bridge.SafetyLevel", FakeSafetyLevel):
                    with mock.patch("core.safety_bridge.ValidationResult", FakeValidationResult):
                        ok, risk_dict, errors, warnings = run_device_safety("/dev/sdb")

        assert ok is False
        assert any("DANGEROUS" in e or "dangerous" in e.lower() for e in errors)

    def test_risk_dict_has_required_keys(self):
        from core.safety_bridge import run_device_safety
        from enum import Enum

        class FakeValidationResult(Enum):
            SAFE = "safe"
            WARNING = "warning"
            DANGEROUS = "dangerous"
            BLOCKED = "blocked"

        dr = self._make_mock_result("safe")
        dr.overall_risk = FakeValidationResult.SAFE

        class FakeSafetyLevel(Enum):
            STANDARD = "standard"

        class FakeValidator:
            def __init__(self, level):
                pass
            def validate_device_safety(self, path):
                return dr

        with mock.patch("core.safety_bridge._VALIDATOR_AVAILABLE", True):
            with mock.patch("core.safety_bridge.SafetyValidator", FakeValidator):
                with mock.patch("core.safety_bridge.SafetyLevel", FakeSafetyLevel):
                    with mock.patch("core.safety_bridge.ValidationResult", FakeValidationResult):
                        _, risk_dict, _, _ = run_device_safety("/dev/sdb")

        expected_keys = {
            "device_path", "is_system_disk", "is_boot_disk", "is_removable",
            "size_gb", "mount_points", "risk_factors", "overall_risk"
        }
        assert expected_keys.issubset(set(risk_dict.keys()))

    def test_risk_factors_added_to_warnings(self):
        from core.safety_bridge import run_device_safety
        from enum import Enum

        class FakeValidationResult(Enum):
            SAFE = "safe"
            WARNING = "warning"
            DANGEROUS = "dangerous"
            BLOCKED = "blocked"

        dr = self._make_mock_result("warning", risk_factors=["large_drive", "unusual_format"])
        dr.overall_risk = FakeValidationResult.WARNING

        class FakeSafetyLevel(Enum):
            STANDARD = "standard"

        class FakeValidator:
            def __init__(self, level):
                pass
            def validate_device_safety(self, path):
                return dr

        with mock.patch("core.safety_bridge._VALIDATOR_AVAILABLE", True):
            with mock.patch("core.safety_bridge.SafetyValidator", FakeValidator):
                with mock.patch("core.safety_bridge.SafetyLevel", FakeSafetyLevel):
                    with mock.patch("core.safety_bridge.ValidationResult", FakeValidationResult):
                        ok, _, _, warnings = run_device_safety("/dev/sdb")

        assert ok is True
        assert "large_drive" in warnings
        assert "unusual_format" in warnings


class TestMapRiskLevelFromValidator:
    def test_safe_maps_to_low(self):
        from core.safety_bridge import map_risk_level_from_validator
        assert map_risk_level_from_validator({"overall_risk": "safe"}) == "low"

    def test_warning_maps_to_medium(self):
        from core.safety_bridge import map_risk_level_from_validator
        assert map_risk_level_from_validator({"overall_risk": "warning"}) == "medium"

    def test_dangerous_maps_to_high(self):
        from core.safety_bridge import map_risk_level_from_validator
        assert map_risk_level_from_validator({"overall_risk": "dangerous"}) == "high"

    def test_blocked_maps_to_critical(self):
        from core.safety_bridge import map_risk_level_from_validator
        assert map_risk_level_from_validator({"overall_risk": "blocked"}) == "critical"

    def test_unknown_value_maps_to_medium(self):
        from core.safety_bridge import map_risk_level_from_validator
        assert map_risk_level_from_validator({"overall_risk": "unknown_level"}) == "medium"

    def test_missing_key_maps_to_low(self):
        """Default when overall_risk missing is 'safe' -> 'low'."""
        from core.safety_bridge import map_risk_level_from_validator
        # When key is missing, defaults to "safe" -> "low"
        assert map_risk_level_from_validator({}) == "low"

    def test_case_insensitive_mapping(self):
        """overall_risk values should match case-insensitively."""
        from core.safety_bridge import map_risk_level_from_validator
        assert map_risk_level_from_validator({"overall_risk": "SAFE"}) == "low"
        assert map_risk_level_from_validator({"overall_risk": "WARNING"}) == "medium"
        assert map_risk_level_from_validator({"overall_risk": "BLOCKED"}) == "critical"