"""Reusable graph lens for agent memory and source knowledge graphs."""

from .adapters import FixtureGraphProvider, build_fixture_graph
from .models import (
    GraphFakosCitation,
    GraphFakosDiagnostics,
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosProvenance,
    GraphFakosRequest,
    GraphFakosScreen,
    GraphFakosVisual,
)
from .provider import (
    GraphFakosProvider,
    diagnose_graph,
    load_provider_graph,
    validate_graph,
)
from .server import (
    LocalViewerHttpServer,
    LocalViewerServerResult,
    RenderPath,
    make_local_viewer_server,
    serve_local_viewer,
)
from .static import render_static_html, write_static_html
from .ui import render_graph_viewer, render_provider_path, screen_manifest

__version__ = "0.0.1"
PACKAGE_STATUS = "semantic-alpha"
STABLE_IMPORT_ROOTS = (
    "graphfakos",
    "graphfakos.adapters",
    "graphfakos.contracts",
    "graphfakos.models",
    "graphfakos.provider",
    "graphfakos.render",
    "graphfakos.server",
    "graphfakos.static",
    "graphfakos.testing",
    "graphfakos.ui",
)

__all__ = [
    "PACKAGE_STATUS",
    "STABLE_IMPORT_ROOTS",
    "__version__",
    "FixtureGraphProvider",
    "GraphFakosCitation",
    "GraphFakosDiagnostics",
    "GraphFakosEdge",
    "GraphFakosGraph",
    "GraphFakosNode",
    "GraphFakosProvider",
    "GraphFakosProvenance",
    "GraphFakosRequest",
    "GraphFakosScreen",
    "GraphFakosVisual",
    "LocalViewerHttpServer",
    "LocalViewerServerResult",
    "RenderPath",
    "build_fixture_graph",
    "diagnose_graph",
    "load_provider_graph",
    "make_local_viewer_server",
    "render_graph_viewer",
    "render_provider_path",
    "render_static_html",
    "screen_manifest",
    "serve_local_viewer",
    "validate_graph",
    "write_static_html",
]
