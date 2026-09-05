import { stableHash } from "./link-shape.js";

const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(maximum, value));

function clusterWeight(node) {
  const payload = node.provider_payload || node.providerPayload || {};
  return Math.max(
    1,
    Number(payload.node_count || payload.raw_node_count || node.rawNodeCount || 1) || 1,
  );
}

function visibleNodes(nodes) {
  const visible = nodes.filter((node) => !node.hidden);
  return visible.length ? visible : nodes;
}

function nodeRegion(node) {
  const payload = node.provider_payload || node.providerPayload || {};
  return node.regionId || payload.region_id || "";
}

export function clusterCenters(nodes) {
  const clusterIds = [...new Set(nodes.map((node) => node.clusterId || node.kind || "unclustered"))].sort();
  if (clusterIds.length === 1) return new Map([[clusterIds[0], { x: 0, y: 0, z: 0 }]]);

  const shownNodes = visibleNodes(nodes);
  const regionIds = [...new Set(shownNodes.map(nodeRegion).filter(Boolean))].sort();
  const visibleCount = shownNodes.length;
  const totalWeight = shownNodes.reduce((total, node) => total + clusterWeight(node), 0);
  const spread = visibleCount > 160
    ? Math.min(7200, 1900 + Math.sqrt(clusterIds.length) * 340)
    : visibleCount > 80
      ? Math.min(5000, 1400 + Math.sqrt(clusterIds.length) * 280)
      : Math.min(2800, 760 + Math.sqrt(clusterIds.length) * 180);
  const goldenAngle = Math.PI * (3 - Math.sqrt(5));

  if (regionIds.length > 1) {
    const regionSpread = visibleCount > 160 ? 3800 : visibleCount > 80 ? 2900 : 1800;
    const regionCenters = new Map(regionIds.map((regionId, index) => {
      const ring = 0.66 + (index % 3) * 0.13;
      const angle = index * goldenAngle;
      return [regionId, {
        x: Math.cos(angle) * regionSpread * ring,
        y: Math.sin(angle) * regionSpread * ring,
        z: ((index % 5) - 2) * regionSpread * 0.16,
      }];
    }));
    const regionClusters = new Map(regionIds.map((regionId) => [
      regionId,
      clusterIds.filter((clusterId) => shownNodes.some((node) => (
        (node.clusterId || node.kind || "unclustered") === clusterId
        && nodeRegion(node) === regionId
      ))),
    ]));
    return new Map(clusterIds.map((clusterId) => {
      const member = shownNodes.find((node) => (
        node.clusterId || node.kind || "unclustered"
      ) === clusterId);
      const regionId = nodeRegion(member || {});
      const peers = regionClusters.get(regionId) || [clusterId];
      const index = Math.max(0, peers.indexOf(clusterId));
      const center = regionCenters.get(regionId) || { x: 0, y: 0, z: 0 };
      const ring = Math.sqrt((index + 1) / peers.length);
      const angle = index * goldenAngle + (stableHash(regionId) % 100) / 100;
      const localSpread = visibleCount > 160 ? 430 : visibleCount > 80 ? 360 : 280;
      return [clusterId, {
        x: center.x + Math.cos(angle) * localSpread * ring,
        y: center.y + Math.sin(angle) * localSpread * ring,
        z: center.z + ((index % 7) - 3) * localSpread * 0.12,
      }];
    }));
  }

  return new Map(clusterIds.map((clusterId, index) => {
    const members = shownNodes.filter((node) => (node.clusterId || node.kind || "unclustered") === clusterId);
    const weight = members.reduce((total, node) => total + clusterWeight(node), 0);
    const mass = Math.sqrt(weight / Math.max(1, totalWeight));
    const ring = Math.sqrt((index + 1.2) / clusterIds.length);
    const wobble = ((stableHash(`${clusterId}:wobble`) % 100) - 50) / 100;
    const radius = spread * ring * (0.92 + mass * 1.35 + Math.abs(wobble) * 0.28);
    const angle = index * goldenAngle + wobble * 0.72;
    return [clusterId, {
      x: Math.cos(angle) * radius,
      y: Math.sin(angle) * radius,
      z: ((index % 17) - 8) * Math.max(54, spread * 0.014) + wobble * 90,
    }];
  }));
}

