"""Groundworkers' shared lint types, re-exported for this plugin's modules.

The host has defined these since Groundworkers 0.8, so they are imported, not copied.
"""

from groundworkers.plugins import (
    PluginLintDiagnostic,
    PluginLintReport,
    PluginLintSeverity,
)

__all__ = ["PluginLintDiagnostic", "PluginLintReport", "PluginLintSeverity"]
