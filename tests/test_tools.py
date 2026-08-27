"""The MCP surface: names, shapes, and that readiness is reachable as a tool."""

from __future__ import annotations

EXPECTED = {
    "gw_plugin_template_list",
    "gw_plugin_template_search",
    "gw_plugin_template_status",
}


def test_every_tool_is_registered_once(server) -> None:
    assert set(server.tools) == EXPECTED


def test_tool_names_are_prefixed_with_the_plugin_name(server) -> None:
    """Tool names share one namespace with the host and every other plugin."""

    from gw_plugin_template.plugin import plugin

    assert all(name.startswith(plugin.name) for name in server.tools)


def test_list_returns_entries(server) -> None:
    payload = server.tools["gw_plugin_template_list"]()
    assert payload["count"] == 3
    assert payload["entries"][0]["key"] == "alpha"


def test_search_returns_the_term_it_was_given(server) -> None:
    payload = server.tools["gw_plugin_template_search"]("beta")
    assert payload["term"] == "beta"
    assert payload["count"] == 1


def test_status_returns_the_readiness_report(server) -> None:
    payload = server.tools["gw_plugin_template_status"]()
    assert payload["state"] == "ready"
