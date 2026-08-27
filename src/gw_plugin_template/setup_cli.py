"""Out-of-process setup commands launched by Groundworkers' setup console.

Long-running plugin work runs here, not inside `build()`. The host starts this
module as a subprocess through its durable maintenance-run store, so logs,
progress, cancellation and retry are shared with core operations. Groundworkers
never imports plugin internals to do this — it only runs the argv the plugin's
`build_plan` returned.
"""

from __future__ import annotations

import argparse

from groundworkers.bootstrap import build_app_config
from oa_configurator import Resolver

from gw_plugin_template.adapters import CatalogueAdapter, CatalogueEntry
from gw_plugin_template.config import GwPluginTemplateConfig
from gw_plugin_template.paths import resolve_catalogue_path


def _config(config_path: str | None) -> GwPluginTemplateConfig:
    app_config = build_app_config(config_path=config_path)
    plugin_config = GwPluginTemplateConfig.validate_candidate(app_config.stack)
    if plugin_config.catalogue_db is not None:
        # Resolving here proves the reference is usable before any long work
        # starts, and is where your own queries would get their connection.
        Resolver(app_config.stack).resolve_database(plugin_config.catalogue_db)
    return plugin_config


def _refresh(config_path: str | None, source: str | None) -> int:
    plugin_config = _config(config_path)
    path = resolve_catalogue_path(plugin_config.catalogue_path)
    if path is None:
        print("catalogue_path is not configured; nothing to refresh.")
        return 1

    # Replace this with the real extraction your plugin performs.
    entries = _collect(source)
    written = CatalogueAdapter.write(path, entries)
    print(f"Wrote {written} catalogue entries.")
    return 0


def _collect(source: str | None) -> tuple[CatalogueEntry, ...]:
    """Stand-in for the work a real plugin does here."""

    label = source or "example"
    return (
        CatalogueEntry("example-1", f"{label} entry one", "Replace this."),
        CatalogueEntry("example-2", f"{label} entry two", "Replace this too."),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="gw-plugin-template setup")
    parser.add_argument("--config-path", default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    refresh = subparsers.add_parser("refresh", help="Rebuild the catalogue snapshot.")
    refresh.add_argument("--source", default=None)

    args = parser.parse_args(argv)
    if args.command == "refresh":
        return _refresh(args.config_path, args.source)
    parser.error(f"Unknown command {args.command!r}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
