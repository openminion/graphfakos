import ForceGraph3D from "3d-force-graph";
import { Group, Mesh, MeshBasicMaterial, SphereGeometry } from "three";
import { CSS2DRenderer, CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";
import {
  collidingLabelIds,
  rectanglesOverlap,
  translatedCameraForReservation,
} from "./focus-readability.js";
import { shapeLinks, stableHash } from "./link-shape.js";
import {
  detailLevelForCamera,
  labelBudgetForDetail,
  nodeScaleForCount,
  semanticZoom,
} from "./semantic-detail.js";
import { directionalNodeId } from "./spatial-navigation.js";

const colorByKind = {
  artifact: "#ff936b",
  document: "#f4d06f",
  memory: "#9ce070",
  provider: "#5de1e6",
  warning: "#ff6b7a",
};

const nodeHitGeometry = new SphereGeometry(4.5, 8, 6);
const nodeHitMaterial = new MeshBasicMaterial({
  colorWrite: false,
  depthWrite: false,
  opacity: 0,
  transparent: true,
});

function clusterCenters(nodes) {
  const clusterIds = [...new Set(nodes.map((node) => node.clusterId || node.kind || "unclustered"))].sort();
  if (clusterIds.length === 1) return new Map([[clusterIds[0], { x: 0, y: 0, z: 0 }]]);
  const spread = Math.min(1460, 310 + Math.sqrt(clusterIds.length) * 138);
  const goldenAngle = Math.PI * (3 - Math.sqrt(5));
  return new Map(clusterIds.map((clusterId, index) => {
    const ring = Math.sqrt((index + 0.9) / clusterIds.length);
    const radius = spread * ring;
    const angle = index * goldenAngle;
    return [clusterId, {
      x: Math.cos(angle) * radius,
      y: Math.sin(angle) * radius,
      z: ((index % 7) - 3) * 92,
    }];
  }));
}

function seededPosition(id, clusterId, centers) {
  const nodeHash = stableHash(id);
  const center = centers.get(clusterId || "unclustered") || { x: 0, y: 0, z: 0 };
  const localAngle = (nodeHash % 360) * (Math.PI / 180);
  const localRadius = 12 + (nodeHash % 46);
  return {
    x: center.x + Math.cos(localAngle) * localRadius,
    y: center.y + Math.sin(localAngle) * localRadius,
    z: center.z + ((nodeHash % 47) - 23) * 1.7,
  };
}

function clusterForce(nodes, centers) {
  let strength = 0.18;
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

function labelContext(node) {
  const kind = node.kind || "node";
  const links = `${node.degree || 0} link${node.degree === 1 ? "" : "s"}`;
  const summary = String(node.summary || node.contentPreview || "").trim();
  const preview = summary.length > 92 ? `${summary.slice(0, 89).trimEnd()}...` : summary;
  return [kind, links, preview].filter(Boolean).join(" | ");
}

function createLabelObject(node) {
  const element = document.createElement("span");
  element.className = "gf-webgl-label";
  const title = document.createElement("strong");
  const context = document.createElement("small");
  element.append(title, context);
  const object = new CSS2DObject(element);
  object.position.set(0, 8, 0);
  return { element, object, title, context };
}

function createNodeObject() {
  const group = new Group();
  const hitTarget = new Mesh(nodeHitGeometry, nodeHitMaterial);
  hitTarget.name = "graphfakos-node-hit-target";
  group.add(hitTarget);
  return { group, label: null };
}

function updateNodeObject(record, node, showLabel, hovered, selected, related, previewed) {
  if (!showLabel && record.label) {
    record.group.remove(record.label.object);
    record.label = null;
  }
  if (!showLabel) return record.group;
  if (!record.label) {
    record.label = createLabelObject(node);
    record.group.add(record.label.object);
  }
  const { element, title, context } = record.label;
  element.dataset.nodeId = node.id;
  element.dataset.priority = node.priority || "ambient";
  element.dataset.hovered = String(hovered);
  element.dataset.selected = String(selected);
  element.dataset.related = String(related);
  element.dataset.previewed = String(previewed);
  title.textContent = node.label;
  context.textContent = labelContext(node);
  return record.group;
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
  const localRadius = 12 + (nodeHash % 46);
  return {
    id,
    x: center.x + Math.cos(localAngle) * localRadius,
    y: center.y + Math.sin(localAngle) * localRadius,
    z: center.z + ((nodeHash % 47) - 23) * 1.7,
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

function labelIds(nodes, scene, detailLevel) {
  const budget = labelBudgetForDetail(detailLevel, scene.labelDensity, nodes.length);
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
  let links = shapeLinks(nodes, scene.links);
  let activeScene = scene;
  let hoveredNodeId = "";
  let previewedNodeId = "";
  let semanticReferenceDistance = 0;
  let semanticDetail = detailLevelForCamera({ nodeCount: nodes.length });
  let visibleLabelIds = labelIds(nodes, activeScene, semanticDetail);
  const nodeObjects = new Map();
  let initialFit = true;
  let frameTimer = 0;
  let cameraFrame = 0;
  let labelFrame = 0;
  let labelLayoutFrame = 0;
  let cameraPreserved = false;
  let cameraInteractionGeneration = 0;
  const markCameraInteraction = () => {
    cameraInteractionGeneration += 1;
    cameraPreserved = true;
    initialFit = false;
    window.clearTimeout(frameTimer);
  };
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
  let contextLabelIds = new Set();
  let pointerGesture = null;
  const markTouchEngaged = (event) => {
    const point = event?.touches?.[0] || event;
    if (Number.isFinite(point?.clientX) && Number.isFinite(point?.clientY)) {
      const bounds = element.getBoundingClientRect();
      if (
        point.clientX < bounds.left || point.clientX > bounds.right
        || point.clientY < bounds.top || point.clientY > bounds.bottom
      ) return;
    }
    element.closest(".gf-canvas-shell")?.setAttribute("data-touch-engaged", "true");
  };
  const markTouchPointer = (event) => {
    if (event.pointerType === "touch") markTouchEngaged(event);
  };
  window.addEventListener("pointerdown", markTouchPointer, true);
  window.addEventListener("touchstart", markTouchEngaged, { capture: true, passive: true });
  const refreshInteractionContext = () => {
    selectedNodeIds = new Set(activeScene.nodes.filter((node) => node.selected).map((node) => node.id));
    activeFocusId = previewedNodeId || hoveredNodeId || [...selectedNodeIds][0] || "";
    focusedNodeIds = connectedIds(links, activeFocusId);
    contextLabelIds = new Set(nodes
      .filter((node) => node.id !== activeFocusId && focusedNodeIds.has(node.id) && !node.hidden)
      .sort((left, right) => (right.degree || 0) - (left.degree || 0) || left.label.localeCompare(right.label))
      .slice(0, 6)
      .map((node) => node.id));
  };
  refreshInteractionContext();
  const nodeColor = (node) => {
    if (selectedNodeIds.has(node.id)) return "#ffffff";
    if (node.id === hoveredNodeId || node.id === previewedNodeId) return "#f8fbff";
    if (activeFocusId && !focusedNodeIds.has(node.id)) {
      return activeScene.theme === "space" ? "#435171" : "#aebbb7";
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
    if (linkTouchesFocus(link)) return activeScene.theme === "space" ? "#c2f3ff" : "#17677c";
    if (activeFocusId) return activeScene.theme === "space" ? "#3e4a68" : "#a4afac";
    return activeScene.theme === "space" ? "#7890b8" : "#7f908c";
  };
  const linkWidth = (link) => (link.selected ? 2.1 : linkTouchesFocus(link) ? 1.35 : 0.28);
  const visibleNodeCount = () => activeScene.nodes.filter((node) => !node.hidden).length;
  const sceneLinkOpacity = () => {
    const visibleCount = visibleNodeCount();
    let base = {
      overview: 0.13,
      balanced: 0.22,
      detail: 0.32,
      precision: 0.42,
    }[semanticDetail] || 0.13;
    if (visibleCount <= 48) base = Math.max(base, 0.42);
    else if (visibleCount <= 110) base = Math.max(base, 0.3);
    return base * (activeScene.edgeOpacity || 1);
  };
  const nodeObject = (node) => {
    if (!nodeObjects.has(node.id)) nodeObjects.set(node.id, createNodeObject());
    const hovered = node.id === hoveredNodeId;
    const previewed = node.id === previewedNodeId;
    const selected = selectedNodeIds.has(node.id);
    const related = contextLabelIds.has(node.id);
    return updateNodeObject(
      nodeObjects.get(node.id),
      node,
      hovered || previewed || selected || related || visibleLabelIds.has(node.id),
      hovered,
      selected,
      related,
      previewed,
    );
  };
  const nodeSize = (node) => {
    const baseSize = 0.42 + Math.sqrt(Math.max(0, node.degree || 0)) * 0.09;
    const focusBoost = selectedNodeIds.has(node.id) || node.id === hoveredNodeId || node.id === previewedNodeId
      ? 1.8
      : focusedNodeIds.has(node.id) && activeFocusId ? 1.4 : 1;
    const sparseScale = nodeScaleForCount(visibleNodeCount());
    return Math.max(0.3, Math.min(16, baseSize * focusBoost * sparseScale * (activeScene.nodeScale || 1)));
  };
  const scheduleLabelLayout = () => {
    window.cancelAnimationFrame(labelLayoutFrame);
    labelLayoutFrame = window.requestAnimationFrame(() => {
      labelLayoutFrame = 0;
      const surfaceBounds = element.getBoundingClientRect();
      const overlay = element.closest("graphfakos-viewer")
        ?.querySelector("[data-gf-inspect-overlay][data-open='true']");
      const overlayBounds = overlay?.getBoundingClientRect?.();
      const reservedBounds = overlayBounds && rectanglesOverlap(surfaceBounds, overlayBounds, 0)
        ? overlayBounds
        : null;
      const rank = (node) => (
        (node.id === hoveredNodeId || node.id === previewedNodeId ? 4000 : 0)
        + (selectedNodeIds.has(node.id) ? 3000 : 0)
        + (contextLabelIds.has(node.id) ? 2000 : 0)
        + (node.priority === "focus" ? 1000 : node.priority === "hub" ? 500 : 0)
        + Math.min(200, node.degree || 0)
      );
      const records = nodes.map((node) => ({
        id: node.id,
        label: nodeObjects.get(node.id)?.label,
        forced: node.id === hoveredNodeId || node.id === previewedNodeId || selectedNodeIds.has(node.id),
        rank: rank(node),
      })).filter(({ label }) => label);
      const blocked = collidingLabelIds(
        records.map((record) => ({
          ...record,
          bounds: record.label.element.getBoundingClientRect(),
        })),
        surfaceBounds,
        reservedBounds,
        window.innerHeight,
      );
      records.forEach(({ id, label }) => {
        label.element.dataset.collided = String(blocked.has(id));
      });
    });
  };
  const refreshVisuals = () => {
    graph.nodeColor(nodeColor);
    graph.linkColor(linkColor);
    graph.linkWidth(linkWidth);
    graph.nodeThreeObject(nodeObject);
    graph.refresh();
    scheduleLabelLayout();
  };
  const placeHoveredLabel = () => {
    window.cancelAnimationFrame(labelFrame);
    labelFrame = window.requestAnimationFrame(() => {
      labelFrame = 0;
      const label = nodeObjects.get(previewedNodeId || hoveredNodeId)?.label;
      if (!label) return;
      const surfaceBounds = element.getBoundingClientRect();
      const labelBounds = label.element.getBoundingClientRect();
      const visibleTop = Math.max(0, surfaceBounds.top);
      const visibleBottom = Math.min(window.innerHeight, surfaceBounds.bottom);
      if (labelBounds.top < visibleTop + 8) label.object.position.y = -42;
      else if (labelBounds.bottom > visibleBottom - 8) label.object.position.y = 42;
      else return;
      graph.refresh();
      scheduleLabelLayout();
    });
  };
  const pointerDown = (event) => {
    if (event.pointerType === "touch") markTouchEngaged();
    if (event.button !== 0) return;
    const labelNodeId = event.target.closest?.(".gf-webgl-label")?.dataset.nodeId || "";
    pointerGesture = labelNodeId ? {
      nodeId: labelNodeId,
      x: event.clientX,
      y: event.clientY,
      moved: false,
    } : null;
  };
  const pointerMove = (event) => {
    const labelNodeId = event.target.closest?.(".gf-webgl-label")?.dataset.nodeId || "";
    if (labelNodeId && labelNodeId !== hoveredNodeId) {
      hoveredNodeId = labelNodeId;
      refreshInteractionContext();
      refreshVisuals();
      placeHoveredLabel();
      callbacks.onHover?.(nodes.find((item) => item.id === labelNodeId) || null);
    }
    if (!pointerGesture) return;
    pointerGesture.moved ||= Math.hypot(
      event.clientX - pointerGesture.x,
      event.clientY - pointerGesture.y,
    ) > 4;
  };
  const pointerUp = (event) => {
    const gesture = pointerGesture;
    pointerGesture = null;
    if (!gesture || gesture.moved || !gesture.nodeId) return;
    const node = nodes.find((item) => item.id === gesture.nodeId);
    if (!node) return;
    event.preventDefault();
    event.stopPropagation();
    callbacks.onSelect?.(node, event);
  };
  const pointerCancel = () => {
    pointerGesture = null;
  };
  const doubleClick = (event) => {
    const labelNodeId = event.target.closest?.(".gf-webgl-label")?.dataset.nodeId || "";
    const node = nodes.find((item) => item.id === (labelNodeId || hoveredNodeId));
    if (node) focusNeighborhood(node.id);
  };
  const focusNodes = (nodeIds, duration = 520) => {
    markCameraInteraction();
    const ids = new Set(Array.isArray(nodeIds) ? nodeIds.filter(Boolean) : []);
    const targets = nodes.filter((node) => ids.has(node.id) && !node.hidden);
    if (!targets.length) {
      frameGraph(duration, { preserve: true, resetReference: true });
      return;
    }
    const center = targets.reduce((next, node) => ({
      x: next.x + (node.x || 0),
      y: next.y + (node.y || 0),
      z: next.z + (node.z || 0),
    }), { x: 0, y: 0, z: 0 });
    center.x /= targets.length;
    center.y /= targets.length;
    center.z /= targets.length;
    const radius = targets.reduce((largest, node) => Math.max(
      largest,
      Math.hypot((node.x || 0) - center.x, (node.y || 0) - center.y, (node.z || 0) - center.z),
    ), 1);
    const camera = graph.cameraPosition();
    const direction = {
      x: camera.x - center.x,
      y: camera.y - center.y,
      z: camera.z - center.z,
    };
    const length = Math.hypot(direction.x, direction.y, direction.z) || 1;
    const distance = Math.max(170, Math.min(2200, radius * 2.8 + 150));
    graph.cameraPosition(
      {
        x: center.x + (direction.x / length) * distance,
        y: center.y + (direction.y / length) * distance,
        z: center.z + (direction.z / length) * distance,
      },
      center,
      reducedMotion ? 0 : duration,
    );
  };
  const focusNeighborhood = (nodeId, duration = 520) => {
    const nodeIds = [...connectedIds(links, nodeId)]
      .filter((id) => nodes.some((node) => node.id === id && !node.hidden));
    focusNodes(nodeIds.length > 1 ? nodeIds : [nodeId], duration);
  };
  const ensureNodeVisible = (nodeId, duration = 360) => {
    const node = nodes.find((item) => item.id === nodeId && !item.hidden);
    const overlay = element.closest("graphfakos-viewer")
      ?.querySelector("[data-gf-inspect-overlay][data-open='true']");
    if (!node || !overlay) return false;
    const surfaceBounds = element.getBoundingClientRect();
    const overlayBounds = overlay.getBoundingClientRect();
    if (!rectanglesOverlap(surfaceBounds, overlayBounds, 0)) return false;
    const camera = graph.camera?.();
    if (!camera) return false;
    const labelWidth = nodeObjects.get(nodeId)?.label?.element?.getBoundingClientRect?.().width || 0;
    const snapshot = cameraState();
    const translated = translatedCameraForReservation({
      camera,
      labelWidth,
      node,
      overlayBounds,
      snapshot,
      surfaceBounds,
    });
    if (!translated) return false;
    markCameraInteraction();
    graph.cameraPosition(
      translated.position,
      translated.target,
      reducedMotion ? 0 : duration,
    );
    return true;
  };
  const cameraState = () => {
    const camera = graph.cameraPosition();
    const liveCamera = graph.camera?.();
    const target = graph.controls?.()?.target || { x: 0, y: 0, z: 0 };
    const position = { x: camera.x || 0, y: camera.y || 0, z: camera.z || 0 };
    const lookAt = { x: target.x || 0, y: target.y || 0, z: target.z || 0 };
    const offset = {
      x: position.x - lookAt.x,
      y: position.y - lookAt.y,
      z: position.z - lookAt.z,
    };
    const distance = Math.hypot(offset.x, offset.y, offset.z) || 1;
    const zoom = semanticZoom(semanticReferenceDistance || distance, distance);
    return {
      mode: "3d",
      position,
      target: lookAt,
      yaw: Math.atan2(offset.x, offset.z) * 180 / Math.PI,
      pitch: Math.asin(Math.max(-1, Math.min(1, offset.y / distance))) * 180 / Math.PI,
      distance,
      aspect: Number(liveCamera?.aspect) || element.clientWidth / Math.max(1, element.clientHeight),
      fov: Number(liveCamera?.fov) || 60,
      semanticZoom: zoom,
      detailLevel: semanticDetail,
    };
  };
  const refreshSemanticDetail = (camera = cameraState()) => {
    const next = detailLevelForCamera({
      nodeCount: visibleNodeCount(),
      referenceDistance: semanticReferenceDistance || camera.distance,
      cameraDistance: camera.distance,
    });
    const changed = next !== semanticDetail;
    semanticDetail = next;
    if (changed) {
      visibleLabelIds = labelIds(nodes, activeScene, semanticDetail);
      graph.linkOpacity(sceneLinkOpacity());
      refreshVisuals();
    }
    callbacks.onDetailChange?.({
      level: semanticDetail,
      zoom: camera.semanticZoom,
      cameraDistance: camera.distance,
      referenceDistance: semanticReferenceDistance || camera.distance,
    });
    return changed;
  };
  const transitionCamera = (position, target, duration = 180) => {
    const values = [position.x, position.y, position.z, target.x, target.y, target.z];
    if (!values.every(Number.isFinite)) return false;
    markCameraInteraction();
    graph.cameraPosition(position, target, reducedMotion ? 0 : duration);
    frameTimer = window.setTimeout(reportCamera, reducedMotion ? 0 : duration + 24);
    return true;
  };
  const zoomBy = (factor, duration = 180) => {
    if (!Number.isFinite(factor) || factor <= 0) return false;
    const snapshot = cameraState();
    const nextDistance = Math.max(24, Math.min(10000, snapshot.distance / factor));
    const scale = nextDistance / snapshot.distance;
    return transitionCamera({
      x: snapshot.target.x + (snapshot.position.x - snapshot.target.x) * scale,
      y: snapshot.target.y + (snapshot.position.y - snapshot.target.y) * scale,
      z: snapshot.target.z + (snapshot.position.z - snapshot.target.z) * scale,
    }, snapshot.target, duration);
  };
  const panByScreen = (dx, dy, duration = 160) => {
    if (![dx, dy].every(Number.isFinite)) return false;
    const snapshot = cameraState();
    const camera = graph.camera?.();
    if (!camera?.matrixWorld?.elements) return false;
    camera.updateMatrixWorld?.();
    const matrix = camera.matrixWorld.elements;
    const worldPerPixel = (
      2 * snapshot.distance * Math.tan(((camera.fov || 60) * Math.PI) / 360)
    ) / Math.max(1, element.clientHeight);
    const shift = {
      x: (matrix[0] * dx - matrix[4] * dy) * worldPerPixel,
      y: (matrix[1] * dx - matrix[5] * dy) * worldPerPixel,
      z: (matrix[2] * dx - matrix[6] * dy) * worldPerPixel,
    };
    return transitionCamera({
      x: snapshot.position.x + shift.x,
      y: snapshot.position.y + shift.y,
      z: snapshot.position.z + shift.z,
    }, {
      x: snapshot.target.x + shift.x,
      y: snapshot.target.y + shift.y,
      z: snapshot.target.z + shift.z,
    }, duration);
  };
  const orbitBy = (yawDegrees, duration = 180) => {
    if (!Number.isFinite(yawDegrees)) return false;
    const snapshot = cameraState();
    const radians = yawDegrees * Math.PI / 180;
    const cosine = Math.cos(radians);
    const sine = Math.sin(radians);
    const offsetX = snapshot.position.x - snapshot.target.x;
    const offsetZ = snapshot.position.z - snapshot.target.z;
    return transitionCamera({
      x: snapshot.target.x + offsetX * cosine + offsetZ * sine,
      y: snapshot.position.y,
      z: snapshot.target.z - offsetX * sine + offsetZ * cosine,
    }, snapshot.target, duration);
  };
  const overviewState = () => {
    const primarySelectedNodeId = selectedNodeIds.values().next().value || "";
    return {
      camera: cameraState(),
      nodes: nodes.map((node) => ({
        id: node.id,
        label: node.label || node.id,
        x: node.x || 0,
        y: node.y || 0,
        z: node.z || 0,
        hidden: Boolean(node.hidden),
        primary: node.id === primarySelectedNodeId,
        selected: selectedNodeIds.has(node.id),
      })),
    };
  };
  const directionalNode = (originId, direction) => directionalNodeId(
    nodes.map((node) => ({
      id: node.id,
      hidden: Boolean(node.hidden),
      ...graph.graph2ScreenCoords(node.x || 0, node.y || 0, node.z || 0),
    })),
    originId,
    direction,
    { width: element.clientWidth, height: element.clientHeight },
  );
  const focusPoint = (point, duration = 420) => {
    if (![point?.x, point?.y, point?.z].every(Number.isFinite)) return false;
    const snapshot = cameraState();
    const offset = {
      x: snapshot.position.x - snapshot.target.x,
      y: snapshot.position.y - snapshot.target.y,
      z: snapshot.position.z - snapshot.target.z,
    };
    graph.cameraPosition(snapshot.position, snapshot.target, 0);
    return transitionCamera(
      { x: point.x + offset.x, y: point.y + offset.y, z: point.z + offset.z },
      point,
      duration,
    );
  };
  const restoreCamera = (snapshot, duration = 360) => {
    const position = snapshot?.position;
    const target = snapshot?.target;
    if (!position || !target) return false;
    const values = [position.x, position.y, position.z, target.x, target.y, target.z];
    if (!values.every(Number.isFinite)) return false;
    return transitionCamera(position, target, duration);
  };
  const reportCamera = () => {
    window.cancelAnimationFrame(cameraFrame);
    cameraFrame = window.requestAnimationFrame(() => {
      cameraFrame = 0;
      const camera = cameraState();
      refreshSemanticDetail(camera);
      callbacks.onCameraChange?.({ ...camera, detailLevel: semanticDetail });
      callbacks.onOverview?.(overviewState());
      scheduleLabelLayout();
    });
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
    .linkOpacity(sceneLinkOpacity())
    .linkVisibility((link) => !activeScene.links.find((item) => item.id === link.id)?.hidden)
    .linkWidth(linkWidth)
    .linkCurvature("curvature")
    .linkCurveRotation("curveRotation")
    .warmupTicks(reducedMotion ? 0 : 72)
    .cooldownTicks(reducedMotion ? 0 : 120)
    .d3AlphaDecay(0.035)
    .d3VelocityDecay(0.36)
    .onNodeClick((node, event) => callbacks.onSelect?.(node, event))
    .onNodeHover((node) => {
      hoveredNodeId = node?.id || "";
      refreshInteractionContext();
      refreshVisuals();
      placeHoveredLabel();
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
    .onNodeDragEnd((node) => {
      callbacks.onPin?.(node);
      reportCamera();
    })
    .onBackgroundClick((event) => {
      if (!event.target.closest?.(".gf-webgl-label")) callbacks.onBackground?.();
    })
    .onEngineStop(() => {
      reportCamera();
      if (!initialFit || cameraPreserved) return;
      initialFit = false;
      frameGraph(0);
    });

  const frameGraph = (duration = 0, { preserve = false, resetReference = false } = {}) => {
    const establishReference = resetReference || !semanticReferenceDistance || !preserve;
    const generation = cameraInteractionGeneration;
    cameraPreserved = preserve;
    window.clearTimeout(frameTimer);
    graph.zoomToFit(duration, 18);
    frameTimer = window.setTimeout(() => {
      if (generation !== cameraInteractionGeneration) return;
      const camera = graph.cameraPosition();
      const target = graph.controls?.()?.target || { x: 0, y: 0, z: 0 };
      const scale = activeScene.sceneLevel === "precision" ? 0.78 : activeScene.sceneLevel === "local" ? 0.72 : 0.66;
      const position = {
        x: target.x + (camera.x - target.x) * scale,
        y: target.y + (camera.y - target.y) * scale,
        z: target.z + (camera.z - target.z) * scale,
      };
      if (establishReference) {
        semanticReferenceDistance = Math.hypot(
          position.x - target.x,
          position.y - target.y,
          position.z - target.z,
        );
      }
      graph.cameraPosition(
        position,
        target,
        reducedMotion || duration === 0 ? 0 : 180,
      );
      reportCamera();
    }, reducedMotion ? 0 : duration + 20);
  };

  graph.d3Force("charge")?.strength(-210);
  graph.d3Force("link")?.distance(112).strength(0.2);
  graph.d3Force("cluster", clusterForce(nodes, centers));
  graph.nodeThreeObject(nodeObject);
  graph.nodeThreeObjectExtend(true);
  const controls = graph.controls?.();
  if (controls) {
    controls.rotateSpeed = 0.72;
    controls.zoomSpeed = 0.9;
    controls.panSpeed = 0.72;
  }
  controls?.addEventListener?.("start", markCameraInteraction);
  controls?.addEventListener?.("change", reportCamera);
  reportCamera();

  const resize = () => {
    graph.width(Math.max(320, element.clientWidth));
    graph.height(Math.max(420, element.clientHeight));
  };
  const observer = new ResizeObserver(resize);
  observer.observe(element);
  element.addEventListener("pointerdown", pointerDown);
  element.addEventListener("pointermove", pointerMove);
  element.addEventListener("pointerup", pointerUp);
  element.addEventListener("pointercancel", pointerCancel);
  element.addEventListener("dblclick", doubleClick);
  resize();
  frameGraph();
  const layoutJob = startLayoutJob(nodes, centers, (positions) => {
    const byId = new Map(positions.map((position) => [position.id, position]));
    for (const node of nodes) Object.assign(node, byId.get(node.id) || {});
    reportCamera();
    if (!reducedMotion) graph.d3ReheatSimulation();
    if (!cameraPreserved) frameGraph(0);
  });

  return {
    fit: () => {
      markCameraInteraction();
      frameGraph(360, { preserve: true, resetReference: true });
    },
    focusNodes,
    focusNeighborhood,
    ensureNodeVisible,
    cameraState,
    overviewState,
    directionalNode,
    focusPoint,
    restoreCamera,
    zoomBy,
    panByScreen,
    orbitBy,
    previewNode(nodeId) {
      previewedNodeId = nodes.some((node) => node.id === nodeId && !node.hidden) ? nodeId : "";
      refreshInteractionContext();
      refreshVisuals();
      placeHoveredLabel();
      return previewedNodeId;
    },
    reset: () => {
      markCameraInteraction();
      graph.cameraPosition({ x: 0, y: 0, z: 720 }, { x: 0, y: 0, z: 0 }, 500);
      graph.d3ReheatSimulation();
    },
    resetOrientation: () => {
      markCameraInteraction();
      graph.cameraPosition({ x: 0, y: 0, z: 720 }, { x: 0, y: 0, z: 0 }, reducedMotion ? 0 : 420);
    },
    resetLayout: () => {
      markCameraInteraction();
      for (const node of nodes) {
        const position = seededPosition(node.id, node.clusterId || node.kind, centers);
        Object.assign(node, position, { fx: undefined, fy: undefined, fz: undefined });
      }
      graph.d3ReheatSimulation();
      frameGraph(420, { preserve: true, resetReference: true });
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
        const activeNodeIds = new Set(nodes.map((node) => node.id));
        for (const nodeId of nodeObjects.keys()) {
          if (!activeNodeIds.has(nodeId)) nodeObjects.delete(nodeId);
        }
        links = shapeLinks(nodes, nextScene.links);
        if (!nodes.some((node) => node.id === previewedNodeId && !node.hidden)) previewedNodeId = "";
        graph.graphData({ nodes, links });
        graph.d3Force("cluster", clusterForce(nodes, centers));
        if (!reducedMotion) graph.d3ReheatSimulation();
      }
      refreshInteractionContext();
      visibleLabelIds = labelIds(nodes, activeScene, semanticDetail);
      graph.backgroundColor(activeScene.theme === "space" ? "#070d24" : "#eef4f2");
      graph.nodeVal(nodeSize);
      graph.linkOpacity(sceneLinkOpacity());
      graph.nodeVisibility(graph.nodeVisibility());
      graph.linkVisibility(graph.linkVisibility());
      refreshVisuals();
      reportCamera();
    },
    destroy() {
      observer.disconnect();
      layoutJob?.cancel();
      window.clearTimeout(frameTimer);
      window.cancelAnimationFrame(cameraFrame);
      window.cancelAnimationFrame(labelFrame);
      window.cancelAnimationFrame(labelLayoutFrame);
      controls?.removeEventListener?.("start", markCameraInteraction);
      controls?.removeEventListener?.("change", reportCamera);
      element.removeEventListener("pointerdown", pointerDown);
      element.removeEventListener("pointermove", pointerMove);
      element.removeEventListener("pointerup", pointerUp);
      element.removeEventListener("pointercancel", pointerCancel);
      element.removeEventListener("dblclick", doubleClick);
      nodeObjects.clear();
      window.removeEventListener("keydown", setClusterDrag);
      window.removeEventListener("keyup", clearClusterDrag);
      window.removeEventListener("pointerdown", markTouchPointer, true);
      window.removeEventListener("touchstart", markTouchEngaged, true);
      graph._destructor?.();
      element.replaceChildren();
    },
    graph,
  };
}

globalThis.GraphFakos3D = { hasWebGL, mount, version: "1" };

export { hasWebGL, mount };
