/**
 * Mono Components
 *
 * Vanilla JS Web Component for Universal A/B Testing.
 * Uses Web Audio API with crossfading for seamless, pop-free switching.
 * Implements "Lab-Gear Aesthetic" and strict event-driven architecture.
 */

class MonoABTest extends MonoInteractiveElement {
  constructor() {
    super();

    // Component State
    this.title = this.getAttribute("title") || "A/B Test";
    this.srcA = this.getAttribute("src-a") || "";
    this.srcB = this.getAttribute("src-b") || "";
    this.componentId =
      this.getAttribute("id") ||
      `abtest-${Math.random().toString(36).substring(2, 9)}`;

    // Playback State
    this.audioContext = null;
    this.audioBufferA = null;
    this.audioBufferB = null;
    this.sourceNodeA = null;
    this.sourceNodeB = null;
    this.gainNodeA = null;
    this.gainNodeB = null;

    this.isPlaying = false;
    this.mediaType = "audio"; // Default to audio, update if image is detected
    this.currentTrack = "A"; // 'A' or 'B'
    this.startTime = 0;
    this.pauseOffset = 0;
    this.duration = 0;
    this.animationFrameId = null;

    // Vote State
    this.hasVoted = false;

    // Cache for DOM references

    this.handleKeyDown = this.handleKeyDown.bind(this);

    // Accessibility & Focus Management
    this.setAttribute("tabindex", "0");
    this.setAttribute("role", "region");
    this.setAttribute("aria-label", "Audio A/B Test Player");
  }


  connectedCallback() {
    if (super.connectedCallback) {
        super.connectedCallback();
    }
    this.mountTemplate();

    this.title = this.getAttribute("title") || "A/B Test";
    if (this.refs.title) this.refs.title.textContent = this.title;

    this.srcA = this.getAttribute("src-a");
    this.srcB = this.getAttribute("src-b");

    if (this.srcA && this.srcA.startsWith("data:")) {
      if (this.srcA.includes("image/")) {
         this.mediaType = "image";
      } else {
         this.mediaType = "audio";
      }
    } else if (this.srcA) {
      const ext = this.srcA.split('.').pop().toLowerCase();
      if (["mp3", "wav", "ogg", "flac", "aac", "m4a"].includes(ext)) {
        this.mediaType = "audio";
      } else {
        this.mediaType = "image";
      }
    }

    this.setupMediaElements();
    this.checkPreviousVote();
    this.setupEventListeners();

    this.addEventListener("keydown", this.handleKeyDown);

    this.addEventListener("click", () => {
      if (document.activeElement !== this) {
        this.focus();
      }
    });
  }

  setupMediaElements() {
     if (this.mediaType === "image") {
         const imgContainer = document.createElement("div");
         imgContainer.style.position = "relative";
         imgContainer.style.width = "100%";
         imgContainer.style.height = "400px";
         imgContainer.style.overflow = "hidden";
         imgContainer.style.marginBottom = "1rem";
         imgContainer.style.borderRadius = "8px";
         imgContainer.style.backgroundColor = "#e5e7eb";

         const imgA = document.createElement("img");
         imgA.src = this.srcA;
         imgA.style.position = "absolute";
         imgA.style.top = "0";
         imgA.style.left = "0";
         imgA.style.width = "100%";
         imgA.style.height = "100%";
         imgA.style.objectFit = "contain";
         imgA.style.transition = "opacity 0.2s ease";
         imgA.style.opacity = "1";
         this.imgA = imgA;

         const imgB = document.createElement("img");
         imgB.src = this.srcB;
         imgB.style.position = "absolute";
         imgB.style.top = "0";
         imgB.style.left = "0";
         imgB.style.width = "100%";
         imgB.style.height = "100%";
         imgB.style.objectFit = "contain";
         imgB.style.transition = "opacity 0.2s ease";
         imgB.style.opacity = "0";
         this.imgB = imgB;

         imgContainer.appendChild(imgB);
         imgContainer.appendChild(imgA);

         this.refs.title.insertAdjacentElement("afterend", imgContainer);

         if (this.refs.playBtn) this.refs.playBtn.style.display = "none";
         if (this.refs.stopBtn) this.refs.stopBtn.style.display = "none";
         if (this.refs.timeDisplay) this.refs.timeDisplay.style.display = "none";
         if (this.refs.progressContainer) this.refs.progressContainer.style.display = "none";
         if (this.refs.statusLed) this.refs.statusLed.style.display = "none";
         if (this.refs.loadingOverlay) this.refs.loadingOverlay.style.display = "none";

         if (this.refs.switchA) this.refs.switchA.disabled = false;
         if (this.refs.switchB) this.refs.switchB.disabled = false;
     }
  }

