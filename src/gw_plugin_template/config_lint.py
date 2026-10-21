"""Template example of checks specific to a plugin's configuration."""

from __future__ import annotations

from oa_configurator import PackageConfigBase

from gw_plugin_template.adapters import CatalogueAdapter
from gw_plugin_template.config import GwPluginTemplateConfig
from gw_plugin_template.linting import (
    PluginLintDiagnostic,
    PluginLintReport,
    PluginLintSeverity,
)
from gw_plugin_template.paths import resolve_catalogue_path


def lint_template_config(
    config: PackageConfigBase | None, plugin_name: str
) -> PluginLintReport:
    """Check this template's optional catalogue setting."""

    if not isinstance(config, GwPluginTemplateConfig):
        diagnostic = PluginLintDiagnostic(
            "config.type_mismatch",
            PluginLintSeverity.ERROR,
            "The plugin configuration is missing or has the wrong type.",
            "tools.gw_plugin_template",
        )
        return PluginLintReport(plugin_name, (diagnostic,))

    configured_path = config.catalogue_path
    config_path = "tools.gw_plugin_template.catalogue_path"
    if configured_path is None:
        return PluginLintReport(plugin_name)
    if not configured_path.strip():
        diagnostic = PluginLintDiagnostic(
            "catalogue.path_blank",
            PluginLintSeverity.ERROR,
            "Set catalogue_path to a non-empty path or leave it unset.",
            config_path,
        )
        return PluginLintReport(plugin_name, (diagnostic,))

    try:
        catalogue_path = resolve_catalogue_path(configured_path)
    except (OSError, RuntimeError, ValueError):
        catalogue_path = None
    if catalogue_path is None:
        diagnostic = PluginLintDiagnostic(
            "catalogue.path_invalid",
            PluginLintSeverity.ERROR,
            "catalogue_path could not be resolved.",
            config_path,
        )
        return PluginLintReport(plugin_name, (diagnostic,))

    catalogue = CatalogueAdapter.build(catalogue_path)
    if catalogue.load_error is None:
        return PluginLintReport(plugin_name)
    diagnostic = PluginLintDiagnostic(
        "catalogue.snapshot_unavailable",
        PluginLintSeverity.WARNING,
        catalogue.load_error,
        config_path,
    )
    return PluginLintReport(plugin_name, (diagnostic,))
