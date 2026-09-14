/**
 * Mono Components
 *
 * Vanilla JS Web Component for code blocks.
 * Implements "Light DOM" enhancement strategy: Wraps the original Markdown
 * <pre><code> output to preserve SEO and accessibility, while injecting
 * a copy button.
 */

class MonoCodeBlock extends MonoBaseElement {
  constructor() {
    super();

    // Component state
    this.language = this.getAttribute("language") || "";
  }

  connectedCallback() {
    this.mountTemplate();
    this.setupEventListeners();
  }

  mountTemplate() {
        super.mountTemplate('mono-code-block-template');
        // Cache references

    // Set Header Label
    if (this.refs.languageLabel) {
      this.refs.languageLabel.textContent = this.language
        ? this.language
        : "Code";
    }

    // Move Light DOM content (the original <pre><code> from markdown) into the slot container
    if (this.refs.contentSlot) {
      // Create a <slot> to project the light DOM content into the Shadow DOM
      const slot = document.createElement("slot");
      this.refs.contentSlot.appendChild(slot);
    }
  }

  setupEventListeners() {
    if (this.refs.copyButton) {
      this.refs.copyButton.addEventListener("click", () =>
        this.handleCopyClick(),
      );
    }
  }

  handleCopyClick() {
    // Look for the <code> element within the Light DOM (children of <mono-code-block>)
    const codeElement = this.querySelector("code");
    if (!codeElement) return;

    // Use textContent to grab raw text
    const text = codeElement.textContent;

    navigator.clipboard
      .writeText(text)
      .then(() => {
        this.showCopySuccess();
      })
      .catch((err) => {
        console.error("Failed to copy text: ", err);
        this.showCopyError();
      });
  }

  showCopySuccess() {
    const btn = this.refs.copyButton;
    if (!btn) return;

    const originalText = btn.textContent;
    btn.textContent = "✅ Copied!";
    btn.classList.add("copied");

    // Reset after 2 seconds
    setTimeout(() => {
      btn.textContent = originalText;
      btn.classList.remove("copied");
    }, 2000);
  }

  showCopyError() {
    const btn = this.refs.copyButton;
    if (!btn) return;

    const originalText = btn.textContent;
    btn.textContent = "❌ Error";

    setTimeout(() => {
      btn.textContent = originalText;
    }, 2000);
  }

}

// Register the custom element
if (!customElements.get("mono-code-block")) {
  customElements.define("mono-code-block", MonoCodeBlock);
}
