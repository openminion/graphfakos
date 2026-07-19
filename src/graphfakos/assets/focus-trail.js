(() => {
  const nodeLabels = (graph) => new Map(
    (graph?.nodes || []).map((node) => [String(node.id || ""), String(node.label || node.id || "Node")]),
  );

  const focusEntryLabel = (entry, graph) => {
    const group = String(entry?.group || "").trim();
    if (group) return `${group.charAt(0).toUpperCase()}${group.slice(1)} group`;
    const nodeIds = [...new Set(entry?.node_ids || [])].filter(Boolean);
    if (!nodeIds.length) return "All graph";
    const labels = nodeLabels(graph);
    const first = labels.get(nodeIds[0]) || nodeIds[0];
    return nodeIds.length === 1 ? first : `${first} +${nodeIds.length - 1}`;
  };

  const focusTrailModel = (back = [], current = null, forward = [], graph = {}, limit = 3) => {
    const history = [...back, current].filter(Boolean);
    const rootIndex = history.findIndex((entry) => !(entry?.node_ids || []).length && !entry?.group);
    const focused = history
      .map((entry, historyIndex) => ({
        current: historyIndex === history.length - 1,
        historyIndex,
        label: focusEntryLabel(entry, graph),
        root: historyIndex === rootIndex,
      }))
      .filter((item) => !item.root);
    return {
      backLabel: back.length ? focusEntryLabel(back.at(-1), graph) : "",
      forwardLabel: forward.length ? focusEntryLabel(forward.at(-1), graph) : "",
      items: focused.slice(-Math.max(1, Number(limit) || 3)),
      rootIndex,
      visible: focused.length > 0,
    };
  };

  globalThis.GraphFakosFocusTrail = Object.freeze({
    focusEntryLabel,
    focusTrailModel,
  });
})();
