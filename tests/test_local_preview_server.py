from __future__ import annotations

from threading import Thread
from urllib.request import urlopen

import pytest

from graphfakos import FixtureGraphProvider, GraphFakosRequest, make_local_viewer_server
from graphfakos.ui import render_provider_path


def test_local_preview_server_serves_viewer_routes() -> None:
    provider = FixtureGraphProvider()
    request = GraphFakosRequest(screen="explore")
    try:
        server = make_local_viewer_server(
            render_path=lambda path, query: render_provider_path(
                provider,
                request,
                path,
                query,
            ),
            port=0,
        )
    except PermissionError:
        pytest.skip("local socket binding is unavailable in this sandbox")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(server.preview_url, timeout=5) as response:
            explore_html = response.read().decode("utf-8")
        status_url = server.preview_url.rsplit("/", 1)[0] + "/provider_status"
        with urlopen(status_url, timeout=5) as response:
            status_html = response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert "Graph Canvas" in explore_html
    assert "Provider Status" in status_html
