"""Shared fixtures: a fake MCP server and a built plugin state."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from gw_plugin_template.config import GwPluginTemplateConfig
from gw_plugin_template.plugin import plugin


@dataclass
class FakeServer:
    """Records what a plugin registers, without running an MCP server.

    Mirrors only the surface `register_tools` uses. If your plugin registers
    resources or prompts too, add the matching methods here.
    """

    tools: dict[str, Callable[..., Any]] = field(default_factory=dict)

    def tool(self, name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[name] = func
            return func

        return decorator


@dataclass(frozen=True)
class FakeResolver:
    """Stands in for `PluginConfigResolver` in tests that configure a database."""

    def resolve_database(self, name: str) -> str:
        return name

    def resolve_model(self, name: str) -> str:
        return name

    def resolve_vector_store(self, name: str) -> str:
        return name


@dataclass(frozen=True)
class FakeContext:
    """The subset of `PluginContext` this plugin actually reads."""

    resolver: FakeResolver = FakeResolver()
    cdm_database: object | None = None
    cdm_engine: object | None = "engine"
    vector_store: object | None = None
    embedding_backend_factory: object | None = None
    embedding_model_backend_factory: object | None = None
    chat_backend_factory: object | None = None


@pytest.fixture
def fake_context() -> FakeContext:
    return FakeContext()


@pytest.fixture
def catalogue_file(tmp_path: Path) -> Path:
    path = tmp_path / "catalogue.json"
    path.write_text(
        json.dumps(
            [
                {"key": "alpha", "label": "Alpha entry", "description": "First."},
                {"key": "beta", "label": "Beta entry", "description": "Second."},
                {"key": "gamma", "label": "Gamma entry", "description": "Third."},
            ]
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def built_state(catalogue_file: Path):
    config = GwPluginTemplateConfig(catalogue_path=str(catalogue_file))
    state = plugin.build(FakeContext(), config)
    assert state is not None
    return state


@pytest.fixture
def server(built_state) -> FakeServer:
    fake = FakeServer()
    plugin.register(fake, built_state)
    return fake
