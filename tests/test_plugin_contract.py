"""The wiring a new plugin most often gets wrong. Keep these tests."""

from __future__ import annotations

from importlib.metadata import entry_points
from types import SimpleNamespace

from groundworkers import plugins as host_plugin_contract
from groundworkers.plugins import (
    GroundworkersPluginConfigUI,
    GroundworkersPluginReadiness,
    GroundworkersPluginSetup,
)
from oa_configurator import PackageConfigBase

from gw_plugin_template import linting as linting_contract
from gw_plugin_template.config import GwPluginTemplateConfig
from gw_plugin_template.linting import PluginLintSeverity
from gw_plugin_template.plugin import plugin

DISTRIBUTION = "gw-plugin-template"


def test_entry_point_is_registered_and_loads_the_singleton() -> None:
    """An unbuilt class or a typo'd path fails silently at runtime, not here."""

    points = [
        ep
        for ep in entry_points(group="groundworkers.plugins")
        if ep.dist is not None and ep.dist.name == DISTRIBUTION
    ]
    assert len(points) == 1, "Expected exactly one groundworkers.plugins entry point."
    assert points[0].load() is plugin


def test_config_entry_point_is_registered() -> None:
    points = [
        ep
        for ep in entry_points(group="omop.config")
        if ep.dist is not None and ep.dist.name == DISTRIBUTION
    ]
    assert len(points) == 1
    assert points[0].load() is GwPluginTemplateConfig


def test_plugin_name_matches_config_tool_name() -> None:
    """Groundworkers rejects the plugin at startup when these disagree."""

    assert plugin.name == GwPluginTemplateConfig.tool_name


def test_plugin_satisfies_the_required_contract() -> None:
    """`GroundworkersPlugin` is not runtime_checkable, so check it by hand."""

    assert isinstance(plugin.name, str) and plugin.name
    assert callable(plugin.build)
    assert callable(plugin.register)
    assert plugin.config_cls is None or issubclass(plugin.config_cls, PackageConfigBase)


def test_plugin_satisfies_the_optional_protocols_it_opts_into() -> None:
    """These three are runtime_checkable, and the host checks them this way."""

    assert isinstance(plugin, GroundworkersPluginReadiness)
    assert isinstance(plugin, GroundworkersPluginSetup)
    assert isinstance(plugin, GroundworkersPluginConfigUI)


def test_template_demonstrates_structured_config_linting(tmp_path) -> None:
    """The proposed host hook returns stable, secret-safe diagnostics."""

    empty = plugin.lint_config(GwPluginTemplateConfig())
    assert empty.plugin == plugin.name
    assert empty.valid
    assert empty.diagnostics == ()

    blank = plugin.lint_config(GwPluginTemplateConfig(catalogue_path=" "))
    assert not blank.valid
    assert blank.diagnostics[0].code == "catalogue.path_blank"
    assert blank.diagnostics[0].severity is PluginLintSeverity.ERROR
    assert blank.diagnostics[0].message == (
        "Set catalogue_path to a non-empty path or leave it unset."
    )

    missing = plugin.lint_config(
        GwPluginTemplateConfig(catalogue_path=str(tmp_path / "missing.json"))
    )
    assert missing.valid
    assert missing.diagnostics[0].code == "catalogue.snapshot_unavailable"
    assert missing.diagnostics[0].severity is PluginLintSeverity.WARNING
    assert str(tmp_path) not in missing.diagnostics[0].message

    wrong_type = plugin.lint_config(None)
    assert not wrong_type.valid
    assert wrong_type.diagnostics[0].code == "config.type_mismatch"


def test_config_linter_accepts_a_valid_catalogue_snapshot(tmp_path) -> None:
    snapshot = tmp_path / "catalogue.json"
    snapshot.write_text('[{"key":"a","label":"A"}]', encoding="utf-8")

    report = plugin.lint_config(GwPluginTemplateConfig(catalogue_path=str(snapshot)))

    assert report.valid
    assert report.diagnostics == ()


def test_host_accepts_template_lint_report_when_contract_is_available() -> None:
    host_report_type = getattr(host_plugin_contract, "PluginLintReport", None)
    host_dispatch = getattr(host_plugin_contract, "lint_plugin_config", None)
    if host_report_type is None or host_dispatch is None:
        import pytest

        pytest.skip("Installed Groundworkers does not expose plugin linting yet.")

    report = host_dispatch(plugin, GwPluginTemplateConfig())

    assert isinstance(report, host_report_type)
    assert report.plugin == plugin.name
    assert report.valid


def test_partial_host_lint_contract_uses_local_types_as_a_set(monkeypatch) -> None:
    monkeypatch.setattr(
        linting_contract,
        "_host_plugin_contract",
        SimpleNamespace(PluginLintReport=object),
    )

    assert linting_contract._host_lint_types() == linting_contract._LOCAL_LINT_TYPES


def test_build_returns_none_for_foreign_config(fake_context) -> None:
    """`register` is never called when `build` declines."""

    assert plugin.build(fake_context, None) is None


def test_setup_step_keys_are_prefixed() -> None:
    """Setup step keys share one namespace across every installed plugin."""

    for step in plugin.setup_steps:
        assert step.key.startswith(plugin.name)


def test_tui_workflow_defers_to_the_generic_page() -> None:
    from groundskeeping.configurator import MutationOperation

    assert plugin.tui_workflow(MutationOperation.UPDATE) is None
