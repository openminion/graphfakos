const detailBudgets = {
  overview: 3,
  balanced: 7,
  detail: 14,
  precision: 24,
};

const sceneLevelDetails = {
  cluster: "balanced",
  local: "detail",
  precision: "precision",
};

const detailLevels = ["overview", "balanced", "detail", "precision"];
const detailEnterZoom = { balanced: 0.78, detail: 1.45, precision: 2.4 };
const detailLeaveZoom = { balanced: 0.64, detail: 1.22, precision: 2.05 };

const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(maximum, value));

export function semanticZoom(referenceDistance, cameraDistance) {
  const reference = Number(referenceDistance);
  const distance = Number(cameraDistance);
  if (!Number.isFinite(reference) || reference <= 0 || !Number.isFinite(distance) || distance <= 0) {
    return 1;
  }
  return clamp(reference / distance, 0.2, 8);
}

export function detailLevelForCamera({
  nodeCount,
  referenceDistance,
  cameraDistance,
  currentLevel = "",
}) {
  const count = Math.max(0, Number(nodeCount) || 0);
  const zoom = semanticZoom(referenceDistance, cameraDistance);
  let nextLevel = "overview";
  if (zoom >= 2.25) nextLevel = "precision";
  else if (zoom >= 1.35 || count <= 48) nextLevel = "detail";
  else if (zoom >= 0.72 || count <= 110) nextLevel = "balanced";
  if (!detailLevels.includes(currentLevel) || count <= 110 || currentLevel === nextLevel) {
    return nextLevel;
  }
  const currentIndex = detailLevels.indexOf(currentLevel);
  const nextIndex = detailLevels.indexOf(nextLevel);
  if (nextIndex > currentIndex) {
    return zoom >= detailEnterZoom[nextLevel] ? nextLevel : currentLevel;
  }
  return zoom < detailLeaveZoom[currentLevel] ? nextLevel : currentLevel;
}

export function detailLevelForSceneLevel(sceneLevel, autoLevel = "overview") {
  if (sceneLevel === "islands") return "overview";
  const requestedLevel = sceneLevelDetails[sceneLevel];
  if (!requestedLevel) return autoLevel;
  return detailLevels.indexOf(requestedLevel) > detailLevels.indexOf(autoLevel)
    ? requestedLevel
    : autoLevel;
}

export function detailLevelForPerformance(level, { fps, frameMs }) {
  const index = Math.max(0, detailLevels.indexOf(level));
  if (Number(frameMs) > 38 || Number(fps) < 26) {
    return detailLevels[Math.max(0, index - 1)];
  }
  return detailLevels[index];
}

export function limitDetailLevel(level, maximum) {
  const levelIndex = Math.max(0, detailLevels.indexOf(level));
  const maximumIndex = Math.max(0, detailLevels.indexOf(maximum));
  return detailLevels[Math.min(levelIndex, maximumIndex)];
}

export function labelBudgetForDetail(level, density = 1, nodeCount = Infinity) {
  const base = detailBudgets[level] || detailBudgets.overview;
  const count = Math.max(0, Number(nodeCount) || 0);
  const densityScale = 0.15 + clamp(Number(density) || 0, 0, 1) * 0.6;
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
  if (count <= 110) return 0.9;
  if (count <= 260) return 0.5;
  if (count <= 600) return 0.38;
  return 0.3;
}

export function zoomStableNodeScale(zoom) {
  const value = Number(zoom);
  if (!Number.isFinite(value) || value <= 0) return 1;
  return clamp(1 / Math.sqrt(value), 0.24, 1.18);
}

export function nodeRelSizeForCamera({ cameraDistance, viewportHeight, fov = 60, nodeCount }) {
  const distance = Math.max(1, Number(cameraDistance) || 1);
  const height = Math.max(1, Number(viewportHeight) || 1);
  const fieldOfView = clamp(Number(fov) || 60, 20, 120) * Math.PI / 180;
  const worldPerPixel = 2 * distance * Math.tan(fieldOfView / 2) / height;
  const targetPixels = Number(nodeCount) > 160 ? 2.2 : Number(nodeCount) > 80 ? 2.7 : 3.2;
  return clamp(worldPerPixel * targetPixels / Math.cbrt(0.018), 3, 180);
}
