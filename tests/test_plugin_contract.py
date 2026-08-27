"""The wiring a new plugin most often gets wrong. Keep these tests."""

from __future__ import annotations

from importlib.metadata import entry_points

from groundworkers.plugins import (
    GroundworkersPluginConfigUI,
    GroundworkersPluginReadiness,
    GroundworkersPluginSetup,
)
from oa_configurator import PackageConfigBase

from gw_plugin_template.config import GwPluginTemplateConfig
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
