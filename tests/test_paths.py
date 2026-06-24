"""Tests for dual-path install resolution."""

from __future__ import annotations

import os

import pytest

from elysium.core import paths


@pytest.fixture(autouse=True)
def reset_path_cache():
    paths.reset_base_dir_cache()
    paths.resolve_app_dir.cache_clear()
    yield
    paths.reset_base_dir_cache()
    paths.resolve_app_dir.cache_clear()


def test_legacy_base_dir_under_documents():
    legacy = paths.get_legacy_base_dir()
    assert legacy.endswith(os.path.join("Documents", "Elysium"))


def test_new_default_base_dir_under_localappdata():
    new_base = paths.get_new_default_base_dir()
    assert "Protech" in new_base
    assert new_base.endswith(os.path.join("Protech", "Elysium"))


def test_resolve_prefers_legacy_when_only_legacy_has_data(tmp_path, monkeypatch):
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "ELYSIUM.py").write_text("# stub", encoding="utf-8")

    monkeypatch.setattr(paths, "get_legacy_base_dir", lambda: str(legacy))
    monkeypatch.setattr(paths, "get_new_default_base_dir", lambda: str(tmp_path / "new"))

    assert paths.resolve_base_dir() == str(legacy)
    assert paths.uses_legacy_layout() is True


def test_resolve_app_dir_legacy_layout(tmp_path, monkeypatch):
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "DFR").mkdir()

    monkeypatch.setattr(paths, "_BASE_DIR_CACHE", str(legacy))
    monkeypatch.setattr(paths, "get_legacy_base_dir", lambda: str(legacy))

    app_dir = paths.resolve_app_dir("dfr", "DFR")
    assert app_dir == os.path.join(str(legacy), "DFR")


def test_resolve_app_dir_new_layout(tmp_path, monkeypatch):
    new_base = tmp_path / "new"
    apps = new_base / "apps"
    apps.mkdir(parents=True)

    monkeypatch.setattr(paths, "_BASE_DIR_CACHE", str(new_base))
    monkeypatch.setattr(paths, "get_legacy_base_dir", lambda: str(tmp_path / "legacy"))

    app_dir = paths.resolve_app_dir("dfr", "DFR")
    assert app_dir == os.path.join(str(new_base), "apps", "DFR")
