class MonoSynth extends MonoBaseElement {
  constructor() {
    super();
    this.mountTemplate('mono-synth-template');

    // UI Elements
    this.canvas = this.shadowRoot.querySelector('.synth-scope');
    this.ctx = this.canvas.getContext('2d');
    this.knobs = this.shadowRoot.querySelectorAll('.knob');
    this.keyboardInner = this.shadowRoot.querySelector('.keyboard-inner');
    this.startOverlay = this.shadowRoot.querySelector('.overlay-start');
    this.startBtn = this.shadowRoot.querySelector('.start-btn');

    // Tone.js nodes
    this.synth = null;
    this.analyzer = null;
    this.isToneLoaded = false;
    this.isAudioStarted = false;

    // Nodes mapping
    this.nodes = {};

    // State
    this.activePointers = new Map();
    this.animationFrameId = null;

    // Bindings
    this.drawScope = this.drawScope.bind(this);
    this.initAudio = this.initAudio.bind(this);
  }

  connectedCallback() {
    this.generateKeyboard();
    this.setupKnobs();

    this.startBtn.addEventListener('click', this.initAudio);

    // Resize observer for canvas
    const resizeObserver = new ResizeObserver(() => {
      if (this.canvas.clientWidth && this.canvas.clientHeight) {
        this.canvas.width = this.canvas.clientWidth;
        this.canvas.height = this.canvas.clientHeight;
      }
    });
    resizeObserver.observe(this.canvas);

    this.loadToneJs();
  }

