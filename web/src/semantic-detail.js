const detailBudgets = {
  overview: 1,
  balanced: 2,
  detail: 3,
  precision: 5,
};

const sceneLevelDetails = {
  cluster: "balanced",
  local: "detail",
  precision: "precision",
};

const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(maximum, value));

export function semanticZoom(referenceDistance, cameraDistance) {
  const reference = Number(referenceDistance);
  const distance = Number(cameraDistance);
  if (!Number.isFinite(reference) || reference <= 0 || !Number.isFinite(distance) || distance <= 0) {
    return 1;
  }
  return clamp(reference / distance, 0.2, 8);
}

export function detailLevelForCamera({ nodeCount, referenceDistance, cameraDistance }) {
  const count = Math.max(0, Number(nodeCount) || 0);
  const zoom = semanticZoom(referenceDistance, cameraDistance);
  if (zoom >= 2.25) return "precision";
  if (zoom >= 1.35 || count <= 48) return "detail";
  if (zoom >= 0.72 || count <= 110) return "balanced";
  return "overview";
}

export function detailLevelForSceneLevel(sceneLevel, autoLevel = "overview") {
  if (sceneLevel === "islands") return "overview";
  const requestedLevel = sceneLevelDetails[sceneLevel];
  if (!requestedLevel) return autoLevel;
  const levels = ["overview", "balanced", "detail", "precision"];
  return levels.indexOf(requestedLevel) > levels.indexOf(autoLevel)
    ? requestedLevel
    : autoLevel;
}

export function labelBudgetForDetail(level, density = 1, nodeCount = Infinity) {
  const base = detailBudgets[level] || detailBudgets.overview;
  const count = Math.max(0, Number(nodeCount) || 0);
  const densityScale = 0.08 + clamp(Number(density) || 0, 0, 1) * 0.42;
  const countScale = count > 600 ? 0.42 : count > 260 ? 0.58 : count > 110 ? 0.78 : 1;
  return Math.min(count, Math.max(1, Math.round(base * densityScale * countScale)));
}

export function modeSummaryForSceneLevel(sceneLevel) {
  return {
    overview: "tiny points, only the highest-signal labels",
    islands: "cluster islands first, sparse labels, large spatial gaps",
    cluster: "cluster and bridge labels with balanced link detail",
    local: "focused neighborhood labels and selected context",
    precision: "maximum local labels for close inspection",
  }[sceneLevel] || "automatic dense graph detail";
}

export function nodeScaleForCount(nodeCount) {
  const count = Math.max(0, Number(nodeCount) || 0);
  if (count <= 16) return 8;
  if (count <= 48) return 2.8;
  if (count <= 110) return 0.72;
  if (count <= 260) return 0.09;
  if (count <= 600) return 0.06;
  return 0.04;
}

export function zoomStableNodeScale(zoom) {
  const value = Number(zoom);
  if (!Number.isFinite(value) || value <= 0) return 1;
  return clamp(1 / Math.sqrt(value), 0.24, 1.18);
}
