"""The plugin's behaviour, independent of MCP and of Groundworkers itself.

Nothing here imports `mcp` or a server type, so every rule below is testable
by calling a method. `tools.py` is the only module that knows about MCP.
"""

from __future__ import annotations

from dataclasses import dataclass

from groundworkers.plugins import (
    PluginReadinessField,
    PluginReadinessResult,
    PluginReadinessState,
)

from gw_plugin_template.adapters import CatalogueAdapter, CatalogueEntry


@dataclass(frozen=True)
class GwPluginTemplateService:
    """Lookups over the loaded catalogue."""

    catalogue: CatalogueAdapter
    default_limit: int = 10
    cdm_available: bool = False
    database_source: str = "Shared Groundworkers CDM database"

    def entries(self, limit: int | None = None) -> tuple[CatalogueEntry, ...]:
        """Return up to ``limit`` entries, defaulting to the configured limit."""

        resolved = self.default_limit if limit is None else limit
        if resolved < 1:
            raise ValueError("limit must be 1 or greater.")
        return self.catalogue.entries[:resolved]

    def search(self, term: str, limit: int | None = None) -> tuple[CatalogueEntry, ...]:
        """Case-insensitive substring match over key, label and description."""

        if not term.strip():
            raise ValueError("term must not be empty.")
        needle = term.casefold()
        matches = tuple(
            entry
            for entry in self.catalogue.entries
            if needle in entry.key.casefold()
            or needle in entry.label.casefold()
            or needle in entry.description.casefold()
        )
        resolved = self.default_limit if limit is None else limit
        if resolved < 1:
            raise ValueError("limit must be 1 or greater.")
        return matches[:resolved]

    def verify_readiness(self) -> PluginReadinessResult:
        """Report what an operator needs to know, with no secrets in it.

        Display values must never carry credentials, connection URLs or raw
        exception text: this result is rendered in the setup console and is
        also returned verbatim by the plugin's own status tool.
        """

        fields: list[PluginReadinessField] = []
        warnings = False

        count = len(self.catalogue.entries)
        if self.catalogue.path is None:
            warnings = True
            fields.append(
                PluginReadinessField(
                    "catalogue",
                    "Catalogue snapshot",
                    "Not configured",
                    PluginReadinessState.WARNING,
                    "Set catalogue_path, then run the Refresh catalogue setup step.",
                )
            )
        elif self.catalogue.load_error is not None:
            warnings = True
            fields.append(
                PluginReadinessField(
                    "catalogue",
                    "Catalogue snapshot",
                    "Unavailable",
                    PluginReadinessState.WARNING,
                    self.catalogue.load_error,
                )
            )
        else:
            empty = count == 0
            warnings |= empty
            fields.append(
                PluginReadinessField(
                    "catalogue",
                    "Catalogue snapshot",
                    f"{count} entr{'y' if count == 1 else 'ies'}",
                    (
                        PluginReadinessState.WARNING
                        if empty
                        else PluginReadinessState.READY
                    ),
                    "Run the Refresh catalogue setup step." if empty else None,
                )
            )

        fields.append(
            PluginReadinessField(
                "database",
                "Database",
                self.database_source,
                (
                    PluginReadinessState.READY
                    if self.cdm_available
                    else PluginReadinessState.WARNING
                ),
                (
                    None
                    if self.cdm_available
                    else "No database connection was available at startup."
                ),
            )
        )
        warnings |= not self.cdm_available

        return PluginReadinessResult(
            PluginReadinessState.WARNING if warnings else PluginReadinessState.READY,
            (
                f"{count} catalogue entr{'y' if count == 1 else 'ies'} with warnings."
                if warnings
                else f"{count} catalogue entr{'y' if count == 1 else 'ies'} available."
            ),
            tuple(fields),
        )
