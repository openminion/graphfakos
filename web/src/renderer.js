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

function clusterCenters(nodes) {
  const clusterIds = [...new Set(nodes.map((node) => node.clusterId || node.kind || "unclustered"))].sort();
  if (clusterIds.length === 1) return new Map([[clusterIds[0], { x: 0, y: 0, z: 0 }]]);
  const spread = Math.min(620, 210 + Math.sqrt(clusterIds.length) * 92);
  const goldenAngle = Math.PI * (3 - Math.sqrt(5));
  return new Map(clusterIds.map((clusterId, index) => {
    const radius = spread * Math.sqrt((index + 0.7) / clusterIds.length);
    const angle = index * goldenAngle;
    return [clusterId, {
      x: Math.cos(angle) * radius,
      y: Math.sin(angle) * radius,
      z: ((index % 5) - 2) * 72,
    }];
  }));
}

function seededPosition(id, clusterId, centers) {
  const nodeHash = hash(id);
  const center = centers.get(clusterId || "unclustered") || { x: 0, y: 0, z: 0 };
  const localAngle = (nodeHash % 360) * (Math.PI / 180);
  const localRadius = 24 + (nodeHash % 64);
  return {
    x: center.x + Math.cos(localAngle) * localRadius,
    y: center.y + Math.sin(localAngle) * localRadius,
    z: center.z + ((nodeHash % 41) - 20) * 2,
  };
}

