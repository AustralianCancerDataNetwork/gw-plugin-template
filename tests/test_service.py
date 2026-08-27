"""Behaviour, tested without a server or a database."""

from __future__ import annotations

from pathlib import Path

import pytest
from groundworkers.plugins import PluginReadinessState

from gw_plugin_template.adapters import CatalogueAdapter
from gw_plugin_template.service import GwPluginTemplateService


def _service(path: Path | None, **kwargs) -> GwPluginTemplateService:
    return GwPluginTemplateService(
        catalogue=CatalogueAdapter.build(path), cdm_available=True, **kwargs
    )


def test_entries_respect_the_configured_default_limit(catalogue_file: Path) -> None:
    assert len(_service(catalogue_file, default_limit=2).entries()) == 2


def test_explicit_limit_overrides_the_default(catalogue_file: Path) -> None:
    assert len(_service(catalogue_file, default_limit=1).entries(3)) == 3


def test_search_matches_key_label_and_description(catalogue_file: Path) -> None:
    service = _service(catalogue_file)
    assert [e.key for e in service.search("beta")] == ["beta"]
    assert [e.key for e in service.search("Gamma entry")] == ["gamma"]
    assert [e.key for e in service.search("second")] == ["beta"]


def test_a_bad_limit_raises_value_error(catalogue_file: Path) -> None:
    """The server wrapper turns a bare ValueError into INVALID_INPUT."""

    with pytest.raises(ValueError):
        _service(catalogue_file).entries(0)
    with pytest.raises(ValueError):
        _service(catalogue_file).search("   ")


def test_a_missing_snapshot_warns_instead_of_failing(tmp_path: Path) -> None:
    result = _service(tmp_path / "absent.json").verify_readiness()
    assert result.state is PluginReadinessState.WARNING
    assert not result.ready


def test_a_malformed_snapshot_never_leaks_its_path(tmp_path: Path) -> None:
    path = tmp_path / "catalogue.json"
    path.write_text("{not json", encoding="utf-8")
    result = _service(path).verify_readiness()
    assert result.state is PluginReadinessState.WARNING
    rendered = repr(result.as_dict())
    assert str(tmp_path) not in rendered


def test_a_loaded_snapshot_is_ready(catalogue_file: Path) -> None:
    result = _service(catalogue_file).verify_readiness()
    assert result.state is PluginReadinessState.READY
    assert result.ready
