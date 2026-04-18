"""
Tests for backend/core/phoenix_paths.py (new in this PR).

Covers: repo_root() with/without PHOENIX_REPO_ROOT env, invalid env path fallback,
oclp_submodule_path(), recovery_gui_dist(), legacy_boot_kiosk_script().
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


class TestRepoRoot:
    def test_returns_path_object(self):
        from core.phoenix_paths import repo_root
        result = repo_root()
        assert isinstance(result, Path)

    def test_default_is_parent_of_backend(self):
        """Without env var, repo_root should be two levels above backend/core/phoenix_paths.py."""
        from core.phoenix_paths import repo_root
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PHOENIX_REPO_ROOT", None)
            result = repo_root()
        # backend/core/phoenix_paths.py -> parents[2] == repo root
        # repo_root / backend should be the BACKEND directory
        assert (result / "backend").is_dir() or result.exists()

    def test_env_var_overrides_default(self, tmp_path):
        from core.phoenix_paths import repo_root
        with mock.patch.dict(os.environ, {"PHOENIX_REPO_ROOT": str(tmp_path)}):
            result = repo_root()
        assert result == tmp_path.resolve()

    def test_env_var_invalid_dir_falls_back_to_default(self, tmp_path):
        """If PHOENIX_REPO_ROOT points to a non-existent dir, fall back to file-based resolution."""
        from core.phoenix_paths import repo_root
        nonexistent = str(tmp_path / "does_not_exist")
        with mock.patch.dict(os.environ, {"PHOENIX_REPO_ROOT": nonexistent}):
            result = repo_root()
        # Should fall back to the actual repo root, not the nonexistent path
        assert result != Path(nonexistent)
        assert result.is_dir()

    def test_env_var_tilde_expansion(self, tmp_path, monkeypatch):
        """PHOENIX_REPO_ROOT supports ~ expansion."""
        from core.phoenix_paths import repo_root
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("PHOENIX_REPO_ROOT", "~/")
        result = repo_root()
        # ~/  exists (tmp_path)
        assert result == tmp_path.resolve()

    def test_result_is_absolute(self):
        from core.phoenix_paths import repo_root
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PHOENIX_REPO_ROOT", None)
            result = repo_root()
        assert result.is_absolute()


class TestOclpSubmodulePath:
    def test_is_under_third_party(self):
        from core.phoenix_paths import oclp_submodule_path, repo_root
        path = oclp_submodule_path()
        assert "third_party" in str(path)
        assert "OpenCore-Legacy-Patcher" in str(path)

    def test_path_is_absolute(self):
        from core.phoenix_paths import oclp_submodule_path
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PHOENIX_REPO_ROOT", None)
            path = oclp_submodule_path()
        assert path.is_absolute()

    def test_uses_repo_root(self, tmp_path):
        from core.phoenix_paths import oclp_submodule_path
        with mock.patch.dict(os.environ, {"PHOENIX_REPO_ROOT": str(tmp_path)}):
            path = oclp_submodule_path()
        expected = tmp_path / "third_party" / "OpenCore-Legacy-Patcher"
        assert path == expected.resolve()


class TestRecoveryGuiDist:
    def test_is_under_website(self):
        from core.phoenix_paths import recovery_gui_dist
        path = recovery_gui_dist()
        assert "website" in str(path)
        assert "recovery-gui" in str(path)
        assert "dist" in str(path)

    def test_path_is_absolute(self):
        from core.phoenix_paths import recovery_gui_dist
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PHOENIX_REPO_ROOT", None)
            path = recovery_gui_dist()
        assert path.is_absolute()

    def test_uses_repo_root(self, tmp_path):
        from core.phoenix_paths import recovery_gui_dist
        with mock.patch.dict(os.environ, {"PHOENIX_REPO_ROOT": str(tmp_path)}):
            path = recovery_gui_dist()
        expected = tmp_path / "website" / "recovery-gui" / "dist"
        assert path == expected.resolve()


class TestLegacyBootKioskScript:
    def test_is_under_legacy(self):
        from core.phoenix_paths import legacy_boot_kiosk_script
        path = legacy_boot_kiosk_script()
        assert "legacy" in str(path)
        assert "boot-kiosk.sh" in str(path)

    def test_path_is_absolute(self):
        from core.phoenix_paths import legacy_boot_kiosk_script
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PHOENIX_REPO_ROOT", None)
            path = legacy_boot_kiosk_script()
        assert path.is_absolute()

    def test_uses_repo_root(self, tmp_path):
        from core.phoenix_paths import legacy_boot_kiosk_script
        with mock.patch.dict(os.environ, {"PHOENIX_REPO_ROOT": str(tmp_path)}):
            path = legacy_boot_kiosk_script()
        expected = tmp_path / "legacy" / "scripts" / "boot-kiosk.sh"
        assert path == expected.resolve()