  disconnectedCallback() {
    this.stopPlayback();
    if (this.audioContext) {
      this.audioContext.close();
    }
    this.removeEventListener("keydown", this.handleKeyDown);
  }

  // ============================================================================
  // Initialization & Rendering
  // ============================================================================

  mountTemplate() {
        super.mountTemplate('mono-ab-test-template');
        // Cache references

    if (this.refs.title) {
      this.refs.title.textContent = this.title;
    }
  }

  checkPreviousVote() {
    try {
      const data = this.loadState(`mono_abtest_${this.componentId}`);
      if (data && data.selected) {
        this.hasVoted = true;
        this.updateVoteUI(data.selected);
      }
    } catch (e) {
      console.warn("Failed to read from localStorage:", e);
    }
  }

  setupEventListeners() {
    // Lazy Load: Initialize AudioContext and load files on first interaction
    const initOnFirstClick = async () => {
      if (this.mediaType === "audio" && !this.audioContext) {
        await this.initializeAudioEngine();
      }
    };

    // Transport Controls
    if (this.refs.playBtn) {
      // Enable play button initially to trigger lazy load
      this.refs.playBtn.disabled = false;
      this.refs.playBtn.title = "Play / Pause (Press 'Space')";
      this.refs.playBtn.addEventListener("click", async () => {
        await initOnFirstClick();
        this.togglePlayPause();
      });
    }

    if (this.refs.stopBtn) {
      this.refs.stopBtn.addEventListener("click", () => this.stopPlayback());
    }

    // Switch Controls
    if (this.refs.switchA) {
      this.refs.switchA.title = "Switch to A (Press 'A' key)";
      this.refs.switchA.addEventListener("click", async () => {
        await initOnFirstClick();
        this.switchTrack("A");
      });
    }
    if (this.refs.switchB) {
      this.refs.switchB.title = "Switch to B (Press 'B' key)";
      this.refs.switchB.addEventListener("click", async () => {
        await initOnFirstClick();
        this.switchTrack("B");
      });
    }

    // Vote Controls
    const voteButtons = ["voteA", "voteNeutral", "voteB"];
    voteButtons.forEach((refName) => {
      if (this.refs[refName]) {
        this.refs[refName].addEventListener("click", (e) => {
          if (!this.hasVoted) {
            this.saveVote(e.target.dataset.vote);
          }
        });
      }
    });
  }

  async handleKeyDown(event) {
    // Prevent interfering if an input inside shadow DOM is focused
    const activeEl = this.shadowRoot.activeElement;
    if (
      activeEl &&
      (activeEl.tagName === "INPUT" || activeEl.tagName === "TEXTAREA")
    ) {
      return;
    }

    const key = event.key.toLowerCase();

    if (key === "a") {
      event.preventDefault();
      if (this.mediaType === "audio" && !this.audioContext) await this.initializeAudioEngine();
      this.switchTrack("A");
    } else if (key === "b") {
      event.preventDefault();
      if (this.mediaType === "audio" && !this.audioContext) await this.initializeAudioEngine();
      this.switchTrack("B");
    } else if (key === " " && this.mediaType === "audio") {
      event.preventDefault(); // Prevent page scroll
      if (!this.audioContext) await this.initializeAudioEngine();
      this.togglePlayPause();
    }
  }

  // ============================================================================
  // Audio Engine (Web Audio API)
  // ============================================================================

