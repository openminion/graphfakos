(() => {
  const perspectiveStorageKey = "graphfakos:viewer-perspectives:v1";
  const readPerspectives = () => {
    try {
      return JSON.parse(localStorage.getItem(perspectiveStorageKey) || "[]");
    } catch (_error) {
      return [];
    }
  };
  const writePerspectives = (items) => localStorage.setItem(
    perspectiveStorageKey,
    JSON.stringify(items.slice(-12)),
  );
  const viewerFor = (element) => element.closest("graphfakos-viewer");
  const selectedIds = (viewer) => new Set(viewer.getState?.().selected_node_ids || []);
  const nodeId = (endpoint) => typeof endpoint === "object" ? endpoint.id : endpoint;
  const connectedIds = (viewer, direction) => {
    const selected = selectedIds(viewer);
    const result = new Set(selected);
    for (const edge of viewer.graph?.edges || []) {
      const source = nodeId(edge.source_id ?? edge.source);
      const target = nodeId(edge.target_id ?? edge.target);
      if (direction !== "incoming" && selected.has(source)) result.add(target);
      if (direction !== "outgoing" && selected.has(target)) result.add(source);
    }
    return [...result];
  };
  const applyGraph = (viewer, graph) => viewer.applyLivePatch?.({
    patch_id: `viewer-workflow:${Date.now()}`,
    base_revision: { value: viewer.getState?.().live_revision || "" },
    result_revision: { value: viewer.getState?.().live_revision || "" },
    operations: [{ kind: "snapshot_reset", graph }],
  });
  const filteredGraph = (viewer, keep) => ({
    ...viewer.graph,
    nodes: (viewer.graph?.nodes || []).map((node) => ({
      ...node,
      provider_payload: {
        ...(node.provider_payload || {}),
        viewer_hidden: !keep.has(node.id),
      },
    })),
    edges: (viewer.graph?.edges || []).map((edge) => ({
      ...edge,
      provider_payload: {
        ...(edge.provider_payload || {}),
        viewer_hidden: !keep.has(nodeId(edge.source_id ?? edge.source))
          || !keep.has(nodeId(edge.target_id ?? edge.target)),
      },
    })),
  });
  const selectionAction = async (button) => {
    const viewer = viewerFor(button);
    if (!viewer) return;
    const action = button.dataset.gfSelectionAction;
    const selected = selectedIds(viewer);
    const all = (viewer.graph?.nodes || []).map((node) => node.id);
    const status = viewer.querySelector("[data-gf-selection-workflow-status]");
    if (action === "incoming" || action === "outgoing") {
      const ids = connectedIds(viewer, action);
      viewer.dispatch({ name: "select-many", payload: { node_ids: ids } });
      if (status) status.textContent = `Selected ${ids.length} ${action} neighborhood nodes.`;
      return;
    }
    if (action === "invert") {
      const ids = all.filter((id) => !selected.has(id));
      viewer.dispatch({ name: "select-many", payload: { node_ids: ids } });
      if (status) status.textContent = `Selected ${ids.length} inverse nodes.`;
      return;
    }
    if (action === "expand") {
      const sourceId = [...selected][0];
      if (!sourceId) return;
      button.disabled = true;
      try {
        const response = await fetch("/api/expand", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ source_id: sourceId, depth: 1 }),
        });
        const result = await response.json();
        if (!response.ok || !result.ok) throw new Error(result.error || "Expansion failed");
        if (status) status.textContent = `Loaded provider details around ${sourceId}.`;
        await viewer.navigate?.("/explore");
      } catch (error) {
        if (status) status.textContent = String(error.message || error);
      } finally {
        button.disabled = false;
      }
      return;
    }
    if (action === "restore") {
      button.disabled = true;
      try {
        const response = await fetch("/api/reset", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
        const result = await response.json();
        if (!response.ok || !result.ok) throw new Error(result.error || "Restore failed");
        if (status) status.textContent = "Restored the current provider graph.";
        await viewer.navigate?.("/explore");
      } catch (error) {
        if (status) status.textContent = String(error.message || error);
      } finally {
        button.disabled = false;
      }
      return;
    }
    let keep = new Set(all);
    if (action === "only") keep = selected;
    if (action === "exclude") keep = new Set(all.filter((id) => !selected.has(id)));
    if (action === "dismiss") keep = new Set(connectedIds(viewer, "both"));
    applyGraph(viewer, filteredGraph(viewer, keep));
    if (status) status.textContent = `Showing ${keep.size} of ${all.length} nodes. Use Restore to return to the provider view.`;
  };
  const brushDistribution = (button) => {
    const viewer = viewerFor(button);
    if (!viewer) return;
    const key = button.dataset.gfDistribution;
    const minimum = Number(button.dataset.min);
    const maximum = Number(button.dataset.max);
    const nodes = [...viewer.querySelectorAll(".gf-node")];
    const ids = nodes.filter((node) => {
      const raw = key === "degree" ? node.dataset.degree : node.dataset.score;
      if (raw === "" || raw == null) return false;
      const value = Number(raw);
      return Number.isFinite(value) && value >= minimum && value < maximum;
    }).map((node) => node.dataset.nodeId).filter(Boolean);
    viewer.dispatch({ name: "select-many", payload: { node_ids: ids } });
    button.closest("[data-gf-histogram]")?.querySelectorAll("button").forEach((item) => {
      item.dataset.selected = String(item === button);
    });
  };
  const renderLocalPerspectives = (root) => {
    root.querySelectorAll("[data-gf-local-perspectives]").forEach((target) => {
      const items = readPerspectives();
      const signature = JSON.stringify(items);
      if (target.dataset.gfPerspectiveRendered === signature) return;
      target.dataset.gfPerspectiveRendered = signature;
      target.replaceChildren(...items.map((item, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = item.label;
        button.dataset.gfPerspectiveIndex = String(index);
        return button;
      }));
    });
  };
  const savePerspective = (button) => {
    const viewer = viewerFor(button);
    if (!viewer) return;
    const items = readPerspectives();
    const state = viewer.getState();
    items.push({ label: `View ${items.length + 1}`, state });
    writePerspectives(items);
    renderLocalPerspectives(viewer);
  };
  const applyPerspective = (button) => {
    const viewer = viewerFor(button);
    const item = readPerspectives()[Number(button.dataset.gfPerspectiveIndex)];
    if (viewer && item?.state) viewer.setState(item.state);
  };
  const importGraph = async (form) => {
    const viewer = viewerFor(form);
    const status = form.parentElement.querySelector("[data-gf-import-status]");
    const file = form.elements.file.files?.[0];
    if (!viewer || !file) return;
    status.textContent = `Reading ${file.name}...`;
    try {
      const payload = JSON.parse(await file.text());
      const response = await fetch("/api/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ format: form.elements.format.value, payload }),
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || "Import failed");
      status.textContent = `Opened ${result.graph.label}.`;
      await viewer.navigate?.("/explore");
    } catch (error) {
      status.textContent = `Unable to open file: ${error.message || error}`;
    }
  };
  const wire = (root = document) => {
    root.querySelectorAll("[data-gf-selection-action]:not([data-gf-workflow-wired])").forEach((button) => {
      button.dataset.gfWorkflowWired = "true";
      button.addEventListener("click", () => selectionAction(button));
    });
    root.querySelectorAll("[data-gf-distribution]:not([data-gf-workflow-wired])").forEach((button) => {
      button.dataset.gfWorkflowWired = "true";
      button.addEventListener("click", () => brushDistribution(button));
    });
    root.querySelectorAll("[data-gf-perspective-save]:not([data-gf-workflow-wired])").forEach((button) => {
      button.dataset.gfWorkflowWired = "true";
      button.addEventListener("click", () => savePerspective(button));
    });
    root.querySelectorAll("[data-gf-perspective-index]:not([data-gf-workflow-wired])").forEach((button) => {
      button.dataset.gfWorkflowWired = "true";
      button.addEventListener("click", () => applyPerspective(button));
    });
    root.querySelectorAll("[data-gf-import-form]:not([data-gf-workflow-wired])").forEach((form) => {
      form.dataset.gfWorkflowWired = "true";
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        importGraph(form);
      });
    });
    renderLocalPerspectives(root);
  };
  if (typeof document !== "undefined") {
    document.addEventListener("DOMContentLoaded", () => wire());
    document.addEventListener("graphfakos:ready", (event) => wire(event.target));
    document.addEventListener("graphfakos:route", (event) => wire(event.target));
    if (typeof MutationObserver === "function") {
      new MutationObserver(() => wire()).observe(
        document.documentElement,
        { childList: true, subtree: true },
      );
    }
  }
})();
