/* Geometry and navigation are pure, DOM-independent and shared with tests. */
const SpatialCore = (() => {
  const CONFIG = Object.freeze({
    focusScale: 2.024,
    overviewScale: 1.54,
    minScale: 0.025,
    maxScale: 4,
    desktopBreakpoint: 850,
    focusLeft: 0.16,
    mobileLeft: 0.09,
    focusTop: 0.15,
    focusTopOffset: 0,
    rightMargin: 0.08,
    overviewPadding: 180,
    zoomStep: 1.35,
    resizeDelay: 120,
    dotMinimum: 0.08,
    dotExponent: 1.15,
    dragThreshold: 5,
  });
  const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
  function worldRect(rect, origin, scale) {
    return {
      x: (rect.left - origin.left) / scale,
      y: (rect.top - origin.top) / scale,
      w: rect.width / scale,
      h: rect.height / scale,
    };
  }
  function fitCamera(box, view, close = false) {
    if (close) {
      const left =
        view.w >= CONFIG.desktopBreakpoint
          ? CONFIG.focusLeft
          : CONFIG.mobileLeft;
      const s = Math.min(
        CONFIG.focusScale,
        (Math.max(1, view.w * (1 - left - CONFIG.rightMargin)) /
          Math.max(1, box.w)) *
          1.1,
      );
      return {
        s,
        x: view.w * left - box.x * s,
        y: view.h * CONFIG.focusTop - CONFIG.focusTopOffset - box.y * s,
      };
    }
    const s = Math.min(
      CONFIG.overviewScale,
      (Math.max(1, view.w - CONFIG.overviewPadding) / Math.max(1, box.w)) * 1.1,
      (Math.max(1, view.h - CONFIG.overviewPadding) / Math.max(1, box.h)) * 1.1,
    );
    return {
      s,
      x: (view.w - box.w * s) / 2 - box.x * s,
      y: (view.h - box.h * s) / 2 - box.y * s,
    };
  }
  function zoomCamera(camera, factor, x, y) {
    const s = clamp(camera.s * factor, CONFIG.minScale, CONFIG.maxScale);
    return {
      s,
      x: x - ((x - camera.x) * s) / camera.s,
      y: y - ((y - camera.y) * s) / camera.s,
    };
  }
  function pinchCamera(camera, start, current) {
    const result = zoomCamera(
      camera,
      current.distance / Math.max(1, start.distance),
      start.x,
      start.y,
    );
    return {
      ...result,
      x: result.x + current.x - start.x,
      y: result.y + current.y - start.y,
    };
  }
  class Navigation {
    constructor(route, ids) {
      this.ids = ids;
      this.route = [...new Set(route)];
      this.selectedId = this.route[0];
      this.mode = "overview";
    }
    get index() {
      return this.route.indexOf(this.selectedId);
    }
    focus(id) {
      if (!this.ids.includes(id)) throw Error("Unknown section: " + id);
      this.selectedId = id;
      this.mode = "focus";
    }
    overview() {
      this.mode = "overview";
    }
    explore() {
      this.mode = "free";
    }
    adjacent(delta) {
      if (this.mode === "overview") return this.route[0];
      if (this.index < 0) {
        const position = this.ids.indexOf(this.selectedId);
        const candidates = this.route.filter(id => delta > 0 ? this.ids.indexOf(id) > position : this.ids.indexOf(id) < position);
        return (delta > 0 ? candidates[0] : candidates[candidates.length - 1]) || null;
      }
      return this.route[this.index + delta] || null;
    }
  }
  return { CONFIG, Navigation, worldRect, fitCamera, zoomCamera, pinchCamera };
})();
if (typeof module !== "undefined") module.exports = SpatialCore;
