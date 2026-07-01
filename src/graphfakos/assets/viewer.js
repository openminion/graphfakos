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
  };

  const normalizeState = (state) => {
    const next = { ...defaultState, ...clone(state) };
    next.camera_x = number(next.camera_x, 0);
    next.camera_y = number(next.camera_y, 0);
    next.camera_zoom = clamp(number(next.camera_zoom, 1), 0.35, 3);
    next.filters = clone(next.filters);
    next.expanded_groups = Array.isArray(next.expanded_groups) ? next.expanded_groups : [];
    next.hidden_groups = Array.isArray(next.hidden_groups) ? next.hidden_groups : [];
    return next;
  };

  const reduce = (state, command) => {
    const next = normalizeState(state);
    const action = command?.name || "";
    const payload = clone(command?.payload);
    if (action === "select-node") {
      next.selected_node_id = command.target_id || payload.node_id || null;
      next.selected_edge_id = null;
    }
    if (action === "select-edge") next.selected_edge_id = command.target_id || payload.edge_id || null;
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

  class GraphFakosViewer extends (typeof HTMLElement === "undefined" ? class {} : HTMLElement) {
    #wired = false;

    connectedCallback() {
      this.graph = parseJsonAttribute(this, "data-graph-json", {});
      this.state = normalizeState(parseJsonAttribute(this, "data-state-json", {}));
      this.setAttribute("data-render-engine", this.state.render_engine);
      this.setAttribute("data-theme", this.state.theme);
      this.#wireFallbackDom();
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

    destroy() {
      this.replaceWith(...this.childNodes);
    }

    #applyState(action, previous) {
      this.setAttribute("data-state-json", JSON.stringify(this.state));
      this.querySelectorAll(".gf-canvas-shell").forEach((shell) => applyCamera(shell, this.state));
      this.querySelectorAll(".gf-node").forEach((node) => {
        node.dataset.selected = node.dataset.nodeId === this.state.selected_node_id ? "true" : "false";
        node.dataset.hidden = this.state.hidden_groups.includes(node.dataset.kind) ? "true" : "false";
      });
      this.querySelectorAll(".gf-edge").forEach((edge) => {
        const selected = edge.dataset.edgeId === this.state.selected_edge_id;
        const source = this.querySelector(`.gf-node[data-node-id="${CSS.escape(edge.dataset.sourceId || "")}"]`);
        const target = this.querySelector(`.gf-node[data-node-id="${CSS.escape(edge.dataset.targetId || "")}"]`);
        edge.dataset.selected = selected ? "true" : "false";
        edge.dataset.hidden = source?.dataset.hidden === "true" || target?.dataset.hidden === "true" ? "true" : "false";
      });
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
        node.addEventListener("click", () => this.dispatch({ name: "select-node", target_id: node.dataset.nodeId || "" }));
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
