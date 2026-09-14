class MonoTextfieldInput extends MonoInteractiveElement {
    constructor() {
        super();
        this.placeholder = this.getAttribute("placeholder") || "";
        this.size = this.getAttribute("size");
        this.label = this.getAttribute("label");
        this.inputId = this.getAttribute("id") || `textfield-${Math.random().toString(36).substr(2, 9)}`;
        this.debounceTimeout = null;
        this.storageUnavailable = false;
    }

    connectedCallback() {
        if (super.connectedCallback) {
            super.connectedCallback();
        }
        this.mountTemplate();
        this.setupEventListeners();
        this.restoreData();
    }

    mountTemplate() {
        super.mountTemplate('mono-textfield-input-template');
        this.inputArea = this.shadowRoot.getElementById("textfield");
        this.inputArea.placeholder = this.placeholder;

        this.labelElement = this.shadowRoot.getElementById("textfield-label");
        if (this.label) {
            this.labelElement.textContent = this.label;
        } else {
            this.labelElement.style.display = 'none';
        }

        if (this.size) {
            this.inputArea.setAttribute("size", this.size);
            // Size specifies character width, adjust style to allow sizing
            this.inputArea.style.width = "auto";
            const container = this.shadowRoot.querySelector(".mono-textfield-container");
            if (container) {
                container.style.width = "auto";
                container.style.maxWidth = "none";
            }
        }
        this.statusIndicator = this.shadowRoot.querySelector("[data-ref='statusIndicator']");

        try {
            const testKey = '__storage_test__';
            this.saveState(testKey, testKey);
            this.removeState(testKey);
        } catch (e) {
            this.storageUnavailable = true;
            console.warn("Local Storage is not available. Input will not be persisted.", e);
        }
    }

    setupEventListeners() {
        if (this.inputArea) {
            this.inputArea.addEventListener("input", () => this.handleInput());
        }
    }

    getPageId() {
        return window.location.pathname || 'default-page';
    }

    getStorageKey() {
        // Prefix must be mono_ for mono-export to pick it up
        return `mono_textfield::${this.getPageId()}::${this.inputId}`;
    }

    restoreData() {
        if (this.storageUnavailable || !this.inputArea) return;
        try {
            const data = this.loadState(this.getStorageKey());
            if (data && data.value !== undefined) {
                this.inputArea.value = data.value;
            }
        } catch (e) {
            console.error("Failed to restore textfield data", e);
        }
    }

    handleInput() {
        if (this.storageUnavailable) return;
        if (this.debounceTimeout) {
            clearTimeout(this.debounceTimeout);
        }
        this.debounceTimeout = setTimeout(() => {
            this.saveData();
        }, 500);
    }

    saveData() {
        if (!this.inputArea) return;
        const value = this.inputArea.value;
        const data = {
            id: this.inputId,
            placeholder: this.placeholder,
            value: value,
            updated_at: new Date().toISOString()
        };
        try {
            this.saveState(this.getStorageKey(), data);
            this.showSaveFeedback();
        } catch (e) {
            console.error("Failed to save textfield data", e);
        }
    }

    showSaveFeedback() {
        if (!this.statusIndicator) return;
        this.statusIndicator.textContent = "✓ Saved";
        this.statusIndicator.classList.remove("error");
        this.statusIndicator.classList.add("visible");
        setTimeout(() => {
            this.statusIndicator.classList.remove("visible");
        }, 2000);
    }
}

if (!customElements.get("mono-textfield-input")) {
    customElements.define("mono-textfield-input", MonoTextfieldInput);
}
