class MonoSound extends MonoBaseElement {
  constructor() {
    super();
    this.mountTemplate('mono-sound-template');

    this.audio = this.shadowRoot.querySelector(".mono-sound-audio");
    this.playBtn = this.shadowRoot.querySelector(".mono-sound-play-btn");
    this.labelEl = this.shadowRoot.querySelector(".mono-sound-label");
    this.iconPlay = this.shadowRoot.querySelector(".mono-sound-icon-play");
    this.iconPause = this.shadowRoot.querySelector(".mono-sound-icon-pause");

    this.isPlaying = false;
  }

  connectedCallback() {
    const label = this.getAttribute("label");
    if (label && this.labelEl) {
      this.labelEl.textContent = label;
      // Add more descriptive ARIA label if a text label is provided
      if (this.playBtn) {
        this.playBtn.setAttribute("aria-label", `Play ${label}`);
      }
    }

    const rawSrc = this.getAttribute("src");
    if (rawSrc && this.audio) {
      const isValidUrl = (url) => {
        if (!url || typeof url !== 'string') return false;
        try {
            const parsed = new URL(url, window.location.href);
            const protocol = parsed.protocol.toLowerCase();
            return ['http:', 'https:', 'data:'].includes(protocol);
        } catch (e) {
            return false;
        }
      };

      // Handle asset-store logic
      if (rawSrc.startsWith("asset-")) {
        const store = document.getElementById("mono-asset-store");
        if (store) {
          try {
            const assets = JSON.parse(store.textContent);
            if (assets[rawSrc] && isValidUrl(assets[rawSrc])) {
              this.audio.src = assets[rawSrc];
            }
          } catch (e) {
            console.error("Asset store parse error in mono-sound:", e);
          }
        }
      } else if (isValidUrl(rawSrc)) {
        this.audio.src = rawSrc;
      }
    }

    if (this.playBtn && this.audio) {
      this.playBtn.addEventListener("click", () => this.togglePlay());
      this.audio.addEventListener("ended", () => this.onEnded());
      this.audio.addEventListener("pause", () => this.onPause());
      this.audio.addEventListener("play", () => this.onPlay());
      
      // Accessibility improvements
      this.playBtn.setAttribute('role', 'button');
      this.playBtn.setAttribute('aria-pressed', 'false');
    }
  }

  togglePlay() {
    if (this.audio.paused) {
      this.audio.play().catch(e => console.error("Audio playback failed:", e));
    } else {
      this.audio.pause();
    }
  }

  onPlay() {
    this.isPlaying = true;
    if (this.iconPlay) this.iconPlay.style.display = "none";
    if (this.iconPause) this.iconPause.style.display = "block";
    if (this.playBtn) {
        this.playBtn.setAttribute('aria-pressed', 'true');
        const label = this.getAttribute("label");
        this.playBtn.setAttribute("aria-label", label ? `Pause ${label}` : "Pause sound");
    }
  }

  onPause() {
    this.isPlaying = false;
    if (this.iconPlay) this.iconPlay.style.display = "block";
    if (this.iconPause) this.iconPause.style.display = "none";
    if (this.playBtn) {
        this.playBtn.setAttribute('aria-pressed', 'false');
        const label = this.getAttribute("label");
        this.playBtn.setAttribute("aria-label", label ? `Play ${label}` : "Play sound");
    }
  }

  onEnded() {
    this.onPause();
    this.audio.currentTime = 0;
  }
}

customElements.define("mono-sound", MonoSound);
