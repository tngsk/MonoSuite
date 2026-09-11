/* Direct gestures only: no animation or application-generated inertia. */
const SpatialInput = {
  attach(viewport, getCamera, setCamera, zoomAt) {
    const { CONFIG, pinchCamera } = SpatialCore,
      pointers = new Map();
    const gesture = { moved: false };
    let start = null;
    const local = (e) => {
      const r = viewport.getBoundingClientRect();
      return { x: e.clientX - r.left, y: e.clientY - r.top };
    };
    const pair = () => {
      const [a, b] = [...pointers.values()];
      return {
        x: (a.x + b.x) / 2,
        y: (a.y + b.y) / 2,
        distance: Math.hypot(a.x - b.x, a.y - b.y),
      };
    };
    function rebase() {
      start =
        pointers.size >= 2
          ? { pair: pair(), camera: { ...getCamera() } }
          : pointers.size
            ? { point: [...pointers.values()][0], camera: { ...getCamera() } }
            : null;
    }
    viewport.addEventListener("pointerdown", (e) => {
      if (e.button !== 0 || e.target?.closest?.("code,.codeblock,.math-copy")) return;
      if (!pointers.size) gesture.moved = false;
      pointers.set(e.pointerId, local(e));
      rebase();
      if (pointers.size >= 2) {
        gesture.moved = true;
        for (const id of pointers.keys()) viewport.setPointerCapture(id);
      }
    });
    viewport.addEventListener("pointermove", (e) => {
      if (!pointers.has(e.pointerId)) return;
      pointers.set(e.pointerId, local(e));
      if (pointers.size >= 2) {
        gesture.moved = true;
        setCamera(pinchCamera(start.camera, start.pair, pair()));
        return;
      }
      const p = local(e),
        dx = p.x - start.point.x,
        dy = p.y - start.point.y;
      if (Math.hypot(dx, dy) > CONFIG.dragThreshold) {
        gesture.moved = true;
        viewport.setPointerCapture(e.pointerId);
      }
      if (gesture.moved) {
        viewport.classList.add("dragging");
        setCamera({
          ...start.camera,
          x: start.camera.x + dx,
          y: start.camera.y + dy,
        });
      }
    });
    function end(e) {
      if (!pointers.delete(e.pointerId)) return;
      viewport.classList.remove("dragging");
      rebase();
    }
    for (const type of ["pointerup", "pointercancel", "lostpointercapture"])
      viewport.addEventListener(type, end);
    viewport.addEventListener(
      "wheel",
      (e) => {
        e.preventDefault();
        const unit =
          e.deltaMode === 1
            ? 16
            : e.deltaMode === 2
              ? viewport.clientHeight
              : 1;
        const p = local(e);
        if (e.ctrlKey || e.metaKey)
          zoomAt(Math.exp(-e.deltaY * unit * 0.008), p.x, p.y);
        else {
          const c = getCamera();
          setCamera({
            ...c,
            x: c.x - e.deltaX * unit,
            y: c.y - e.deltaY * unit,
          });
        }
      },
      { passive: false },
    );
    return gesture;
  },
};
if (typeof module !== "undefined") module.exports = SpatialInput;
