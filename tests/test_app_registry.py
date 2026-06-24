"""Tests for manifest loading."""

from __future__ import annotations

from elysium.services.app_registry import AppRegistry


def test_registry_loads_all_apps():
    registry = AppRegistry()
    assert len(registry.apps) == 8


def test_legacy_programs_dict_shape():
    registry = AppRegistry()
    programs = registry.legacy_programs_dict()

    assert "DFR" in programs
    dfr = programs["DFR"]
    assert dfr["script"] == "DFR.py"
    assert dfr["repo_url"].endswith("DFR.git")
    assert dfr["id"] == "dfr"


def test_flow_uses_script_launch():
    registry = AppRegistry()
    flow = registry.get("flow")
    assert flow is not None
    assert flow.launch.entry == "launcher/launch-flow.vbs"
    assert flow.requirements is not None
    assert flow.requirements.node is True
