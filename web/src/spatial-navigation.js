const directionVectors = {
  down: { x: 0, y: 1 },
  left: { x: -1, y: 0 },
  right: { x: 1, y: 0 },
  up: { x: 0, y: -1 },
};

function directionalNodeId(points, originId, direction, viewport = {}) {
  const vector = directionVectors[direction];
  const projected = points.filter((point) => (
    point?.id && !point.hidden && Number.isFinite(point.x) && Number.isFinite(point.y)
  ));
  if (!vector || !projected.length) return "";

  const origin = projected.find((point) => point.id === originId) || {
    id: "",
    x: Number(viewport.width) / 2 || 0,
    y: Number(viewport.height) / 2 || 0,
  };
  const width = Number(viewport.width);
  const height = Number(viewport.height);
  const hasViewport = width > 0 && height > 0;
  const candidates = projected.filter((point) => (
    !hasViewport || (point.x >= 0 && point.x <= width && point.y >= 0 && point.y <= height)
  )).map((point) => {
    const dx = point.x - origin.x;
    const dy = point.y - origin.y;
    const forward = dx * vector.x + dy * vector.y;
    const lateral = Math.abs(dx * vector.y - dy * vector.x);
    const distance = Math.hypot(dx, dy);
    return {
      id: point.id,
      forward,
      score: distance * (1 + (lateral / Math.max(1, forward)) * 2.4) + lateral * 0.35,
    };
  }).filter((candidate) => candidate.id !== origin.id && candidate.forward > 3);

  candidates.sort((left, right) => left.score - right.score || left.id.localeCompare(right.id));
  return candidates[0]?.id || "";
}

export { directionalNodeId };
