"""Reusable assertions for GraphFakos-backed viewer output."""

from __future__ import annotations


def assert_graph_viewer_contract(
    html: str,
    *,
    expected_role: str,
    expected_provider: str,
    expected_node: str,
    expected_edge: str,
) -> None:
    assert "GraphFakos" in html
    assert "Graph Canvas" in html
    assert "Integration Commands" in html
    assert expected_role in html
    assert expected_provider in html
    assert expected_node in html
    assert expected_edge in html


__all__ = [
    "assert_graph_viewer_contract",
]
