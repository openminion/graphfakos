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

const localCurve = 0.24;
const bridgeCurve = 0.18;
const parallelSpacing = 0.12;

function curveProfile(source, target, sameCluster, key, index, lane) {
  if (source === target) {
    return {
      curvature: curveSign(`${key}:loop`) * (0.58 + index * 0.08),
      curveRotation: (stableHash(`${key}:rotation`) % 6283) / 1000,
    };
  }

  const base = (sameCluster ? localCurve : bridgeCurve) + (stableHash(key) % 7) * 0.014;
  const sign = lane === 0 ? curveSign(key) : Math.sign(lane);
  return {
    curvature: rounded(sign * Math.min(0.48, base + Math.abs(lane) * parallelSpacing)),
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
      const lane = index - (ordered.length - 1) / 2;
      profileById.set(link.id, curveProfile(source, target, sameCluster, key, index, lane));
    });
  }

  return links.map((link) => ({
    ...link,
    source: endpointId(link.source ?? link.sourceId),
    target: endpointId(link.target ?? link.targetId),
    ...profileById.get(link.id),
  }));
}
