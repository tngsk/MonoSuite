class MonoReaction extends MonoInteractiveElement {
  constructor() {
    super();
    this.mountTemplate('mono-reaction-template');
  }

  connectedCallback() {
    if (super.connectedCallback) {
        super.connectedCallback();
    }
    this.options = (this.getAttribute("options") || "")
      .split(",")
      .map((opt) => opt.trim())
      .filter((opt) => opt);

    this.componentId =
      this.getAttribute("id") ||
      `reaction-${Math.random().toString(36).substring(2, 9)}`;

    this.counts = {};

    // Load existing counts from local storage if any
    try {
      const data = this.loadState(`mono_reaction_${this.componentId}`);
      if (data && data.counts) {
         this.counts = data.counts;
      }
    } catch (e) {
      console.info("リアクションデータの読み込みに失敗しました:", e);
    }

    this.render();
  }

  onAuthStateChanged(user) {
    if (user) {
      console.log(`[mono-reaction] User logged in: ${user.name}`);
    } else {
      console.log("[mono-reaction] Running in guest/standalone mode");
    }
  }

  render() {
    const container = this.shadowRoot.getElementById("reaction-buttons");
    if (!container) return;

    container.textContent = "";

    this.options.forEach((option, index) => {
      const btn = document.createElement("button");
      btn.className = "mono-reaction-btn";

      const label = document.createElement("span");
      label.textContent = option;
      btn.appendChild(label);

      const countLabel = document.createElement("span");
      countLabel.className = "mono-reaction-count";
      const currentCount = this.counts[option] || 0;
      countLabel.textContent = currentCount;
      btn.appendChild(countLabel);

      btn.addEventListener("click", () => this.handleReaction(option, index));

      container.appendChild(btn);
    });
  }

  handleReaction(option, index) {
    this.counts[option] = (this.counts[option] || 0) + 1;
    this.render();

    const payload = {
      timestamp: new Date().toISOString(),
      componentId: this.componentId,
      reactionType: `type_${index}`,
      reactionLabel: option,
      counts: this.counts // store counts for local continuity
    };

    try {
      this.saveState(`mono_reaction_${this.componentId}`, payload);
    } catch (e) {
      console.info("リアクションデータの保存に失敗しました", e);
    }

    const event = new CustomEvent("mono-data", {
      detail: payload,
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }
}

if (!customElements.get("mono-reaction")) {
  customElements.define("mono-reaction", MonoReaction);
}
