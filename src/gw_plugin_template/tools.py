"""The MCP surface. The only module in this package that knows about a server.

No try/except is needed in a tool body: the shared server wrapper already
catches `GroundworkersError`, converts a bare `ValueError` to `INVALID_INPUT`,
and converts anything else to a logged `INTERNAL_ERROR` — the same guard every
core Groundworkers tool gets.

Tool names must be globally unique across the host and every other installed
plugin, so prefix each one with the plugin name.
"""

from __future__ import annotations

from typing import Any

from gw_plugin_template.adapters import CatalogueEntry
from gw_plugin_template.service import GwPluginTemplateService


def _entry(entry: CatalogueEntry) -> dict[str, str]:
    return {"key": entry.key, "label": entry.label, "description": entry.description}


def register_tools(server: Any, service: GwPluginTemplateService) -> None:
    """Register this plugin's tools against the shared guarded server."""

    @server.tool("gw_plugin_template_list")
    def gw_plugin_template_list(limit: int | None = None) -> dict[str, object]:
        """List catalogue entries published by this plugin."""

        entries = service.entries(limit)
        return {"count": len(entries), "entries": [_entry(e) for e in entries]}

    @server.tool("gw_plugin_template_search")
    def gw_plugin_template_search(
        term: str, limit: int | None = None
    ) -> dict[str, object]:
        """Find catalogue entries whose key, label or description matches a term."""

        entries = service.search(term, limit)
        return {
            "term": term,
            "count": len(entries),
            "entries": [_entry(e) for e in entries],
        }

    @server.tool("gw_plugin_template_status")
    def gw_plugin_template_status() -> dict[str, object]:
        """Return the same read-only readiness report the setup console shows."""

        return service.verify_readiness().as_dict()
