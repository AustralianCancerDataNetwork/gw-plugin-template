"""The out-of-process setup command and the plan the host runs to reach it."""

from __future__ import annotations

import sys
from pathlib import Path

from gw_plugin_template.adapters import CatalogueAdapter
from gw_plugin_template.plugin import plugin
from gw_plugin_template.setup_cli import _refresh


def test_refresh_writes_a_readable_snapshot(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "nested" / "catalogue.json"
    monkeypatch.setattr(
        "gw_plugin_template.setup_cli._config",
        lambda _config_path: type(
            "Cfg", (), {"catalogue_path": str(path), "catalogue_db": None}
        )(),
    )
    assert _refresh(None, "unit-test") == 0
    loaded = CatalogueAdapter.build(path)
    assert loaded.load_error is None
    assert len(loaded.entries) == 2


def test_refresh_reports_missing_configuration(monkeypatch) -> None:
    monkeypatch.setattr(
        "gw_plugin_template.setup_cli._config",
        lambda _config_path: type(
            "Cfg", (), {"catalogue_path": None, "catalogue_db": None}
        )(),
    )
    assert _refresh(None, None) == 1


def test_the_setup_plan_runs_this_package_out_of_process() -> None:
    """The host runs this argv; it never imports plugin internals itself."""

    step = plugin.setup_steps[0]
    plan = step.build_plan({"source": "demo"}, "/tmp/config.toml")
    command = plan.steps[0].command
    assert command.argv[:4] == (
        sys.executable,
        "-m",
        "gw_plugin_template.setup_cli",
        "refresh",
    )
    assert ("OA_CONFIG_PATH", "/tmp/config.toml") in command.environment
