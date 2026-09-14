class MonoTopicRail extends MonoBaseElement {
    constructor() {
        super();
        this.topics = [];
        this.onResizeBound = this.onResize.bind(this);
        this.resizeTimer = null;
    }

    connectedCallback() {
        this.mountTemplate("template-mono-topic-rail");
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", () => this.initRail());
        } else {
            setTimeout(() => this.initRail(), 30);
        }

        // 画像やフォント読み込み完了時の座標再計算
        window.addEventListener("load", () => this.renderSegments());
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(() => this.renderSegments());
        }
    }

    disconnectedCallback() {
        window.removeEventListener("resize", this.onResizeBound);
        if (this.resizeTimer) clearTimeout(this.resizeTimer);
    }

    getAbsoluteTop(element) {
        let top = 0;
        let current = element;
        while (current) {
            top += current.offsetTop || 0;
            current = current.offsetParent;
        }
        return top;
    }

    calculateRailLeft() {
        // ドキュメント内のコンテンツ要素（見出しや最初のトピック要素）の左端座標を取得
        const sampleElement = this.topics.length > 0 
            ? this.topics[0].element 
            : document.querySelector("h1, h2, p, .column");
        
        if (!sampleElement) return 16;

        const rect = sampleElement.getBoundingClientRect();
        const contentLeft = rect.left;

        // コンテンツ左側とブラウザ左端（0px）の間の中間位置
        if (contentLeft > 4) {
            return Math.round(contentLeft / 2);
        }
        return 4;
    }

    initRail() {
        // 見出しの .topic または .section を走査
        const elements = Array.from(
            document.querySelectorAll(
                "h1.topic, h2.topic, h3.topic, h4.topic, h5.topic, h6.topic, .topic, h1.section, h2.section, h3.section, .section"
            )
        );

        const uniqueElements = Array.from(new Set(elements));
        if (uniqueElements.length === 0) return;

        // Doc 5-tone 高視認性カラー配列（2pxソリッド用）
        const toneVars = [
            "#eab308", // Yellow
            "#ec4899", // Pink
            "#10b981", // Green
            "#06b6d4", // Cyan
            "#f97316"  // Orange
        ];

        this.topics = uniqueElements.map((el, i) => {
            const title = el.textContent.trim() || `Topic ${i + 1}`;
            const color = toneVars[i % toneVars.length];
            return { element: el, title, color, index: i, top: 0 };
        });

        this.renderSegments();
        window.addEventListener("resize", this.onResizeBound, { passive: true });
    }

    renderSegments() {
        const container = this.shadowRoot ? this.shadowRoot.querySelector(".topic-scroll-rail-container") : null;
        if (!container || !this.topics.length) return;

        // コンテンツ左端とブラウザ左端の中間位置を計算して配置
        const railLeft = this.calculateRailLeft();
        container.style.setProperty("--rail-left", `${railLeft}px`);
        container.style.left = `${railLeft}px`;

        // 各トピックの絶対座標を再計算
        this.topics.forEach(t => {
            t.top = this.getAbsoluteTop(t.element);
        });

        container.innerHTML = "";
        const totalHeight = Math.max(
            document.documentElement.scrollHeight,
            document.body.scrollHeight
        );

        for (let i = 0; i < this.topics.length; i++) {
            const current = this.topics[i];
            const startTop = current.top;

            let endTop;
            if (i < this.topics.length - 1) {
                endTop = this.topics[i + 1].top;
            } else {
                endTop = totalHeight;
            }

            const segHeight = Math.max(0, endTop - startTop);

            const seg = document.createElement("div");
            seg.className = "topic-scroll-segment";
            seg.style.top = `${startTop}px`;
            seg.style.height = `${segHeight}px`;
            seg.style.setProperty("--segment-color", current.color);
            container.appendChild(seg);
        }
    }

    onResize() {
        if (this.resizeTimer) clearTimeout(this.resizeTimer);
        this.resizeTimer = setTimeout(() => {
            this.renderSegments();
        }, 100);
    }
}

if (typeof customElements !== "undefined") {
    customElements.define("mono-topic-rail", MonoTopicRail);
}
