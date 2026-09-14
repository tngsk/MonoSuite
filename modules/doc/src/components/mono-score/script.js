class MonoScore extends MonoBaseElement {
    constructor() {
        super({ shadowMode: null });
    }

    async connectedCallback() {
        const template = document.getElementById('mono-score-template');
        if (template && !this.querySelector('.score-container')) {
            this.appendChild(template.content.cloneNode(true));
        }

        const container = this.querySelector('.score-container') || this;

        // Ensure VexFlow is loaded
        await this.loadVexFlow();

        this.renderScore(container);
    }

    async loadVexFlow() {
        if (window.Vex && window.Vex.Flow) return;

        // Cache the promise so multiple components don't inject multiple scripts
        if (!window.__vexFlowLoadingPromise) {
            window.__vexFlowLoadingPromise = new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = "https://cdn.jsdelivr.net/npm/vexflow@4.2.2/build/cjs/vexflow.js";
                script.onload = () => {
                    if (window.Vex && window.Vex.Flow) {
                        resolve();
                    } else {
                        setTimeout(() => {
                            if (window.Vex && window.Vex.Flow) {
                                resolve();
                            } else {
                                console.error("VexFlow failed to load correctly on window");
                                reject(new Error("VexFlow not on window"));
                            }
                        }, 100);
                    }
                };
                script.onerror = reject;
                document.head.appendChild(script);
            });
        }

        return window.__vexFlowLoadingPromise;
    }

            renderScore(container) {
        if (!window.Vex || !window.Vex.Flow) return;
        container.textContent = '';

        const VF = window.Vex.Flow;
        const { Factory } = VF;

        let notesAttr = this.getAttribute('notes') || '';
        const voicesAttr = this.getAttribute('voices') || '';
        const clefAttr = this.getAttribute('clef') || 'treble';
        const timeAttr = this.getAttribute('time') || '4/4';

        // Calculate a rough width based on string lengths to avoid crowding
        let totalLength = Math.max(notesAttr.length, voicesAttr.length);
        const staveWidth = Math.max(200, totalLength * 15);
        const rendererWidth = staveWidth + 20;

        const vf = new Factory({ renderer: { elementId: container, width: rendererWidth, height: 120 } });
        const score = vf.EasyScore();
        const system = vf.System();

        let voicesData = [];

        if (voicesAttr) {
            try {
                const decodedVoices = voicesAttr.replace(/&quot;/g, '"').replace(/&amp;/g, '&');
                let parsedVoices = [];
                // If it is a valid JSON array
                if (decodedVoices.trim().startsWith('[')) {
                     parsedVoices = JSON.parse(decodedVoices);
                } else {
                     // Support string splits by | or something if needed, but JSON array is expected
                     parsedVoices = [decodedVoices];
                }

                if (Array.isArray(parsedVoices)) {
                    parsedVoices.forEach((voiceStr, i) => {
                        let options = {};
                        // For 2 voices, usually top is up, bottom is down
                        if (parsedVoices.length > 1) {
                            options.stem = i % 2 === 0 ? 'up' : 'down';
                        }
                        voicesData.push(score.voice(score.notes(voiceStr, options), { time: timeAttr }).setStrict(false));
                    });
                }
            } catch (e) {
                console.error("Failed to parse voices attribute for mono-score:", e);
            }
        } else if (notesAttr) {
            try {
                // If legacy space separated like "C4 D4 E4", replace space with comma
                if (!notesAttr.includes(',') && notesAttr.trim().length > 0) {
                    notesAttr = notesAttr.split(/[\s]+/).filter(n => n).join(', ');
                }
                voicesData.push(score.voice(score.notes(notesAttr), { time: timeAttr }).setStrict(false));
            } catch (e) {
                console.error("Failed to parse notes attribute for mono-score:", e);
            }
        }

        if (voicesData.length > 0) {
            try {
                system.addStave({
                    voices: voicesData
                }).addClef(clefAttr).addTimeSignature(timeAttr);
                vf.draw();
            } catch (e) {
                console.error("Failed to draw mono-score:", e);
                const fallbackVf = new Factory({ renderer: { elementId: container, width: rendererWidth, height: 120 } });
                fallbackVf.System().addStave({}).addClef(clefAttr).addTimeSignature(timeAttr);
                fallbackVf.draw();
            }
        } else {
            system.addStave({}).addClef(clefAttr).addTimeSignature(timeAttr);
            vf.draw();
        }

        const svg = container.querySelector("svg");
        if (svg) {
            svg.style.cssText = "height: 6em; width: auto; display: inline-block; vertical-align: middle;";
            svg.querySelectorAll("*").forEach((el) => {
                if (el.tagName !== "svg") {
                    if (el.getAttribute("fill") === "black" || el.getAttribute("fill") === "#000000") {
                        el.setAttribute("fill", "currentColor");
                    }
                    if (el.getAttribute("stroke") === "black" || el.getAttribute("stroke") === "#000000") {
                        el.setAttribute("stroke", "currentColor");
                    }
                }
            });
        }
    }

    static get observedAttributes() {
        return ['notes', 'clef', 'time', 'voices'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue !== newValue && this.isConnected) {
            const container = this.querySelector('.score-container') || this;
            if (window.Vex && window.Vex.Flow) {
                this.renderScore(container);
            }
        }
    }
}

if (!customElements.get('mono-score')) {
    customElements.define('mono-score', MonoScore);
}
