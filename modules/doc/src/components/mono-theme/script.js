class MonoTheme extends MonoBaseElement {
    constructor() {
        super();

        this.mountTemplate('mono-theme-template');

        this.container = this.shadowRoot.querySelector('.theme-switcher-container');
        this.select = this.shadowRoot.querySelector('#theme-select');

        this.btnDecrease = this.shadowRoot.querySelector('#font-size-decrease');
        this.btnReset = this.shadowRoot.querySelector('#font-size-reset');
        this.btnIncrease = this.shadowRoot.querySelector('#font-size-increase');

        this.defaultFontSize = 16;
        this.currentFontSize = this.defaultFontSize;
        this.minFontSize = 8;
        this.maxFontSize = 96;
        this.stepSize = 2;
    }

    connectedCallback() {
        const theme = this.getAttribute('theme') || 'light';
        const showUi = this.getAttribute('show-ui') === 'true';
        const fontSizeAttr = this.getAttribute('font-size');

        // Apply theme to the whole document
        document.documentElement.setAttribute('data-theme', theme);

        // Handle initial font size
        if (fontSizeAttr) {
            const parsedSize = parseInt(fontSizeAttr, 10);
            if (!isNaN(parsedSize)) {
                this.currentFontSize = Math.min(Math.max(parsedSize, this.minFontSize), this.maxFontSize);
                this.updateFontSize();
            }
        }

        if (showUi) {
            this.container.classList.remove('hidden');
            if (this.select) {
                this.select.value = theme;
                this.select.addEventListener('change', (e) => {
                    document.documentElement.setAttribute('data-theme', e.target.value);
                });
            }

            // Setup font size controls
            if (this.btnDecrease) {
                this.btnDecrease.addEventListener('click', () => {
                    this.currentFontSize = Math.max(this.minFontSize, this.currentFontSize - this.stepSize);
                    this.updateFontSize();
                });
            }

            if (this.btnReset) {
                this.btnReset.addEventListener('click', () => {
                    this.currentFontSize = this.defaultFontSize;
                    this.updateFontSize();
                });
            }

            if (this.btnIncrease) {
                this.btnIncrease.addEventListener('click', () => {
                    this.currentFontSize = Math.min(this.maxFontSize, this.currentFontSize + this.stepSize);
                    this.updateFontSize();
                });
            }
        }
    }

    updateFontSize() {
        document.documentElement.style.fontSize = `${this.currentFontSize}px`;
    }
}

if (!customElements.get('mono-theme')) {
    customElements.define('mono-theme', MonoTheme);
}
