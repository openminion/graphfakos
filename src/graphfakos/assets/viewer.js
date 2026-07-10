(() => {
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const number = (value, fallback) => {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  };
  const clone = (value) => JSON.parse(JSON.stringify(value || {}));
  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;",
  })[char]);
  const splitList = (value) => String(value || "")
    .split(/[,\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
  const workbookStorageKey = "graphfakos:viewer-workbook:v1";
  const themeStorageKey = "graphfakos:viewer-theme:v1";
  const safeLocalStorage = () => {
    try {
      return typeof window !== "undefined" ? window.localStorage : null;
    } catch (_error) {
      return null;
    }
  };
  const readStoredTheme = () => {
    const value = safeLocalStorage()?.getItem?.(themeStorageKey);
    return ["default", "ink", "paper", "space"].includes(value) ? value : "";
  };
  const writeStoredTheme = (theme) => {
    const storage = safeLocalStorage();
    if (!storage?.setItem || !["default", "ink", "paper", "space"].includes(theme)) return;
    storage.setItem(themeStorageKey, theme);
  };
  const viewerContext = (state) => {
    const current = normalizeState(state);
    return {
      screen: current.screen,
      selected_node_id: current.selected_node_id || "",
      selected_node_ids: [...current.selected_node_ids],
      selected_edge_id: current.selected_edge_id || "",
      query: current.query || "",
      camera: {
        x: current.camera_x,
        y: current.camera_y,
        zoom: current.camera_zoom,
        yaw: current.camera_yaw,
        pitch: current.camera_pitch,
      },
      layout: current.layout,
      render_engine: current.render_engine,
      theme: current.theme,
      saved_view_id: current.saved_view_id || "",
      filters: clone(current.filters),
    };
  };
  const viewerContextRows = (state, labels = {}) => {
    const context = viewerContext(state);
    const selectedLabels = context.selected_node_ids
      .map((nodeId) => labels.nodes?.[nodeId] || nodeId)
      .filter(Boolean);
    const edgeLabel = context.selected_edge_id ? labels.edges?.[context.selected_edge_id] || context.selected_edge_id : "";
    const selection = edgeLabel || selectedLabels.join(", ") || context.selected_node_id || "visible graph";
    const filters = Object.entries(context.filters || {})
      .filter(([, value]) => value)
      .map(([key, value]) => `${key}=${value}`)
      .sort()
      .join(", ") || "none";
    return {
      screen: context.query ? `${context.screen}: ${context.query}` : context.screen,
      selection,
      camera: `x=${number(context.camera.x, 0).toFixed(1)}, y=${number(context.camera.y, 0).toFixed(1)}, zoom=${number(context.camera.zoom, 1).toFixed(2)}, yaw=${number(context.camera.yaw, 0).toFixed(1)}, pitch=${number(context.camera.pitch, 0).toFixed(1)}`,
      view: `${context.layout} / ${context.render_engine} / ${context.theme}`,
      filters,
    };
  };
  const defaultState = {
    screen: "explore",
    query: "",
    layout: "force",
    selected_node_id: null,
    selected_node_ids: [],
    selected_edge_id: null,
    camera_x: 0,
    camera_y: 0,
    camera_zoom: 1,
    camera_yaw: 0,
    camera_pitch: 0,
    render_engine: "svg",
    theme: "default",
    filters: {},
    expanded_groups: [],
    hidden_groups: [],
    saved_view_id: "",
    show_orphans: true,
    show_neighbor_links: true,
    edge_clutter: "normal",
    analytics_overlay: "degree",
    center_force: 0.012,
    repel_force: 1,
    link_distance: 1,
    node_scale: 1,
    edge_scale: 1,
    edge_opacity: 1,
    label_density: 1,
    pinned_positions: {},
    style_color_by: "kind",
    style_size_by: "score",
    style_edge_width_by: "kind",
    min_degree: null,
    max_degree: null,
    component_id: "",
    connected_to_node_id: "",
    evidence_filter: "",
    cluster_id: "",
    timeline_frame: "",
    timeline_playback: "stopped",
    pivot_node_id: "",
    pivot_mode: "",
  };

  const normalizeState = (state) => {
    const next = { ...defaultState, ...clone(state) };
    next.camera_x = number(next.camera_x, 0);
    next.camera_y = number(next.camera_y, 0);
    next.camera_zoom = clamp(number(next.camera_zoom, 1), 0.35, 3);
    next.camera_yaw = clamp(number(next.camera_yaw, 0), -180, 180);
    next.camera_pitch = clamp(number(next.camera_pitch, 0), -72, 72);
    next.filters = clone(next.filters);
    next.selected_node_ids = Array.isArray(next.selected_node_ids) ? next.selected_node_ids.filter(Boolean) : [];
    next.expanded_groups = Array.isArray(next.expanded_groups) ? next.expanded_groups : [];
    next.hidden_groups = Array.isArray(next.hidden_groups) ? next.hidden_groups : [];
    next.pinned_positions = clone(next.pinned_positions);
    next.show_orphans = next.show_orphans !== false && next.show_orphans !== "false";
    next.show_neighbor_links = next.show_neighbor_links !== false && next.show_neighbor_links !== "false";
    next.center_force = number(next.center_force, defaultState.center_force);
    next.repel_force = number(next.repel_force, defaultState.repel_force);
    next.link_distance = number(next.link_distance, defaultState.link_distance);
    next.node_scale = number(next.node_scale, defaultState.node_scale);
    next.edge_scale = number(next.edge_scale, defaultState.edge_scale);
    next.edge_opacity = clamp(number(next.edge_opacity, defaultState.edge_opacity), 0.15, 1);
    next.label_density = clamp(number(next.label_density, defaultState.label_density), 0, 1);
    return next;
  };

  const reduce = (state, command) => {
    const next = normalizeState(state);
    const action = command?.name || "";
    const payload = clone(command?.payload);
    if (action === "select-node") {
      const nodeId = command.target_id || payload.node_id || null;
      next.selected_node_id = nodeId;
      next.selected_edge_id = null;
      if (nodeId && payload.additive) {
        const selected = new Set(next.selected_node_ids);
        if (selected.has(nodeId)) selected.delete(nodeId);
        else selected.add(nodeId);
        next.selected_node_ids = [...selected].sort();
      } else {
        next.selected_node_ids = nodeId ? [nodeId] : [];
      }
    }
    if (action === "select-many") next.selected_node_ids = Array.isArray(payload.node_ids) ? payload.node_ids.filter(Boolean).sort() : [];
    if (action === "clear-selection") {
      next.selected_node_id = null;
      next.selected_node_ids = [];
      next.selected_edge_id = null;
    }
    if (action === "select-edge") next.selected_edge_id = command.target_id || payload.edge_id || null;
    if (action === "pin-node") {
      const nodeId = command.target_id || payload.node_id;
      if (nodeId) next.pinned_positions[nodeId] = [number(payload.x, 0), number(payload.y, 0)];
    }
    if (action === "pin-many") {
      Object.entries(payload.positions || {}).forEach(([nodeId, position]) => {
        if (Array.isArray(position) && position.length === 2) {
          next.pinned_positions[nodeId] = [number(position[0], 0), number(position[1], 0)];
        }
      });
    }
    if (action === "unpin-node") {
      const nodeId = command.target_id || payload.node_id;
      if (nodeId) delete next.pinned_positions[nodeId];
    }
    if (action === "reset-pins") next.pinned_positions = {};
    if (action === "camera") {
      next.camera_x = number(payload.x ?? payload.camera_x, next.camera_x);
      next.camera_y = number(payload.y ?? payload.camera_y, next.camera_y);
      next.camera_zoom = clamp(number(payload.zoom ?? payload.camera_zoom, next.camera_zoom), 0.35, 3);
      next.camera_yaw = clamp(number(payload.yaw ?? payload.camera_yaw, next.camera_yaw), -180, 180);
      next.camera_pitch = clamp(number(payload.pitch ?? payload.camera_pitch, next.camera_pitch), -72, 72);
    }
    if (action === "layout") next.layout = command.value || payload.layout || next.layout;
    if (action === "filter") {
      const key = payload.key || command.target_id;
      if (key) {
        if (payload.value === "" || payload.value === null || payload.value === undefined) delete next.filters[key];
        else next.filters[key] = String(payload.value);
      }
    }
    if (action === "group-toggle") {
      const group = command.target_id || payload.group;
      if (group) {
        const hidden = new Set(next.hidden_groups);
        if (hidden.has(group)) hidden.delete(group);
        else hidden.add(group);
        next.hidden_groups = [...hidden].sort();
      }
    }
    if (action === "group-show-all") next.hidden_groups = [];
    if (action === "expand") {
      const group = command.target_id || payload.source_id;
      if (group && !next.expanded_groups.includes(group)) next.expanded_groups = [...next.expanded_groups, group].sort();
    }
    return next;
  };

  const eventName = (name) => `graphfakos:${name}`;

  const parseJsonAttribute = (element, name, fallback) => {
    try {
      const value = element.getAttribute(name);
      return value ? JSON.parse(value) : fallback;
    } catch (_error) {
      return fallback;
    }
  };

  const emit = (element, name, detail) => {
    if (typeof CustomEvent === "function") {
      element.dispatchEvent(new CustomEvent(eventName(name), { bubbles: true, detail }));
    }
  };

  const routeFromUrl = (url) => `${url.pathname}${url.search}`;

  const savedViewRoute = (state) => {
    const current = normalizeState(state);
    const params = new URLSearchParams();
    const put = (key, value) => {
      if (value === null || value === undefined || value === "" || (Array.isArray(value) && value.length === 0)) return;
      params.set(key, Array.isArray(value) ? value.join(",") : String(value));
    };
    put("query", current.query);
    put("layout", current.layout);
    put("focus_node_id", current.selected_node_id);
    put("selected_node_ids", current.selected_node_ids);
    put("selected_edge_id", current.selected_edge_id);
    put("camera_x", current.camera_x.toFixed(2));
    put("camera_y", current.camera_y.toFixed(2));
    put("camera_zoom", current.camera_zoom.toFixed(2));
    put("camera_yaw", current.camera_yaw.toFixed(2));
    put("camera_pitch", current.camera_pitch.toFixed(2));
    put("render_engine", current.render_engine);
    put("theme", current.theme);
    put("saved_view_id", current.saved_view_id);
    put("hidden_groups", current.hidden_groups);
    if (Object.keys(current.pinned_positions || {}).length) {
      put("pinned_positions", JSON.stringify(current.pinned_positions));
    }
    Object.entries(current.filters || {}).forEach(([key, value]) => put(key, value));
    const query = params.toString();
    return `/${current.screen || "explore"}${query ? `?${query}` : ""}`;
  };

  const workbookSlotPayload = (state, label = "", savedAt = null) => {
    const current = normalizeState(state);
    const name = String(label || "").trim() || current.saved_view_id || "Local saved view";
    const timestamp = savedAt || new Date().toISOString();
    return {
      id: `${name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "view"}:${timestamp}`,
      label: name,
      saved_at: timestamp,
      route: savedViewRoute(current),
      state: current,
    };
  };

  const workbookSlotsFromStorage = (storage) => {
    if (!storage?.getItem) return [];
    try {
      const parsed = JSON.parse(storage.getItem(workbookStorageKey) || "[]");
      return Array.isArray(parsed) ? parsed.filter((item) => item?.route && item?.state) : [];
    } catch (_error) {
      return [];
    }
  };

  const writeWorkbookSlots = (storage, slots) => {
    if (!storage?.setItem) return false;
    storage.setItem(workbookStorageKey, JSON.stringify(slots.slice(0, 8)));
    return true;
  };

  const renderWorkbookSlots = (root, slots, navigate) => {
    const list = root.querySelector("[data-gf-workbook-list]");
    if (!list) return;
    list.replaceChildren();
    if (!slots.length) {
      const empty = document.createElement("p");
      empty.className = "gf-note";
      empty.textContent = "No local saved slots yet. Save one to keep this camera, filters, selection, and pins in this browser.";
      list.appendChild(empty);
      return;
    }
    slots.forEach((slot) => {
      const row = document.createElement("div");
      row.className = "gf-workbook-slot";
      const summary = document.createElement("span");
      summary.textContent = `${slot.label || "Local saved view"} · ${slot.state?.screen || "explore"}`;
      const link = document.createElement("a");
      link.href = slot.route || "/";
      link.textContent = "Load";
      link.addEventListener("click", (event) => {
        event.preventDefault();
        navigate(slot.route || "/");
      });
      row.append(summary, link);
      list.appendChild(row);
    });
  };

  const isInternalRoute = (url) => (
    typeof window !== "undefined"
    && (window.location.protocol === "http:" || window.location.protocol === "https:")
    && url.origin === window.location.origin
    && !url.hash
  );

  const setUrlParam = (url, key, value) => {
    if (value === null || value === undefined || value === "" || (Array.isArray(value) && value.length === 0)) {
      url.searchParams.delete(key);
      return;
    }
    url.searchParams.set(key, Array.isArray(value) ? value.join(",") : String(value));
  };

  const updateSavedLink = (root, state) => {
    const link = root.querySelector("[data-gf-save-view]");
    if (!link || typeof URL !== "function") return;
    const url = new URL(link.getAttribute("href") || "/", "http://graphfakos.local");
    url.searchParams.set("camera_x", state.camera_x.toFixed(2));
    url.searchParams.set("camera_y", state.camera_y.toFixed(2));
    url.searchParams.set("camera_zoom", state.camera_zoom.toFixed(2));
    url.searchParams.set("camera_yaw", state.camera_yaw.toFixed(2));
    url.searchParams.set("camera_pitch", state.camera_pitch.toFixed(2));
    setUrlParam(url, "focus_node_id", state.selected_node_id);
    setUrlParam(url, "selected_node_ids", state.selected_node_ids);
    setUrlParam(url, "selected_edge_id", state.selected_edge_id);
    setUrlParam(url, "hidden_groups", state.hidden_groups);
    const pinned = state.pinned_positions || {};
    if (Object.keys(pinned).length) {
      url.searchParams.set("pinned_positions", JSON.stringify(pinned));
    } else {
      url.searchParams.delete("pinned_positions");
    }
    link.setAttribute("href", `${url.pathname}${url.search}`);
  };

  const minimapViewportRect = (state, viewport = {}, minimap = {}) => {
    const current = normalizeState(state);
    const graphWidth = Math.max(1, number(viewport.width, 920));
    const graphHeight = Math.max(1, number(viewport.height, 460));
    const minimapWidth = Math.max(1, number(minimap.width, 180));
    const minimapHeight = Math.max(1, number(minimap.height, 90));
    const zoom = Math.max(0.01, number(current.camera_zoom, 1));
    const minX = clamp(-current.camera_x / zoom, 0, graphWidth);
    const minY = clamp(-current.camera_y / zoom, 0, graphHeight);
    const maxX = clamp((graphWidth - current.camera_x) / zoom, 0, graphWidth);
    const maxY = clamp((graphHeight - current.camera_y) / zoom, 0, graphHeight);
    return {
      x: (Math.min(minX, maxX) / graphWidth) * minimapWidth,
      y: (Math.min(minY, maxY) / graphHeight) * minimapHeight,
      width: (Math.max(0, Math.abs(maxX - minX)) / graphWidth) * minimapWidth,
      height: (Math.max(0, Math.abs(maxY - minY)) / graphHeight) * minimapHeight,
    };
  };

  const updateMinimapViewport = (shell, state) => {
    const canvasViewBox = shell.querySelector(".gf-canvas")?.viewBox?.baseVal;
    const minimapSvg = shell.closest(".gf-canvas-panel")?.querySelector(".gf-minimap svg");
    const minimapViewBox = minimapSvg?.viewBox?.baseVal;
    const viewport = shell.closest(".gf-canvas-panel")?.querySelector("[data-gf-minimap-viewport]");
    if (!canvasViewBox || !minimapViewBox || !viewport) return;
    const rect = minimapViewportRect(
      state,
      { width: canvasViewBox.width, height: canvasViewBox.height },
      { width: minimapViewBox.width, height: minimapViewBox.height },
    );
    viewport.setAttribute("x", rect.x.toFixed(1));
    viewport.setAttribute("y", rect.y.toFixed(1));
    viewport.setAttribute("width", rect.width.toFixed(1));
    viewport.setAttribute("height", rect.height.toFixed(1));
    viewport.dataset.cameraX = state.camera_x.toFixed(2);
    viewport.dataset.cameraY = state.camera_y.toFixed(2);
    viewport.dataset.cameraZoom = state.camera_zoom.toFixed(2);
  };

  const detailMode = (state, visibleNodeCount = 0) => {
    const current = normalizeState(state);
    const count = number(visibleNodeCount, 0);
    if (current.camera_zoom >= 2.1) return "precision";
    if (current.camera_zoom >= 1.35 || count <= 48) return "detail";
    if (current.camera_zoom >= 0.85 || current.label_density >= 0.62 || count <= 110) return "balanced";
    return "overview";
  };

  const applyDetailMode = (shell, state) => {
    const count = number(shell?.dataset?.visibleNodes, shell?.querySelectorAll?.(".gf-node")?.length || 0);
    const mode = detailMode(state, count);
    shell.dataset.detailMode = mode;
    const status = shell.closest(".gf-canvas-panel")?.querySelector("[data-gf-detail-mode]");
    if (status) status.textContent = `${mode.charAt(0).toUpperCase()}${mode.slice(1)} view`;
    return mode;
  };

  const applyCamera = (shell, state) => {
    const viewport = shell.querySelector(".gf-viewport");
    if (!viewport) return;
    viewport.setAttribute("transform", `translate(${state.camera_x} ${state.camera_y}) scale(${state.camera_zoom})`);
    shell.dataset.cameraX = state.camera_x.toFixed(2);
    shell.dataset.cameraY = state.camera_y.toFixed(2);
    shell.dataset.cameraZoom = state.camera_zoom.toFixed(2);
    shell.dataset.cameraYaw = state.camera_yaw.toFixed(2);
    shell.dataset.cameraPitch = state.camera_pitch.toFixed(2);
    applyDetailMode(shell, state);
    apply3DProjection(shell, state);
    updateMinimapViewport(shell, state);
    updateSavedLink(shell.closest("graphfakos-viewer") || document, state);
  };

  const connectedEdges = (shell, nodeId) => [
    ...shell.querySelectorAll(`[data-source-id="${CSS.escape(nodeId)}"], [data-target-id="${CSS.escape(nodeId)}"]`),
  ];

  const curvedEdgePath = (x1, y1, x2, y2, edgeId = "") => {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const distance = Math.hypot(dx, dy) || 1;
    const bendSign = [...String(edgeId)].reduce((total, char) => total + char.charCodeAt(0), 0) % 2 ? -1 : 1;
    const bend = clamp(distance * 0.12, 10, 46) * bendSign;
    const cx = (x1 + x2) / 2 - (dy / distance) * bend;
    const cy = (y1 + y2) / 2 + (dx / distance) * bend;
    return `M${x1.toFixed(1)},${y1.toFixed(1)} Q${cx.toFixed(1)},${cy.toFixed(1)} ${x2.toFixed(1)},${y2.toFixed(1)}`;
  };

  const shellViewport = (shell) => {
    const viewBox = shell.querySelector(".gf-canvas")?.viewBox?.baseVal;
    return {
      width: viewBox?.width || 1280,
      height: viewBox?.height || 720,
    };
  };

  const is3DMode = (shell, state) => (
    (state?.render_engine || shell?.dataset?.renderEngine || "") === "3d"
  );

  const nodeWorldPoint = (node) => ({
    x: number(node.dataset.x, number(node.dataset.layoutX, 0)),
    y: number(node.dataset.y, number(node.dataset.layoutY, 0)),
    z: number(node.dataset.z, number(node.dataset.layoutZ, 0)),
  });

  const projectPoint3D = (point, state, viewport) => {
    const centerX = viewport.width / 2;
    const centerY = viewport.height / 2;
    const yaw = number(state.camera_yaw, 0) * Math.PI / 180;
    const pitch = number(state.camera_pitch, 0) * Math.PI / 180;
    const dx = point.x - centerX;
    const dy = point.y - centerY;
    const dz = point.z;
    const yawX = dx * Math.cos(yaw) - dz * Math.sin(yaw);
    const yawZ = dx * Math.sin(yaw) + dz * Math.cos(yaw);
    const pitchY = dy * Math.cos(pitch) - yawZ * Math.sin(pitch);
    const pitchZ = dy * Math.sin(pitch) + yawZ * Math.cos(pitch);
    const perspective = clamp(760 / (760 + pitchZ), 0.42, 1.7);
    return {
      x: centerX + yawX * perspective,
      y: centerY + pitchY * perspective,
      z: pitchZ,
      scale: perspective,
      opacity: clamp(0.5 + perspective * 0.42, 0.42, 1),
    };
  };

  const apply3DProjection = (shell, state) => {
    if (!is3DMode(shell, state)) {
      shell.dataset.projection = "flat";
      shell.querySelectorAll(".gf-node").forEach((node) => {
        const x = number(node.dataset.x, 0);
        const y = number(node.dataset.y, 0);
        node.dataset.projectedX = x.toFixed(1);
        node.dataset.projectedY = y.toFixed(1);
        node.dataset.projectedZ = number(node.dataset.z, 0).toFixed(1);
        node.dataset.depthScale = "1.00";
        node.style.opacity = "";
        node.setAttribute("transform", `translate(${x.toFixed(1)} ${y.toFixed(1)})`);
      });
      shell.querySelectorAll(".gf-edge").forEach((edge) => updateEdgeGeometry(edge));
      return;
    }
    shell.dataset.projection = "perspective";
    const viewport = shellViewport(shell);
    const nodes = [...shell.querySelectorAll(".gf-node")];
    nodes.forEach((node) => {
      const projected = projectPoint3D(nodeWorldPoint(node), state, viewport);
      node.dataset.projectedX = projected.x.toFixed(1);
      node.dataset.projectedY = projected.y.toFixed(1);
      node.dataset.projectedZ = projected.z.toFixed(1);
      node.dataset.depthScale = projected.scale.toFixed(2);
      node.style.opacity = projected.opacity.toFixed(2);
      node.setAttribute(
        "transform",
        `translate(${projected.x.toFixed(1)} ${projected.y.toFixed(1)}) scale(${projected.scale.toFixed(3)})`,
      );
    });
    shell.querySelectorAll(".gf-edge").forEach((edge) => updateEdgeGeometry(edge));
  };

  const updateEdgeGeometry = (edge) => {
    const root = edge.closest?.(".gf-canvas-shell");
    const source = root?.querySelector?.(`.gf-node[data-node-id="${CSS.escape(edge.dataset.sourceId || "")}"]`);
    const target = root?.querySelector?.(`.gf-node[data-node-id="${CSS.escape(edge.dataset.targetId || "")}"]`);
    const x1 = number(source?.dataset.projectedX, number(edge.dataset.sourceX, number(edge.getAttribute("x1"), 0)));
    const y1 = number(source?.dataset.projectedY, number(edge.dataset.sourceY, number(edge.getAttribute("y1"), 0)));
    const x2 = number(target?.dataset.projectedX, number(edge.dataset.targetX, number(edge.getAttribute("x2"), 0)));
    const y2 = number(target?.dataset.projectedY, number(edge.dataset.targetY, number(edge.getAttribute("y2"), 0)));
    if (edge.tagName?.toLowerCase() === "path") {
      edge.setAttribute("d", curvedEdgePath(x1, y1, x2, y2, edge.dataset.edgeId || ""));
      return;
    }
    edge.setAttribute("x1", x1.toFixed(1));
    edge.setAttribute("y1", y1.toFixed(1));
    edge.setAttribute("x2", x2.toFixed(1));
    edge.setAttribute("y2", y2.toFixed(1));
  };

  const applyNodePosition = (shell, nodeId, x, y, pinned = true) => {
    const node = shell.querySelector(`.gf-node[data-node-id="${CSS.escape(nodeId)}"]`);
    if (!node) return;
    const roundedX = number(x, 0).toFixed(1);
    const roundedY = number(y, 0).toFixed(1);
    node.dataset.x = roundedX;
    node.dataset.y = roundedY;
    node.dataset.pinned = pinned ? "true" : node.dataset.providerPinned || "false";
    node.setAttribute("transform", `translate(${roundedX} ${roundedY})`);
    connectedEdges(shell, nodeId).forEach((edge) => {
      if (edge.dataset.sourceId === nodeId) {
        edge.dataset.sourceX = roundedX;
        edge.dataset.sourceY = roundedY;
      }
      if (edge.dataset.targetId === nodeId) {
        edge.dataset.targetX = roundedX;
        edge.dataset.targetY = roundedY;
      }
      updateEdgeGeometry(edge);
    });
    const root = shell.closest?.("graphfakos-viewer");
    if (root?.getState) apply3DProjection(shell, root.getState());
  };

  const clearConnectedEmphasis = (shell) => {
    shell.querySelectorAll(".gf-node[data-neighbor='true']").forEach((node) => {
      node.dataset.neighbor = "false";
    });
    shell.querySelectorAll(".gf-edge[data-stretched='true']").forEach((edge) => {
      edge.dataset.stretched = "false";
    });
  };

  const emphasizeConnectedEdges = (shell, nodeIds) => {
    const ids = new Set(Array.isArray(nodeIds) ? nodeIds.filter(Boolean) : []);
    if (!ids.size) return;
    shell.querySelectorAll(".gf-edge").forEach((edge) => {
      const connected = ids.has(edge.dataset.sourceId) || ids.has(edge.dataset.targetId);
      edge.dataset.stretched = connected ? "true" : edge.dataset.stretched || "false";
      if (!connected) return;
      [edge.dataset.sourceId, edge.dataset.targetId].forEach((nodeId) => {
        if (!nodeId || ids.has(nodeId)) return;
        const neighbor = shell.querySelector(`.gf-node[data-node-id="${CSS.escape(nodeId)}"]`);
        if (neighbor) neighbor.dataset.neighbor = "true";
      });
    });
  };

  const applyPinnedPositions = (shell, state) => {
    const pinned = state.pinned_positions || {};
    shell.querySelectorAll(".gf-node").forEach((node) => {
      const nodeId = node.dataset.nodeId || "";
      const position = pinned[nodeId];
      if (Array.isArray(position) && position.length === 2) {
        applyNodePosition(shell, nodeId, number(position[0], 0), number(position[1], 0), true);
        return;
      }
      applyNodePosition(
        shell,
        nodeId,
        number(node.dataset.layoutX, number(node.dataset.x, 0)),
        number(node.dataset.layoutY, number(node.dataset.y, 0)),
        false,
      );
    });
  };

  const svgPoint = (svg, event) => {
    const rect = svg.getBoundingClientRect();
    const viewBox = svg.viewBox?.baseVal;
    const width = viewBox?.width || 920;
    const height = viewBox?.height || 460;
    const originX = viewBox?.x || 0;
    const originY = viewBox?.y || 0;
    return {
      x: originX + ((event.clientX - rect.left) / Math.max(rect.width, 1)) * width,
      y: originY + ((event.clientY - rect.top) / Math.max(rect.height, 1)) * height,
      width,
      height,
    };
  };

  const pointerPoint = (svg, event, state) => {
    const point = svgPoint(svg, event);
    return {
      x: (point.x - state.camera_x) / state.camera_zoom,
      y: (point.y - state.camera_y) / state.camera_zoom,
    };
  };

  const boundsFromPoints = (start, end) => ({
    minX: Math.min(start.x, end.x),
    minY: Math.min(start.y, end.y),
    maxX: Math.max(start.x, end.x),
    maxY: Math.max(start.y, end.y),
  });

  const selectedNodeIdsInBounds = (nodes, bounds) => nodes
    .filter((node) => {
      const x = number(node.x, Number.NaN);
      const y = number(node.y, Number.NaN);
      return x >= bounds.minX && x <= bounds.maxX && y >= bounds.minY && y <= bounds.maxY;
    })
    .map((node) => node.id)
    .filter(Boolean)
    .sort();

  const fittedCameraState = (state, nodes, viewport = {}) => {
    const current = normalizeState(state);
    const points = (Array.isArray(nodes) ? nodes : [])
      .map((node) => ({
        x: number(node.x, Number.NaN),
        y: number(node.y, Number.NaN),
      }))
      .filter((node) => Number.isFinite(node.x) && Number.isFinite(node.y));
    if (!points.length) return normalizeState({ ...current, camera_x: 0, camera_y: 0, camera_zoom: 1 });
    const bounds = points.reduce((next, point) => ({
      minX: Math.min(next.minX, point.x),
      minY: Math.min(next.minY, point.y),
      maxX: Math.max(next.maxX, point.x),
      maxY: Math.max(next.maxY, point.y),
    }), {
      minX: points[0].x,
      minY: points[0].y,
      maxX: points[0].x,
      maxY: points[0].y,
    });
    const width = Math.max(1, number(viewport.width, 920));
    const height = Math.max(1, number(viewport.height, 460));
    const padding = Math.max(0, number(viewport.padding, 56));
    const availableWidth = Math.max(1, width - padding * 2);
    const availableHeight = Math.max(1, height - padding * 2);
    const graphWidth = Math.max(1, bounds.maxX - bounds.minX);
    const graphHeight = Math.max(1, bounds.maxY - bounds.minY);
    const zoom = clamp(Math.min(availableWidth / graphWidth, availableHeight / graphHeight), 0.35, 3);
    const centerX = (bounds.minX + bounds.maxX) / 2;
    const centerY = (bounds.minY + bounds.maxY) / 2;
    return normalizeState({
      ...current,
      camera_x: width / 2 - centerX * zoom,
      camera_y: height / 2 - centerY * zoom,
      camera_zoom: zoom,
    });
  };

  const fitNodesFromShell = (shell, state) => {
    const allNodes = [...shell.querySelectorAll(".gf-node")]
      .filter((node) => node.dataset.hidden !== "true")
      .map((node) => ({
        id: node.dataset.nodeId || "",
        x: node.dataset.x,
        y: node.dataset.y,
      }));
    const selectedIds = new Set(state.selected_node_ids || []);
    if (state.selected_edge_id) {
      const edge = shell.querySelector(`.gf-edge[data-edge-id="${CSS.escape(state.selected_edge_id)}"]`);
      if (edge?.dataset.sourceId) selectedIds.add(edge.dataset.sourceId);
      if (edge?.dataset.targetId) selectedIds.add(edge.dataset.targetId);
    }
    const selectedNodes = allNodes.filter((node) => selectedIds.has(node.id));
    return selectedNodes.length ? selectedNodes : allNodes;
  };

  const viewportSize = (shell) => {
    const viewBox = shell.querySelector(".gf-canvas")?.viewBox?.baseVal;
    return {
      width: viewBox?.width || 920,
      height: viewBox?.height || 460,
      padding: 56,
    };
  };

  const closeSurfaceMenus = (root) => {
    root.querySelectorAll(".gf-surface-menu").forEach((menu) => menu.remove());
  };

  const menuButton = (label, onClick) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", onClick);
    return button;
  };

  const menuLink = (label, route, navigate) => {
    const link = document.createElement("a");
    link.href = route || "#";
    link.textContent = label;
    link.addEventListener("click", (event) => {
      if (!route) return;
      event.preventDefault();
      navigate(route);
    });
    return link;
  };

  const keyboardShortcuts = [
    { key: "/ or Ctrl/Meta+K", action: "Focus graph search" },
    { key: "+ / =", action: "Zoom in" },
    { key: "-", action: "Zoom out" },
    { key: "Arrow keys / WASD", action: "Pan graph" },
    { key: "0", action: "Reset camera" },
    { key: "F", action: "Fullscreen" },
    { key: "Delete / Backspace", action: "Clear selection" },
    { key: "Esc", action: "Close surface menu" },
  ];

  const isEditableTarget = (target) => Boolean(
    target?.closest?.("input, textarea, select, button, a, [contenteditable='true']"),
  );

  const isGraphSearchShortcut = (event) => {
    const key = event?.key?.length === 1 ? event.key.toLowerCase() : event?.key;
    return key === "/" || Boolean((event?.ctrlKey || event?.metaKey) && key === "k");
  };

  const focusGraphSearch = (root) => {
    const input = root.querySelector("[data-gf-command-search]");
    if (!input) return false;
    input.focus();
    input.select?.();
    return true;
  };

  const normalizeCommandQuery = (query) => String(query || "").trim().toLowerCase();

  const commandPaletteActionMatches = (action, query) => {
    const needle = normalizeCommandQuery(query);
    if (!needle) return true;
    const haystack = [
      action?.id,
      action?.label,
      action?.summary,
      action?.group,
      action?.verb,
      action?.route,
    ].map((value) => String(value || "").toLowerCase()).join(" ");
    return needle.split(/\s+/).every((term) => haystack.includes(term));
  };

  const commandPaletteFilterSummary = (actions, query) => {
    const items = Array.isArray(actions) ? actions : [];
    const visible = items.filter((action) => commandPaletteActionMatches(action, query));
    return {
      query: normalizeCommandQuery(query),
      total_count: items.length,
      visible_count: visible.length,
      first_action_id: visible[0]?.id || "",
      first_route: visible[0]?.route || "",
    };
  };

  const commandRows = (panel) => [...panel.querySelectorAll("[data-command-id]")];

  const commandRowAction = (row) => ({
    id: row.dataset.commandId || "",
    group: row.dataset.commandGroup || "",
    label: row.querySelector("strong")?.textContent || row.textContent || "",
    summary: row.querySelector(".gf-inline-note")?.textContent || "",
    verb: row.querySelector("a")?.textContent || "",
    route: row.querySelector("a")?.getAttribute("href") || "",
  });

  const filterCommandPalettePanel = (panel, query) => {
    const rows = commandRows(panel);
    const actions = rows.map(commandRowAction);
    const summary = commandPaletteFilterSummary(actions, query);
    rows.forEach((row, index) => {
      const visible = commandPaletteActionMatches(actions[index], query);
      row.hidden = !visible;
      row.dataset.commandHidden = visible ? "false" : "true";
    });
    panel.querySelectorAll(".gf-command-group").forEach((group) => {
      const hasVisible = Boolean(group.querySelector("[data-command-hidden='false']"));
      group.hidden = !hasVisible;
    });
    const status = panel.querySelector("[data-gf-command-palette-status]");
    if (status) {
      status.textContent = summary.query
        ? `${summary.visible_count} of ${summary.total_count} command(s) match "${summary.query}".`
        : `${summary.total_count} command(s) available.`;
    }
    return summary;
  };

  const selectionStatusText = (state, labels = {}) => {
    const nodeIds = Array.isArray(state.selected_node_ids) ? state.selected_node_ids.filter(Boolean) : [];
    const nodeLabels = nodeIds.map((nodeId) => labels.nodes?.[nodeId] || nodeId);
    const edgeLabel = state.selected_edge_id ? labels.edges?.[state.selected_edge_id] || state.selected_edge_id : "";
    const parts = [];
    if (nodeLabels.length === 1) parts.push(`Selected 1 node: ${nodeLabels[0]}.`);
    if (nodeLabels.length > 1) {
      const suffix = nodeLabels.length > 3 ? ", ..." : ".";
      parts.push(`Selected ${nodeLabels.length} nodes: ${nodeLabels.slice(0, 3).join(", ")}${suffix}`);
    }
    if (edgeLabel) parts.push(`Selected edge: ${edgeLabel}.`);
    return parts.join(" ") || "No selected graph items. Shift-click nodes or Shift-drag canvas to select several.";
  };

  const graphItemLabels = (root) => ({
    nodes: Object.fromEntries([...root.querySelectorAll(".gf-node")].map((node) => [
      node.dataset.nodeId || "",
      node.dataset.label || node.dataset.nodeId || "",
    ])),
    edges: Object.fromEntries([...root.querySelectorAll(".gf-edge")].map((edge) => [
      edge.dataset.edgeId || "",
      edge.dataset.label || edge.dataset.edgeId || "",
    ])),
  });

  const authoringDefaults = (state, edges = []) => {
    const current = normalizeState(state);
    const selectedEdge = edges.find((edge) => edge?.id === current.selected_edge_id);
    if (selectedEdge) {
      const sourceId = selectedEdge.source_id || selectedEdge.sourceId || "";
      const targetNodeId = selectedEdge.target_id || selectedEdge.targetId || "";
      return {
        action_type: "draft_edge",
        target_id: current.selected_node_id || sourceId || targetNodeId,
        source_id: sourceId,
        target_node_id: targetNodeId,
      };
    }
    const selectedNodeIds = current.selected_node_ids.filter(Boolean);
    const sourceId = selectedNodeIds[0] || current.selected_node_id || "";
    const targetNodeId = selectedNodeIds.find((nodeId) => nodeId !== sourceId) || "";
    return {
      action_type: sourceId && targetNodeId ? "draft_edge" : "draft_node",
      target_id: current.selected_node_id || sourceId,
      source_id: sourceId,
      target_node_id: targetNodeId,
    };
  };

  const graphEdgeRefs = (root) => [...root.querySelectorAll(".gf-edge")].map((edge) => ({
    id: edge.dataset.edgeId || "",
    source_id: edge.dataset.sourceId || "",
    target_id: edge.dataset.targetId || "",
  }));

  const setFormValue = (form, name, value) => {
    const field = form?.elements?.[name];
    if (!field || value === undefined || value === null) return;
    field.value = String(value);
  };

  const captureTemplatePayload = (button) => ({
    label: String(button?.textContent || "").trim(),
    kind: String(button?.dataset?.kind || "note"),
    tags: String(button?.dataset?.tags || ""),
    source: String(button?.dataset?.source || "workbench"),
    placeholder: String(button?.dataset?.placeholder || ""),
  });

  const applyCaptureTemplate = (form, button) => {
    const payload = captureTemplatePayload(button);
    setFormValue(form, "kind", payload.kind);
    setFormValue(form, "tags", payload.tags);
    setFormValue(form, "source", payload.source);
    const text = form?.elements?.text;
    if (text && payload.placeholder) text.placeholder = payload.placeholder;
    const status = form?.querySelector?.("[data-gf-knowledge-status]");
    if (status) {
      status.textContent = `Template selected: ${payload.label || payload.kind}. Write the provider-owned note, then submit.`;
      status.dataset.state = "";
    }
    return payload;
  };

  const updateWorkbenchForms = (root, state) => {
    const defaults = authoringDefaults(state, graphEdgeRefs(root));
    const context = viewerContext(state);
    root.querySelectorAll("[data-gf-action-form]").forEach((form) => {
      setFormValue(form, "action_type", defaults.action_type);
      setFormValue(form, "target_id", defaults.target_id);
      setFormValue(form, "source_id", defaults.source_id);
      setFormValue(form, "target_node_id", defaults.target_node_id);
      setFormValue(form, "viewer_context", JSON.stringify(context));
    });
    root.querySelectorAll("[data-gf-knowledge-form]").forEach((form) => {
      setFormValue(form, "link_node_id", defaults.target_id || defaults.source_id);
      setFormValue(form, "viewer_context", JSON.stringify(context));
    });
    const rows = viewerContextRows(state, graphItemLabels(root));
    root.querySelectorAll("[data-gf-viewer-context-preview]").forEach((preview) => {
      Object.entries(rows).forEach(([key, value]) => {
        const row = preview.querySelector(`[data-gf-viewer-context-row="${CSS.escape(key)}"]`);
        if (row) row.textContent = value;
      });
    });
  };

  const updateSelectionStatus = (root, state) => {
    const status = root.querySelector("[data-gf-live-selection]");
    if (!status) return;
    const text = selectionStatusText(state, graphItemLabels(root));
    status.textContent = text;
    status.dataset.selectedCount = String((state.selected_node_ids || []).length);
    status.dataset.edgeSelected = state.selected_edge_id ? "true" : "false";
  };

  const drawCanvas = (shell) => {
    const canvas = shell.querySelector(".gf-canvas-renderer");
    if (!canvas?.getContext) return;
    const context = canvas.getContext("2d");
    if (!context) return;
    const nodes = new Map([...shell.querySelectorAll(".gf-node")].map((node) => [
      node.dataset.nodeId,
      {
        x: number(node.dataset.x, 0),
        y: number(node.dataset.y, 0),
        selected: node.dataset.selected === "true",
        kind: node.dataset.kind || "node",
        degree: number(node.dataset.degree, 0),
      },
    ]));
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.save();
    context.lineCap = "round";
    shell.querySelectorAll(".gf-edge").forEach((edge) => {
      const source = nodes.get(edge.dataset.sourceId);
      const target = nodes.get(edge.dataset.targetId);
      if (!source || !target) return;
      context.beginPath();
      context.moveTo(source.x, source.y);
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const distance = Math.hypot(dx, dy) || 1;
      const bend = clamp(distance * 0.12, 10, 46);
      const cx = (source.x + target.x) / 2 - (dy / distance) * bend;
      const cy = (source.y + target.y) / 2 + (dx / distance) * bend;
      context.quadraticCurveTo(cx, cy, target.x, target.y);
      context.strokeStyle = edge.dataset.selected === "true" ? "#f97316" : "rgba(62,74,92,0.34)";
      context.lineWidth = number(edge.dataset.edgeWidth, 1.4);
      context.globalAlpha = number(edge.dataset.edgeOpacity, 1);
      context.stroke();
    });
    context.globalAlpha = 1;
    nodes.forEach((node) => {
      context.beginPath();
      context.arc(node.x, node.y, Math.max(3, Math.min(12, 4 + node.degree)), 0, Math.PI * 2);
      context.fillStyle = node.selected ? "#f97316" : node.kind === "provider" ? "#2563eb" : "#111827";
      context.fill();
      context.strokeStyle = "rgba(255,255,255,0.85)";
      context.lineWidth = 2;
      context.stroke();
    });
    context.restore();
  };

  const nodeInspectPayload = (node) => ({
    id: node?.dataset.nodeId || "",
    label: node?.dataset.label || node?.dataset.nodeId || "Node",
    kind: node?.dataset.kind || "node",
    summary: node?.dataset.summary || "",
    source: node?.dataset.source || "",
    contentTitle: node?.dataset.contentTitle || node?.dataset.label || "Content",
    contentPreview: node?.dataset.contentPreview || node?.dataset.summary || "",
    degree: node?.dataset.degree || "0",
    clusterId: node?.dataset.clusterId || "",
    componentId: node?.dataset.componentId || "",
    provenanceIds: splitList(node?.dataset.provenanceIds || ""),
    citationIds: splitList(node?.dataset.citationIds || ""),
    focusRoute: node?.dataset.focusRoute || "",
    localRoute: node?.dataset.localRoute || "",
    evidenceRoute: node?.dataset.evidenceRoute || "",
  });

  const setText = (root, selector, value) => {
    const element = root.querySelector(selector);
    if (element) element.textContent = value || "";
  };

  const propertiesMarkup = (payload) => [
    ["id", payload.id],
    ["source", payload.source],
    ["kind", payload.kind],
    ["cluster", payload.clusterId],
    ["component", payload.componentId],
    ["degree", payload.degree],
    ["provenance", payload.provenanceIds.length],
    ["citations", payload.citationIds.length],
  ]
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(String(value))}</dd>`)
    .join("");

  const openInspectOverlay = (root, node) => {
    const overlay = root.querySelector("[data-gf-inspect-overlay]");
    if (!overlay || !node) return;
    const payload = nodeInspectPayload(node);
    overlay.dataset.open = "true";
    overlay.dataset.nodeId = payload.id;
    setText(overlay, "[data-gf-inspect-kind]", payload.kind);
    setText(overlay, "[data-gf-inspect-title]", payload.contentTitle || payload.label);
    setText(overlay, "[data-gf-inspect-summary]", payload.summary);
    setText(overlay, "[data-gf-inspect-content]", payload.contentPreview || payload.summary);
    setText(
      overlay,
      "[data-gf-inspect-evidence]",
      `${payload.provenanceIds.length} provenance item(s), ${payload.citationIds.length} citation(s).`,
    );
    const properties = overlay.querySelector("[data-gf-inspect-properties]");
    if (properties) {
      properties.innerHTML = propertiesMarkup(payload);
      properties.dataset.propertiesJson = JSON.stringify(payload);
    }
    const targetInput = overlay.querySelector("[data-gf-inspect-target-id]");
    if (targetInput) targetInput.value = payload.id;
    const sourceInput = overlay.querySelector("[data-gf-inspect-source]");
    if (sourceInput) sourceInput.value = payload.source;
    overlay.querySelector("[data-gf-overlay-action='center']")?.setAttribute("data-route", payload.focusRoute);
    overlay.querySelector("[data-gf-overlay-action='local']")?.setAttribute("data-route", payload.localRoute);
    overlay.querySelector("[data-gf-overlay-action='evidence']")?.setAttribute("data-route", payload.evidenceRoute);
    emit(root, "inspect-open", { node: payload, state: root.getState?.() || {} });
  };

  const closeInspectOverlay = (root) => {
    const overlay = root.querySelector("[data-gf-inspect-overlay]");
    if (!overlay) return;
    overlay.dataset.open = "false";
    emit(root, "inspect-close", { state: root.getState?.() || {} });
  };

  class GraphFakosViewer extends (typeof HTMLElement === "undefined" ? class {} : HTMLElement) {
    #wired = false;
    #suppressNextClick = false;

    connectedCallback() {
      this.graph = parseJsonAttribute(this, "data-graph-json", {});
      this.state = normalizeState(parseJsonAttribute(this, "data-state-json", {}));
      const urlHasTheme = typeof window !== "undefined" && new URLSearchParams(window.location.search).has("theme");
      const storedTheme = readStoredTheme();
      if (!urlHasTheme && storedTheme) this.state.theme = storedTheme;
      writeStoredTheme(this.state.theme);
      if (typeof document !== "undefined") document.body?.setAttribute?.("data-theme", this.state.theme);
      this.setAttribute("data-render-engine", this.state.render_engine);
      this.setAttribute("data-theme", this.state.theme);
      this.#wireFallbackDom();
      this.querySelectorAll(".gf-canvas-shell").forEach((shell) => {
        applyPinnedPositions(shell, this.state);
        applyCamera(shell, this.state);
      });
      updateSelectionStatus(this, this.state);
      updateWorkbenchForms(this, this.state);
      this.#renderWorkbook();
      this.querySelectorAll(".gf-canvas-shell").forEach((shell) => drawCanvas(shell));
      emit(this, "ready", { state: this.getState(), graph: this.graph });
    }

    loadGraph(graph) {
      this.graph = clone(graph);
      emit(this, "graph-loaded", { state: this.getState(), graph: this.graph });
    }

    dispatch(command) {
      const previous = this.getState();
      this.state = reduce(this.state, command);
      this.#applyState(command?.name || "state", previous);
      return this.getState();
    }

    getState() {
      return normalizeState(this.state);
    }

    setState(state) {
      const previous = this.getState();
      this.state = normalizeState(state);
      this.#applyState("state", previous);
      return this.getState();
    }

    exportState() {
      const state = this.getState();
      emit(this, "export-state", { state });
      return state;
    }

    fitSelection(shell = null) {
      const targetShell = shell || this.querySelector(".gf-canvas-shell");
      if (!targetShell) return this.resetCamera();
      const fitted = fittedCameraState(this.state, fitNodesFromShell(targetShell, this.state), viewportSize(targetShell));
      return this.dispatch({
        name: "camera",
        payload: {
          x: fitted.camera_x,
          y: fitted.camera_y,
          zoom: fitted.camera_zoom,
          yaw: this.state.camera_yaw,
          pitch: this.state.camera_pitch,
        },
      });
    }

    resetCamera() {
      return this.dispatch({ name: "camera", payload: { x: 0, y: 0, zoom: 1, yaw: 0, pitch: 0 } });
    }

    #handleCanvasKey(shell, event) {
      if (isEditableTarget(event.target)) return;
      const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
      const panStep = event.shiftKey ? 64 : 32;
      const camera = {};
      if (key === "+" || key === "=") camera.zoom = this.state.camera_zoom * 1.18;
      if (key === "-") camera.zoom = this.state.camera_zoom / 1.18;
      if (key === "q") {
        if (this.state.render_engine === "3d") camera.yaw = this.state.camera_yaw - 8;
        else camera.zoom = this.state.camera_zoom * 1.08;
      }
      if (key === "e") {
        if (this.state.render_engine === "3d") camera.yaw = this.state.camera_yaw + 8;
        else camera.zoom = this.state.camera_zoom / 1.08;
      }
      if (key === "0") {
        event.preventDefault();
        this.resetCamera();
        return;
      }
      if (key === "ArrowLeft" || key === "a") camera.x = this.state.camera_x + panStep;
      if (key === "ArrowRight" || key === "d") camera.x = this.state.camera_x - panStep;
      if (key === "ArrowUp" || key === "w") camera.y = this.state.camera_y + panStep;
      if (key === "ArrowDown" || key === "s") camera.y = this.state.camera_y - panStep;
      if (key === "f") {
        event.preventDefault();
        shell.requestFullscreen?.();
        return;
      }
      if (key === "Escape") {
        closeSurfaceMenus(document);
        return;
      }
      if (key === "Delete" || key === "Backspace") {
        event.preventDefault();
        this.dispatch({ name: "clear-selection" });
        return;
      }
      if (!Object.keys(camera).length) return;
      event.preventDefault();
      this.dispatch({ name: "camera", payload: camera });
    }

    async navigate(url, options = {}) {
      if (typeof fetch !== "function" || typeof DOMParser !== "function") {
        if (typeof window !== "undefined") window.location.href = String(url);
        return false;
      }
      const target = new URL(String(url), window.location.href);
      if (!isInternalRoute(target)) return false;
      if (!target.searchParams.has("theme")) target.searchParams.set("theme", this.state.theme);
      emit(this, "route-loading", { route: routeFromUrl(target), state: this.getState() });
      try {
        const response = await fetch(routeFromUrl(target), {
          headers: {
            Accept: "application/json",
            "X-GraphFakos-Fragment": "1",
          },
        });
        if (!response.ok) throw new Error(`route fetch failed: ${response.status}`);
        const payload = await response.json();
        const fragment = String(payload.fragment || "");
        const doc = new DOMParser().parseFromString(fragment, "text/html");
        const next = doc.querySelector("graphfakos-viewer");
        if (!next) throw new Error("route fragment did not include graphfakos-viewer");
        this.replaceWith(next);
        if (options.push !== false && window.history?.pushState) {
          window.history.pushState({ graphfakos: true }, "", routeFromUrl(target));
        }
        emit(next, "route-loaded", { route: payload.route || routeFromUrl(target), state: next.getState?.() || {} });
        return true;
      } catch (error) {
        emit(this, "error", { message: error?.message || String(error), route: routeFromUrl(target) });
        if (typeof window !== "undefined") window.location.href = routeFromUrl(target);
        return false;
      }
    }

    async submitKnowledge(form) {
      const status = form.querySelector("[data-gf-knowledge-status]");
      const setStatus = (message, state = "") => {
        if (!status) return;
        status.textContent = message;
        status.dataset.state = state;
      };
      if (!["http:", "https:"].includes(window.location.protocol)) {
        setStatus("Run the local preview server to add notes; static exports are read-only.", "error");
        return false;
      }
      const data = new FormData(form);
      const tags = String(data.get("tags") || "")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
      const payload = {
        text: String(data.get("text") || ""),
        kind: String(data.get("kind") || "note"),
        tags,
        source: String(data.get("source") || "workbench"),
        link_node_id: String(data.get("link_node_id") || ""),
        link_edge_kind: String(data.get("link_edge_kind") || "mentions"),
        provider_payload: {
          screen: String(data.get("screen") || this.state.screen || "explore"),
          viewer_context: viewerContext(this.state),
        },
      };
      emit(this, "knowledge-submit", { payload, state: this.getState() });
      setStatus("Adding note...", "");
      try {
        const response = await fetch(form.getAttribute("action") || "/api/knowledge", {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });
        const result = await response.json();
        if (!response.ok || result.ok === false) {
          throw new Error(result.error || `capture failed: ${response.status}`);
        }
        form.reset();
        setStatus("Added. Refreshing graph...", "saved");
        emit(this, "knowledge-saved", { payload, result, state: this.getState() });
        await this.navigate(window.location.href, { push: false });
        return true;
      } catch (error) {
        setStatus(error?.message || String(error), "error");
        emit(this, "error", { message: error?.message || String(error), action: "knowledge" });
        return false;
      }
    }

    async submitAction(form) {
      const status = form.querySelector("[data-gf-action-status-text]");
      const setStatus = (message, state = "") => {
        if (!status) return;
        status.textContent = message;
        status.dataset.state = state;
      };
      if (!["http:", "https:"].includes(window.location.protocol)) {
        setStatus("Run the local preview server to queue graph actions; static exports are read-only.", "error");
        return false;
      }
      const data = new FormData(form);
      const payload = {
        action_id: String(data.get("action_id") || `draft:${Date.now()}`),
        action_type: String(data.get("action_type") || "draft_node"),
        target_id: String(data.get("target_id") || ""),
        source_id: String(data.get("source_id") || ""),
        target_node_id: String(data.get("target_node_id") || ""),
        label: String(data.get("label") || ""),
        body: String(data.get("body") || ""),
        tags: splitList(data.get("tags")),
        provider_payload: {
          screen: this.state.screen || "explore",
          saved_view_id: this.state.saved_view_id || "",
          viewer_context: viewerContext(this.state),
        },
      };
      emit(this, "action-submit", { payload, state: this.getState() });
      setStatus("Queueing action...", "");
      try {
        const response = await fetch(form.getAttribute("action") || "/api/action", {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });
        const result = await response.json();
        if (!response.ok || result.ok === false) {
          throw new Error(result.error || result.status?.message || `action failed: ${response.status}`);
        }
        form.reset();
        const message = result.status?.message || "Action queued for provider review.";
        setStatus(`${message} Refreshing graph...`, "saved");
        emit(this, "action-saved", { payload, result, state: this.getState() });
        await this.navigate(window.location.href, { push: false });
        return true;
      } catch (error) {
        setStatus(error?.message || String(error), "error");
        emit(this, "error", { message: error?.message || String(error), action: "graph-action" });
        return false;
      }
    }

    #workbookStorage() {
      return safeLocalStorage();
    }

    #setWorkbookStatus(message, state = "") {
      const status = this.querySelector("[data-gf-workbook-status]");
      if (!status) return;
      status.textContent = message;
      status.dataset.state = state;
    }

    #renderWorkbook() {
      renderWorkbookSlots(
        this,
        workbookSlotsFromStorage(this.#workbookStorage()),
        (route) => this.navigate(route),
      );
    }

    #saveWorkbookSlot() {
      const storage = this.#workbookStorage();
      if (!storage) {
        this.#setWorkbookStatus("Local saved slots are unavailable in this browser context.", "error");
        return;
      }
      const label = this.querySelector("[data-gf-workbook-name]")?.value || "";
      const slot = workbookSlotPayload(this.getState(), label);
      const slots = [slot, ...workbookSlotsFromStorage(storage).filter((item) => item.id !== slot.id)].slice(0, 8);
      writeWorkbookSlots(storage, slots);
      this.#renderWorkbook();
      this.#setWorkbookStatus(`Saved local slot: ${slot.label}.`, "saved");
      emit(this, "workbook-saved", { slot, state: this.getState() });
    }

    #clearWorkbookSlots() {
      const storage = this.#workbookStorage();
      if (!storage?.removeItem) {
        this.#setWorkbookStatus("Local saved slots are unavailable in this browser context.", "error");
        return;
      }
      storage.removeItem(workbookStorageKey);
      this.#renderWorkbook();
      this.#setWorkbookStatus("Cleared local saved slots.", "");
      emit(this, "workbook-cleared", { state: this.getState() });
    }

    #wireCommandPalette() {
      this.querySelectorAll("[data-gf-command-palette-panel]").forEach((panel) => {
        const input = panel.querySelector("[data-gf-command-palette-search]");
        if (!input) return;
        const apply = () => {
          const summary = filterCommandPalettePanel(panel, input.value);
          emit(this, "command-palette-filtered", { ...summary, state: this.getState() });
          return summary;
        };
        apply();
        input.addEventListener("input", apply);
        input.addEventListener("keydown", (event) => {
          if (event.key === "Escape") {
            input.value = "";
            apply();
            event.preventDefault();
            return;
          }
          if (event.key !== "Enter") return;
          const first = commandRows(panel).find((row) => !row.hidden && row.dataset.disabled !== "true");
          const link = first?.querySelector("a[href]");
          if (!link) return;
          event.preventDefault();
          link.click();
        });
      });
    }

    destroy() {
      this.replaceWith(...this.childNodes);
    }

    #applyState(action, previous) {
      this.setAttribute("data-state-json", JSON.stringify(this.state));
      this.setAttribute("data-theme", this.state.theme);
      this.setAttribute("data-render-engine", this.state.render_engine);
      if (typeof document !== "undefined") document.body?.setAttribute?.("data-theme", this.state.theme);
      writeStoredTheme(this.state.theme);
      this.querySelectorAll(".gf-canvas-shell").forEach((shell) => applyCamera(shell, this.state));
      this.querySelectorAll(".gf-canvas-shell").forEach((shell) => applyPinnedPositions(shell, this.state));
      this.querySelectorAll(".gf-node").forEach((node) => {
        node.dataset.selected = this.state.selected_node_ids.includes(node.dataset.nodeId) ? "true" : "false";
        node.dataset.pinned = this.state.pinned_positions[node.dataset.nodeId] ? "true" : node.dataset.pinned || "false";
        node.dataset.hidden = this.state.hidden_groups.includes(node.dataset.kind) ? "true" : "false";
        node.dataset.neighbor = "false";
      });
      this.querySelectorAll(".gf-edge").forEach((edge) => {
        const selected = edge.dataset.edgeId === this.state.selected_edge_id;
        const source = this.querySelector(`.gf-node[data-node-id="${CSS.escape(edge.dataset.sourceId || "")}"]`);
        const target = this.querySelector(`.gf-node[data-node-id="${CSS.escape(edge.dataset.targetId || "")}"]`);
        edge.dataset.selected = selected ? "true" : "false";
        edge.dataset.hidden = source?.dataset.hidden === "true" || target?.dataset.hidden === "true" ? "true" : "false";
        edge.dataset.stretched = "false";
      });
      this.querySelectorAll(".gf-canvas-shell").forEach((shell) => {
        emphasizeConnectedEdges(shell, this.state.selected_node_ids || []);
      });
      this.querySelectorAll("[data-gf-group]").forEach((button) => {
        const group = button.dataset.gfGroup || "";
        const active = !this.state.hidden_groups.includes(group);
        button.dataset.active = active ? "true" : "false";
        button.title = `${active ? "Hide" : "Show"} ${group} nodes`;
      });
      updateSelectionStatus(this, this.state);
      updateWorkbenchForms(this, this.state);
      this.querySelectorAll(".gf-canvas-shell").forEach((shell) => drawCanvas(shell));
      emit(this, action, { previous, state: this.getState() });
    }

    async #copyText(value) {
      if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(value);
      }
      emit(this, "copy", { value, state: this.getState() });
    }

    #showSurfaceMenu(target, event) {
      const node = target?.closest?.(".gf-node");
      const edge = target?.closest?.(".gf-edge");
      if (!node && !edge) return false;
      event.preventDefault();
      event.stopPropagation();
      closeSurfaceMenus(document);
      const menu = document.createElement("div");
      menu.className = "gf-surface-menu";
      menu.setAttribute("role", "menu");
      menu.setAttribute("aria-label", node ? "Node actions" : "Edge actions");
      const heading = document.createElement("strong");
      heading.textContent = node
        ? node.dataset.label || node.dataset.nodeId || "Node"
        : edge.dataset.label || edge.dataset.edgeId || "Edge";
      menu.appendChild(heading);
      const closeAfter = (handler) => async () => {
        try {
          await handler();
        } finally {
          closeSurfaceMenus(document);
        }
      };
      const navigate = (route) => closeAfter(() => this.navigate(route))();
      if (node) {
        menu.appendChild(menuLink("Focus", node.dataset.focusRoute, navigate));
        menu.appendChild(menuLink("Local graph", node.dataset.localRoute, navigate));
        menu.appendChild(menuLink("Evidence", node.dataset.evidenceRoute, navigate));
        menu.appendChild(menuLink("Trace path", node.dataset.pathRoute, navigate));
        menu.appendChild(menuLink("Case packet", node.dataset.pivotRoute, navigate));
        menu.appendChild(menuButton(
          node.dataset.pinned === "true" ? "Unpin node" : "Pin node",
          closeAfter(() => {
            const command = node.dataset.pinned === "true" ? "unpin-node" : "pin-node";
            this.dispatch({
              name: command,
              target_id: node.dataset.nodeId || "",
              payload: {
                x: number(node.dataset.x, 0),
                y: number(node.dataset.y, 0),
              },
            });
          }),
        ));
        menu.appendChild(menuButton("Copy node ID", closeAfter(() => this.#copyText(node.dataset.nodeId || ""))));
      }
      if (edge) {
        menu.appendChild(menuLink("Inspect edge", edge.dataset.inspectRoute, navigate));
        menu.appendChild(menuLink("Trace path", edge.dataset.pathRoute, navigate));
        menu.appendChild(menuLink("Filter edge kind", edge.dataset.kindRoute, navigate));
        menu.appendChild(menuButton("Copy edge ID", closeAfter(() => this.#copyText(edge.dataset.edgeId || ""))));
      }
      menu.addEventListener("click", (menuEvent) => menuEvent.stopPropagation());
      document.body.appendChild(menu);
      const left = clamp(event.clientX, 8, Math.max(8, window.innerWidth - menu.offsetWidth - 8));
      const top = clamp(event.clientY, 8, Math.max(8, window.innerHeight - menu.offsetHeight - 8));
      menu.style.left = `${left}px`;
      menu.style.top = `${top}px`;
      menu.querySelector("a, button")?.focus?.();
      emit(this, "surface-menu", {
        edge_id: edge?.dataset.edgeId || "",
        node_id: node?.dataset.nodeId || "",
        state: this.getState(),
      });
      return true;
    }

    #showKeyboardSurfaceMenu(target, event) {
      const link = target?.closest?.("[data-gf-graph-item]");
      if (!link) return false;
      const graphItem = link.querySelector(".gf-node, .gf-edge");
      if (!graphItem) return false;
      const rect = link.getBoundingClientRect?.();
      return this.#showSurfaceMenu(graphItem, {
        preventDefault: () => event.preventDefault(),
        stopPropagation: () => event.stopPropagation(),
        clientX: rect ? rect.left + rect.width / 2 : 24,
        clientY: rect ? rect.top + rect.height / 2 : 24,
      });
    }

    #wireCanvasGestures(shell) {
      const svg = shell.querySelector(".gf-canvas");
      const viewport = shell.querySelector(".gf-viewport");
      if (!svg) return;
      let drag = null;
      let selectionBox = null;
      const removeSelectionBox = () => {
        selectionBox?.remove();
        selectionBox = null;
      };
      const updateSelectionBox = (start, end) => {
        if (!viewport) return;
        const bounds = boundsFromPoints(start, end);
        if (!selectionBox) {
          selectionBox = document.createElementNS("http://www.w3.org/2000/svg", "rect");
          selectionBox.classList.add("gf-selection-box");
          selectionBox.setAttribute("aria-hidden", "true");
          viewport.appendChild(selectionBox);
        }
        selectionBox.setAttribute("x", bounds.minX.toFixed(1));
        selectionBox.setAttribute("y", bounds.minY.toFixed(1));
        selectionBox.setAttribute("width", (bounds.maxX - bounds.minX).toFixed(1));
        selectionBox.setAttribute("height", (bounds.maxY - bounds.minY).toFixed(1));
      };
      const selectableNodesIn = (bounds) => selectedNodeIdsInBounds(
        [...shell.querySelectorAll(".gf-node")].map((node) => ({
          id: node.dataset.nodeId || "",
          x: node.dataset.x,
          y: node.dataset.y,
        })),
        bounds,
      );
      const clusterMembersFor = (node, point) => {
        const clusterId = node?.dataset.clusterId || "";
        if (!clusterId) return [];
        return [...shell.querySelectorAll(`.gf-node[data-cluster-id="${CSS.escape(clusterId)}"]`)].map((member) => ({
          nodeId: member.dataset.nodeId || "",
          offsetX: point.x - number(member.dataset.x, 0),
          offsetY: point.y - number(member.dataset.y, 0),
        })).filter((member) => member.nodeId);
      };
      const nearestNodeAt = (point, maxDistance = 28) => {
        let best = null;
        let bestDistance = maxDistance;
        shell.querySelectorAll(".gf-node").forEach((candidate) => {
          if (candidate.dataset.hidden === "true") return;
          const distance = Math.hypot(
            point.x - number(candidate.dataset.projectedX, number(candidate.dataset.x, 0)),
            point.y - number(candidate.dataset.projectedY, number(candidate.dataset.y, 0)),
          );
          if (distance <= bestDistance) {
            best = candidate;
            bestDistance = distance;
          }
        });
        return best;
      };
      const svgDelta = (event) => {
        const rect = svg.getBoundingClientRect();
        const viewBox = svg.viewBox?.baseVal;
        return {
          x: ((event.clientX - drag.startClientX) / Math.max(rect.width, 1)) * (viewBox?.width || 920),
          y: ((event.clientY - drag.startClientY) / Math.max(rect.height, 1)) * (viewBox?.height || 460),
        };
      };
      const markMoved = (event) => {
        const dx = event.clientX - drag.startClientX;
        const dy = event.clientY - drag.startClientY;
        if (Math.hypot(dx, dy) > 3) {
          drag.moved = true;
          this.#suppressNextClick = true;
        }
        return drag.moved;
      };
      svg.addEventListener("click", (event) => {
        if (this.#suppressNextClick) {
          event.preventDefault();
          event.stopPropagation();
          this.#suppressNextClick = false;
          return;
        }
        const directNode = event.target?.closest?.(".gf-node");
        if (directNode) return;
        const node = nearestNodeAt(pointerPoint(svg, event, this.state));
        if (!node) return;
        event.preventDefault();
        event.stopPropagation();
        this.dispatch({
          name: "select-node",
          target_id: node.dataset.nodeId || "",
          payload: { additive: event.shiftKey },
        });
        openInspectOverlay(this, node);
      }, true);
      const startDrag = (event, pointerCapture = false) => {
        if (event.button !== 0) return;
        const point = pointerPoint(svg, event, this.state);
        const node = event.target?.closest?.(".gf-node") || nearestNodeAt(point);
        const wantsClusterDrag = node && (event.altKey || node.dataset.kind === "cluster");
        const clusterMembers = wantsClusterDrag ? clusterMembersFor(node, point) : [];
        const backgroundDragType = this.state.render_engine === "3d" && !event.shiftKey && !event.altKey ? "orbit" : "pan";
        clearConnectedEmphasis(shell);
        drag = {
          type: clusterMembers.length > 1 ? "cluster" : node ? "node" : event.shiftKey ? "box" : backgroundDragType,
          nodeId: node?.dataset.nodeId || "",
          clusterId: node?.dataset.clusterId || "",
          clusterMembers,
          startClientX: event.clientX,
          startClientY: event.clientY,
          startPoint: point,
          startCameraX: this.state.camera_x,
          startCameraY: this.state.camera_y,
          startCameraYaw: this.state.camera_yaw,
          startCameraPitch: this.state.camera_pitch,
          offsetX: node ? point.x - number(node.dataset.x, 0) : 0,
          offsetY: node ? point.y - number(node.dataset.y, 0) : 0,
          moved: false,
        };
        if (node) emphasizeConnectedEdges(shell, clusterMembers.length > 1 ? clusterMembers.map((member) => member.nodeId) : [drag.nodeId]);
        if (pointerCapture && event.pointerId !== undefined) svg.setPointerCapture?.(event.pointerId);
        event.preventDefault();
      };
      const moveDrag = (event) => {
        if (!drag || !markMoved(event)) return;
        event.preventDefault();
        const point = pointerPoint(svg, event, this.state);
        if (drag.type === "box") {
          updateSelectionBox(drag.startPoint, point);
          return;
        }
        if (drag.type === "pan") {
          const delta = svgDelta(event);
          this.dispatch({
            name: "camera",
            payload: {
              x: drag.startCameraX + delta.x,
              y: drag.startCameraY + delta.y,
            },
          });
          return;
        }
        if (drag.type === "orbit") {
          const dx = event.clientX - drag.startClientX;
          const dy = event.clientY - drag.startClientY;
          this.dispatch({
            name: "camera",
            payload: {
              yaw: drag.startCameraYaw + dx * 0.28,
              pitch: drag.startCameraPitch - dy * 0.18,
            },
          });
          return;
        }
        if (drag.type === "cluster") {
          drag.clusterMembers.forEach((member) => {
            applyNodePosition(shell, member.nodeId, point.x - member.offsetX, point.y - member.offsetY);
          });
          emphasizeConnectedEdges(shell, drag.clusterMembers.map((member) => member.nodeId));
          drawCanvas(shell);
          return;
        }
        applyNodePosition(shell, drag.nodeId, point.x - drag.offsetX, point.y - drag.offsetY);
        emphasizeConnectedEdges(shell, [drag.nodeId]);
        drawCanvas(shell);
      };
      const finishDrag = (event) => {
        if (!drag) return;
        if (event.pointerId !== undefined) svg.releasePointerCapture?.(event.pointerId);
        if (drag.type === "box" && drag.moved) {
          const point = pointerPoint(svg, event, this.state);
          this.dispatch({
            name: "select-many",
            payload: {
              node_ids: selectableNodesIn(boundsFromPoints(drag.startPoint, point)),
            },
          });
          removeSelectionBox();
          drag = null;
          return;
        }
        if (drag.type === "node" && drag.moved) {
          const point = pointerPoint(svg, event, this.state);
          this.dispatch({
            name: "pin-node",
            target_id: drag.nodeId,
            payload: {
              x: point.x - drag.offsetX,
              y: point.y - drag.offsetY,
            },
          });
          this.dispatch({ name: "select-node", target_id: drag.nodeId });
          openInspectOverlay(this, shell.querySelector(`.gf-node[data-node-id="${CSS.escape(drag.nodeId)}"]`));
        }
        if (drag.type === "cluster" && drag.moved) {
          const point = pointerPoint(svg, event, this.state);
          this.dispatch({
            name: "pin-many",
            target_id: drag.clusterId,
            payload: {
              positions: Object.fromEntries(drag.clusterMembers.map((member) => [
                member.nodeId,
                [point.x - member.offsetX, point.y - member.offsetY],
              ])),
            },
          });
          this.dispatch({
            name: "select-many",
            payload: { node_ids: drag.clusterMembers.map((member) => member.nodeId) },
          });
          openInspectOverlay(this, shell.querySelector(`.gf-node[data-node-id="${CSS.escape(drag.clusterMembers[0]?.nodeId || "")}"]`));
        }
        removeSelectionBox();
        drag = null;
      };
      svg.addEventListener("pointerdown", (event) => startDrag(event, true));
      svg.addEventListener("mousedown", (event) => {
        if (!drag) startDrag(event, false);
      });
      svg.addEventListener("pointermove", moveDrag);
      svg.addEventListener("mousemove", moveDrag);
      svg.addEventListener("pointerup", finishDrag);
      svg.addEventListener("pointercancel", finishDrag);
      svg.addEventListener("mouseup", finishDrag);
      svg.addEventListener("mouseleave", finishDrag);
      svg.addEventListener("wheel", (event) => {
        event.preventDefault();
        const before = pointerPoint(svg, event, this.state);
        const point = svgPoint(svg, event);
        const zoom = clamp(this.state.camera_zoom * (event.deltaY < 0 ? 1.12 : 1 / 1.12), 0.35, 3);
        this.dispatch({
          name: "camera",
          payload: {
            x: point.x - before.x * zoom,
            y: point.y - before.y * zoom,
            zoom,
          },
        });
      }, { passive: false });
      svg.addEventListener("dblclick", (event) => {
        const node = event.target?.closest?.(".gf-node");
        if (!node) return;
        event.preventDefault();
        const point = svgPoint(svg, event);
        const zoom = Math.max(this.state.camera_zoom, 1.25);
        this.dispatch({
          name: "camera",
          payload: {
            x: point.width / 2 - number(node.dataset.projectedX, number(node.dataset.x, 0)) * zoom,
            y: point.height / 2 - number(node.dataset.projectedY, number(node.dataset.y, 0)) * zoom,
            zoom,
          },
        });
      });
    }

    #wireFallbackDom() {
      if (this.#wired) return;
      this.#wired = true;
      this.addEventListener("click", (event) => {
        if (!event.target?.closest?.(".gf-surface-menu")) closeSurfaceMenus(document);
        const template = event.target?.closest?.("[data-gf-capture-template]");
        if (template) {
          event.preventDefault();
          applyCaptureTemplate(template.closest("[data-gf-knowledge-form]"), template);
          return;
        }
        const inspectClose = event.target?.closest?.("[data-gf-inspect-close]");
        if (inspectClose) {
          event.preventDefault();
          closeInspectOverlay(this);
          return;
        }
        const overlayAction = event.target?.closest?.("[data-gf-overlay-action]");
        if (overlayAction) {
          event.preventDefault();
          const action = overlayAction.dataset.gfOverlayAction || "";
          const route = overlayAction.getAttribute("data-route") || "";
          const overlay = overlayAction.closest("[data-gf-inspect-overlay]");
          if (overlay) overlay.dataset.lastCommand = action;
          if (route && action !== "draft_note") {
            this.navigate(route);
            return;
          }
          emit(this, "edit-command", {
            action,
            target_id: this.querySelector("[data-gf-inspect-target-id]")?.value || "",
            note: this.querySelector("[data-gf-inspect-command] textarea")?.value || "",
            state: this.getState(),
          });
          return;
        }
        const link = event.target?.closest?.("a[href]");
        if (!link || event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        const target = new URL(link.getAttribute("href"), window.location.href);
        if (!isInternalRoute(target)) return;
        event.preventDefault();
        this.navigate(target);
      });
      this.addEventListener("contextmenu", (event) => {
        this.#showSurfaceMenu(event.target, event);
      });
      this.addEventListener("keydown", (event) => {
        if (!isEditableTarget(event.target) && isGraphSearchShortcut(event)) {
          event.preventDefault();
          if (focusGraphSearch(this)) emit(this, "search-focus", { state: this.getState() });
          return;
        }
        if (event.key === "Escape") closeSurfaceMenus(document);
        if (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10")) {
          this.#showKeyboardSurfaceMenu(event.target, event);
        }
      });
      if (typeof window !== "undefined" && !window.__graphfakosSurfaceMenuWired) {
        window.__graphfakosSurfaceMenuWired = true;
        document.addEventListener("click", (event) => {
          if (event.target?.closest?.(".gf-surface-menu")) return;
          closeSurfaceMenus(document);
        });
        document.addEventListener("keydown", (event) => {
          if (event.key === "Escape") closeSurfaceMenus(document);
        });
      }
      this.addEventListener("submit", (event) => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement)) return;
        if (form.matches("[data-gf-knowledge-form]")) {
          event.preventDefault();
          this.submitKnowledge(form);
          return;
        }
        if (form.matches("[data-gf-action-form]")) {
          event.preventDefault();
          this.submitAction(form);
          return;
        }
        if ((form.getAttribute("method") || "get").toLowerCase() !== "get") return;
        const target = new URL(form.getAttribute("action") || window.location.pathname, window.location.href);
        if (!isInternalRoute(target)) return;
        event.preventDefault();
        target.search = new URLSearchParams(new FormData(form)).toString();
        this.navigate(target);
      });
      this.querySelectorAll(".gf-canvas-shell").forEach((shell) => {
        applyCamera(shell, this.state);
        applyPinnedPositions(shell, this.state);
        this.#wireCanvasGestures(shell);
        shell.addEventListener("keydown", (event) => this.#handleCanvasKey(shell, event));
      });
      this.querySelectorAll("[data-gf-camera]").forEach((button) => {
        button.addEventListener("click", () => {
          const action = button.dataset.gfCamera;
          if (action === "zoom-in") this.dispatch({ name: "camera", payload: { zoom: this.state.camera_zoom * 1.18 } });
          if (action === "zoom-out") this.dispatch({ name: "camera", payload: { zoom: this.state.camera_zoom / 1.18 } });
          if (action === "fit") this.fitSelection(button.closest(".gf-canvas-panel")?.querySelector(".gf-canvas-shell"));
          if (action === "reset") this.resetCamera();
          if (action === "fullscreen") this.querySelector(".gf-canvas-shell")?.requestFullscreen?.();
        });
      });
      this.querySelectorAll("[data-gf-pin='reset']").forEach((button) => {
        button.addEventListener("click", () => this.dispatch({ name: "reset-pins" }));
      });
      this.querySelectorAll("[data-gf-workbook-action]").forEach((button) => {
        button.addEventListener("click", () => {
          if (button.dataset.gfWorkbookAction === "save") this.#saveWorkbookSlot();
          if (button.dataset.gfWorkbookAction === "clear") this.#clearWorkbookSlots();
        });
      });
      this.#wireCommandPalette();
      this.querySelectorAll(".gf-node").forEach((node) => {
        node.addEventListener("click", (event) => {
          event.preventDefault();
          event.stopPropagation();
          this.dispatch({
            name: "select-node",
            target_id: node.dataset.nodeId || "",
            payload: { additive: event.shiftKey },
          });
          openInspectOverlay(this, node);
        });
      });
      this.querySelectorAll(".gf-edge").forEach((edge) => {
        edge.addEventListener("click", (event) => {
          event.preventDefault();
          event.stopPropagation();
          this.dispatch({ name: "select-edge", target_id: edge.dataset.edgeId || "" });
        });
      });
      this.querySelectorAll("[data-gf-minimap-node]").forEach((item) => {
        item.addEventListener("click", (event) => {
          const nodeId = item.dataset.minimapNodeId || "";
          if (!nodeId) return;
          event.preventDefault();
          event.stopPropagation();
          this.dispatch({ name: "select-node", target_id: nodeId });
          this.fitSelection(item.closest(".gf-canvas-panel")?.querySelector(".gf-canvas-shell"));
          emit(this, "minimap-select", { node_id: nodeId, state: this.getState() });
        });
      });
      this.querySelectorAll("[data-gf-group]").forEach((button) => {
        button.addEventListener("click", () => this.dispatch({ name: "group-toggle", target_id: button.dataset.gfGroup || "" }));
      });
      this.querySelectorAll("[data-gf-group-show-all]").forEach((button) => {
        button.addEventListener("click", () => this.dispatch({ name: "group-show-all" }));
      });
      this.querySelectorAll("[data-node-ref]").forEach((item) => {
        item.addEventListener("mouseenter", () => {
          this.querySelectorAll(`[data-node-ref="${CSS.escape(item.dataset.nodeRef || "")}"]`).forEach((match) => {
            match.dataset.highlight = "true";
          });
        });
        item.addEventListener("mouseleave", () => {
          this.querySelectorAll("[data-highlight]").forEach((match) => {
            match.dataset.highlight = "false";
          });
        });
      });
    }
  }

  const runtime = {
    defaultState,
    normalizeState,
    reduce,
    eventName,
    fittedCameraState,
    projectPoint3D,
    detailMode,
    applyDetailMode,
    minimapViewportRect,
    keyboardShortcuts,
    isGraphSearchShortcut,
    selectionStatusText,
    selectedNodeIdsInBounds,
    nodeInspectPayload,
    viewerContext,
    viewerContextRows,
    authoringDefaults,
    captureTemplatePayload,
    commandPaletteActionMatches,
    commandPaletteFilterSummary,
    savedViewRoute,
    workbookSlotPayload,
    workbookSlotsFromStorage,
  };
  if (typeof window !== "undefined") window.GraphFakosViewerRuntime = runtime;
  if (typeof globalThis !== "undefined") globalThis.GraphFakosViewerRuntime = runtime;
  if (typeof window !== "undefined" && !window.__graphfakosPopstateWired) {
    window.__graphfakosPopstateWired = true;
    window.addEventListener("popstate", () => {
      document.querySelector("graphfakos-viewer")?.navigate?.(window.location.href, { push: false });
    });
  }
  if (typeof customElements !== "undefined" && !customElements.get("graphfakos-viewer")) {
    customElements.define("graphfakos-viewer", GraphFakosViewer);
  }
})();
