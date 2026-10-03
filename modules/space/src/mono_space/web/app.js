"use strict";
(() => {
  const { CONFIG, Navigation, worldRect, fitCamera, zoomCamera, pinchCamera } =
    SpatialCore;
  const data = JSON.parse(document.querySelector("#data").textContent),
    world = document.querySelector("#world"),
    viewport = document.querySelector("#viewport"),
    svg = document.querySelector("#connections"),
    els = new Map();
  viewport.addEventListener("scroll", () => {
    if (viewport.scrollLeft !== 0 || viewport.scrollTop !== 0) {
      viewport.scrollLeft = 0;
      viewport.scrollTop = 0;
    }
  });
  window.addEventListener("scroll", () => {
    if (window.scrollX !== 0 || window.scrollY !== 0) {
      window.scrollTo(0, 0);
    }
  });
  const nodeById = new Map(data.nodes.map((n) => [n.id, n]));
  const nav = new Navigation(
    data.route,
    data.nodes.map((n) => n.id),
  );
  const state = { camera: { x: 0, y: 0, s: 1 } };
  data.route = nav.route;
  const picker = document.querySelector("#section-picker");
  const toc = document.querySelector("#section-toc"),
    jump = document.querySelector("#section-jump");
  const tocItems = new Map();
  for (const node of data.nodes) {
    const item = document.createElement("button");
    item.type = "button";
    item.textContent = node.title;
    item.dataset.section = node.id;
    let depth = 0,
      parent = node.parent;
    while (parent) {
      depth++;
      parent = nodeById.get(parent).parent;
    }
    item.style.setProperty("--depth", depth);
    item.onclick = () => {
      show(node.id);
      closeToc(true);
    };
    toc.append(item);
    tocItems.set(node.id, item);
  }
  function closeToc(restore = false) {
    toc.hidden = true;
    picker.setAttribute("aria-expanded", "false");
    if (restore) picker.focus({ preventScroll: true });
  }
  function openToc() {
    toc.hidden = false;
    picker.setAttribute("aria-expanded", "true");
    const current = tocItems.get(nav.selectedId);
    current.focus({ preventScroll: true });
    current.scrollIntoView({ block: "nearest", behavior: "instant" });
  }
  picker.onclick = () => (toc.hidden ? openToc() : closeToc());
  document.addEventListener("pointerdown", (e) => {
    if (!jump.contains(e.target)) closeToc();
  });
  document.addEventListener("focusin", (e) => {
    if (!jump.contains(e.target)) closeToc();
  });
  toc.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      closeToc(true);
      return;
    }
    if (["ArrowDown", "ArrowUp", "Home", "End"].includes(e.key)) {
      e.preventDefault();
      const items = [...tocItems.values()],
        i = items.indexOf(document.activeElement);
      const next =
        e.key === "Home"
          ? 0
          : e.key === "End"
            ? items.length - 1
            : Math.max(
                0,
                Math.min(
                  items.length - 1,
                  i + (e.key === "ArrowDown" ? 1 : -1),
                ),
              );
      items[next].focus({ preventScroll: true });
      items[next].scrollIntoView({ block: "nearest", behavior: "instant" });
    }
    if (!/^[0-9]$/.test(e.key) && e.key.toLowerCase() !== "h" && e.key !== "?") e.stopPropagation();
  });
  for (const [i, n] of data.nodes.entries()) {
    const el = document.createElement("section");
    el.className = `node ${n.layout} tone-${n.tone} ${n.style === "note" ? "note" : ""}`;
    el.dataset.level = n.level;
    el.dataset.id = n.id;
    if (!n.parent) el.classList.add("atlas");
    el.setAttribute("aria-label", n.title);
    const eyebrow = document.createElement("div");
    eyebrow.className = "eyebrow";
    eyebrow.textContent = `${String(i + 1).padStart(2, "0")} / ${n.tone === "neutral" ? "CONTEXT" : n.tone.toUpperCase()}`;
    const heading = document.createElement("h2");
    const headingText = document.createElement("span");
    headingText.className = "heading-text";
    headingText.textContent = n.title;
    heading.append(headingText);
    const marked =
      n.marker === "on" ||
      ((!n.marker || n.marker === "auto") &&
        n.level === 2 &&
        n.style !== "note" &&
        nodeById.get(n.parent)?.layout !== "flow");
    heading.classList.toggle("marked", marked);
    const body = document.createElement("div");
    body.innerHTML = n.html;
    const content = document.createElement("div");
    content.className = "content";
    content.append(eyebrow, heading, body);
    el.append(content);
    for (const button of el.querySelectorAll(".copy-code")) {
      button.addEventListener("click", async (e) => {
        e.stopPropagation();
        const block = button.closest(".codeblock"),
          status = block.querySelector(".copy-status");
        try {
          await navigator.clipboard.writeText(
            block.querySelector("code").textContent,
          );
          status.textContent = "コピーしました";
        } catch {
          status.textContent = "コードを選択してコピーしてください";
        }
        clearTimeout(button.copyTimer);
        button.copyTimer = setTimeout(() => {
          status.textContent = "";
        }, 2500);
      });
    }
    for (const button of el.querySelectorAll('.math-copy')) {
      button.addEventListener('click', async (event) => {
        event.stopPropagation();
        const wrap = button.closest('.math-wrap');
        const status = wrap.querySelector('.math-status');
        try {
          await navigator.clipboard.writeText(button.dataset.tex);
          status.textContent = 'TeXをコピーしました';
        } catch {
          wrap.querySelector('.math-source').hidden = false;
          status.textContent = '表示されたTeXを選択してコピーしてください';
        }
        clearTimeout(button.copyTimer);
        button.copyTimer = setTimeout(() => { status.textContent = ''; }, 2500);
      });
      button.addEventListener('keydown', event => event.stopPropagation());
    }
    for (const anchor of el.querySelectorAll("a")) anchor.draggable = false;
    for (const img of el.querySelectorAll("img")) {
      img.draggable = false;
      img.src = data.assets[img.dataset.asset];
    }
    els.set(n.id, el);
    const parent = n.parent
      ? els.get(n.parent)
      : document.querySelector(".roots");
    let target = parent;
    if (n.parent) {
      parent.classList.add("group");
      target = parent.querySelector(":scope > .children");
      if (!target) {
        target = document.createElement("div");
        target.className = "children";
        parent.append(target);
      }
    }
    target.append(el);
    el.addEventListener("click", (e) => {
      e.stopPropagation();
      if (e.target.closest("code,.codeblock")) {
        if (!gestures.moved && e.target.closest(".code-tools") && !e.target.closest("button"))
          show(n.id, e.target.closest(".codeblock"));
        return;
      }
      if (e.target.closest("a")) {
        if (gestures.moved) e.preventDefault();
        return;
      }
      if (!gestures.moved) show(n.id, e.target.closest("img,.markdown-table"));
    });
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.stopPropagation();
        focusId(n.id);
      }
    });
  }
  function bounds(el) {
    return worldRect(
      el.getBoundingClientRect(),
      world.getBoundingClientRect(),
      world.getBoundingClientRect().width / world.offsetWidth || 1,
    );
  }
  let focusedElement = null;
  function focusElement(id) {
    if (focusedElement && els.get(id).contains(focusedElement)) return focusedElement;
    const node = els.get(id),
      scope = nodeById.get(id).focus;
    if (scope === "subtree") return node;
    if (scope === "image")
      return (
        node.querySelector(":scope > .content img") ||
        node.querySelector(":scope > .content .image-error") ||
        node.querySelector(":scope > .content")
      );
    return node.querySelector(":scope > .content");
  }
  function point(a, b, c, d, t) {
    const u = 1 - t;
    return {
      x:
        u * u * u * a.x +
        3 * u * u * t * b.x +
        3 * u * t * t * c.x +
        t * t * t * d.x,
      y:
        u * u * u * a.y +
        3 * u * u * t * b.y +
        3 * u * t * t * c.y +
        t * t * t * d.y,
    };
  }
  function draw() {
    svg.replaceChildren();
    svg.setAttribute("width", world.offsetWidth);
    svg.setAttribute("height", world.offsetHeight);
    const ns = "http://www.w3.org/2000/svg";
    const make = (tag, attrs) => {
      const e = document.createElementNS(ns, tag);
      for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
      return e;
    };
    for (const [eid, e] of data.edges.entries()) {
      const a = bounds(els.get(e.source)),
        b = bounds(els.get(e.target));
      const horizontal = Math.abs(b.x - a.x) > Math.abs(b.y - a.y),
        forward = horizontal ? b.x >= a.x : b.y >= a.y;
      const p = horizontal
        ? { x: a.x + (forward ? a.w : 0), y: a.y + a.h / 2 }
        : { x: a.x + a.w / 2, y: a.y + (forward ? a.h : 0) };
      const q = horizontal
        ? { x: b.x + (forward ? 0 : b.w), y: b.y + b.h / 2 }
        : { x: b.x + b.w / 2, y: b.y + (forward ? 0 : b.h) };
      const bend =
        Math.max(
          70,
          (horizontal ? Math.abs(q.x - p.x) : Math.abs(q.y - p.y)) * 0.5,
        ) * (forward ? 1 : -1);
      const c = horizontal
          ? { x: p.x + bend, y: p.y }
          : { x: p.x, y: p.y + bend },
        d = horizontal ? { x: q.x - bend, y: q.y } : { x: q.x, y: q.y - bend };
      const color = getComputedStyle(els.get(e.source))
        .getPropertyValue("--tone-color")
        .trim();
      const marker = make("marker", {
        id: "arrow" + eid,
        viewBox: "0 0 10 10",
        refX: 9,
        refY: 5,
        markerWidth: 7,
        markerHeight: 7,
        orient: "auto-start-reverse",
      });
      marker.append(make("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: color }));
      svg.append(marker);
      svg.append(
        make("path", {
          d: `M${p.x} ${p.y} C${c.x} ${c.y} ${d.x} ${d.y} ${q.x} ${q.y}`,
          stroke: color,
          "stroke-width": 2,
          fill: "none",
          "marker-end": `url(#arrow${eid})`,
        }),
      );
      const mid = point(p, c, d, q, 0.5),
        label = make("text", {
          x: mid.x,
          y: mid.y - 12,
          fill: color,
          "text-anchor": "middle",
        });
      label.textContent = e.label;
      svg.append(label);
    }
  }
  function paint() {
    world.style.transform = `translate(${state.camera.x}px,${state.camera.y}px) scale(${state.camera.s})`;
    const dotOpacity = Math.min(
      1,
      Math.max(CONFIG.dotMinimum, Math.pow(state.camera.s, CONFIG.dotExponent)),
    );
    viewport.style.setProperty(
      "--dot-color",
      `rgba(184,187,185,${dotOpacity})`,
    );
    const spacing = SpatialLayout.settings.grid;
    const grid =
      spacing *
      state.camera.s *
      Math.pow(
        2,
        Math.max(0, Math.ceil(Math.log2(12 / (spacing * state.camera.s)))),
      );
    viewport.style.backgroundSize = `${grid}px ${grid}px`;
    viewport.style.backgroundPosition = `${state.camera.x - grid / 2}px ${state.camera.y - grid / 2}px`;
    document.querySelector("#zoom").textContent =
      Math.round(state.camera.s * 100) + "%";
    const rect = document.querySelector("#map-camera");
    rect.setAttribute("x", -state.camera.x / state.camera.s);
    rect.setAttribute("y", -state.camera.y / state.camera.s);
    rect.setAttribute("width", viewport.clientWidth / state.camera.s);
    rect.setAttribute("height", viewport.clientHeight / state.camera.s);
  }
  function drawMap() {
    const map = document.querySelector("#minimap"),
      g = document.querySelector("#map-nodes");
    map.setAttribute(
      "viewBox",
      `0 0 ${world.offsetWidth} ${world.offsetHeight}`,
    );
    g.replaceChildren();
    for (const n of data.nodes) {
      if (!n.parent) continue;
      const b = bounds(els.get(n.id)),
        r = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      for (const [k, v] of Object.entries({
        x: b.x,
        y: b.y,
        width: b.w,
        height: b.h,
        fill:
          n.level === 2
            ? "none"
            : getComputedStyle(els.get(n.id))
                .getPropertyValue("--tone-soft")
                .trim(),
        stroke: n.level === 2 ? "#b7d9ef" : "none",
        "stroke-width": 0.5,
      }))
        r.setAttribute(k, v);
      g.append(r);
    }
  }
  function explore() {
    motion.cancel();
    nav.explore();
    renderNavigation();
  }
  function zoomAt(
    factor,
    x = viewport.clientWidth / 2,
    y = viewport.clientHeight / 2,
  ) {
    state.camera = zoomCamera(state.camera, factor, x, y);
    explore();
    paint();
  }
  function fit(box, close = false) {
    const w = viewport.clientWidth || window.innerWidth;
    const h = viewport.clientHeight || window.innerHeight;
    return fitCamera(
      box,
      { w: Math.max(1, w), h: Math.max(1, h) },
      close,
    );
  }
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const motionToggle = document.querySelector("#reduce-motion");
  const motion = SpatialMotion.create({
    read: () => state.camera,
    write: (target) => {
      state.camera = { ...target };
      paint();
    },
    opacity: (value) => {
      viewport.style.opacity = value;
    },
    view: () => ({ w: viewport.clientWidth, h: viewport.clientHeight }),
    reduced: () => reducedMotion.matches || motionToggle.checked,
  });
  function syncMotion() {
    document.body.classList.toggle(
      "reduce-motion",
      reducedMotion.matches || motionToggle.checked,
    );
    motion.cancel();
    if (nav.mode === "focus") {
      state.camera = focusCamera(nav.selectedId);
      paint();
    } else if (nav.mode === "overview") {
      state.camera = fit({
        x: 0,
        y: 0,
        w: Math.max(100, world.offsetWidth),
        h: Math.max(100, world.offsetHeight),
      });
      paint();
    }
  }
  motionToggle.addEventListener("change", syncMotion);
  reducedMotion.addEventListener("change", syncMotion);
  document.body.classList.toggle("reduce-motion", reducedMotion.matches);
  viewport.addEventListener("pointerdown", () => motion.cancel());
  function move(target) {
    motion.move(target, !document.documentElement.dataset.ready);
  }
  function chapterTitle(id) {
    let node = nodeById.get(id);
    while (node.parent && nodeById.get(node.parent).parent)
      node = nodeById.get(node.parent);
    return node.title;
  }
  function renderNavigation() {
    const focused = nav.mode === "focus";
    const selected = els.get(nav.selectedId);
    const includeChildren = nodeById.get(nav.selectedId).focus === "subtree";
    let dimmedCount = 0;
    for (const [id, node] of els) {
      const keep =
        id === nav.selectedId || (includeChildren && selected.contains(node));
      const dim = focused && !keep;
      // Dim each content block, never its ancestor: nested targets stay at 100%.
      node.classList.toggle("context-muted", dim);
      if (dim) dimmedCount++;
    }
    svg.style.opacity = focused && dimmedCount > 0 ? "0.25" : "1";
    picker.dataset.selected = focused ? nav.selectedId : "";
    picker.textContent = focused
      ? nodeById.get(nav.selectedId).title
      : nav.mode === "free"
        ? "自由に探索中"
        : "目次";
    for (const [id, item] of tocItems) {
      if (focused && id === nav.selectedId)
        item.setAttribute("aria-current", "location");
      else item.removeAttribute("aria-current");
    }
    document.querySelector("#label").textContent = focused
      ? chapterTitle(nav.selectedId)
      : nav.mode === "free"
        ? "自由に探索"
        : "キャンバス全体";
    document.querySelector("#status").textContent = focused
      ? (nav.index >= 0 ? `${nav.index + 1} / ${nav.route.length}` : "章")
      : nav.mode === "free"
        ? "探索"
        : "全体";
    for (const [button, delta] of [
      ["prev", -1],
      ["next", 1],
    ]) {
      const el = document.querySelector("#" + button),
        id = nav.adjacent(delta);
      el.disabled = id === null;
      el.title = id
        ? (delta < 0 ? "前へ：" : "次へ：") + nodeById.get(id).title
        : delta < 0
          ? "最初のセクション"
          : "最後のセクション";
    }
  }
  function focusCamera(id) {
    const box = bounds(focusElement(id));
    if (nodeById.get(id).focus === 'image' || focusedElement?.tagName === 'IMG') {
      const heading = els.get(id).querySelector(':scope > .content > h2');
      if (heading) box.y = bounds(heading).y;
    }
    return fit(box, true);
  }
  function show(id, element = null) {
    focusedElement = element;
    closeToc();
    nav.focus(id);
    renderNavigation();
    move(focusCamera(id));
  }
  function focusId(id) {
    show(id);
  }
  function step(delta) {
    const id = nav.adjacent(delta);
    if (id) show(id);
  }
  function all() {
    focusedElement = null;
    closeToc();
    nav.overview();
    renderNavigation();
    if (!world.offsetWidth || !world.offsetHeight) {
      SpatialLayout.apply(world);
      draw();
      drawMap();
    }
    const w = Math.max(100, world.offsetWidth);
    const h = Math.max(100, world.offsetHeight);
    move(fit({ x: 0, y: 0, w, h }));
  }
  function toggleOverview() {
    nav.mode === "overview" ? show(nav.selectedId) : all();
  }
  document.querySelector("#next").onclick = () => step(1);
  document.querySelector("#prev").onclick = () => step(-1);
  document.querySelector("#overview").onclick = () => all();
  document.querySelector("#zoom-in").onclick = () => zoomAt(CONFIG.zoomStep);
  document.querySelector("#zoom-out").onclick = () =>
    zoomAt(1 / CONFIG.zoomStep);
  document.querySelector("#zoom").onclick = () => zoomAt(1 / state.camera.s);
  document.querySelector("#map-toggle").onclick = () => {
    const panel = document.querySelector("#map-panel"),
      button = document.querySelector("#map-toggle");
    panel.hidden = !panel.hidden;
    button.setAttribute("aria-pressed", String(!panel.hidden));
    button.textContent = panel.hidden
      ? "ミニマップを表示"
      : "ミニマップを非表示";
  };
  function toggleHelp() {
    const help = document.querySelector("#help");
    const toggle = document.querySelector("#help-toggle");
    help.hidden = !help.hidden;
    toggle.setAttribute("aria-expanded", String(!help.hidden));
  }
  document.querySelector("#help-toggle").onclick = toggleHelp;
  function setUiCollapsed(collapsed) {
    closeToc();
    document.querySelector("#help").hidden = true;
    document.querySelector("#help-toggle").setAttribute("aria-expanded", "false");
    document.body.classList.toggle("quiet", collapsed);
    for (const panel of document.querySelectorAll(".hud")) panel.inert = collapsed;
    const floatingNav = document.querySelector("#mono-floating-nav");
    if (floatingNav) floatingNav.inert = collapsed;
    if (collapsed && document.activeElement?.closest?.(".hud, #mono-floating-nav")) {
      document.activeElement.blur();
    }
  }
  document.querySelector("#fullscreen").onclick = async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch {
      document.querySelector("#label").textContent =
        "全画面表示を利用できません";
    }
  };
  window.addEventListener("keydown", (e) => {
    if (
      e.isComposing ||
      e.target.closest("input,textarea,select,[contenteditable],.live-sticky")
    )
      return;
    if (e.key === "Escape" && !toc.hidden) {
      e.preventDefault();
      closeToc(true);
      return;
    }
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (/^[0-9]$/.test(e.key)) {
      e.preventDefault();
      const number = Number(e.key);
      if (number === 0) all();
      else if (nav.route[number - 1]) show(nav.route[number - 1]);
      return;
    }
    if (e.target.closest("select,input,textarea")) return;
    if (e.target.closest("button") && (e.key === " " || e.key === "Enter"))
      return;
    if (["ArrowRight", "ArrowDown", " "].includes(e.key)) {
      e.preventDefault();
      step(1);
    } else if (["ArrowLeft", "ArrowUp"].includes(e.key)) {
      e.preventDefault();
      step(-1);
    } else if (e.key.toLowerCase() === "o") {
      toggleOverview();
    } else if (e.key === "Escape") {
      const help = document.querySelector("#help");
      if (!help.hidden) {
        help.hidden = true;
        document
          .querySelector("#help-toggle")
          .setAttribute("aria-expanded", "false");
        return;
      }
      if (document.body.classList.contains("quiet")) {
        setUiCollapsed(false);
        return;
      }
      all();
    } else if (e.key === "Home") {
      all();
    } else if (e.key.toLowerCase() === "h") {
      e.preventDefault();
      setUiCollapsed(!document.body.classList.contains("quiet"));
    } else if (e.key === "?" || (e.key === "/" && e.shiftKey)) {
      e.preventDefault();
      toggleHelp();
    } else if (e.key === "+" || e.key === "=") {
      zoomAt(CONFIG.zoomStep);
    } else if (e.key === "-") {
      zoomAt(1 / CONFIG.zoomStep);
    }
  });
  SpatialStickies.attach(viewport, world, () => state.camera);
  SpatialAnnotations.attach(viewport, world, () => state.camera);
  const gestures = SpatialInput.attach(
    viewport,
    () => state.camera,
    (c) => {
      state.camera = c;
      explore();
      paint();
    },
    zoomAt,
  );
  document.querySelector("#minimap").addEventListener("click", (e) => {
    const map = e.currentTarget,
      r = map.getBoundingClientRect(),
      w = world.offsetWidth,
      h = world.offsetHeight,
      s = Math.min(r.width / w, r.height / h),
      x = (e.clientX - r.left - (r.width - w * s) / 2) / s,
      y = (e.clientY - r.top - (r.height - h * s) / 2) / s;
    explore();
    move({
      s: state.camera.s,
      x:
        viewport.clientWidth / 2 - Math.max(0, Math.min(w, x)) * state.camera.s,
      y:
        viewport.clientHeight / 2 -
        Math.max(0, Math.min(h, y)) * state.camera.s,
    });
  });
  async function initialize() {
    await Promise.all(
      [...document.images].map(async (img) => {
        try {
          await img.decode();
        } catch {
          const error = document.createElement("div");
          error.className = "image-error";
          error.setAttribute("role", "status");
          error.textContent =
            "画像を表示できません：" + (img.alt || "名称なし");
          img.replaceWith(error);
        }
      }),
    );
    await document.fonts.ready;
    SpatialLayout.apply(world);
    draw();
    drawMap();
    all();
    document.documentElement.dataset.ready = "true";
  }
  initialize();
  let resize;
  window.addEventListener("resize", () => {
    clearTimeout(resize);
    resize = setTimeout(() => {
      if (!viewport || !viewport.clientWidth || !viewport.clientHeight) return;
      SpatialLayout.apply(world);
      draw();
      drawMap();
      if (nav.mode === "overview") all();
      else if (nav.mode === "focus") show(nav.selectedId, focusedElement);
      else paint();
    }, CONFIG.resizeDelay);
  });
})();
