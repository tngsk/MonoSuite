/* Ephemeral annotations: DOM only, independent of document layout and navigation. */
const SpatialStickies = {
  attach(viewport, world, getCamera) {
    let cursor = null;
    viewport.addEventListener("pointermove", (e) => {
      cursor = { x: e.clientX, y: e.clientY };
    });
    function create() {
      const rect = viewport.getBoundingClientRect(),
        camera = getCamera();
      const point =
        cursor &&
        cursor.x >= rect.left &&
        cursor.x <= rect.right &&
        cursor.y >= rect.top &&
        cursor.y <= rect.bottom
          ? cursor
          : { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
      const note = document.createElement("aside");
      note.className = "live-sticky";
      note.setAttribute("aria-label", "一時付箋");
      let x = (point.x - rect.left - camera.x) / camera.s,
        y = (point.y - rect.top - camera.y) / camera.s;
      const place = () => {
        note.style.left = x + "px";
        note.style.top = y + "px";
      };
      // Start at a readable screen size, then remain attached to the canvas.
      note.style.width = 240 / camera.s + "px";
      note.style.fontSize = 16 / camera.s + "px";
      place();
      const handle = document.createElement("button");
      handle.className = "sticky-handle";
      handle.type = "button";
      handle.textContent = "⋯";
      handle.title = "ドラッグで移動";
      handle.setAttribute("aria-label", "付箋を移動（ドラッグ／矢印キー）");
      const text = document.createElement("textarea");
      text.rows = 3;
      text.placeholder = "メモを入力…";
      text.setAttribute("aria-label", "付箋のテキスト");
      note.append(handle, text);
      world.append(note);
      const resize = () => {
        text.style.height = "auto";
        text.style.height = text.scrollHeight + "px";
      };
      text.addEventListener("input", resize);
      text.addEventListener("keydown", (e) => {
        e.stopPropagation();
        if (e.key === "Escape" && !e.isComposing) {
          e.preventDefault();
          text.blur();
        }
      });
      let drag = null;
      handle.addEventListener("pointerdown", (e) => {
        if (e.button !== 0) return;
        e.preventDefault();
        drag = {
          id: e.pointerId,
          cx: e.clientX,
          cy: e.clientY,
          x,
          y,
          scale: getCamera().s,
        };
        handle.setPointerCapture(e.pointerId);
        handle.classList.add("moving");
      });
      handle.addEventListener("pointermove", (e) => {
        if (!drag || e.pointerId !== drag.id) return;
        x = drag.x + (e.clientX - drag.cx) / drag.scale;
        y = drag.y + (e.clientY - drag.cy) / drag.scale;
        place();
      });
      const end = () => {
        drag = null;
        handle.classList.remove("moving");
      };
      for (const type of ["pointerup", "pointercancel", "lostpointercapture"])
        handle.addEventListener(type, end);
      handle.addEventListener("keydown", (e) => {
        e.stopPropagation();
        const delta = {
          ArrowLeft: [-1, 0],
          ArrowRight: [1, 0],
          ArrowUp: [0, -1],
          ArrowDown: [0, 1],
        }[e.key];
        if (delta) {
          e.preventDefault();
          const step = (e.shiftKey ? 20 : 5) / getCamera().s;
          x += delta[0] * step;
          y += delta[1] * step;
          place();
        }
      });
      for (const type of ["pointerdown", "click", "dblclick"])
        note.addEventListener(type, (e) => e.stopPropagation());
      note.addEventListener("wheel", (e) => e.stopPropagation());
      resize();
      text.focus({ preventScroll: true });
    }
    window.addEventListener("keydown", (e) => {
      if (
        e.defaultPrevented ||
        e.repeat ||
        e.isComposing ||
        e.ctrlKey ||
        e.metaKey ||
        e.altKey
      )
        return;
      if (
        e.target.closest("input,textarea,select,[contenteditable],.live-sticky")
      )
        return;
      if (e.key.toLowerCase() === "s") {
        e.preventDefault();
        create();
      }
    });
  },
};
