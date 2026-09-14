class MonoCompare extends MonoBaseElement {
    constructor() {
        super();
    }

    connectedCallback() {
        this.mountTemplate("template-mono-compare");
        this.resolveMode();
        this.resolveGap();
    }

    resolveGap() {
        const gap = this.getAttribute("gap");
        if (gap && !["item", "group", "flow", "none"].includes(gap.toLowerCase())) {
            this.style.setProperty("--compare-custom-gap", gap);
        }
    }

    resolveMode() {
        if (!this.getAttribute("mode")) {
            // スロット内の子要素数をカウントして自動判別
            const children = Array.from(this.children).filter(
                (el) => el.nodeType === Node.ELEMENT_NODE
            );
            if (children.length === 2) {
                this.setAttribute("mode", "2");
            } else if (children.length === 3) {
                this.setAttribute("mode", "3");
            } else {
                this.setAttribute("mode", "2");
            }
        }
    }
}

if (typeof customElements !== "undefined") {
    customElements.define("mono-compare", MonoCompare);
}
