/**
 * Mono Components
 *
 * Vanilla JS Web Components for educational and research acoustic systems.
 * Designed with a clean, readable aesthetic.
 * This file relies on HTML templates injected into the main document.
 */

class MonoPoll extends MonoInteractiveElement {
  constructor() {
    super();

    // Component state
    this.title = this.getAttribute("title") || "Poll";
    this.options = (this.getAttribute("options") || "")
      .split(",")
      .map((opt) => opt.trim())
      .filter((opt) => opt);
    this.componentId =
      this.getAttribute("id") ||
      `poll-${Math.random().toString(36).substring(2, 9)}`;
    this.hasVoted = false;
    this.selectedValue = null;

    // Cache for DOM references
    this.optionNodes = [];
  }

  connectedCallback() {
    if (super.connectedCallback) {
        super.connectedCallback();
    }
    this.checkPreviousVote();
    this.mountTemplate();
    this.setupEventListeners();
    this.updateView();
  }

  onAuthStateChanged(user) {
    if (user) {
      console.log(`[mono-poll] User logged in: ${user.name}`);
    } else {
      console.log("[mono-poll] Running in guest/standalone mode");
    }
  }

  checkPreviousVote() {
    try {
      const data = this.loadState(`mono_poll_${this.componentId}`);
      if (data && data.selected) {
        this.hasVoted = true;
        this.selectedValue = data.selected;
      }
    } catch (e) {
      console.warn("Failed to read from localStorage:", e);
    }
  }

  saveVote(value) {
    const payload = {
      componentId: this.componentId,
      type: "poll",
      title: this.title,
      selected: value,
      timestamp: new Date().toISOString(),
    };

    // Phase 3 Compatibility: Dispatch custom event for future backend integration
    const event = new CustomEvent("mono:vote", {
      detail: payload,
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);

    // Mock Persistence (Phase 2)
    try {
      this.saveState(`mono_poll_${this.componentId}`, payload);
      this.hasVoted = true;
      this.selectedValue = value;
      this.updateView();
    } catch (e) {
      console.error("Failed to save vote:", e);
      alert("投票の保存に失敗しました。");
    }
  }

  mountTemplate() {
    // 1. Clone main layout template
        super.mountTemplate('mono-poll-template');

    // 2. Cache main references

    // 3. Bind static data
    if (this.refs.title) {
      this.refs.title.textContent = this.title;
    }

    // 4. Render options dynamically
    const optionTemplate = document.getElementById("mono-poll-option-template");
    if (!optionTemplate || !this.refs.optionsContainer) return;

    this.options.forEach((opt) => {
      const node = optionTemplate.content.cloneNode(true);

      const label = node.querySelector('[data-ref="label"]');
      const radio = node.querySelector('[data-ref="radio"]');
      const text = node.querySelector('[data-ref="text"]');

      text.textContent = opt;
      radio.value = opt;

      this.refs.optionsContainer.appendChild(node);

      // Store references to the appended elements for state updates
      const appendedLabel = this.refs.optionsContainer.lastElementChild;
      const appendedRadio = appendedLabel.querySelector("input");

      this.optionNodes.push({
        value: opt,
        label: appendedLabel,
        radio: appendedRadio,
      });
    });
  }

  handleSelection(value) {
    if (this.hasVoted) return;

    // Reset visual state
    this.optionNodes.forEach((node) => {
      node.label.classList.remove("selected");
    });

    // Apply selected state
    const selectedNode = this.optionNodes.find((n) => n.value === value);
    if (selectedNode) {
      selectedNode.label.classList.add("selected");
    }

    // Enable submit button
    if (this.refs.submitBtn) {
      this.refs.submitBtn.disabled = false;
    }
  }

  setupEventListeners() {
    // Radio selection events
    this.optionNodes.forEach((node) => {
      node.radio.addEventListener("change", () => {
        this.handleSelection(node.value);
      });
    });

    // Submit button event
    if (this.refs.submitBtn) {
      this.refs.submitBtn.addEventListener("click", () => {
        const selectedNode = this.optionNodes.find((n) => n.radio.checked);
        if (selectedNode) {
          this.saveVote(selectedNode.value);
        }
      });
    }
  }

  updateView() {
    if (!this.hasVoted) return;

    // Update options state (lock inputs, set final visual selection)
    this.optionNodes.forEach((node) => {
      node.radio.disabled = true;
      node.label.classList.add("voted");

      if (node.value === this.selectedValue) {
        node.radio.checked = true;
        node.label.classList.add("selected");
      } else {
        node.radio.checked = false;
        node.label.classList.remove("selected");
      }
    });

    // Toggle visibility between submit button and success message
    if (this.refs.submitBtn) {
      this.refs.submitBtn.classList.add("hidden");
    }
    if (this.refs.votedMessage) {
      this.refs.votedMessage.classList.remove("hidden");
    }
  }
}

// Register the custom element
if (!customElements.get("mono-poll")) {
  customElements.define("mono-poll", MonoPoll);
}