  async initializeAudioEngine() {
    if (this.refs.loadingOverlay) {
      this.refs.loadingOverlay.classList.add("is-loading");
    }

    try {
      this.audioContext = new (
        window.AudioContext || window.webkitAudioContext
      )();

      // Fetch and decode both files concurrently
      const [bufferA, bufferB] = await Promise.all([
        this.loadAudioFile(this.srcA),
        this.loadAudioFile(this.srcB),
      ]);

      this.audioBufferA = bufferA;
      this.audioBufferB = bufferB;

      // Use the longer duration for the progress bar
      this.duration = Math.max(bufferA.duration, bufferB.duration);

      // Enable UI controls
      if (this.refs.switchA) this.refs.switchA.disabled = false;
      if (this.refs.switchB) this.refs.switchB.disabled = false;
      if (this.refs.stopBtn) this.refs.stopBtn.disabled = false;

      this.updateTimeDisplay();
    } catch (error) {
      console.error("Audio Initialization Error:", error);
      if (this.refs.errorMessage) {
        this.refs.errorMessage.classList.remove("hidden");
      }
      if (this.refs.playBtn) this.refs.playBtn.disabled = true;
    } finally {
      if (this.refs.loadingOverlay) {
        this.refs.loadingOverlay.classList.remove("is-loading");
      }
    }
  }

  async loadAudioFile(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const arrayBuffer = await response.arrayBuffer();
    return await this.audioContext.decodeAudioData(arrayBuffer);
  }

  createSourceAndGains() {
    // Create dual sources for simultaneous playback (perfect sync)
    this.sourceNodeA = this.audioContext.createBufferSource();
    this.sourceNodeA.buffer = this.audioBufferA;

    this.sourceNodeB = this.audioContext.createBufferSource();
    this.sourceNodeB.buffer = this.audioBufferB;

    // Create gain nodes for crossfading
    this.gainNodeA = this.audioContext.createGain();
    this.gainNodeB = this.audioContext.createGain();

    // Initial volumes based on current track
    this.gainNodeA.gain.value = this.currentTrack === "A" ? 1 : 0;
    this.gainNodeB.gain.value = this.currentTrack === "B" ? 1 : 0;

    // Connect routing: Source -> Gain -> Destination
    this.sourceNodeA.connect(this.gainNodeA);
    this.gainNodeA.connect(this.audioContext.destination);

    this.sourceNodeB.connect(this.gainNodeB);
    this.gainNodeB.connect(this.audioContext.destination);

    // Event listener for end of track
    this.sourceNodeA.onended = () => {
      // Only reset if it naturally ended (not manually stopped)
      if (this.isPlaying && this.getCurrentTime() >= this.duration - 0.1) {
        this.stopPlayback();
      }
    };
  }

  // ============================================================================
  // Playback Controls
  // ============================================================================

  togglePlayPause() {
    if (this.audioContext.state === "suspended") {
      this.audioContext.resume();
    }

    if (this.isPlaying) {
      // Pause
      if (this.sourceNodeA) this.sourceNodeA.stop();
      if (this.sourceNodeB) this.sourceNodeB.stop();
      this.pauseOffset = this.getCurrentTime();
      this.isPlaying = false;
    this.mediaType = "audio"; // Default to audio, update if image is detected
      this.updateTransportUI();
      cancelAnimationFrame(this.animationFrameId);
    } else {
      // Play
      // If we reached the end, reset to beginning
      if (this.pauseOffset >= this.duration) {
        this.pauseOffset = 0;
      }

      this.createSourceAndGains();
      this.sourceNodeA.start(0, this.pauseOffset);
      this.sourceNodeB.start(0, this.pauseOffset);
      this.startTime = this.audioContext.currentTime - this.pauseOffset;
      this.isPlaying = true;
      this.updateTransportUI();
      this.animationFrameId = requestAnimationFrame(() =>
        this.updateProgress(),
      );
    }
  }

  stopPlayback() {
    if (this.isPlaying) {
      if (this.sourceNodeA) this.sourceNodeA.stop();
      if (this.sourceNodeB) this.sourceNodeB.stop();
    }
    this.isPlaying = false;
    this.mediaType = "audio"; // Default to audio, update if image is detected
    this.pauseOffset = 0;
    this.updateTransportUI();
    this.updateProgress(true); // Force reset to 0
    cancelAnimationFrame(this.animationFrameId);
  }

