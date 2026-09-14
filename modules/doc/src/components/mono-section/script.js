class MonoSection extends MonoBaseElement {
    constructor() {
        super();
        this.mountTemplate('mono-section-template');
    }

    connectedCallback() {
        const container = this.shadowRoot.getElementById('section-container');
        if (!container) return;

        // Apply background image
        const image = this.getAttribute('image');
        if (image) {
            this.style.setProperty('--section-bg-image', `url('${image}')`);
            container.style.backgroundImage = `url('${image}')`;
        }

        // Apply background mode (cover, fit/contain)
        const mode = this.getAttribute('mode');
        if (mode === 'fit' || mode === 'contain') {
            this.style.setProperty('--section-bg-mode', 'contain');
            container.style.backgroundSize = 'contain';
        } else {
            this.style.setProperty('--section-bg-mode', 'cover');
            container.style.backgroundSize = 'cover';
        }

        // Apply background color
        const bgColor = this.getAttribute('bg-color');
        if (bgColor) {
            this.style.setProperty('--section-bg-color', bgColor);
            container.style.backgroundColor = bgColor;
        }

        // Apply text color
        const textColor = this.getAttribute('text-color');
        if (textColor) {
            this.style.setProperty('--section-text-color', textColor);
            container.style.color = textColor;
        }

        // Apply height
        const height = this.getAttribute('height');
        if (height) {
            if (!isNaN(height)) {
                this.style.setProperty('--section-height', height + "px");
                container.style.minHeight = height + "px";
            } else {
                this.style.setProperty('--section-height', height);
                container.style.minHeight = height;
            }
        }
    }
}

customElements.define('mono-section', MonoSection);
