class MonoClock extends MonoBaseElement {
    constructor() {
        super();
        this._intervalId = null;
    }

    connectedCallback() {
        this.mountTemplate('mono-clock-template');

        this.clockElement = this.shadowRoot.querySelector('.clock-display');
        this.analogClockElement = this.shadowRoot.querySelector('.analog-clock');
        this.hourHand = this.shadowRoot.querySelector('.hour-hand');
        this.minuteHand = this.shadowRoot.querySelector('.minute-hand');
        this.secondHand = this.shadowRoot.querySelector('.second-hand');

        // Add accessibility attributes
        this.setAttribute('role', 'timer');
        this.setAttribute('aria-live', 'off'); // 'off' to avoid spamming screen readers every second

        const displayType = this.getAttribute('display');
        this.isAnalog = displayType === 'analog';

        if (this.isAnalog) {
            this.clockElement.classList.add('hidden');
            this.analogClockElement.classList.remove('hidden');
        } else {
            this.analogClockElement.classList.add('hidden');
            this.clockElement.classList.remove('hidden');
            if (displayType && displayType !== "block" && displayType !== "inline" && displayType !== "digital") {
                this.style.display = displayType;
            }
        }

        this.format = this.getAttribute('format') || 'HH:mm:ss';

        this.updateClock();
        this._intervalId = setInterval(() => this.updateClock(), 1000);
    }

    disconnectedCallback() {
        if (this._intervalId) {
            clearInterval(this._intervalId);
            this._intervalId = null;
        }
    }

    updateClock() {
        const now = new Date();
        const seconds = now.getSeconds();
        const minutes = now.getMinutes();
        const hours = now.getHours();
        
        // Update aria-label for accessibility regardless of mode
        const ampm = hours >= 12 ? 'PM' : 'AM';
        const hours12 = hours % 12 || 12;
        this.setAttribute('aria-label', `Current time is ${hours12}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')} ${ampm}`);

        if (this.isAnalog) {
            if (!this.hourHand || !this.minuteHand || !this.secondHand) return;

            const secondDegrees = (seconds / 60) * 360;
            const minuteDegrees = ((minutes + seconds / 60) / 60) * 360;
            const hourDegrees = ((hours % 12 + minutes / 60) / 12) * 360;

            this.secondHand.setAttribute('transform', `rotate(${secondDegrees} 50 50)`);
            this.minuteHand.setAttribute('transform', `rotate(${minuteDegrees} 50 50)`);
            this.hourHand.setAttribute('transform', `rotate(${hourDegrees} 50 50)`);

        } else {
            if (!this.clockElement) return;

            const tokens = {
                'YYYY': now.getFullYear(),
                'YY': String(now.getFullYear()).slice(-2),
                'MM': String(now.getMonth() + 1).padStart(2, '0'),
                'DD': String(now.getDate()).padStart(2, '0'),
                'HH': String(hours).padStart(2, '0'),
                'mm': String(minutes).padStart(2, '0'),
                'ss': String(seconds).padStart(2, '0')
            };

            let output = this.format;
            for (const [key, value] of Object.entries(tokens)) {
                output = output.replace(new RegExp(key, 'g'), value);
            }

            this.clockElement.textContent = output;
        }
    }
}

if (!customElements.get('mono-clock')) {
    customElements.define('mono-clock', MonoClock);
}
