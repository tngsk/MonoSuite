class MonoCountdown extends MonoBaseElement {
    constructor() {
        super();
        this._intervalId = null;
        this.totalSeconds = 0;
        this.remainingSeconds = 0;
        this.circle = null;
        this.circumference = 0;
    }

    connectedCallback() {
        this.mountTemplate('mono-countdown-template');

        this.timeDisplayElement = this.shadowRoot.querySelector('.time-display');
        this.circle = this.shadowRoot.querySelector('.progress-ring-circle');

        // Add accessibility attributes
        this.setAttribute('role', 'timer');
        this.setAttribute('aria-live', 'off'); // 'off' so it doesn't spam screen readers on tick
        
        if (this.circle) {
            const radius = this.circle.r.baseVal.value;
            this.circumference = radius * 2 * Math.PI;
            this.circle.style.strokeDasharray = `${this.circumference} ${this.circumference}`;
            this.circle.style.strokeDashoffset = this.circumference;
        }

        const color = this.getAttribute('color');
        if (color) {
            this.style.setProperty('--countdown-color', color);
        }

        const timeStr = this.getAttribute('time');
        this.totalSeconds = this.parseTime(timeStr);
        this.remainingSeconds = this.totalSeconds;

        this.updateDisplay();

        if (this.totalSeconds > 0) {
            this.startCountdown();
        } else {
            this.handleTimeUp();
        }
    }

    disconnectedCallback() {
        if (this._intervalId) {
            clearInterval(this._intervalId);
            this._intervalId = null;
        }
    }

    parseTime(timeStr) {
        if (!timeStr) return 0;

        // Check if it's an absolute datetime (e.g., ISO string)
        const date = new Date(timeStr);
        if (!isNaN(date.getTime()) && timeStr.includes('-')) {
            const remaining = Math.max(0, Math.floor((date.getTime() - Date.now()) / 1000));
            return remaining;
        }

        const match = timeStr.trim().match(/^(\d+)(s|m|h)?$/i);
        if (!match) return 0;

        const value = parseInt(match[1], 10);
        const unit = match[2] ? match[2].toLowerCase() : 's';

        switch (unit) {
            case 'h': return value * 3600;
            case 'm': return value * 60;
            case 's':
            default: return value;
        }
    }

    formatTime(seconds) {
        if (seconds < 0) seconds = 0;

        const d = Math.floor(seconds / 86400);
        const h = Math.floor((seconds % 86400) / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;

        if (d > 0) {
            return `${d}d ${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        }
        if (h > 0) {
            return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        }
        return `${m}:${String(s).padStart(2, '0')}`;
    }

    updateDisplay() {
        if (this.timeDisplayElement) {
            const formatted = this.formatTime(this.remainingSeconds);
            this.timeDisplayElement.textContent = formatted;
            this.setAttribute('aria-label', `Time remaining: ${formatted}`);
            
            if (this.remainingSeconds >= 86400) {
                this.classList.add('has-days');
            } else {
                this.classList.remove('has-days');
            }
        }

        if (this.circle && this.totalSeconds > 0) {
            const progress = this.remainingSeconds / this.totalSeconds;
            const offset = this.circumference - (progress * this.circumference);
            this.circle.style.strokeDashoffset = offset;
        }
    }

    startCountdown() {
        if (this._intervalId) return;

        const endTime = Date.now() + (this.remainingSeconds * 1000);

        this._intervalId = setInterval(() => {
            const now = Date.now();
            this.remainingSeconds = Math.max(0, Math.ceil((endTime - now) / 1000));

            if (this.remainingSeconds <= 0) {
                this.remainingSeconds = 0;
                this.updateDisplay();
                this.handleTimeUp();
            } else {
                this.updateDisplay();
            }
        }, 1000);
    }

    handleTimeUp() {
        if (this._intervalId) {
            clearInterval(this._intervalId);
            this._intervalId = null;
        }
        this.classList.add('time-up');
        this.setAttribute('aria-label', 'Time is up');
        // Announce time up to screen readers explicitly
        this.setAttribute('aria-live', 'assertive');
        
        // Dispatch an event so other components can react
        this.dispatchEvent(new CustomEvent('timeup', { bubbles: true, composed: true }));
    }
}

if (!customElements.get('mono-countdown')) {
    customElements.define('mono-countdown', MonoCountdown);
}
