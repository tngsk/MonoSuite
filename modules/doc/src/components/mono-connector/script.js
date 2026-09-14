(function () {
    if (typeof window === "undefined") return;

    // Space 3-tone および テーマカラーの定義
    const TONE_COLORS = {
        normal: "#8d83b0",
        ai: "#a855f7",
        warning: "#b96727",
        primary: "var(--color-primary, #2563eb)",
        secondary: "var(--color-secondary, #4b5563)",
        accent: "var(--color-accent, #0ea5e9)",
    };

    /**
     * ドキュメント全体のコネクタ描画を一元管理するシングルトンマネージャー
     */
    class ConnectorManager {
        constructor() {
            this.connectors = new Set();
            this.svg = null;
            this.defs = null;
            this.rafId = null;
            this.resizeObserver = null;
            this.observedElements = new Set();
            this.isInitialized = false;
        }

        init() {
            if (this.isInitialized || !document.body) return;
            this.isInitialized = true;

            // bodyに position: relative を確保
            const bodyComputed = window.getComputedStyle(document.body);
            if (bodyComputed.position === "static") {
                document.body.style.position = "relative";
            }

            // グローバルスタイルの注入
            if (!document.getElementById("mono-connector-global-style")) {
                const style = document.createElement("style");
                style.id = "mono-connector-global-style";
                style.textContent = `
                    #mono-connector-layer {
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        pointer-events: none;
                        z-index: var(--z-index-connector, 10);
                        overflow: visible;
                    }
                    #mono-connector-layer text {
                        font-family: inherit;
                        font-size: 0.875rem;
                        font-weight: 500;
                        paint-order: stroke;
                        stroke: var(--color-base-100, #ffffff);
                        stroke-width: 6px;
                        stroke-linejoin: round;
                        user-select: none;
                    }
                    @media print {
                        #mono-connector-layer {
                            position: absolute;
                            -webkit-print-color-adjust: exact !important;
                            print-color-adjust: exact !important;
                        }
                    }
                `;
                document.head.appendChild(style);
            }

            // 集約SVGレイヤーの生成
            let svg = document.getElementById("mono-connector-layer");
            if (!svg) {
                svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                svg.id = "mono-connector-layer";
                svg.setAttribute("aria-hidden", "true");
                document.body.appendChild(svg);
            }
            this.svg = svg;

            let defs = svg.querySelector("defs");
            if (!defs) {
                defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
                svg.appendChild(defs);
            }
            this.defs = defs;

            // ResizeObserverの初期化
            if (window.ResizeObserver) {
                this.resizeObserver = new ResizeObserver(() => this.requestRedraw());
                this.resizeObserver.observe(document.body);
            }

            window.addEventListener("resize", () => this.requestRedraw(), { passive: true });
            window.addEventListener("load", () => this.requestRedraw(), { passive: true });

            if (document.fonts && document.fonts.ready) {
                document.fonts.ready.then(() => this.requestRedraw());
            }
        }

        register(connector) {
            this.init();
            this.connectors.add(connector);
            this.requestRedraw();
        }

        unregister(connector) {
            this.connectors.delete(connector);
            this.requestRedraw();
        }

        requestRedraw() {
            if (this.rafId) return;
            this.rafId = requestAnimationFrame(() => {
                this.rafId = null;
                this.redraw();
            });
        }

        redraw() {
            if (!this.svg) return;

            // SVGサイズをbodyのスクロール可能領域全体に合わせる
            const scrollW = Math.max(document.body.scrollWidth, document.documentElement.scrollWidth);
            const scrollH = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
            this.svg.setAttribute("width", scrollW);
            this.svg.setAttribute("height", scrollH);
            this.svg.style.width = scrollW + "px";
            this.svg.style.height = scrollH + "px";

            // 既存の動的パスとマーカーのクリア（defsは保持して更新）
            this.defs.replaceChildren();
            const children = Array.from(this.svg.children);
            for (const child of children) {
                if (child !== this.defs) {
                    child.remove();
                }
            }

            const bodyRect = document.body.getBoundingClientRect();
            let index = 0;

            for (const connector of this.connectors) {
                index++;
                this.renderConnector(connector, bodyRect, index);
            }
        }

        renderConnector(connector, bodyRect, index) {
            const fromAttr = connector.getAttribute("from") || "";
            const toAttr = connector.getAttribute("to") || "";
            if (!fromAttr || !toAttr) return;

            const fromRect = this.resolveTarget(fromAttr, bodyRect);
            const toRect = this.resolveTarget(toAttr, bodyRect);
            if (!fromRect || !toRect) return;

            // 属性の取得
            const tone = connector.getAttribute("tone") || "normal";
            const color = TONE_COLORS[tone] || tone;
            const fromAnchor = connector.getAttribute("from-anchor") || "auto";
            const toAnchor = connector.getAttribute("to-anchor") || "auto";
            const curveType = connector.getAttribute("curve") || "bezier";
            const strokeWidth = connector.getAttribute("stroke") || "2";
            const dashed = connector.getAttribute("dashed");
            const arrowMode = connector.getAttribute("arrow") || "end";
            const label = connector.getAttribute("label") || "";
            const customBend = connector.getAttribute("bend");

            // 主軸および自動アンカーの決定
            const dx = (toRect.x + toRect.w / 2) - (fromRect.x + fromRect.w / 2);
            const dy = (toRect.y + toRect.h / 2) - (fromRect.y + fromRect.h / 2);
            const horizontal = Math.abs(dx) > Math.abs(dy);
            const forward = horizontal ? dx >= 0 : dy >= 0;

            const p = this.computeAnchorPoint(fromRect, fromAnchor, horizontal, forward, true);
            const q = this.computeAnchorPoint(toRect, toAnchor, horizontal, forward, false);

            // ベジェ曲線の制御点算出 (Space由来のアルゴリズム)
            const bend = customBend
                ? parseFloat(customBend)
                : Math.max(50, (horizontal ? Math.abs(q.x - p.x) : Math.abs(q.y - p.y)) * 0.5) * (forward ? 1 : -1);

            const c = horizontal ? { x: p.x + bend, y: p.y } : { x: p.x, y: p.y + bend };
            const d = horizontal ? { x: q.x - bend, y: q.y } : { x: q.x, y: q.y - bend };

            let pathD = "";
            let mid = { x: (p.x + q.x) / 2, y: (p.y + q.y) / 2 };

            if (curveType === "straight") {
                pathD = `M ${p.x} ${p.y} L ${q.x} ${q.y}`;
            } else if (curveType === "step") {
                if (horizontal) {
                    const midX = (p.x + q.x) / 2;
                    pathD = `M ${p.x} ${p.y} L ${midX} ${p.y} L ${midX} ${q.y} L ${q.x} ${q.y}`;
                } else {
                    const midY = (p.y + q.y) / 2;
                    pathD = `M ${p.x} ${p.y} L ${p.x} ${midY} L ${q.x} ${midY} L ${q.x} ${q.y}`;
                }
            } else {
                // 3次ベジェ曲線 (Cubic Bézier)
                pathD = `M ${p.x} ${p.y} C ${c.x} ${c.y}, ${d.x} ${d.y}, ${q.x} ${q.y}`;
                // パラメータ t = 0.5 における厳密な中間座標計算
                const u = 0.5;
                mid = {
                    x: u * u * u * p.x + 3 * u * u * 0.5 * c.x + 3 * u * 0.5 * 0.5 * d.x + 0.125 * q.x,
                    y: u * u * u * p.y + 3 * u * u * 0.5 * c.y + 3 * u * 0.5 * 0.5 * d.y + 0.125 * q.y,
                };
            }

            // 矢印マーカーの生成
            const markerId = `mono-connector-arrow-${index}`;
            const marker = document.createElementNS("http://www.w3.org/2000/svg", "marker");
            marker.setAttribute("id", markerId);
            marker.setAttribute("viewBox", "0 0 10 10");
            marker.setAttribute("refX", "9");
            marker.setAttribute("refY", "5");
            marker.setAttribute("markerWidth", "7");
            marker.setAttribute("markerHeight", "7");
            marker.setAttribute("orient", "auto-start-reverse");

            const arrowPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
            arrowPath.setAttribute("d", "M 0 0 L 10 5 L 0 10 z");
            arrowPath.setAttribute("fill", color);
            marker.appendChild(arrowPath);
            this.defs.appendChild(marker);

            // コネクタパスの描画
            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            path.setAttribute("d", pathD);
            path.setAttribute("stroke", color);
            path.setAttribute("stroke-width", strokeWidth);
            path.setAttribute("fill", "none");

            if (dashed && dashed !== "false") {
                path.setAttribute("stroke-dasharray", dashed === "true" ? "6 4" : dashed);
            }

            if (arrowMode === "end" || arrowMode === "both") {
                path.setAttribute("marker-end", `url(#${markerId})`);
            }
            if (arrowMode === "start" || arrowMode === "both") {
                path.setAttribute("marker-start", `url(#${markerId})`);
            }

            this.svg.appendChild(path);

            // ラベルの描画
            if (label) {
                const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
                text.setAttribute("x", mid.x);
                text.setAttribute("y", mid.y - 10);
                text.setAttribute("fill", color);
                text.setAttribute("text-anchor", "middle");
                text.textContent = label;
                this.svg.appendChild(text);
            }
        }

        resolveTarget(targetStr, bodyRect) {
            targetStr = targetStr.trim();
            // 相対パーセントまたはピクセル指定の検出: "10%, 20%" または "100px, 200px"
            const coordMatch = targetStr.match(/^([\d.]+(?:%|px)?)\s*,\s*([\d.]+(?:%|px)?)$/);
            if (coordMatch) {
                const parseCoord = (val, total) => {
                    if (val.endsWith("%")) {
                        return (parseFloat(val) / 100) * total;
                    }
                    return parseFloat(val);
                };
                return {
                    x: parseCoord(coordMatch[1], bodyRect.width),
                    y: parseCoord(coordMatch[2], bodyRect.height),
                    w: 0,
                    h: 0,
                };
            }

            // セレクタ指定の要素解決
            try {
                const el = document.querySelector(targetStr);
                if (!el) return null;

                // 対象要素をResizeObserverに登録
                if (this.resizeObserver && !this.observedElements.has(el)) {
                    this.observedElements.add(el);
                    this.resizeObserver.observe(el);
                }

                const r = el.getBoundingClientRect();
                return {
                    x: r.left - bodyRect.left,
                    y: r.top - bodyRect.top,
                    w: r.width,
                    h: r.height,
                };
            } catch (e) {
                return null;
            }
        }

        computeAnchorPoint(rect, anchor, horizontal, forward, isSource) {
            if (rect.w === 0 && rect.h === 0) {
                return { x: rect.x, y: rect.y };
            }

            switch (anchor) {
                case "top":
                    return { x: rect.x + rect.w / 2, y: rect.y };
                case "bottom":
                    return { x: rect.x + rect.w / 2, y: rect.y + rect.h };
                case "left":
                    return { x: rect.x, y: rect.y + rect.h / 2 };
                case "right":
                    return { x: rect.x + rect.w, y: rect.y + rect.h / 2 };
                case "center":
                    return { x: rect.x + rect.w / 2, y: rect.y + rect.h / 2 };
                case "auto":
                default:
                    if (isSource) {
                        return horizontal
                            ? { x: rect.x + (forward ? rect.w : 0), y: rect.y + rect.h / 2 }
                            : { x: rect.x + rect.w / 2, y: rect.y + (forward ? rect.h : 0) };
                    } else {
                        return horizontal
                            ? { x: rect.x + (forward ? 0 : rect.w), y: rect.y + rect.h / 2 }
                            : { x: rect.x + rect.w / 2, y: rect.y + (forward ? 0 : rect.h) };
                    }
            }
        }
    }

    const manager = new ConnectorManager();

    class MonoConnector extends (typeof HTMLElement !== "undefined" ? HTMLElement : Object) {
        static get observedAttributes() {
            return ["from", "to", "label", "tone", "from-anchor", "to-anchor", "curve", "bend", "stroke", "dashed", "arrow"];
        }

        connectedCallback() {
            manager.register(this);
        }

        disconnectedCallback() {
            manager.unregister(this);
        }

        attributeChangedCallback() {
            manager.requestRedraw();
        }
    }

    if (typeof customElements !== "undefined" && !customElements.get("mono-connector")) {
        customElements.define("mono-connector", MonoConnector);
    }
})();
