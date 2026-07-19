(() => {
  const finite = (value, fallback = 0) => Number.isFinite(Number(value)) ? Number(value) : fallback;
  const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(maximum, value));

  const overviewProjection = (nodes = [], size = {}, padding = 6) => {
    const width = Math.max(1, finite(size.width, 180));
    const height = Math.max(1, finite(size.height, 90));
    const points = nodes.filter((node) => !node.hidden).map((node) => ({
      id: String(node.id || ""),
      label: String(node.label || node.id || ""),
      primary: Boolean(node.primary),
      selected: Boolean(node.selected),
      x: finite(node.x),
      y: finite(node.y),
      z: finite(node.z),
    })).filter((node) => node.id);
    if (!points.length) return { bounds: null, positions: [] };
    const bounds = points.reduce((result, point) => ({
      minX: Math.min(result.minX, point.x),
      maxX: Math.max(result.maxX, point.x),
      minY: Math.min(result.minY, point.y),
      maxY: Math.max(result.maxY, point.y),
      minZ: Math.min(result.minZ, point.z),
      maxZ: Math.max(result.maxZ, point.z),
    }), { minX: points[0].x, maxX: points[0].x, minY: points[0].y, maxY: points[0].y, minZ: points[0].z, maxZ: points[0].z });
    const spanX = Math.max(1, bounds.maxX - bounds.minX);
    const spanY = Math.max(1, bounds.maxY - bounds.minY);
    const spanZ = Math.max(1, bounds.maxZ - bounds.minZ);
    const usableWidth = Math.max(1, width - padding * 2);
    const usableHeight = Math.max(1, height - padding * 2);
    return {
      bounds,
      positions: points.map((point) => {
        const depth = (point.z - bounds.minZ) / spanZ;
        return {
          id: point.id,
          label: point.label,
          primary: point.primary,
          selected: point.selected,
          x: padding + ((point.x - bounds.minX) / spanX) * usableWidth,
          y: padding + ((point.y - bounds.minY) / spanY) * usableHeight,
          depth,
          layer: depth > 0.66 ? "near" : depth < 0.33 ? "far" : "middle",
        };
      }),
    };
  };

  const worldPointFromMap = (point = {}, bounds = null, size = {}, padding = 6) => {
    if (!bounds) return null;
    const width = Math.max(1, finite(size.width, 180));
    const height = Math.max(1, finite(size.height, 90));
    const xRatio = clamp((finite(point.x) - padding) / Math.max(1, width - padding * 2), 0, 1);
    const yRatio = clamp((finite(point.y) - padding) / Math.max(1, height - padding * 2), 0, 1);
    return {
      x: bounds.minX + (bounds.maxX - bounds.minX) * xRatio,
      y: bounds.minY + (bounds.maxY - bounds.minY) * yRatio,
      z: (bounds.minZ + bounds.maxZ) / 2,
    };
  };

  const mapPointFromWorld = (point = {}, bounds = null, size = {}, padding = 6) => {
    if (!bounds) return null;
    const width = Math.max(1, finite(size.width, 180));
    const height = Math.max(1, finite(size.height, 90));
    const xRatio = (finite(point.x) - bounds.minX) / Math.max(1, bounds.maxX - bounds.minX);
    const yRatio = (finite(point.y) - bounds.minY) / Math.max(1, bounds.maxY - bounds.minY);
    return {
      x: padding + clamp(xRatio, 0, 1) * Math.max(1, width - padding * 2),
      y: padding + clamp(yRatio, 0, 1) * Math.max(1, height - padding * 2),
    };
  };

  const cameraFootprint = (camera = {}, bounds = null, size = {}, padding = 6) => {
    if (!bounds || !camera?.target) return null;
    const width = Math.max(1, finite(size.width, 180));
    const height = Math.max(1, finite(size.height, 90));
    const usableWidth = Math.max(1, width - padding * 2);
    const usableHeight = Math.max(1, height - padding * 2);
    const center = mapPointFromWorld(camera.target, bounds, size, padding);
    const distance = Math.max(1, finite(camera.distance, 1));
    const fov = clamp(finite(camera.fov, 60), 20, 120) * Math.PI / 180;
    const aspect = clamp(finite(camera.aspect, width / height), 0.4, 3);
    const semanticZoom = clamp(finite(camera.semanticZoom, 1), 0.2, 8);
    const fovScale = Math.tan(fov / 2) / Math.tan(Math.PI / 6);
    const coverage = clamp(0.72 * fovScale / semanticZoom, 0.1, 0.9);
    const footprintWidth = usableWidth * coverage;
    const footprintHeight = Math.min(usableHeight * coverage, footprintWidth / aspect);
    const x = center.x - footprintWidth / 2;
    const y = center.y - footprintHeight / 2;
    const yaw = finite(camera.yaw);
    const headingLength = Math.max(6, Math.min(16, Math.min(footprintWidth, footprintHeight) * 0.42));
    const radians = yaw * Math.PI / 180;
    return {
      center,
      distance,
      height: footprintHeight,
      heading: {
        x1: center.x,
        y1: center.y,
        x2: center.x + Math.sin(radians) * headingLength,
        y2: center.y - Math.cos(radians) * headingLength,
      },
      rotation: -yaw,
      width: footprintWidth,
      x,
      y,
    };
  };

  globalThis.GraphFakosSpatialMap = Object.freeze({
    cameraFootprint,
    mapPointFromWorld,
    overviewProjection,
    worldPointFromMap,
  });
})();
