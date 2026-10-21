"""Groundworkers' shared lint types, with a load-safe fallback for old hosts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from groundworkers import plugins as _host_plugin_contract


class PluginLintSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class PluginLintDiagnostic:
    code: str
    severity: PluginLintSeverity
    message: str
    path: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "path": self.path,
        }


@dataclass(frozen=True)
class PluginLintReport:
    plugin: str
    diagnostics: tuple[PluginLintDiagnostic, ...] = ()

    @property
    def valid(self) -> bool:
        return not any(
            item.severity is PluginLintSeverity.ERROR for item in self.diagnostics
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "plugin": self.plugin,
            "valid": self.valid,
            "diagnostics": [item.as_dict() for item in self.diagnostics],
        }


# Use one complete host contract when available. Keep the local types together
# on older or partially upgraded hosts so reports never mix incompatible classes.
_LOCAL_LINT_TYPES = (PluginLintSeverity, PluginLintDiagnostic, PluginLintReport)


def _host_lint_types() -> tuple[type, type, type]:
    names = ("PluginLintSeverity", "PluginLintDiagnostic", "PluginLintReport")
    host_types = tuple(getattr(_host_plugin_contract, name, None) for name in names)
    if all(isinstance(item, type) for item in host_types):
        return host_types  # type: ignore[return-value]
    return _LOCAL_LINT_TYPES


PluginLintSeverity, PluginLintDiagnostic, PluginLintReport = _host_lint_types()

__all__ = ["PluginLintDiagnostic", "PluginLintReport", "PluginLintSeverity"]
