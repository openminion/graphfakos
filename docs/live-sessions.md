# Live Graph Sessions

GraphFakos supports provider-issued structural graph patches without becoming a
graph database or inferring graph meaning. The optional live contract is exposed
from `graphfakos.live` and the top-level package.

## Contract

- `GraphFakosGraphPatch` carries ordered node, edge, metadata, or snapshot-reset
  operations.
- `GraphFakosGraphRevision` and `GraphFakosLiveSessionCursor` keep patch ordering
  and transport resume explicit.
- `apply_graph_patch(...)` applies a patch atomically and idempotently.
- `GraphFakosLiveProvider` lets provider packages open sessions and return the
  next patch or typed status.
- `GraphFakosLiveReplayBundle` records an opt-in provider patch journal for
  deterministic offline replay.

GraphFakos never derives patches from prose, embeddings, visual proximity, or
local semantic guesses. Providers remain the graph-truth and action owners.

## Local SSE Reference

`make_local_viewer_server(...)` accepts an optional live provider and exposes
`GET /api/live` as a small Server-Sent Events reference endpoint. It is designed
for local package development:

- loopback binding is the default,
- non-loopback binding requires both `allow_remote=True` and a host-supplied
  authorization hook,
- unexpected browser origins are rejected,
- wildcard CORS is refused,
- clients, provider queues, operation counts, and patch bytes are bounded,
- reconnect, rejection, overflow, and resync behavior is visible through typed
  status and diagnostics.

Hosted deployments must provide their own authentication, authorization, TLS,
reverse proxy, persistence, and transport lifecycle.

## Minimal Example

```python
from graphfakos import (
    GraphFakosGraphRevision,
    InMemoryGraphFakosLiveProvider,
    make_local_viewer_server,
)

live = InMemoryGraphFakosLiveProvider(
    revision=GraphFakosGraphRevision("0"),
)
server = make_local_viewer_server(
    render_path=lambda path, query: "<html>GraphFakos</html>",
    live_provider=live,
    port=0,
)
```

Provider packages can use `graphfakos.testing.assert_live_provider_contract`
to prove initial-load and structural-patch compatibility through public imports.
