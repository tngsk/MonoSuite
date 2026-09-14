/**
 * Mono Components
 *
 * Vanilla JS Web Component for a notebook input area.
 * It provides a simple text area for users to take notes and
 * persists the content automatically to Local Storage.
 */

class MonoNotebookInput extends MonoInteractiveElement {
  constructor() {
    super();
    this.inputId =
      this.getAttribute("id") ||
      `notebook-${Math.random().toString(36).substr(2, 9)}`;
    this.debounceTimeout = null;
    this.storageUnavailable = false;
  }

  connectedCallback() {
    if (super.connectedCallback) {
        super.connectedCallback();
    }
    this.mountTemplate();
    this.setupEventListeners();
    this.restoreData();
  }

  mountTemplate() {
        super.mountTemplate('mono-notebook-template');
        // Cache references

    const title = this.getAttribute("title");
    if (title) {
      const labelEl = this.shadowRoot.querySelector(".notebook-label");
      if (labelEl) {
        labelEl.textContent = title;
      }
    }

    const placeholder = this.getAttribute("placeholder");
    if (placeholder && this.refs.inputArea) {
      this.refs.inputArea.placeholder = placeholder;
    }

    // Test if Local Storage is available
    try {
      const testKey = "__storage_test__";
      this.saveState(testKey, testKey);
      this.removeState(testKey);
    } catch (e) {
      this.storageUnavailable = true;
      console.warn(
        "Local Storage is not available. Notes will not be persisted.",
        e,
      );
      if (this.refs.statusIndicator) {
        this.refs.statusIndicator.textContent = "Storage unavailable";
        this.refs.statusIndicator.classList.add("error");
      }
    }
  }

  setupEventListeners() {
    if (this.refs.inputArea) {
      this.refs.inputArea.addEventListener("input", () => this.handleInput());
    }
  }

  getPageId() {
    // Fallback or easily replaceable logic to determine the current page namespace
    return window.location.pathname || "default-page";
  }

  getStorageKey() {
    return `mono_notebook::${this.getPageId()}::${this.inputId}`;
  }

  restoreData() {
    if (this.storageUnavailable || !this.refs.inputArea) return;

    try {
      const data = this.loadState(this.getStorageKey());
      if (data && data.value !== undefined) {
        this.refs.inputArea.value = data.value;
      }
    } catch (e) {
      console.error("Failed to restore notebook data from Local Storage", e);
    }
  }

  handleInput() {
    if (this.storageUnavailable) return;

    // Clear existing debounce timeout
    if (this.debounceTimeout) {
      clearTimeout(this.debounceTimeout);
    }

    // Set new debounce timeout
    this.debounceTimeout = setTimeout(() => {
      this.saveData();
    }, 500);
  }

  saveData() {
    if (!this.refs.inputArea) return;

    const value = this.refs.inputArea.value;
    const data = {
      id: this.inputId,
      value: value,
      updated_at: new Date().toISOString(),
    };

    try {
      this.saveState(this.getStorageKey(), data);
      this.showSaveFeedback();
    } catch (e) {
      console.error("Failed to save notebook data to Local Storage", e);
    }
  }

  showSaveFeedback() {
    const indicator = this.refs.statusIndicator;
    if (!indicator) return;

    indicator.textContent = "✓ Saved";
    indicator.classList.remove("error");
    indicator.classList.add("visible");

    setTimeout(() => {
      indicator.classList.remove("visible");
    }, 2000);
  }
}

// Register the custom element
if (!customElements.get("mono-notebook")) {
  customElements.define("mono-notebook", MonoNotebookInput);
}
