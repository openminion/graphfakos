export function stableHash(value) {
  let result = 2166136261;
  for (const character of String(value)) {
    result ^= character.charCodeAt(0);
    result = Math.imul(result, 16777619);
  }
  return result >>> 0;
}

function endpointId(endpoint) {
  return typeof endpoint === "object" ? endpoint.id : endpoint;
}

function pairKey(link) {
  return [endpointId(link.source ?? link.sourceId), endpointId(link.target ?? link.targetId)]
    .sort()
    .join("\u0000");
}

function curveSign(value) {
  return stableHash(value) % 2 ? -1 : 1;
}

function rounded(value) {
  return Math.round(value * 10_000) / 10_000;
}

const localCurve = 0.22;
const bridgeCurve = 0.38;
const bundleCurve = 0.56;
const parallelSpacing = 0.16;

function curveProfile(source, target, sameCluster, key, index, lane, aggregate) {
  if (source === target) {
    return {
      curvature: curveSign(`${key}:loop`) * (0.58 + index * 0.08),
      curveRotation: (stableHash(`${key}:rotation`) % 6283) / 1000,
    };
  }

  const rawWeight = aggregate?.edgeCount || aggregate?.weight || aggregate?.edge_count || 1;
  const weight = Math.min(
    0.2,
    Math.log10(Math.max(1, Number(rawWeight))) * 0.04,
  );
  const base = (
    aggregate ? bundleCurve : sameCluster ? localCurve : bridgeCurve
  ) + weight + (stableHash(key) % 9) * 0.018;
  const sign = lane === 0 ? curveSign(key) : Math.sign(lane);
  return {
    curvature: rounded(sign * Math.min(0.82, base + Math.abs(lane) * parallelSpacing)),
    curveRotation: (stableHash(`${key}:${source}:${target}:rotation`) % 6283) / 1000,
  };
}

export function shapeLinks(nodes, links) {
  const clusterByNode = new Map(nodes.map((node) => [node.id, node.clusterId || node.kind || "unclustered"]));
  const linksByPair = new Map();
  for (const link of links) {
    const key = pairKey(link);
    if (!linksByPair.has(key)) linksByPair.set(key, []);
    linksByPair.get(key).push(link);
  }

  const profileById = new Map();
  for (const [key, pairedLinks] of linksByPair) {
    const ordered = [...pairedLinks].sort((left, right) => String(left.id).localeCompare(String(right.id)));
    ordered.forEach((link, index) => {
      const source = endpointId(link.source ?? link.sourceId);
      const target = endpointId(link.target ?? link.targetId);
      const sameCluster = clusterByNode.get(source) === clusterByNode.get(target);
      const aggregate = link.kind === "edge_bundle" || link.aggregate === true;
      const lane = index - (ordered.length - 1) / 2;
      profileById.set(
        link.id,
        curveProfile(source, target, sameCluster, key, index, lane, aggregate ? link : null),
      );
    });
  }

  return links.map((link) => ({
    ...link,
    source: endpointId(link.source ?? link.sourceId),
    target: endpointId(link.target ?? link.targetId),
    ...profileById.get(link.id),
  }));
}

export function linkVisibleForDetail(link, detailLevel, focusId = "") {
  if (link.hidden) return false;
  const source = endpointId(link.source ?? link.sourceId);
  const target = endpointId(link.target ?? link.targetId);
  if (link.selected || (focusId && (source === focusId || target === focusId))) return true;
  if (link.kind === "edge_bundle" || link.aggregate === true) return true;
  const threshold = {
    overview: 18,
    balanced: 46,
    detail: 78,
    precision: 100,
  }[detailLevel] || 18;
  return stableHash(link.id || `${source}:${target}`) % 100 < threshold;
}
