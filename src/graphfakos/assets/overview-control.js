(() => {
  const bind = (map, options = {}) => {
    if (!map || map.dataset.gfOverviewBound === "true") return false;
    map.dataset.gfOverviewBound = "true";
    let drag = null;

    map.addEventListener("pointerdown", (event) => {
      if (event.button !== 0 || event.target?.closest?.("[data-gf-minimap-node]")) return;
      drag = { id: event.pointerId, origin: options.eventPoint(event), moved: false };
      map.setPointerCapture?.(event.pointerId);
      map.dataset.dragging = "true";
      event.preventDefault();
    });
    map.addEventListener("pointermove", (event) => {
      if (!drag || drag.id !== event.pointerId) return;
      const point = options.eventPoint(event);
      drag.moved ||= Math.hypot(point.x - drag.origin.x, point.y - drag.origin.y) > 2;
      if (drag.moved) options.move(point, 0);
    });
    const finishDrag = (event) => {
      if (!drag || drag.id !== event.pointerId) return;
      map.releasePointerCapture?.(event.pointerId);
      map.dataset.dragging = "false";
      map.dataset.dragged = String(drag.moved);
      drag = null;
    };
    map.addEventListener("pointerup", finishDrag);
    map.addEventListener("pointercancel", finishDrag);
    map.addEventListener("click", (event) => {
      if (event.target?.closest?.("[data-gf-minimap-node]")) return;
      event.preventDefault();
      event.stopPropagation();
      if (map.dataset.dragged === "true") {
        map.dataset.dragged = "false";
        return;
      }
      options.move(options.eventPoint(event), 420);
    });
    map.addEventListener("keydown", (event) => {
      const directions = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
      if (!(event.key in directions) && event.key !== "Home") return;
      const overview = options.current();
      const size = overview?.size || { width: 180, height: 90 };
      const [dx, dy] = directions[event.key] || [0, 0];
      const current = globalThis.GraphFakosSpatialMap?.mapPointFromWorld?.(
        overview?.camera?.target,
        overview?.model?.bounds,
        size,
      ) || { x: size.width / 2, y: size.height / 2 };
      const point = event.key === "Home"
        ? { x: size.width / 2, y: size.height / 2 }
        : { x: current.x + dx * size.width * 0.16, y: current.y + dy * size.height * 0.16 };
      event.preventDefault();
      event.stopPropagation();
      options.move(point, 180);
    });
    return true;
  };

  globalThis.GraphFakosOverviewControl = Object.freeze({ bind });
})();
