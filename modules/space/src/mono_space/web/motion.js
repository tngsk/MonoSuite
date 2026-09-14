/* Short, bounded motion; long travel and scale changes are hidden by a fade. */
const SpatialMotion = (() => {
  function kind(from, to, view) {
    if (Math.abs(Math.log(to.s / from.s)) > Math.log(1.03)) return "fade";
    // Compare viewport centres in world coordinates; translation alone includes zoom offsets.
    const dx =
      ((view.w / 2 - to.x) / to.s - (view.w / 2 - from.x) / from.s) * from.s;
    const dy =
      ((view.h / 2 - to.y) / to.s - (view.h / 2 - from.y) / from.s) * from.s;
    return Math.hypot(dx / view.w, dy / view.h) <= 0.75 ? "pan" : "fade";
  }
  function create({ read, write, opacity, view, reduced }) {
    let frame = 0,
      generation = 0;
    function cancel() {
      generation++;
      cancelAnimationFrame(frame);
      frame = 0;
      opacity(1);
    }
    function move(target, instant = false) {
      cancel();
      const token = generation,
        from = { ...read() };
      if (instant || reduced()) {
        write(target);
        return;
      }
      const type = kind(from, target, view()),
        duration = type === "pan" ? 300 : 160;
      if (from.x === target.x && from.y === target.y && from.s === target.s) {
        write(target);
        return;
      }
      let start = null,
        switched = false;
      function tick(now) {
        if (token !== generation) return;
        if (start === null) start = now;
        const t = Math.min(1, (now - start) / duration);
        if (type === "pan") {
          const u = 1 - Math.pow(1 - t, 3);
          write({
            x: from.x + (target.x - from.x) * u,
            y: from.y + (target.y - from.y) * u,
            s: from.s + (target.s - from.s) * u,
          });
        } else {
          if (t >= 0.5 && !switched) {
            opacity(0);
            write(target);
            switched = true;
          }
          opacity(t < 0.5 ? 1 - 2 * t : 2 * t - 1);
        }
        if (t < 1) frame = requestAnimationFrame(tick);
        else {
          write(target);
          opacity(1);
          frame = 0;
        }
      }
      frame = requestAnimationFrame(tick);
    }
    return { move, cancel };
  }
  return { kind, create };
})();
if (typeof module !== "undefined") module.exports = SpatialMotion;
