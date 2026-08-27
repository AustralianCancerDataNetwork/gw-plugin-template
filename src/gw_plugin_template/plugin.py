"""Groundworkers composition root for this plugin.

`ep.load()` must resolve to a ready-to-use instance, so this module ends with a
singleton. Groundworkers never imports this package by name: it only expects
``name``, ``config_cls``, ``build`` and ``register`` on the object, plus the
optional ``setup_steps``, ``verify_readiness`` and ``tui_workflow`` surfaces.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from groundworkers.application.setup.maintenance_runs import (
    MaintenancePlan,
    MaintenanceStep,
)
from groundworkers.application.setup.models import MaintenanceCommand
from groundworkers.plugins import (
    PluginContext,
    PluginReadinessResult,
    PluginSetupArgument,
    PluginSetupStep,
)
from oa_configurator import PackageConfigBase

from gw_plugin_template.adapters import CatalogueAdapter
from gw_plugin_template.config import GwPluginTemplateConfig
from gw_plugin_template.paths import resolve_catalogue_path
from gw_plugin_template.service import GwPluginTemplateService
from gw_plugin_template.tools import register_tools

if TYPE_CHECKING:  # pragma: no cover - import kept out of the headless path
    from groundskeeping.configurator import (
        ConfigMutationService,
        ConfigWorkflowSpec,
        MutationOperation,
    )


def _refresh_plan(values: Mapping[str, object], config_path: str) -> MaintenancePlan:
    """Turn the operator's form values into a runnable plan.

    Setup arguments are per-run inputs, not configuration: a path to an export
    belongs here, while database references and policy defaults belong in
    `GwPluginTemplateConfig`.
    """

    source = values.get("source")
    arguments = ("--source", str(source)) if source else ()
    resource = f"gw-plugin-template:{config_path}"
    return MaintenancePlan(
        kind="gw-plugin-template-refresh",
        steps=(
            MaintenanceStep(
                key="refresh-catalogue",
                command=MaintenanceCommand(
                    argv=(
                        sys.executable,
                        "-m",
                        "gw_plugin_template.setup_cli",
                        "refresh",
                        *arguments,
                    ),
                    environment=(("OA_CONFIG_PATH", config_path),),
                ),
                affected_resources=(resource,),
            ),
        ),
        affected_resources=(resource,),
    )


@dataclass(frozen=True)
class GwPluginTemplateState:
    """Built once in `build()`, then shared by registration and readiness."""

    config: GwPluginTemplateConfig
    service: GwPluginTemplateService
    catalogue_path: Path | None


class GwPluginTemplatePlugin:
    """Example implementation of the Groundworkers plugin contract."""

    # Must be unique across every installed plugin, and must equal
    # GwPluginTemplateConfig.tool_name.
    name = "gw_plugin_template"
    config_cls: ClassVar[type[PackageConfigBase] | None] = GwPluginTemplateConfig

    # Optional. Remove the tuple entirely if this plugin needs no data
    # preparation; the setup console then shows configuration only.
    setup_steps = (
        PluginSetupStep(
            key="gw_plugin_template_refresh",
            title="Refresh catalogue",
            purpose=(
                "Rebuild this plugin's catalogue snapshot from its upstream "
                "source. After the run succeeds, return to this plugin and "
                "select Verify to see the updated status."
            ),
            arguments=(
                PluginSetupArgument(
                    "source",
                    "Source label",
                    kind="text",
                    required=False,
                    help="Optional label recorded against the generated entries.",
                ),
            ),
            build_plan=_refresh_plan,
        ),
    )

    def build(
        self,
        context: PluginContext,
        config: PackageConfigBase | None,
    ) -> GwPluginTemplateState | None:
        """Connect configuration, adapters and services at application startup.

        Return `None` when a prerequisite this plugin cannot work without is
        missing; `register()` is then never called and Groundworkers keeps
        serving its core capabilities, reporting why this plugin was skipped.
        A degraded-but-useful state is better than `None` whenever the plugin
        can still explain itself, which is why a missing snapshot below yields
        a live plugin with a warning rather than no plugin at all.
        """

        if not isinstance(config, GwPluginTemplateConfig):
            return None

        try:
            path = resolve_catalogue_path(config.catalogue_path)
        except ValueError:
            path = None

        # Prefer a resource Groundworkers already resolved. Only resolve your
        # own when the plugin genuinely needs a different database.
        database_source = "Shared Groundworkers CDM database"
        available = context.cdm_engine is not None
        if config.catalogue_db is not None:
            context.resolver.resolve_database(config.catalogue_db)
            database_source = f"Configured database: {config.catalogue_db}"
            available = True

        service = GwPluginTemplateService(
            catalogue=CatalogueAdapter.build(path),
            default_limit=config.default_limit,
            cdm_available=available,
            database_source=database_source,
        )
        return GwPluginTemplateState(
            config=config, service=service, catalogue_path=path
        )

    def register(self, server: Any, state: object) -> None:
        """Register this plugin's MCP tools against the shared server."""

        register_tools(server, self._state(state).service)

    def verify_readiness(self, state: object) -> PluginReadinessResult:
        """Read-only check surfaced in the setup console and the status tool."""

        return self._state(state).service.verify_readiness()

    def tui_workflow(
        self, operation: MutationOperation
    ) -> tuple[ConfigWorkflowSpec, ConfigMutationService] | None:
        """Defer to the host's generic configuration workflow.

        Returning `None` is the right answer for any config built from plain
        scalars and `RefTo` fields: Groundworkers derives the setup-console page
        from the schema, offers existing references of the correct type, and can
        create new ones recursively. Build a custom pair here only when the flow
        needs live discovery or branching. If you do, import Groundskeeping
        inside this method and keep it in the `tui` optional extra, so a
        headless plugin import stays lightweight.
        """

        del operation
        return None

    @staticmethod
    def _state(state: object) -> GwPluginTemplateState:
        if not isinstance(state, GwPluginTemplateState):
            raise TypeError("gw-plugin-template received invalid plugin state.")
        return state


plugin = GwPluginTemplatePlugin()