  disconnectedCallback() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
    // Cleanup nodes
    Object.values(this.nodes).forEach(n => {
      if (n && n.dispose) n.dispose();
    });
    if (this.synth) this.synth.dispose();
  }

  loadToneJs() {
    if (window.Tone) {
      this.isToneLoaded = true;
      return;
    }

    if (!document.getElementById('tone-js')) {
      const script = document.createElement('script');
      script.id = 'tone-js';
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.js';
      script.onload = () => {
        this.isToneLoaded = true;
      };
      document.head.appendChild(script);
    } else {
      const checkTone = setInterval(() => {
        if (window.Tone) {
          this.isToneLoaded = true;
          clearInterval(checkTone);
        }
      }, 100);
    }
  }

  async initAudio() {
    if (!this.isToneLoaded) {
      console.warn("Tone.js not yet loaded");
      return;
    }

    try {
      await window.Tone.start();
      this.isAudioStarted = true;
      this.startOverlay.classList.add('hidden');

      this.setupSynth();
      this.updateSynthParams();
      this.drawScope();
    } catch (e) {
      console.error("Audio context start failed", e);
    }
  }

  setupSynth() {
    const Tone = window.Tone;

    this.nodes.analyzer = new Tone.Analyser('waveform', 512);
    this.nodes.volume = new Tone.Volume(-12).toDestination();

    // Core filter
    this.nodes.filter = new Tone.Filter(2000, "lowpass");
    this.nodes.filter.Q.value = 1;
    this.nodes.filter.chain(this.nodes.analyzer, this.nodes.volume);

    // Synth
    // We use a MonoSynth to get Osc and Amp Env easily,
    // but we'll bypass its internal filter and use our custom chain
    this.synth = new Tone.MonoSynth({
      oscillator: { type: "sine" },
      envelope: { attack: 0.1, decay: 0.2, sustain: 0.5, release: 1 },
      filter: { type: "lowpass", frequency: 20000 }, // Disable internal filter basically
      filterEnvelope: { attack: 0, decay: 0, sustain: 1, release: 0, baseFrequency: 20000, octaves: 0 }
    });
    this.synth.disconnect();
    this.synth.connect(this.nodes.filter);

    // Additional Envelopes
    this.nodes.pitchEnv = new Tone.Envelope(0.1, 0.2, 0, 0); // only A D
    // Scale env 0-1 to detune amount in cents
    this.nodes.pitchScale = new Tone.Scale(0, 0);
    this.nodes.pitchEnv.connect(this.nodes.pitchScale);
    this.nodes.pitchScale.connect(this.synth.oscillator.detune);

    this.nodes.filtEnv = new Tone.Envelope(0.1, 0.2, 0.5, 1);
    this.nodes.filtScale = new Tone.Scale(0, 0);
    this.nodes.filtEnv.connect(this.nodes.filtScale);
    this.nodes.filtScale.connect(this.nodes.filter.frequency);

    // LFOs
    this.nodes.lfo1 = new Tone.LFO(1, 0, 1).start();
    this.nodes.lfo1Scale = new Tone.Scale(0, 0);
    this.nodes.lfo1.connect(this.nodes.lfo1Scale);

    this.nodes.lfo2 = new Tone.LFO(1, 0, 1).start();
    this.nodes.lfo2Scale = new Tone.Scale(0, 0);
    this.nodes.lfo2.connect(this.nodes.lfo2Scale);

    // Track active sample sampler
    this.sampler = null;
    this.isSampleMode = false;

    let rawSrc = this.getAttribute('sample');
    if (rawSrc) {
      const isValidUrl = (url) => {
        if (!url || typeof url !== 'string') return false;
        try {
            const parsed = new URL(url, window.location.href);
            return ['http:', 'https:', 'data:'].includes(parsed.protocol.toLowerCase());
        } catch (e) {
            return false;
        }
      };

      if (rawSrc.startsWith("asset-")) {
        const store = document.getElementById("mono-asset-store");
        if (store) {
          try {
            const assets = JSON.parse(store.textContent);
            if (assets[rawSrc] && isValidUrl(assets[rawSrc])) {
              rawSrc = assets[rawSrc];
            }
          } catch (e) {
            console.error("Asset store error:", e);
          }
        }
      }

      if (isValidUrl(rawSrc)) {
        this.sampler = new window.Tone.Sampler({
          urls: {
            C4: rawSrc
          },
          release: 1,
          baseUrl: ""
        });
        this.sampler.connect(this.nodes.filter);

        // Connect LFOs/Envs to sampler detune if needed, but Sampler API restricts some modularity.
        // We will just connect pitchEnv to sampler detune if available
        this.nodes.pitchEnv.connect(this.nodes.pitchScale);
        // Sampler lacks a direct .detune node array, so we might skip it or use a pitch shift later.
      }
    }
  }

  getParamValue(paramName) {
    const knob = Array.from(this.knobs).find(k => k.dataset.param === paramName);
    if (!knob) return null;
    return knob.dataset.type === 'enum' ? knob.dataset.value : parseFloat(knob.dataset.value);
  }

  triggerAttack(noteIndex) {
    if (!this.isAudioStarted) return;
    const Tone = window.Tone;
    const now = Tone.now();

    const baseFreq = this.getParamValue("baseFreq") || 440;
    // Note index 0 = baseFreq. index 1 = baseFreq * 2^(1/12)
    const freq = baseFreq * Math.pow(2, noteIndex / 12);

    if (this.isSampleMode && this.sampler && this.sampler.loaded) {
      this.sampler.triggerAttack(freq, now);
    } else {
      this.synth.triggerAttack(freq, now);
    }

    this.nodes.pitchEnv.triggerAttack(now);
    this.nodes.filtEnv.triggerAttack(now);
  }

  triggerRelease() {
    if (!this.isAudioStarted) return;
    const Tone = window.Tone;
    const now = Tone.now();

    if (this.isSampleMode && this.sampler && this.sampler.loaded) {
      this.sampler.triggerRelease(now);
    } else {
      this.synth.triggerRelease(now);
    }

    this.nodes.pitchEnv.triggerRelease(now);
    this.nodes.filtEnv.triggerRelease(now);
  }

  // --- UI Logic ---

  generateKeyboard() {
    const numWhiteKeys = 21; // 3 octaves
    const totalKeys = 36; // 12 * 3

    // Pattern of white/black keys
    // W B W B W W B W B W B W ...
    const pattern = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0];

    let whiteIndex = 0;

    for (let i = 0; i < totalKeys; i++) {
      const isBlack = pattern[i % 12] === 1;
      const el = document.createElement('div');

      el.dataset.index = i; // Represents semitones from baseFreq

      if (isBlack) {
        el.className = 'key key-black';
        // Calculate position based on the PREVIOUS white key
        const whiteWidthPercent = 100 / numWhiteKeys;
        const blackWidthPercent = whiteWidthPercent * 0.6;
        // Position it on the line between previous white key and next white key
        const leftPercent = (whiteIndex * whiteWidthPercent) - (blackWidthPercent / 2);
        el.style.width = `${blackWidthPercent}%`;
        el.style.left = `${leftPercent}%`;
      } else {
        el.className = 'key key-white';
        whiteIndex++;
      }

      const startNote = (e) => {
        e.preventDefault();
        el.classList.add('active');
        this.triggerAttack(parseInt(el.dataset.index));
      };

      const stopNote = (e) => {
        e.preventDefault();
        el.classList.remove('active');
        this.triggerRelease();
      };

      el.addEventListener('mousedown', startNote);
      el.addEventListener('mouseup', stopNote);
      el.addEventListener('mouseleave', stopNote);

      el.addEventListener('touchstart', startNote, {passive: false});
      el.addEventListener('touchend', stopNote, {passive: false});
      el.addEventListener('touchcancel', stopNote, {passive: false});

      this.keyboardInner.appendChild(el);
    }
  }

  setupKnobs() {
    let activeKnob = null;
    let startY = 0;
    let startVal = 0;

    const onPointerDown = (e, knob) => {
      e.preventDefault();
      activeKnob = knob;
      startY = e.clientY || e.touches[0].clientY;

      const type = knob.dataset.type;
      if (type === 'enum') {
        startVal = knob.dataset.idx ? parseInt(knob.dataset.idx) : 0;
      } else {
        const min = parseFloat(knob.dataset.min);
        const max = parseFloat(knob.dataset.max);
        const val = parseFloat(knob.dataset.value);
        startVal = (val - min) / (max - min);
      }

      document.addEventListener('mousemove', onPointerMove);
      document.addEventListener('mouseup', onPointerUp);
      document.addEventListener('touchmove', onPointerMove, {passive: false});
      document.addEventListener('touchend', onPointerUp);
    };

    const onPointerMove = (e) => {
      if (!activeKnob) return;
      e.preventDefault();
      const clientY = e.clientY || (e.touches && e.touches[0].clientY);
      const deltaY = startY - clientY;

      const type = activeKnob.dataset.type;
      if (type === 'enum') {
        const options = activeKnob.dataset.options.split(',');
        const step = Math.floor(deltaY / 20);
        let idx = startVal + step;
        idx = Math.max(0, Math.min(options.length - 1, idx));
        activeKnob.dataset.idx = idx;
        const valStr = options[idx];
        activeKnob.dataset.value = valStr;
        this.updateKnobDisplay(activeKnob, idx / (options.length - 1));
      } else {
        const min = parseFloat(activeKnob.dataset.min);
        const max = parseFloat(activeKnob.dataset.max);
        let newVal = startVal + (deltaY / 150);
        newVal = Math.max(0, Math.min(1, newVal));

        let realVal;
        if (activeKnob.dataset.scale === 'log') {
          const logMin = Math.log(min || 0.1);
          const logMax = Math.log(max);
          realVal = Math.exp(logMin + newVal * (logMax - logMin));
        } else {
          realVal = min + newVal * (max - min);
        }

        activeKnob.dataset.value = realVal;
        this.updateKnobDisplay(activeKnob, newVal);
      }

      this.updateSynthParams();
    };

    const onPointerUp = () => {
      activeKnob = null;
      document.removeEventListener('mousemove', onPointerMove);
      document.removeEventListener('mouseup', onPointerUp);
      document.removeEventListener('touchmove', onPointerMove);
      document.removeEventListener('touchend', onPointerUp);
    };

    this.knobs.forEach(knob => {
      const type = knob.dataset.type;
      if (type === 'enum') {
        knob.dataset.idx = 0;
        knob.dataset.value = knob.dataset.options.split(',')[0];
        this.updateKnobDisplay(knob, 0);
      } else {
        const min = parseFloat(knob.dataset.min);
        const max = parseFloat(knob.dataset.max);
        const val = parseFloat(knob.dataset.value);
        let norm = (val - min) / (max - min);
        if (knob.dataset.scale === 'log') {
          const logMin = Math.log(min || 0.1);
          const logMax = Math.log(max);
          norm = (Math.log(val) - logMin) / (logMax - logMin);
        }
        this.updateKnobDisplay(knob, norm);
      }

      knob.addEventListener('mousedown', e => onPointerDown(e, knob));
      knob.addEventListener('touchstart', e => onPointerDown(e, knob), {passive: false});
    });
  }

  updateKnobDisplay(knob, normValue) {
    const dial = knob.querySelector('.knob-dial');
    const angle = -135 + (normValue * 270);
    dial.style.transform = `rotate(${angle}deg)`;
  }

  routeLFO(lfoScaleNode, lfoDepth, destStr) {
    lfoScaleNode.disconnect();
    if (destStr === "pitch") {
      lfoScaleNode.min = -lfoDepth * 1200; // cents
      lfoScaleNode.max = lfoDepth * 1200;
      lfoScaleNode.connect(this.synth.oscillator.detune);
    } else if (destStr === "filter") {
      lfoScaleNode.min = -lfoDepth * 5000;
      lfoScaleNode.max = lfoDepth * 5000;
      lfoScaleNode.connect(this.nodes.filter.frequency);
    } else if (destStr === "amp") {
      lfoScaleNode.min = -lfoDepth * 40; // db
      lfoScaleNode.max = 0;
      lfoScaleNode.connect(this.nodes.volume.volume);
    }
  }

  updateSynthParams() {
    if (!this.synth || !this.isAudioStarted) return;

    const p = {};
    this.knobs.forEach(k => {
      p[k.dataset.param] = k.dataset.type === 'enum' ? k.dataset.value : parseFloat(k.dataset.value);
    });

    // OSC
    if (p.oscType === 'sample') {
      this.isSampleMode = true;
    } else {
      this.isSampleMode = false;
      this.synth.oscillator.type = p.oscType;
    }

    // Filter
    this.nodes.filter.frequency.value = p.filterFreq;
    this.nodes.filter.Q.value = p.filterRes;

    // Amp Env
    this.synth.envelope.attack = p.ampA;
    this.synth.envelope.decay = p.ampD;
    this.synth.envelope.sustain = p.ampS;
    this.synth.envelope.release = p.ampR;

    // Pitch Env
    this.nodes.pitchEnv.attack = p.pitchA;
    this.nodes.pitchEnv.decay = p.pitchD;
    this.nodes.pitchScale.min = 0;
    this.nodes.pitchScale.max = p.pitchEnvAmt;

    // Filter Env
    this.nodes.filtEnv.attack = p.filtA;
    this.nodes.filtEnv.decay = p.filtD;
    this.nodes.filtEnv.sustain = p.filtS;
    this.nodes.filtEnv.release = p.filtR;
    this.nodes.filtScale.min = 0;
    this.nodes.filtScale.max = p.filtEnvAmt;

    // LFO 1
    this.nodes.lfo1.frequency.value = p.lfo1Rate;
    this.routeLFO(this.nodes.lfo1Scale, p.lfo1Depth, p.lfo1Dest);

    // LFO 2
    this.nodes.lfo2.frequency.value = p.lfo2Rate;
    this.routeLFO(this.nodes.lfo2Scale, p.lfo2Depth, p.lfo2Dest);

    // Master
    // Ensure LFO routing doesn't completely override master if dest != amp, but for simplicity
    // we set the base value. Tone.js handles additive signals well.
    if (p.lfo1Dest !== "amp" && p.lfo2Dest !== "amp") {
      this.nodes.volume.volume.value = p.volume;
    } else {
        // If LFO is routed to amp, base volume is max, LFO modulates downwards
        this.nodes.volume.volume.value = p.volume;
    }
  }

  drawScope() {
    if (!this.nodes.analyzer || !this.isAudioStarted) return;

    this.animationFrameId = requestAnimationFrame(this.drawScope);

    const values = this.nodes.analyzer.getValue();
    const width = this.canvas.width;
    const height = this.canvas.height;

    // Background Primary (#1A1C1E)
    // Get variables from host styles
    const computedStyle = getComputedStyle(this);
    const bgColor = computedStyle.getPropertyValue('--color-base-content').trim() || '#1A1C1E';
    const lineColor = computedStyle.getPropertyValue('--color-primary').trim() || '#B8422E';

    this.ctx.fillStyle = bgColor;
    this.ctx.fillRect(0, 0, width, height);

    this.ctx.lineWidth = 2;
    this.ctx.strokeStyle = lineColor; // Tertiary
    this.ctx.beginPath();

    // Zero-crossing trigger logic for stabilization
    let startIndex = 0;
    // Look for a positive zero-crossing in the first half of the buffer
    for (let i = 0; i < values.length / 2; i++) {
        if (values[i] < 0 && values[i + 1] >= 0) {
            startIndex = i;
            break;
        }
    }

    // Determine how many samples to draw (one period could be calculated based on freq, but we use a fixed window size relative to buffer)
    // To make it look "zoomed in" and stable, we draw from the start index up to the width.
    // If the frequency is high, it shows many waves.
    const samplesToDraw = values.length - startIndex;
    const sliceWidth = width * 1.0 / samplesToDraw;

    let x = 0;
    let drewLine = false;

    for (let i = startIndex; i < values.length; i++) {
      const v = values[i];
      const y = (v * -0.5 + 0.5) * height; // Inverted visually so positive is up

      if (!drewLine) {
        this.ctx.moveTo(x, y);
        drewLine = true;
      } else {
        this.ctx.lineTo(x, y);
      }
      x += sliceWidth;
    }

    if (drewLine) {
        this.ctx.stroke();
    }
  }
}

customElements.define('mono-synth', MonoSynth);
