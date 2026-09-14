class MonoDice extends MonoInteractiveElement {
    constructor() {
        super();

        const facesAttr = this.getAttribute("faces") || this.getAttribute("number");
        this.faces = facesAttr ? parseInt(facesAttr, 10) : 6;
        if (isNaN(this.faces) || this.faces < 2) {
            this.faces = 6;
        }

        this.isRolling = false;
    }

    connectedCallback() {
        super.mountTemplate('mono-dice-template');
        
        // Add accessibility attributes
        if (this.refs.dice) {
            this.refs.dice.setAttribute('role', 'button');
            this.refs.dice.setAttribute('tabindex', '0');
            this.refs.dice.setAttribute('aria-label', `Roll ${this.faces}-sided dice`);
            this.refs.dice.setAttribute('aria-live', 'polite');
            
            // Add keyboard support (Enter/Space to roll)
            this.refs.dice.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.roll();
                }
            });
        }
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        if (this.refs.dice) {
            this.refs.dice.addEventListener("click", () => this.roll());
        }
    }

    roll() {
        if (this.isRolling) return;
        this.isRolling = true;

        if (this.refs.dice) {
            this.refs.dice.classList.add("rolling");
            this.refs.dice.setAttribute('aria-label', `Rolling dice...`);
        }

        if (this.refs.number) {
            this.refs.number.textContent = "?";
        }

        let rollInterval = setInterval(() => {
            if (this.refs.number) {
                this.refs.number.textContent = Math.floor(Math.random() * this.faces) + 1;
            }
        }, 100);

        setTimeout(() => {
            clearInterval(rollInterval);
            this.isRolling = false;

            const result = Math.floor(Math.random() * this.faces) + 1;

            if (this.refs.dice) {
                this.refs.dice.classList.remove("rolling");
                this.refs.dice.setAttribute('aria-label', `Rolled ${result} on a ${this.faces}-sided dice`);
            }
            if (this.refs.number) {
                this.refs.number.textContent = result;
            }
        }, 800);
    }
}

if (!customElements.get("mono-dice")) {
    customElements.define("mono-dice", MonoDice);
}