function clusterForce(nodes, centers) {
  let strength = 0.12;
  const force = (alpha) => {
    for (const node of nodes) {
      const center = centers.get(node.clusterId || node.kind || "unclustered") || { x: 0, y: 0, z: 0 };
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

function createLabelObject(node) {
  const element = document.createElement("span");
  element.className = "gf-webgl-label";
  element.dataset.priority = node.priority || "ambient";
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
const position = (id, clusterId, center) => {
  const nodeHash = hash(id);
  const localAngle = (nodeHash % 360) * Math.PI / 180;
  const localRadius = 24 + (nodeHash % 64);
  return {
    id,
    x: center.x + Math.cos(localAngle) * localRadius,
    y: center.y + Math.sin(localAngle) * localRadius,
    z: center.z + ((nodeHash % 41) - 20) * 2,
  };
};
self.onmessage = ({ data }) => {
  self.postMessage({
    requestId: data.requestId,
    positions: data.nodes.map((node) => position(
      node.id,
      node.clusterId,
      data.centers[node.clusterId || "unclustered"],
    )),
  });
};`;

function labelIds(nodes, scene) {
  const baseBudget = scene.sceneLevel === "local" ? 20 : scene.sceneLevel === "cluster" ? 10 : 4;
  const budget = Math.max(2, Math.round(baseBudget * (0.35 + (scene.labelDensity ?? 1) * 0.65)));
  return new Set([...nodes]
    .sort((left, right) => {
      const leftRank = left.selected ? 1000 : left.priority === "focus" ? 800 : left.priority === "hub" ? 500 : 0;
      const rightRank = right.selected ? 1000 : right.priority === "focus" ? 800 : right.priority === "hub" ? 500 : 0;
      return rightRank - leftRank || (right.degree || 0) - (left.degree || 0) || left.label.localeCompare(right.label);
    })
    .slice(0, Math.min(budget, nodes.length))
    .map((node) => node.id));
}

function connectedIds(links, focusId) {
  const result = new Set(focusId ? [focusId] : []);
  if (!focusId) return result;
  for (const link of links) {
    const sourceId = typeof link.source === "object" ? link.source.id : link.source;
    const targetId = typeof link.target === "object" ? link.target.id : link.target;
    if (sourceId === focusId) result.add(targetId);
    if (targetId === focusId) result.add(sourceId);
  }
  return result;
}

function startLayoutJob(nodes, centers, onComplete) {
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
    nodes: nodes.map(({ id, clusterId, kind }) => ({
      id,
      clusterId: clusterId || kind || "unclustered",
    })),
    centers: Object.fromEntries(centers),
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
  let centers = clusterCenters(scene.nodes);
  let nodes = scene.nodes.map((node) => ({
    ...node,
    ...seededPosition(node.id, node.clusterId || node.kind, centers),
  }));
  let links = scene.links.map((link) => ({
    ...link,
    source: link.sourceId,
    target: link.targetId,
  }));
  let activeScene = scene;
  let hoveredNodeId = "";
  let visibleLabelIds = labelIds(nodes, activeScene);
  const labelObjects = new Map();
  let initialFit = true;
  let frameTimer = 0;
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
  let selectedNodeIds = new Set();
  let activeFocusId = "";
  let focusedNodeIds = new Set();
  const refreshInteractionContext = () => {
    selectedNodeIds = new Set(activeScene.nodes.filter((node) => node.selected).map((node) => node.id));
    activeFocusId = hoveredNodeId || [...selectedNodeIds][0] || "";
    focusedNodeIds = connectedIds(links, activeFocusId);
  };
  refreshInteractionContext();
  const nodeColor = (node) => {
    if (selectedNodeIds.has(node.id)) return "#ffffff";
    if (node.id === hoveredNodeId) return "#f8fbff";
    if (activeFocusId && !focusedNodeIds.has(node.id)) {
      return activeScene.theme === "space" ? "#27324f" : "#c4cfcc";
    }
    return colorByKind[node.kind] || "#8aa4c8";
  };
  const linkEndpoints = (link) => ({
    source: typeof link.source === "object" ? link.source.id : link.source,
    target: typeof link.target === "object" ? link.target.id : link.target,
  });
  const linkTouchesFocus = (link) => {
    const { source, target } = linkEndpoints(link);
    return Boolean(activeFocusId && (source === activeFocusId || target === activeFocusId));
  };
  const linkColor = (link) => {
    if (link.selected) return "#72ddff";
    if (linkTouchesFocus(link)) return activeScene.theme === "space" ? "#8adfff" : "#287b91";
    return activeScene.theme === "space" ? "#5d6f91" : "#8f9d9a";
  };
  const nodeObject = (node) => {
    if (node.id !== hoveredNodeId && !node.selected && !visibleLabelIds.has(node.id)) return null;
    if (!labelObjects.has(node.id)) labelObjects.set(node.id, createLabelObject(node));
    return labelObjects.get(node.id);
  };
  const nodeSize = (node) => {
    const baseSize = 0.68 + (node.degree || 0) * 0.055;
    return Math.max(0.56, Math.min(2.35, baseSize * (activeScene.nodeScale || 1)));
  };
  const refreshVisuals = () => {
    graph.nodeColor(nodeColor);
    graph.linkColor(linkColor);
    graph.linkWidth((link) => (link.selected ? 2.1 : linkTouchesFocus(link) ? 1.15 : 0.32));
    graph.nodeThreeObject(nodeObject);
    graph.refresh();
  };
  const focusCamera = (node) => {
    const distance = 145;
    const length = Math.hypot(node.x || 0, node.y || 0, node.z || 0) || 1;
    const ratio = 1 + distance / length;
    graph.cameraPosition(
      { x: (node.x || 0) * ratio, y: (node.y || 0) * ratio, z: (node.z || 0) * ratio },
      node,
      reducedMotion ? 0 : 650,
    );
  };
  const graph = ForceGraph3D({ extraRenderers: [new CSS2DRenderer()] })(element)
    .backgroundColor(scene.theme === "space" ? "#070d24" : "#eef4f2")
    .showNavInfo(false)
    .graphData({ nodes, links })
    .nodeId("id")
    .nodeColor(nodeColor)
    .nodeVal(nodeSize)
    .nodeOpacity(0.92)
    .nodeVisibility((node) => !activeScene.nodes.find((item) => item.id === node.id)?.hidden)
    .nodeResolution(8)
    .linkColor(linkColor)
    .linkOpacity((scene.sceneLevel === "overview" ? 0.24 : 0.34) * (scene.edgeOpacity || 1))
    .linkVisibility((link) => !activeScene.links.find((item) => item.id === link.id)?.hidden)
    .linkWidth((link) => (link.selected ? 2.1 : linkTouchesFocus(link) ? 1.15 : 0.32))
    .linkCurvature((link) => ((hash(link.id) % 11) - 5) * 0.018)
    .linkCurveRotation((link) => (hash(`${link.id}:rotation`) % 628) / 100)
    .warmupTicks(reducedMotion ? 0 : 72)
    .cooldownTicks(reducedMotion ? 0 : 120)
    .d3AlphaDecay(0.035)
    .d3VelocityDecay(0.36)
    .onNodeClick((node, event) => {
      callbacks.onSelect?.(node, event);
      if ((event?.detail || 0) > 1) focusCamera(node);
    })
    .onNodeHover((node) => {
      hoveredNodeId = node?.id || "";
      refreshInteractionContext();
      refreshVisuals();
      callbacks.onHover?.(node || null);
    })
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
      frameGraph(420);
    });

  const frameGraph = (duration = 0) => {
    window.clearTimeout(frameTimer);
    graph.zoomToFit(duration, 18);
    frameTimer = window.setTimeout(() => {
      const camera = graph.cameraPosition();
      const scale = activeScene.sceneLevel === "local" ? 0.76 : 0.72;
      graph.cameraPosition(
        { x: camera.x * scale, y: camera.y * scale, z: camera.z * scale },
        { x: 0, y: 0, z: 0 },
        reducedMotion ? 0 : 180,
      );
    }, reducedMotion ? 0 : duration + 20);
  };

  graph.d3Force("charge")?.strength(-138);
  graph.d3Force("link")?.distance(68).strength(0.38);
  graph.d3Force("cluster", clusterForce(nodes, centers));
  graph.nodeThreeObject(nodeObject);
  graph.nodeThreeObjectExtend(true);

  const resize = () => {
    graph.width(Math.max(320, element.clientWidth));
    graph.height(Math.max(420, element.clientHeight));
  };
  const observer = new ResizeObserver(resize);
  observer.observe(element);
  resize();
  frameGraph();
  const layoutJob = startLayoutJob(nodes, centers, (positions) => {
    const byId = new Map(positions.map((position) => [position.id, position]));
    for (const node of nodes) Object.assign(node, byId.get(node.id) || {});
    if (!reducedMotion) graph.d3ReheatSimulation();
    frameGraph(reducedMotion ? 0 : 420);
  });

  return {
    fit: () => frameGraph(360),
    reset: () => {
      graph.cameraPosition({ x: 0, y: 0, z: 720 }, { x: 0, y: 0, z: 0 }, 500);
      graph.d3ReheatSimulation();
    },
    resetLayout: () => {
      for (const node of nodes) {
        const position = seededPosition(node.id, node.clusterId || node.kind, centers);
        Object.assign(node, position, { fx: undefined, fy: undefined, fz: undefined });
      }
      graph.d3ReheatSimulation();
      frameGraph(420);
    },
    update(nextScene) {
      activeScene = { ...activeScene, ...nextScene };
      if (Array.isArray(nextScene.nodes) && Array.isArray(nextScene.links)) {
        const positions = new Map(nodes.map((node) => [node.id, node]));
        centers = clusterCenters(nextScene.nodes);
        nodes = nextScene.nodes.map((node) => ({
          ...node,
          ...(positions.get(node.id) || seededPosition(node.id, node.clusterId || node.kind, centers)),
        }));
        links = nextScene.links.map((link) => ({
          ...link,
          source: link.sourceId,
          target: link.targetId,
        }));
        graph.graphData({ nodes, links });
        graph.d3Force("cluster", clusterForce(nodes, centers));
        if (!reducedMotion) graph.d3ReheatSimulation();
      }
      refreshInteractionContext();
      visibleLabelIds = labelIds(nodes, activeScene);
      graph.backgroundColor(nextScene.theme === "space" ? "#070d24" : "#eef4f2");
      graph.nodeVal(nodeSize);
      graph.linkOpacity((activeScene.sceneLevel === "overview" ? 0.24 : 0.34) * (activeScene.edgeOpacity || 1));
      graph.nodeVisibility(graph.nodeVisibility());
      graph.linkVisibility(graph.linkVisibility());
      refreshVisuals();
    },
    destroy() {
      observer.disconnect();
      layoutJob?.cancel();
      window.clearTimeout(frameTimer);
      labelObjects.clear();
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
