"""Path resolution shared by the plugin and its out-of-process setup commands."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_catalogue_path(configured: str | None) -> Path | None:
    """Resolve a configured catalogue path against the active config file.

    A relative path resolves against the directory holding the stack config
    file, so a configuration is portable between a checkout and a container.
    Absolute paths are used as given. ``None`` means "not configured".
    """

    if configured is None:
        return None
    if not configured.strip():
        raise ValueError("The configured catalogue path is empty.")

    candidate = Path(configured).expanduser()
    if candidate.is_absolute():
        return candidate

    config_path = os.environ.get("OA_CONFIG_PATH")
    base = Path(config_path).expanduser().parent if config_path else Path.cwd()
    return (base / candidate).resolve()
