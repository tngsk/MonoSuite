class MonoIcon extends MonoBaseElement {
    constructor() {
        super();
    }

    connectedCallback() {
        // Clone the template
        this.mountTemplate('mono-icon-template');

        const iconSpan = this.shadowRoot.querySelector('.material-symbols-outlined');
        const name = this.getAttribute('name');
        if (name && iconSpan) {
            iconSpan.textContent = name;
        }

        // Apply styles based on attributes
        const size = this.getAttribute('size');
        if (size) {
            if (!isNaN(size)) {
                this.style.fontSize = size + "px";
            } else {
                this.style.fontSize = size;
            }
        }

        const color = this.getAttribute('color');
        if (color) {
            this.style.color = color;
        }

        const display = this.getAttribute('display');
        if (display && display !== "block" && display !== "inline") {
            this.style.display = display;
        }
    }
}

// Register the custom element
if (!customElements.get('mono-icon')) {
    customElements.define('mono-icon', MonoIcon);
}
