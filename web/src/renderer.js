import ForceGraph3D from "3d-force-graph";
import { CSS2DRenderer, CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";

const colorByKind = {
  artifact: "#ff936b",
  document: "#f4d06f",
  memory: "#9ce070",
  provider: "#5de1e6",
  warning: "#ff6b7a",
};

function hash(value) {
  let result = 2166136261;
  for (const character of String(value)) {
    result ^= character.charCodeAt(0);
    result = Math.imul(result, 16777619);
  }
  return result >>> 0;
}

function seededPosition(id, clusterId) {
  const clusterHash = hash(clusterId || "unclustered");
  const nodeHash = hash(id);
  const clusterAngle = (clusterHash % 360) * (Math.PI / 180);
  const clusterRadius = 120 + (clusterHash % 9) * 55;
  const localAngle = (nodeHash % 360) * (Math.PI / 180);
  const localRadius = 20 + (nodeHash % 80);
  return {
    x: Math.cos(clusterAngle) * clusterRadius + Math.cos(localAngle) * localRadius,
    y: Math.sin(clusterAngle) * clusterRadius + Math.sin(localAngle) * localRadius,
    z: ((clusterHash % 13) - 6) * 35 + ((nodeHash % 41) - 20) * 2,
  };
}

function clusterCenter(clusterId) {
  const value = hash(clusterId || "unclustered");
  const angle = (value % 360) * (Math.PI / 180);
  const radius = 150 + (value % 7) * 52;
  return {
    x: Math.cos(angle) * radius,
    y: Math.sin(angle) * radius,
    z: ((value % 11) - 5) * 42,
  };
}

function clusterForce(nodes) {
  let strength = 0.085;
  const force = (alpha) => {
    for (const node of nodes) {
      const center = clusterCenter(node.clusterId || node.kind);
      node.vx += (center.x - node.x) * strength * alpha;
      node.vy += (center.y - node.y) * strength * alpha;
      node.vz += (center.z - node.z) * strength * alpha;
    }
  };
  force.initialize = () => {};
  force.strength = (value) => {
    strength = value;
    return force;
  };
  return force;
}

function labelObject(node) {
  const element = document.createElement("span");
  element.className = "gf-webgl-label";
  element.textContent = node.label;
  const object = new CSS2DObject(element);
  object.position.set(0, 8, 0);
  return object;
}

function hasWebGL() {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

const layoutWorkerSource = `
const hash = (value) => {
  let result = 2166136261;
  for (const character of String(value)) {
    result ^= character.charCodeAt(0);
    result = Math.imul(result, 16777619);
  }
  return result >>> 0;
};
const position = (id, clusterId) => {
  const clusterHash = hash(clusterId || "unclustered");
  const nodeHash = hash(id);
  const clusterAngle = (clusterHash % 360) * Math.PI / 180;
  const clusterRadius = 150 + (clusterHash % 7) * 52;
  const localAngle = (nodeHash % 360) * Math.PI / 180;
  const localRadius = 22 + (nodeHash % 68);
  return {
    id,
    x: Math.cos(clusterAngle) * clusterRadius + Math.cos(localAngle) * localRadius,
    y: Math.sin(clusterAngle) * clusterRadius + Math.sin(localAngle) * localRadius,
    z: ((clusterHash % 11) - 5) * 42 + ((nodeHash % 31) - 15) * 2,
  };
};
self.onmessage = ({ data }) => {
  self.postMessage({ requestId: data.requestId, positions: data.nodes.map((node) => position(node.id, node.clusterId)) });
};`;

function startLayoutJob(nodes, onComplete) {
  if (typeof Worker === "undefined" || typeof Blob === "undefined") return null;
  const url = URL.createObjectURL(new Blob([layoutWorkerSource], { type: "text/javascript" }));
  const worker = new Worker(url);
  const requestId = `${Date.now()}:${nodes.length}`;
  worker.onmessage = ({ data }) => {
    if (data.requestId === requestId) onComplete(data.positions);
    worker.terminate();
    URL.revokeObjectURL(url);
  };
  worker.postMessage({
    requestId,
    nodes: nodes.map(({ id, clusterId }) => ({ id, clusterId })),
  });
  return {
    cancel() {
      worker.terminate();
      URL.revokeObjectURL(url);
    },
  };
}

function mount(element, scene, callbacks = {}) {
  if (!hasWebGL()) throw new Error("WebGL is unavailable");
  let nodes = scene.nodes.map((node) => ({
    ...node,
    ...seededPosition(node.id, node.clusterId || node.kind),
  }));
  let links = scene.links.map((link) => ({
    ...link,
    source: link.sourceId,
    target: link.targetId,
  }));
  let activeScene = scene;
  let initialFit = true;
  const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
  let clusterDrag = false;
  const setClusterDrag = (event) => {
    clusterDrag = event.altKey || event.key === "Alt";
  };
  const clearClusterDrag = (event) => {
    if (event.key === "Alt") clusterDrag = false;
  };
  window.addEventListener("keydown", setClusterDrag);
  window.addEventListener("keyup", clearClusterDrag);
  const graph = ForceGraph3D({ extraRenderers: [new CSS2DRenderer()] })(element)
    .backgroundColor(scene.theme === "space" ? "#070d24" : "#eef4f2")
    .graphData({ nodes, links })
    .nodeId("id")
    .nodeColor((node) => {
      const selected = new Set(activeScene.nodes.filter((item) => item.selected).map((item) => item.id));
      return selected.has(node.id) ? "#ffffff" : colorByKind[node.kind] || "#8aa4c8";
    })
    .nodeVal((node) => Math.max(1.1, Math.min(4.2, 1.1 + (node.degree || 0) * 0.12)))
    .nodeOpacity(0.94)
    .nodeVisibility((node) => !activeScene.nodes.find((item) => item.id === node.id)?.hidden)
    .nodeResolution(8)
    .linkColor((link) => (link.selected ? "#68d8ff" : scene.theme === "space" ? "#577198" : "#83949a"))
    .linkOpacity(scene.sceneLevel === "overview" ? 0.18 : 0.34)
    .linkVisibility((link) => !activeScene.links.find((item) => item.id === link.id)?.hidden)
    .linkWidth((link) => (link.selected ? 2.2 : 0.45))
    .linkCurvature((link) => ((hash(link.id) % 9) - 4) * 0.025)
    .linkCurveRotation((link) => (hash(`${link.id}:rotation`) % 628) / 100)
    .cooldownTicks(reducedMotion ? 0 : 160)
    .d3AlphaDecay(0.035)
    .d3VelocityDecay(0.36)
    .onNodeClick((node, event) => callbacks.onSelect?.(node, event))
    .onNodeDrag((node, translate) => {
      if (!clusterDrag || !node.clusterId) return;
      const positions = {};
      for (const member of nodes) {
        if (member.id === node.id || member.clusterId !== node.clusterId) continue;
        member.x += translate.x || 0;
        member.y += translate.y || 0;
        member.z += translate.z || 0;
        positions[member.id] = [member.x, member.y];
      }
      callbacks.onClusterMove?.(positions);
    })
    .onNodeDragEnd((node) => callbacks.onPin?.(node))
    .onBackgroundClick(() => callbacks.onBackground?.())
    .onEngineStop(() => {
      if (!initialFit) return;
      initialFit = false;
      graph.zoomToFit(650, 42);
    });

  graph.d3Force("charge")?.strength(-105);
  graph.d3Force("link")?.distance(62);
  graph.d3Force("cluster", clusterForce(nodes));
  graph.nodeThreeObject((node) => (node.priority === "focus" || node.selected ? labelObject(node) : null));
  graph.nodeThreeObjectExtend(true);

  const resize = () => {
    graph.width(Math.max(320, element.clientWidth));
    graph.height(Math.max(420, element.clientHeight));
  };
  const observer = new ResizeObserver(resize);
  observer.observe(element);
  resize();
  graph.cameraPosition({ x: 0, y: 0, z: 540 }, { x: 0, y: 0, z: 0 }, 0);
  const layoutJob = startLayoutJob(nodes, (positions) => {
    const byId = new Map(positions.map((position) => [position.id, position]));
    for (const node of nodes) Object.assign(node, byId.get(node.id) || {});
    if (!reducedMotion) graph.d3ReheatSimulation();
    graph.zoomToFit(reducedMotion ? 0 : 650, 42);
  });

  return {
    fit: () => graph.zoomToFit(500, 60),
    reset: () => {
      graph.cameraPosition({ x: 0, y: 0, z: 720 }, { x: 0, y: 0, z: 0 }, 500);
      graph.d3ReheatSimulation();
    },
    resetLayout: () => {
      for (const node of nodes) {
        const position = seededPosition(node.id, node.clusterId || node.kind);
        Object.assign(node, position, { fx: undefined, fy: undefined, fz: undefined });
      }
      graph.d3ReheatSimulation();
      graph.zoomToFit(650, 42);
    },
    update(nextScene) {
      activeScene = { ...activeScene, ...nextScene };
      if (Array.isArray(nextScene.nodes) && Array.isArray(nextScene.links)) {
        const positions = new Map(nodes.map((node) => [node.id, node]));
        nodes = nextScene.nodes.map((node) => ({
          ...node,
          ...(positions.get(node.id) || seededPosition(node.id, node.clusterId || node.kind)),
        }));
        links = nextScene.links.map((link) => ({
          ...link,
          source: link.sourceId,
          target: link.targetId,
        }));
        graph.graphData({ nodes, links });
        graph.d3Force("cluster", clusterForce(nodes));
        if (!reducedMotion) graph.d3ReheatSimulation();
      }
      graph.backgroundColor(nextScene.theme === "space" ? "#070d24" : "#eef4f2");
      graph.nodeColor(graph.nodeColor());
      graph.linkColor(graph.linkColor());
      graph.nodeVisibility(graph.nodeVisibility());
      graph.linkVisibility(graph.linkVisibility());
    },
    destroy() {
      observer.disconnect();
      layoutJob?.cancel();
      window.removeEventListener("keydown", setClusterDrag);
      window.removeEventListener("keyup", clearClusterDrag);
      graph._destructor?.();
      element.replaceChildren();
    },
    graph,
  };
}

globalThis.GraphFakos3D = { hasWebGL, mount, version: "1" };

export { hasWebGL, mount };
