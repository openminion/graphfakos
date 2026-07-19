import { Vector3 } from "three";

function rectanglesOverlap(left, right, padding = 6) {
  return !(
    left.right + padding <= right.left
    || right.right + padding <= left.left
    || left.bottom + padding <= right.top
    || right.bottom + padding <= left.top
  );
}

function collidingLabelIds(records, surfaceBounds, reservedBounds, viewportHeight) {
  const accepted = [];
  const blocked = new Set();
  for (const record of [...records].sort((left, right) => right.rank - left.rank)) {
    const outside = record.bounds.right < surfaceBounds.left + 4
      || record.bounds.left > surfaceBounds.right - 4
      || record.bounds.bottom < Math.max(0, surfaceBounds.top) + 4
      || record.bounds.top > Math.min(viewportHeight, surfaceBounds.bottom) - 4;
    const collides = !record.forced && (
      outside
      || (reservedBounds && rectanglesOverlap(record.bounds, reservedBounds, 8))
      || accepted.some((bounds) => rectanglesOverlap(record.bounds, bounds, 7))
    );
    if (collides) blocked.add(record.id);
    else accepted.push(record.bounds);
  }
  return blocked;
}

function translatedCameraForReservation({
  camera,
  labelWidth,
  node,
  overlayBounds,
  snapshot,
  surfaceBounds,
}) {
  if (!camera || !rectanglesOverlap(surfaceBounds, overlayBounds, 0)) return null;
  const projected = new Vector3(node.x || 0, node.y || 0, node.z || 0).project(camera);
  const screenX = surfaceBounds.left + ((projected.x + 1) / 2) * surfaceBounds.width;
  const safeRight = Math.min(
    surfaceBounds.right - 24,
    overlayBounds.left - Math.max(56, labelWidth / 2 + 20),
  );
  if (screenX <= safeRight) return null;
  const distance = Math.hypot(
    snapshot.position.x - snapshot.target.x,
    snapshot.position.y - snapshot.target.y,
    snapshot.position.z - snapshot.target.z,
  ) || 1;
  const horizontalHalfSpan = Math.tan((camera.fov || 60) * Math.PI / 360)
    * distance
    * (camera.aspect || surfaceBounds.width / Math.max(1, surfaceBounds.height));
  const shift = horizontalHalfSpan * ((screenX - safeRight) / Math.max(1, surfaceBounds.width / 2));
  const forward = new Vector3();
  camera.getWorldDirection(forward);
  const right = forward.cross(camera.up).normalize().multiplyScalar(shift);
  const translate = (point) => ({
    x: point.x + right.x,
    y: point.y + right.y,
    z: point.z + right.z,
  });
  return {
    position: translate(snapshot.position),
    target: translate(snapshot.target),
  };
}

export { collidingLabelIds, rectanglesOverlap, translatedCameraForReservation };