export function seededPosition(id, clusterId, centers, nodeCount = 0) {
  const nodeHash = stableHash(id);
  const center = centers.get(clusterId || "unclustered") || { x: 0, y: 0, z: 0 };
  const localAngle = (nodeHash % 360) * (Math.PI / 180);
  const count = Math.max(0, Number(nodeCount) || 0);
  const localSpread = count > 160 ? 112 : count > 80 ? 88 : 64;
  const localRadius = 9 + (nodeHash % localSpread);
  return {
    x: center.x + Math.cos(localAngle) * localRadius,
    y: center.y + Math.sin(localAngle) * localRadius,
    z: center.z + ((nodeHash % 61) - 30) * (count > 160 ? 2.5 : 1.8),
  };
}

export function clusterForce(nodes, centers) {
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

export function forceProfile(visibleCount) {
  if (visibleCount > 160) {
    return { charge: -900, linkDistance: 380, linkStrength: 0.008, clusterStrength: 0.075 };
  }
  if (visibleCount > 80) {
    return { charge: -650, linkDistance: 280, linkStrength: 0.025, clusterStrength: 0.055 };
  }
  return { charge: -300, linkDistance: 160, linkStrength: 0.1, clusterStrength: 0.085 };
}

export function applyForces(graph, nodes, centers, visibleCount) {
  const profile = forceProfile(visibleCount);
  graph.d3Force("charge")?.strength(profile.charge);
  graph.d3Force("link")?.distance(profile.linkDistance).strength(profile.linkStrength);
  graph.d3Force("cluster", clusterForce(nodes, centers).strength(profile.clusterStrength));
}

export function sceneExtent(nodes) {
  const shownNodes = visibleNodes(nodes);
  const values = shownNodes.reduce((extent, node) => ({
    minX: Math.min(extent.minX, node.x || 0),
    maxX: Math.max(extent.maxX, node.x || 0),
    minY: Math.min(extent.minY, node.y || 0),
    maxY: Math.max(extent.maxY, node.y || 0),
    minZ: Math.min(extent.minZ, node.z || 0),
    maxZ: Math.max(extent.maxZ, node.z || 0),
  }), {
    minX: Infinity,
    maxX: -Infinity,
    minY: Infinity,
    maxY: -Infinity,
    minZ: Infinity,
    maxZ: -Infinity,
  });
  if (!Number.isFinite(values.minX)) return { radius: 1 };
  return {
    ...values,
    radius: clamp(
      Math.hypot(values.maxX - values.minX, values.maxY - values.minY, values.maxZ - values.minZ) / 2,
      1,
      80_000,
    ),
  };
}

export function projectedSceneMetrics(points, viewport) {
  const width = Math.max(1, Number(viewport?.width) || 1);
  const height = Math.max(1, Number(viewport?.height) || 1);
  const visible = points.filter((point) => (
    Number.isFinite(point?.x)
    && Number.isFinite(point?.y)
    && point.x >= 0
    && point.x <= width
    && point.y >= 0
    && point.y <= height
  ));
  if (!visible.length) return { coverage: 0, occupancy: 0, visibleCount: 0 };
  const bounds = visible.reduce((result, point) => ({
    minX: Math.min(result.minX, point.x),
    maxX: Math.max(result.maxX, point.x),
    minY: Math.min(result.minY, point.y),
    maxY: Math.max(result.maxY, point.y),
  }), {
    minX: width,
    maxX: 0,
    minY: height,
    maxY: 0,
  });
  const horizontal = clamp((bounds.maxX - bounds.minX) / width, 0, 1);
  const vertical = clamp((bounds.maxY - bounds.minY) / height, 0, 1);
  return {
    coverage: Math.max(horizontal, vertical),
    occupancy: horizontal * vertical,
    visibleCount: visible.length,
  };
}
