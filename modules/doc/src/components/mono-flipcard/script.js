class MonoFlipcard extends MonoBaseElement {
    constructor() {
        super();
        this.toggleFlip = this.toggleFlip.bind(this);
    }

    connectedCallback() {
        this.mountTemplate('mono-flipcard-template');

        const frontText = this.getAttribute("front") || "";
        const backText = this.getAttribute("back") || "";

        const frontEl = this.shadowRoot.getElementById("front-text");
        const backEl = this.shadowRoot.getElementById("back-text");

        if (frontEl) frontEl.textContent = frontText;
        if (backEl) backEl.textContent = backText;

        // Accessibility attributes
        this.setAttribute('role', 'button');
        this.setAttribute('tabindex', '0');
        this.setAttribute('aria-pressed', this.hasAttribute('flipped') ? 'true' : 'false');
        
        // Add keyboard support (Enter/Space to flip)
        this.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggleFlip();
            }
        });

        this.addEventListener('click', this.toggleFlip);
    }

    disconnectedCallback() {
        this.removeEventListener('click', this.toggleFlip);
    }

    toggleFlip() {
        if (this.hasAttribute('flipped')) {
            this.removeAttribute('flipped');
            this.setAttribute('aria-pressed', 'false');
        } else {
            this.setAttribute('flipped', '');
            this.setAttribute('aria-pressed', 'true');
        }
    }
}

if (!customElements.get("mono-flipcard")) {
    customElements.define("mono-flipcard", MonoFlipcard);
}
