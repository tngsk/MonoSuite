class MonoBrush extends MonoBaseElement {
  constructor() {
    super();
    this.isDrawingModeActive = false;
    this.isDrawing = false;
    this.lastX = 0;
    this.lastY = 0;
    this.points = [];
    this.animationFrameId = null;
    this.resizeTimeout = null;
  }

  connectedCallback() {
    super.mountTemplate("mono-brush-template");
    this.setupElements();
    this.setupEventListeners();
    this.resizeCanvas();
  }

  disconnectedCallback() {
    this.removeEventListeners();
  }

  setupElements() {
    this.canvas = this.shadowRoot.getElementById("canvas");
    this.ctx = this.canvas.getContext("2d");
    this.brushColor = "rgba(244, 63, 94, 0.75)";
  }

  setupEventListeners() {
    this.handleKeyDown = this.handleKeyDown.bind(this);
    this.handleKeyUp = this.handleKeyUp.bind(this);
    this.handleMouseMove = this.handleMouseMove.bind(this);
    this.handleMouseDown = this.handleMouseDown.bind(this);
    this.handleMouseUp = this.handleMouseUp.bind(this);
    this.handleResize = this.handleResize.bind(this);

    this.handleBlur = this.handleBlur.bind(this);

    document.addEventListener("keydown", this.handleKeyDown);
    document.addEventListener("keyup", this.handleKeyUp);
    document.addEventListener("mousemove", this.handleMouseMove, {
      passive: false,
    });

    // Canvas events for drawing
    this.canvas.addEventListener("mousedown", this.handleMouseDown);
    this.canvas.addEventListener("mousemove", this.handleMouseMove);
    this.canvas.addEventListener("mouseup", this.handleMouseUp);
    this.canvas.addEventListener("mouseout", this.handleMouseUp);

    // Touch support
    this.canvas.addEventListener(
      "touchstart",
      this.handleTouchStart.bind(this),
      { passive: false },
    );
    this.canvas.addEventListener("touchmove", this.handleTouchMove.bind(this), {
      passive: false,
    });
    this.canvas.addEventListener("touchend", this.handleMouseUp);

    window.addEventListener("resize", this.handleResize);
    window.addEventListener("blur", this.handleBlur);
  }

  removeEventListeners() {
    document.removeEventListener("keydown", this.handleKeyDown);
    document.removeEventListener("keyup", this.handleKeyUp);
    document.removeEventListener("mousemove", this.handleMouseMove);
    window.removeEventListener("resize", this.handleResize);
    window.removeEventListener("blur", this.handleBlur);
  }

  handleBlur() {
    this.isDrawingModeActive = false;
    this.updateMode();
  }

  handleResize() {
    // Debounce resize
    clearTimeout(this.resizeTimeout);
    this.resizeTimeout = setTimeout(() => {
      this.resizeCanvas();
    }, 200);
  }

  resizeCanvas() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }

  updateMode() {
    const inDrawingMode = this.isDrawingModeActive;

    if (inDrawingMode) {
      const style = getComputedStyle(this);
      this.brushColor = style.getPropertyValue("--mono-brush-color").trim() || "rgba(244, 63, 94, 0.75)";
      this.canvas.classList.add("drawing-mode");
      this.canvas.classList.remove("hidden");
    } else {
      this.canvas.classList.remove("drawing-mode");
      this.isDrawing = false;

      // Fade out and clear canvas if we were drawing
      if (!this.canvas.classList.contains("hidden")) {
        this.canvas.classList.add("hidden");
        // Wait for fade out animation before clearing
        setTimeout(() => {
          this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }, 300);
      }
    }
  }

  handleKeyDown(e) {
    const activeEl = document.activeElement;
    const isEditable = activeEl && (
      activeEl.tagName === "INPUT" ||
      activeEl.tagName === "TEXTAREA" ||
      activeEl.isContentEditable
    );
    if (isEditable) return;

    if (e.key === "b" || e.key === "B") {
      this.isDrawingModeActive = !this.isDrawingModeActive;
      this.updateMode();
      e.preventDefault();
    } else if (e.key === "Escape" && this.isDrawingModeActive) {
      this.isDrawingModeActive = false;
      this.updateMode();
      e.preventDefault();
    }
  }

  handleKeyUp(e) {
    // No-op for now, as drawing mode is toggled on keydown
  }

  getPointerPosition(clientX, clientY) {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: clientX - rect.left,
      y: clientY - rect.top
    };
  }

  handleMouseMove(e) {
    // Handle drawing
    if (this.isDrawing && this.isDrawingModeActive) {
      if (e.cancelable) e.preventDefault(); // Prevent text selection/scrolling while drawing
      const pos = this.getPointerPosition(e.clientX, e.clientY);
      this.points.push(pos);

      if (!this.animationFrameId) {
        this.animationFrameId = requestAnimationFrame(() => {
          this.drawPoints();
          this.animationFrameId = null;
        });
      }
    }
  }

  handleMouseDown(e) {
    if (this.isDrawingModeActive) {
      this.isDrawing = true;
      this.points = [];
      const pos = this.getPointerPosition(e.clientX, e.clientY);
      this.lastX = pos.x;
      this.lastY = pos.y;
      this.points.push(pos);

      if (!this.animationFrameId) {
        this.animationFrameId = requestAnimationFrame(() => {
          this.drawPoints();
          this.animationFrameId = null;
        });
      }
    }
  }

  handleMouseUp() {
    if (this.isDrawing && this.points.length > 0) {
       this.drawPoints();
    }
    this.isDrawing = false;
    this.points = [];
  }

  drawPoints() {
    if (this.points.length === 0) return;

    this.ctx.beginPath();
    this.ctx.moveTo(this.lastX, this.lastY);

    for (const point of this.points) {
        this.ctx.lineTo(point.x, point.y);
        this.lastX = point.x;
        this.lastY = point.y;
    }
    this.points = [];

    this.ctx.strokeStyle = this.brushColor || "rgba(244, 63, 94, 0.75)";
    this.ctx.lineWidth = 12;
    this.ctx.lineCap = "round";
    this.ctx.lineJoin = "round";
    this.ctx.stroke();
  }

  handleTouchStart(e) {
    if (this.isDrawingModeActive) {
      if (e.cancelable) e.preventDefault();
      const touch = e.touches[0];
      this.handleMouseDown({ clientX: touch.clientX, clientY: touch.clientY });
    }
  }

  handleTouchMove(e) {
    if (this.isDrawing && this.isDrawingModeActive) {
      if (e.cancelable) e.preventDefault();
      const touch = e.touches[0];
      this.handleMouseMove({
        clientX: touch.clientX,
        clientY: touch.clientY,
        cancelable: false,
        preventDefault: () => {},
      });
    }
  }


}

if (!customElements.get("mono-brush")) {
  customElements.define("mono-brush", MonoBrush);
}

// Automatically inject into page
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    if (!document.querySelector("mono-brush")) {
      document.body.appendChild(document.createElement("mono-brush"));
    }
  });
} else {
  if (!document.querySelector("mono-brush")) {
    document.body.appendChild(document.createElement("mono-brush"));
  }
}
