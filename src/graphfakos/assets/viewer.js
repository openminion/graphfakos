(() => {
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const number = (value, fallback) => {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  };
  const clone = (value) => JSON.parse(JSON.stringify(value || {}));
  const defaultState = {
    screen: "explore",
    layout: "force",
    selected_node_id: null,
    selected_node_ids: [],
    selected_edge_id: null,
    camera_x: 0,
    camera_y: 0,
    camera_zoom: 1,
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
    if (action === "unpin-node") {
      const nodeId = command.target_id || payload.node_id;
      if (nodeId) delete next.pinned_positions[nodeId];
    }
    if (action === "camera") {
      next.camera_x = number(payload.x ?? payload.camera_x, next.camera_x);
      next.camera_y = number(payload.y ?? payload.camera_y, next.camera_y);
      next.camera_zoom = clamp(number(payload.zoom ?? payload.camera_zoom, next.camera_zoom), 0.35, 3);
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

  const isInternalRoute = (url) => (
    typeof window !== "undefined"
    && (window.location.protocol === "http:" || window.location.protocol === "https:")
    && url.origin === window.location.origin
    && !url.hash
  );

  const updateSavedLink = (root, state) => {
    const link = root.querySelector("[data-gf-save-view]");
    if (!link || typeof URL !== "function") return;
    const url = new URL(link.getAttribute("href") || "/", "http://graphfakos.local");
    url.searchParams.set("camera_x", state.camera_x.toFixed(2));
    url.searchParams.set("camera_y", state.camera_y.toFixed(2));
    url.searchParams.set("camera_zoom", state.camera_zoom.toFixed(2));
    link.setAttribute("href", `${url.pathname}${url.search}`);
  };

  const applyCamera = (shell, state) => {
    const viewport = shell.querySelector(".gf-viewport");
    if (!viewport) return;
    viewport.setAttribute("transform", `translate(${state.camera_x} ${state.camera_y}) scale(${state.camera_zoom})`);
    shell.dataset.cameraX = state.camera_x.toFixed(2);
    shell.dataset.cameraY = state.camera_y.toFixed(2);
    shell.dataset.cameraZoom = state.camera_zoom.toFixed(2);
    updateSavedLink(shell.closest("graphfakos-viewer") || document, state);
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
      context.lineTo(target.x, target.y);
      context.strokeStyle = edge.dataset.selected === "true" ? "#f97316" : "rgba(62,74,92,0.34)";
      context.lineWidth = number(edge.dataset.edgeWidth, 1.4);
      context.globalAlpha = number(edge.dataset.edgeOpacity, 1);
      context.stroke();
    });
    context.globalAlpha = 1;
    nodes.forEach((node) => {
      context.beginPath();
      context.arc(node.x, node.y, Math.max(7, Math.min(18, 8 + node.degree * 2)), 0, Math.PI * 2);
      context.fillStyle = node.selected ? "#f97316" : node.kind === "provider" ? "#2563eb" : "#111827";
      context.fill();
      context.strokeStyle = "rgba(255,255,255,0.85)";
      context.lineWidth = 2;
      context.stroke();
    });
    context.restore();
  };

  class GraphFakosViewer extends (typeof HTMLElement === "undefined" ? class {} : HTMLElement) {
    #wired = false;

    connectedCallback() {
      this.graph = parseJsonAttribute(this, "data-graph-json", {});
      this.state = normalizeState(parseJsonAttribute(this, "data-state-json", {}));
      this.setAttribute("data-render-engine", this.state.render_engine);
      this.setAttribute("data-theme", this.state.theme);
      this.#wireFallbackDom();
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

    fitSelection() {
      return this.dispatch({ name: "camera", payload: { x: 0, y: 0, zoom: 1 } });
    }

    async navigate(url, options = {}) {
      if (typeof fetch !== "function" || typeof DOMParser !== "function") {
        if (typeof window !== "undefined") window.location.href = String(url);
        return false;
      }
      const target = new URL(String(url), window.location.href);
      if (!isInternalRoute(target)) return false;
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
        action_id: `draft:${Date.now()}`,
        action_type: String(data.get("action_type") || "draft_node"),
        target_id: String(data.get("target_id") || ""),
        label: String(data.get("label") || ""),
        body: String(data.get("body") || ""),
        provider_payload: {
          screen: this.state.screen || "explore",
          saved_view_id: this.state.saved_view_id || "",
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
        setStatus(result.status?.message || "Action queued for provider review.", "saved");
        emit(this, "action-saved", { payload, result, state: this.getState() });
        return true;
      } catch (error) {
        setStatus(error?.message || String(error), "error");
        emit(this, "error", { message: error?.message || String(error), action: "graph-action" });
        return false;
      }
    }

    destroy() {
      this.replaceWith(...this.childNodes);
    }

    #applyState(action, previous) {
      this.setAttribute("data-state-json", JSON.stringify(this.state));
      this.querySelectorAll(".gf-canvas-shell").forEach((shell) => applyCamera(shell, this.state));
      this.querySelectorAll(".gf-node").forEach((node) => {
        node.dataset.selected = this.state.selected_node_ids.includes(node.dataset.nodeId) ? "true" : "false";
        node.dataset.pinned = this.state.pinned_positions[node.dataset.nodeId] ? "true" : node.dataset.pinned || "false";
        node.dataset.hidden = this.state.hidden_groups.includes(node.dataset.kind) ? "true" : "false";
      });
      this.querySelectorAll(".gf-edge").forEach((edge) => {
        const selected = edge.dataset.edgeId === this.state.selected_edge_id;
        const source = this.querySelector(`.gf-node[data-node-id="${CSS.escape(edge.dataset.sourceId || "")}"]`);
        const target = this.querySelector(`.gf-node[data-node-id="${CSS.escape(edge.dataset.targetId || "")}"]`);
        edge.dataset.selected = selected ? "true" : "false";
        edge.dataset.hidden = source?.dataset.hidden === "true" || target?.dataset.hidden === "true" ? "true" : "false";
      });
      this.querySelectorAll(".gf-canvas-shell").forEach((shell) => drawCanvas(shell));
      emit(this, action, { previous, state: this.getState() });
    }

    #wireFallbackDom() {
      if (this.#wired) return;
      this.#wired = true;
      this.addEventListener("click", (event) => {
        const link = event.target?.closest?.("a[href]");
        if (!link || event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        const target = new URL(link.getAttribute("href"), window.location.href);
        if (!isInternalRoute(target)) return;
        event.preventDefault();
        this.navigate(target);
      });
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
      this.querySelectorAll(".gf-canvas-shell").forEach((shell) => applyCamera(shell, this.state));
      this.querySelectorAll("[data-gf-camera]").forEach((button) => {
        button.addEventListener("click", () => {
          const action = button.dataset.gfCamera;
          if (action === "zoom-in") this.dispatch({ name: "camera", payload: { zoom: this.state.camera_zoom * 1.18 } });
          if (action === "zoom-out") this.dispatch({ name: "camera", payload: { zoom: this.state.camera_zoom / 1.18 } });
          if (action === "fit" || action === "reset") this.fitSelection();
          if (action === "fullscreen") this.querySelector(".gf-canvas-shell")?.requestFullscreen?.();
        });
      });
      this.querySelectorAll(".gf-node").forEach((node) => {
        node.addEventListener("click", (event) => this.dispatch({
          name: "select-node",
          target_id: node.dataset.nodeId || "",
          payload: { additive: event.shiftKey },
        }));
      });
      this.querySelectorAll(".gf-edge").forEach((edge) => {
        edge.addEventListener("click", () => this.dispatch({ name: "select-edge", target_id: edge.dataset.edgeId || "" }));
      });
      this.querySelectorAll("[data-gf-group]").forEach((button) => {
        button.addEventListener("click", () => this.dispatch({ name: "group-toggle", target_id: button.dataset.gfGroup || "" }));
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

  const runtime = { defaultState, normalizeState, reduce, eventName };
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
