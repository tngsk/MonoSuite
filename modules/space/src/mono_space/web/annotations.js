/* Ephemeral spatial annotations: SVG-based drawing and arrows attached to canvas world coordinates. */
const SpatialAnnotations = (() => {
  function createSvgElement(tag, attrs = {}) {
    const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [key, val] of Object.entries(attrs)) {
      el.setAttribute(key, String(val));
    }
    return el;
  }

  function formatPath(points) {
    if (!points || points.length === 0) return "";
    if (points.length === 1) return `M ${points[0].x} ${points[0].y} L ${points[0].x + 0.1} ${points[0].y + 0.1}`;
    let d = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      const p = points[i];
      d += ` L ${p.x} ${p.y}`;
    }
    return d;
  }

  function formatArrow(start, end) {
    return `M ${start.x} ${start.y} L ${end.x} ${end.y}`;
  }

  function attach(viewport, world, getCamera) {
    let mode = "none"; // 'none' | 'draw' | 'arrow' | 'arrow-both'
    let activeStroke = null;
    let currentPath = null;
    let points = [];

    // Ensure SVG layer exists in #world
    let svg = world.querySelector("#annotations-layer");
    if (!svg) {
      svg = createSvgElement("svg", {
        id: "annotations-layer",
        "aria-hidden": "true",
      });

      const defs = createSvgElement("defs");

      // Single-direction arrow head
      const markerEnd = createSvgElement("marker", {
        id: "annotation-arrow-end",
        viewBox: "0 0 10 10",
        refX: "8",
        refY: "5",
        markerWidth: "6",
        markerHeight: "6",
        orient: "auto-start-reverse",
      });
      const headPath = createSvgElement("path", {
        d: "M 0 1.5 L 8 5 L 0 8.5 z",
        fill: "currentColor",
      });
      markerEnd.appendChild(headPath);

      // Bidirectional arrow start
      const markerStart = createSvgElement("marker", {
        id: "annotation-arrow-start",
        viewBox: "0 0 10 10",
        refX: "2",
        refY: "5",
        markerWidth: "6",
        markerHeight: "6",
        orient: "auto-start-reverse",
      });
      const tailPath = createSvgElement("path", {
        d: "M 8 1.5 L 0 5 L 8 8.5 z",
        fill: "currentColor",
      });
      markerStart.appendChild(tailPath);

      defs.appendChild(markerEnd);
      defs.appendChild(markerStart);
      svg.appendChild(defs);

      world.appendChild(svg);
    }

    function toWorld(clientX, clientY) {
      const rect = viewport.getBoundingClientRect();
      const camera = getCamera();
      return {
        x: (clientX - rect.left - camera.x) / camera.s,
        y: (clientY - rect.top - camera.y) / camera.s,
      };
    }

    function setMode(nextMode) {
      if (mode === nextMode) {
        mode = "none";
      } else {
        mode = nextMode;
      }
      viewport.dataset.annotationMode = mode;
      document.dispatchEvent(
        new CustomEvent("annotationmodechange", { detail: { mode } })
      );
    }

    function clearAll() {
      const paths = svg.querySelectorAll(".annotation-item");
      paths.forEach((p) => p.remove());
    }

    function onPointerDown(e) {
      if (mode === "none") return;
      if (e.button !== 0) return;
      if (e.target.closest("input,textarea,button,select,[contenteditable]")) return;

      e.preventDefault();
      e.stopPropagation();

      const startWorld = toWorld(e.clientX, e.clientY);
      const isArrow = mode === "arrow" || mode === "arrow-both";

      currentPath = createSvgElement("path", {
        class: isArrow ? "annotation-item annotation-arrow" : "annotation-item annotation-draw",
      });

      const camera = getCamera();
      const baseWidth = isArrow ? 3.5 : 6;
      const strokeWidth = baseWidth / Math.max(camera.s, 0.1);
      currentPath.style.strokeWidth = strokeWidth + "px";

      if (isArrow) {
        currentPath.setAttribute("marker-end", "url(#annotation-arrow-end)");
        if (mode === "arrow-both") {
          currentPath.setAttribute("marker-start", "url(#annotation-arrow-start)");
        }
      }

      svg.appendChild(currentPath);

      points = [startWorld];
      activeStroke = {
        pointerId: e.pointerId,
        start: startWorld,
        isArrow,
      };

      if (isArrow) {
        currentPath.setAttribute("d", formatArrow(startWorld, startWorld));
      } else {
        currentPath.setAttribute("d", formatPath(points));
      }

      viewport.setPointerCapture(e.pointerId);
    }

    function onPointerMove(e) {
      if (!activeStroke || activeStroke.pointerId !== e.pointerId) return;

      e.preventDefault();
      e.stopPropagation();

      const currentWorld = toWorld(e.clientX, e.clientY);

      if (activeStroke.isArrow) {
        currentPath.setAttribute("d", formatArrow(activeStroke.start, currentWorld));
      } else {
        points.push(currentWorld);
        currentPath.setAttribute("d", formatPath(points));
      }
    }

    function onPointerUp(e) {
      if (!activeStroke || activeStroke.pointerId !== e.pointerId) return;

      e.preventDefault();
      e.stopPropagation();

      activeStroke = null;
      currentPath = null;
      points = [];
    }

    // High priority pointer interception when in annotation mode
    viewport.addEventListener("pointerdown", onPointerDown, true);
    viewport.addEventListener("pointermove", onPointerMove, true);
    viewport.addEventListener("pointerup", onPointerUp, true);
    viewport.addEventListener("pointercancel", onPointerUp, true);

    window.addEventListener("keydown", (e) => {
      if (
        e.isComposing ||
        e.target.closest("input,textarea,select,[contenteditable],.live-sticky")
      ) {
        return;
      }

      if (e.key === "Escape") {
        if (mode !== "none") {
          e.preventDefault();
          setMode("none");
        }
        return;
      }

      if (e.ctrlKey || e.metaKey || e.altKey) return;

      const key = e.key.toLowerCase();
      if (key === "d") {
        e.preventDefault();
        setMode("draw");
      } else if (key === "a") {
        e.preventDefault();
        setMode(e.shiftKey ? "arrow-both" : "arrow");
      } else if (key === "c" && !e.repeat) {
        e.preventDefault();
        clearAll();
      }
    });

    return {
      getMode: () => mode,
      setMode,
      clearAll,
    };
  }

  return {
    attach,
    formatPath,
    formatArrow,
  };
})();

if (typeof module !== "undefined") {
  module.exports = SpatialAnnotations;
}
