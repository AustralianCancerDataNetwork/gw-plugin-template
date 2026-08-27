"""Everything that touches the outside world.

Keeping I/O here means the service layer stays a pure function of its inputs
and can be tested without a database, a filesystem or a network. Replace the
JSON snapshot below with your own SQLAlchemy queries, HTTP client or file
reader; the shape the service depends on is what matters.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CatalogueEntry:
    """One row of whatever this plugin makes searchable."""

    key: str
    label: str
    description: str = ""

    @classmethod
    def from_mapping(cls, value: object) -> CatalogueEntry:
        if not isinstance(value, dict):
            raise ValueError("A catalogue entry must be an object.")
        key = value.get("key")
        label = value.get("label")
        if not isinstance(key, str) or not key:
            raise ValueError("A catalogue entry needs a non-empty 'key'.")
        if not isinstance(label, str) or not label:
            raise ValueError("A catalogue entry needs a non-empty 'label'.")
        description = value.get("description", "")
        return cls(key, label, description if isinstance(description, str) else "")


@dataclass(frozen=True)
class CatalogueAdapter:
    """Reads the catalogue snapshot this plugin's setup step produces."""

    path: Path | None
    entries: tuple[CatalogueEntry, ...] = ()
    load_error: str | None = None

    @classmethod
    def build(cls, path: Path | None) -> CatalogueAdapter:
        """Load the snapshot, degrading to an empty, explainable catalogue.

        A missing or malformed snapshot is not an exception: the plugin still
        loads, its status tool says why it is empty, and the operator is
        pointed at the setup step that fixes it.
        """

        if path is None:
            return cls(path=None)
        if not path.exists():
            return cls(path=path, load_error="The catalogue snapshot does not exist.")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # Never surface raw exception text: it can carry a path or a URL.
            return cls(path=path, load_error="The catalogue snapshot is unreadable.")
        if not isinstance(raw, list):
            return cls(path=path, load_error="The catalogue snapshot is not a list.")
        try:
            entries = tuple(CatalogueEntry.from_mapping(item) for item in raw)
        except ValueError as exc:
            return cls(path=path, load_error=str(exc))
        return cls(path=path, entries=entries)

    @staticmethod
    def write(path: Path, entries: Iterable[CatalogueEntry]) -> int:
        """Write a snapshot, returning how many entries it holds."""

        payload = [
            {"key": e.key, "label": e.label, "description": e.description}
            for e in entries
        ]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return len(payload)