  switchTrack(track) {
    if (this.currentTrack === track) return;
    this.currentTrack = track;

    // Update UI
    if (this.refs.switchA) {
      this.refs.switchA.classList.toggle("active", track === "A");
    }
    if (this.refs.switchB) {
      this.refs.switchB.classList.toggle("active", track === "B");
    }

if (this.mediaType === "image") {
        if (track === "A") {
            this.imgA.style.opacity = "1";
            this.imgB.style.opacity = "0";
        } else {
            this.imgA.style.opacity = "0";
            this.imgB.style.opacity = "1";
        }
    } else if (this.mediaType === "audio") {
        // Apply Crossfade (Pop-noise prevention)
        // 20ms linear ramp for seamless transition
        if (this.isPlaying && this.gainNodeA && this.gainNodeB) {
            const now = this.audioContext.currentTime;
            const fadeDuration = 0.02; // 20ms

            this.gainNodeA.gain.cancelScheduledValues(now);
            this.gainNodeB.gain.cancelScheduledValues(now);

            if (track === "A") {
                this.gainNodeA.gain.linearRampToValueAtTime(1, now + fadeDuration);
                this.gainNodeB.gain.linearRampToValueAtTime(0, now + fadeDuration);
            } else {
                this.gainNodeA.gain.linearRampToValueAtTime(0, now + fadeDuration);
                this.gainNodeB.gain.linearRampToValueAtTime(1, now + fadeDuration);
            }
        }
    }
  }

  // ============================================================================
  // UI & Progress Updates
  // ============================================================================

  getCurrentTime() {
    if (this.isPlaying) {
      return this.audioContext.currentTime - this.startTime;
    }
    return this.pauseOffset;
  }

  updateProgress(forceReset = false) {
    const currentTime = forceReset ? 0 : this.getCurrentTime();
    let percentage = 0;

    if (this.duration > 0) {
      percentage = Math.min((currentTime / this.duration) * 100, 100);
    }

    if (this.refs.progressBar) {
      this.refs.progressBar.style.width = `${percentage}%`;
    }

    this.updateTimeDisplay(currentTime);

    if (this.isPlaying && percentage < 100) {
      this.animationFrameId = requestAnimationFrame(() =>
        this.updateProgress(),
      );
    }
  }

  updateTimeDisplay(currentTime = 0) {
    if (!this.refs.timeDisplay) return;

    const formatTime = (time) => {
      const mins = Math.floor(time / 60);
      const secs = Math.floor(time % 60);
      return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    };

    this.refs.timeDisplay.textContent = `${formatTime(currentTime)} / ${formatTime(this.duration)}`;
  }

  updateTransportUI() {
    if (this.refs.iconPlay && this.refs.iconPause) {
      if (this.isPlaying) {
        this.refs.iconPlay.classList.add("hidden");
        this.refs.iconPause.classList.remove("hidden");
      } else {
        this.refs.iconPlay.classList.remove("hidden");
        this.refs.iconPause.classList.add("hidden");
      }
    }
  }

  // ============================================================================
  // Voting & Persistence
  // ============================================================================

  saveVote(value) {
    if (this.hasVoted) return;

    const payload = {
      componentId: this.componentId,
      type: "ab-test",
      title: this.title,
      selected: value,
      timestamp: new Date().toISOString(),
    };

    // Dispatch Custom Event (Phase 3 Compatibility)
    const event = new CustomEvent("mono:vote", {
      detail: payload,
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);

    // Local Storage Mock Persistence (Phase 2)
    try {
      this.saveState(`mono_abtest_${this.componentId}`, payload);
      this.hasVoted = true;
      this.updateVoteUI(value);
    } catch (e) {
      console.error("Failed to save vote:", e);
      alert("評価の保存に失敗しました。");
    }
  }

  updateVoteUI(selectedValue) {
    // Disable all buttons
    const voteButtons = ["voteA", "voteNeutral", "voteB"];
    voteButtons.forEach((refName) => {
      if (this.refs[refName]) {
        this.refs[refName].disabled = true;
        // Highlight selected
        if (this.refs[refName].dataset.vote === selectedValue) {
          this.refs[refName].classList.add("selected");
        }
      }
    });

    if (this.refs.votedMessage) {
      this.refs.votedMessage.classList.remove("hidden");
    }
  }
}

// Register the custom element
if (!customElements.get("mono-ab-test")) {
  customElements.define("mono-ab-test", MonoABTest);
}
