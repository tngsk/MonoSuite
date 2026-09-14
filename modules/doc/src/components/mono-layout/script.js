class MonoLayout extends MonoBaseElement {
    constructor() {
        super();
        this.mountTemplate('mono-layout-template');
        this.wrapper = this.shadowRoot.querySelector('.layout-wrapper');
    }

    connectedCallback() {
        // Apply classes from class attribute to the wrapper
        if (this.hasAttribute('class')) {
            const classes = this.getAttribute('class').split(/\s+/);
            for (const c of classes) {
                if (c) {
                    this.wrapper.classList.add(c);
                }
            }
        }
    }

    static get observedAttributes() {
        return ['class'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'class' && oldValue !== newValue) {
            // Remove old classes
            if (oldValue) {
                const oldClasses = oldValue.split(/\s+/);
                for (const c of oldClasses) {
                    if (c) {
                        this.wrapper.classList.remove(c);
                    }
                }
            }
            // Add new classes
            if (newValue) {
                const newClasses = newValue.split(/\s+/);
                for (const c of newClasses) {
                    if (c) {
                        this.wrapper.classList.add(c);
                    }
                }
            }
        }
    }
}

customElements.define("mono-layout", MonoLayout);
