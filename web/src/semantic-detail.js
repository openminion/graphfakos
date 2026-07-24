const detailBudgets = {
  overview: 1,
  balanced: 4,
  detail: 9,
  precision: 16,
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

export function labelBudgetForDetail(level, density = 1, nodeCount = Infinity) {
  const base = detailBudgets[level] || detailBudgets.overview;
  const scale = 0.35 + clamp(Number(density) || 0, 0, 1) * 0.65;
  return Math.min(Math.max(0, Number(nodeCount) || 0), Math.max(1, Math.round(base * scale)));
}

export function nodeScaleForCount(nodeCount) {
  const count = Math.max(0, Number(nodeCount) || 0);
  if (count <= 16) return 18;
  if (count <= 48) return 6;
  if (count <= 110) return 1.8;
  if (count <= 260) return 0.48;
  return 0.34;
}

export function zoomStableNodeScale(zoom) {
  const value = Number(zoom);
  if (!Number.isFinite(value) || value <= 0) return 1;
  return clamp(1 / Math.sqrt(value), 0.4, 1.65);
}
