/* Shared grid: positions and outer sizes snap; typography keeps natural metrics. */
const SpatialLayout = (() => {
  const settings = Object.freeze({
    grid: 32,
    bodyWidth: 576,
    sectionWidth: 768,
    density: "standard",
  });
  const snap = (value, grid) => Math.ceil((value - 1e-7) / grid) * grid;
  function metrics(options = settings) {
    if (![16, 32, 64].includes(options.grid))
      throw Error("Grid must be 16, 32 or 64");
    const density = { compact: 2, standard: 3, spacious: 4 }[options.density];
    if (!density || !(options.bodyWidth > 0))
      throw Error("Invalid layout settings");
    const g = options.grid;
    return {
      grid: g,
      body: snap(options.bodyWidth, g),
      section: snap(options.sectionWidth ?? settings.sectionWidth, g),
      gap: density * g,
      chapterGap: (density + 1) * g,
      inset: snap(80, g),
      padding: 3 * g,
    };
  }
  // Only these inline properties belong to the layout engine.
  const owned = {
    node: ["width", "height", "position", "left", "top", "minWidth", "margin"],
    content: ["width", "maxWidth"],
    children: ["position", "left", "top", "width", "height", "margin"],
  };
  function reset(style, properties) {
    for (const property of properties) style[property] = "";
  }

  // Pure bottom-up geometry: no DOM reads or writes.
  function plan(node, m) {
    const round = (value) => snap(value, m.grid);
    const inset = node.chapter ? m.inset : 0,
      top = node.chapter ? m.grid : 0,
      bottom = node.chapter ? m.padding : 0;
    const result = {
      w: node.w + inset,
      h: round(node.h + top) + bottom,
      children: [],
    };
    if (node.children.length) {
      const sizes = node.children.map((child) => plan(child, m));
      const vertical = !node.atlas && node.layout === "stack";
      const gap = node.atlas ? m.chapterGap : m.gap;
      const maxH = Math.max(...sizes.map((b) => b.h));
      let x = 0,
        y = 0;
      sizes.forEach((box, i) => {
        let dy = 0;
        if (node.layout === "compare" && sizes.length === 3)
          dy = i === 0 ? 0 : i === 1 ? round((maxH - box.h) / 2) : maxH - box.h;
        result.children.push({
          ...box,
          x,
          y: y + dy,
          h: node.atlas ? maxH : box.h,
        });
        if (vertical) y += box.h + gap;
        else x += box.w + gap;
      });
      const w = vertical ? Math.max(...sizes.map((b) => b.w)) : x - gap;
      const h = vertical ? y - gap : maxH;
      const cx = node.atlas ? round(node.w + m.gap) : inset;
      const cy = node.atlas ? 0 : round(top + node.h + m.gap);
      result.container = { x: cx, y: cy, w, h };
      result.w = Math.max(result.w, cx + w);
      result.h = Math.max(result.h, cy + h + bottom);
    }
    result.w = round(Math.max(result.w, node.chapter ? round(600) : 0));
    result.h = round(result.h);
    return result;
  }
  function apply(world, options = settings) {
    const m = metrics(options),
      round = (value) => snap(value, m.grid);
    for (const [k, v] of Object.entries({
      "--grid-top": m.grid,
      "--node-width": m.body,
      "--table-width": m.section,
      "--gap": m.gap,
      "--chapter-gap": m.chapterGap,
      "--chapter-inset": m.inset,
      "--world-padding": m.padding,
      "--intro-width": m.body,
      "--chapter-min": round(600),
    }))
      world.style.setProperty(k, v + "px");
    const entries = [...world.querySelectorAll(".node")].map((el) => ({
      el,
      content: el.querySelector(":scope > .content"),
      container: el.querySelector(":scope > .children"),
    }));
    for (const entry of entries)
      entry.el.classList.toggle(
        "compare-pair",
        entry.el.classList.contains("compare") &&
          entry.container?.children.length === 2,
      );
    const byElement = new Map(entries.map((entry) => [entry.el, entry]));
    // Reset only owned styles, so presentation styles survive every reflow.
    for (const entry of entries) {
      reset(entry.el.style, owned.node);
      reset(entry.content.style, owned.content);
      if (entry.container) reset(entry.container.style, owned.children);
    }
    // Width depends only on the element's role, never its text or column count.
    for (const entry of entries) {
      if (entry.el.classList.contains("slide")) {
        entry.w = snap(1120, m.grid);
        entry.content.style.width = entry.w + "px";
      } else {
        entry.w = m.section;
        entry.content.style.width = entry.w + "px";
      }
      entry.content.style.maxWidth = "none";
    }
    // Heights must be measured after the final text wrapping widths are applied.
    for (const entry of entries) entry.h = entry.content.offsetHeight;
    function describe(el) {
      const entry = byElement.get(el);
      entry.children = entry.container ? [...entry.container.children] : [];
      return {
        w: entry.w,
        h: entry.h,
        atlas: el.classList.contains("atlas"),
        chapter: el.parentElement.parentElement.classList.contains("atlas"),
        layout: el.classList.contains("stack")
          ? "stack"
          : el.classList.contains("compare")
            ? "compare"
            : "row",
        children: entry.children.map(describe),
      };
    }
    const roots = [...world.querySelector(".roots").children];
    const plans = roots.map((root) => plan(describe(root), m));
    function commit(el, box, child = false) {
      const entry = byElement.get(el);
      Object.assign(el.style, {
        width: box.w + "px",
        height: box.h + "px",
        minWidth: "0",
      });
      if (child)
        Object.assign(el.style, {
          position: "absolute",
          left: box.x + "px",
          top: box.y + "px",
          margin: "0",
        });
      if (box.container) {
        const b = box.container;
        Object.assign(entry.container.style, {
          position: "absolute",
          left: b.x + "px",
          top: b.y + "px",
          width: b.w + "px",
          height: b.h + "px",
          margin: "0",
        });
        entry.children.forEach((child, i) =>
          commit(child, box.children[i], true),
        );
      }
    }
    roots.forEach((root, i) => commit(root, plans[i]));
  }
  return { settings, metrics, snap, plan, apply };
})();
if (typeof module !== "undefined") module.exports = SpatialLayout;
