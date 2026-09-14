class MonoZoom extends MonoBaseElement {
    constructor() {
        super();
        this.targetSelectors = [
            'h1:not(.no-zoom)',
            'h2:not(.no-zoom)',
            'h3:not(.no-zoom)',
            'h4:not(.no-zoom)',
            'ul:not(.no-zoom)',
            'ol:not(.no-zoom)',
            'blockquote:not(.no-zoom)',
            'table:not(.no-zoom)',
            'mono-code-block:not(.no-zoom)',
            'img:not(.colab-badge):not(.no-zoom)',
            '.mono-math:not(.no-zoom)',
            'mono-score:not(.no-zoom)',
            'mono-section:not(.no-zoom)',
            '.column:not(.no-zoom)',
            'mono-flipcard:not(.no-zoom)',
            '[data-zoomable]'
        ].join(', ');
        
        this.activeTarget = null;
        this.hoverTimeout = null;
        this.isModalOpen = false;
        this.boundHandleMouseOver = this.handleMouseOver.bind(this);
        this.boundHandleMouseLeave = this.handleMouseLeave.bind(this);
        this.boundHandleScroll = this.handleScroll.bind(this);
        this.boundHandleKeyDown = this.handleKeyDown.bind(this);
        
        this.virtualSlides = []; // Array of Arrays of HTMLElements
        this.activeSlideIndex = 0;
        this.scrollTicking = false;
    }

    connectedCallback() {
        super.mountTemplate('mono-zoom-template');
        this.setupElements();
        this.setupEventListeners();
        this.setupVirtualSlideFocus();
    }

    disconnectedCallback() {
        this.removeEventListeners();
        if (this.activeTarget) {
            this.activeTarget.removeEventListener('mouseleave', this.boundHandleMouseLeave);
            this.activeTarget = null;
        }
    }

    setupElements() {
        this.trigger = this.shadowRoot.getElementById('zoom-trigger');
        this.overlay = this.shadowRoot.getElementById('zoom-overlay');
        this.closeBtn = this.shadowRoot.getElementById('zoom-close');
        this.content = this.shadowRoot.getElementById('zoom-content');
    }

    setupEventListeners() {
        document.addEventListener('mouseover', this.boundHandleMouseOver);
        document.addEventListener('scroll', this.boundHandleScroll, { passive: true });
        window.addEventListener('resize', this.boundHandleScroll, { passive: true });
        document.addEventListener('keydown', this.boundHandleKeyDown);
        
        this.trigger.addEventListener('click', () => this.openModal());
        this.trigger.addEventListener('mouseenter', () => this.keepTriggerVisible());
        this.trigger.addEventListener('mouseleave', () => this.hideTriggerDelayed());
        
        this.closeBtn.addEventListener('click', () => this.closeModal());
    }

    removeEventListeners() {
        document.removeEventListener('mouseover', this.boundHandleMouseOver);
        document.removeEventListener('scroll', this.boundHandleScroll);
        window.removeEventListener('resize', this.boundHandleScroll);
        document.removeEventListener('keydown', this.boundHandleKeyDown);
    }

    setupVirtualSlideFocus() {
        // Collect direct body elements, ignoring system tags
        const ignoredTags = new Set(['SCRIPT', 'TEMPLATE', 'STYLE', 'MONO-ZOOM', 'MONO-BRUSH', 'MONO-SYNC']);
        const elements = Array.from(document.body.children).filter(el => !ignoredTags.has(el.tagName));
        if (elements.length === 0) return;

        const hasExplicitHr = elements.some(el => el.tagName === 'HR');

        this.virtualSlides = [];
        let currentSlide = [];

        elements.forEach(el => {
            const tag = el.tagName;
            const isHr = (tag === 'HR');
            const isHeading = (!hasExplicitHr) && (tag === 'H1' || tag === 'H2');

            if (isHr || isHeading) {
                if (currentSlide.length > 0) {
                    this.virtualSlides.push(currentSlide);
                    currentSlide = [];
                }
                if (isHr) {
                    return;
                }
            }
            currentSlide.push(el);
        });

        if (currentSlide.length > 0) {
            this.virtualSlides.push(currentSlide);
        }

        // Run initial focus update
        this.updateActiveVirtualSlide();
    }

    updateActiveVirtualSlide() {
        if (this.virtualSlides.length === 0) return;

        const viewportHeight = window.innerHeight;
        const scrollY = window.scrollY;

        if (scrollY < 60) {
            this.activeSlideIndex = 0;
        } else {
            const focalPoint = viewportHeight * 0.35;
            let activeIndex = 0;

            for (let i = 0; i < this.virtualSlides.length; i++) {
                const firstEl = this.virtualSlides[i][0];
                if (!firstEl) continue;
                const top = firstEl.getBoundingClientRect().top;
                const nextSlide = this.virtualSlides[i + 1];
                const nextTop = (nextSlide && nextSlide[0])
                    ? nextSlide[0].getBoundingClientRect().top
                    : Infinity;

                if (top <= focalPoint + 50 && focalPoint < nextTop + 50) {
                    activeIndex = i;
                    break;
                }
                if (i === this.virtualSlides.length - 1 && top <= focalPoint + 100) {
                    activeIndex = i;
                }
            }

            this.activeSlideIndex = activeIndex;
        }

        // Apply .mono-ambient-dimmed to non-active slides
        this.virtualSlides.forEach((slide, idx) => {
            const isActive = (idx === this.activeSlideIndex);
            slide.forEach(el => {
                if (isActive) {
                    el.classList.remove('mono-ambient-dimmed');
                } else {
                    el.classList.add('mono-ambient-dimmed');
                }
            });
        });
    }

    handleMouseOver(e) {
        if (this.isModalOpen) return;

        const target = e.target.closest(this.targetSelectors);
        if (target) {
            if (this.activeTarget === target) {
                this.keepTriggerVisible();
                return;
            }

            if (this.activeTarget) {
                this.activeTarget.removeEventListener('mouseleave', this.boundHandleMouseLeave);
            }

            this.activeTarget = target;
            this.activeTarget.addEventListener('mouseleave', this.boundHandleMouseLeave);
            this.showTrigger();
        }
    }

    handleMouseLeave(e) {
        if (this.isModalOpen) return;
        this.hideTriggerDelayed();
    }

    handleScroll() {
        if (this.isModalOpen) return;
        if (this.activeTarget) {
            this.positionTrigger();
        }
        if (!this.scrollTicking) {
            this.scrollTicking = true;
            requestAnimationFrame(() => {
                this.updateActiveVirtualSlide();
                this.scrollTicking = false;
            });
        }
    }

    showTrigger() {
        clearTimeout(this.hoverTimeout);
        this.positionTrigger();
        this.trigger.classList.add('visible');
    }

    hideTriggerDelayed() {
        this.hoverTimeout = setTimeout(() => {
            this.trigger.classList.remove('visible');
            if (this.activeTarget) {
                this.activeTarget.removeEventListener('mouseleave', this.boundHandleMouseLeave);
                this.activeTarget = null;
            }
        }, 150);
    }

    keepTriggerVisible() {
        clearTimeout(this.hoverTimeout);
        this.trigger.classList.add('visible');
    }

    positionTrigger() {
        if (!this.activeTarget) return;

        const rect = this.activeTarget.getBoundingClientRect();
        
        let top = rect.top + 8;
        let left = rect.right - 8;

        if (left > window.innerWidth - 30) {
            left = window.innerWidth - 30;
        }
        if (top < 10) {
            top = 10;
        }

        this.trigger.style.top = `${top}px`;
        this.trigger.style.left = `${left}px`;
    }

    openModal() {
        if (!this.activeTarget) return;

        this.isModalOpen = true;
        this.previousActiveElement = document.activeElement;
        
        // Hide trigger
        this.trigger.classList.remove('visible');

        // Prevent body scroll
        document.body.style.overflow = 'hidden';

        // Clone target and append to content
        const clone = this.activeTarget.cloneNode(true);
        this.innerHTML = '';
        this.appendChild(clone);

        // Show overlay
        this.overlay.classList.remove('hidden');

        // Focus close button
        this.closeBtn.focus();
    }

    closeModal() {
        this.isModalOpen = false;
        this.overlay.classList.add('hidden');
        this.innerHTML = '';
        
        // Restore focus
        if (this.previousActiveElement) {
            this.previousActiveElement.focus();
        }
        
        // Restore body scroll
        document.body.style.overflow = '';
        
        // Reset active target
        this.activeTarget = null;
    }

    handleKeyDown(e) {
        // Ignore shortcut keys when typing inside editable fields
        const activeEl = document.activeElement;
        const isEditable = activeEl && (
            activeEl.tagName === 'INPUT' ||
            activeEl.tagName === 'TEXTAREA' ||
            activeEl.tagName === 'SELECT' ||
            activeEl.isContentEditable
        );

        // Toggle zoom on 'Z' key press
        if (!isEditable && (e.key === 'z' || e.key === 'Z')) {
            if (this.isModalOpen) {
                this.closeModal();
                e.preventDefault();
                return;
            } else if (this.activeTarget) {
                this.openModal();
                e.preventDefault();
                return;
            }
        }

        // Toggle Flat Mode on 'D' key press (switch between Ambient Focus and Plain view)
        if (!isEditable && !this.isModalOpen && (e.key === 'd' || e.key === 'D')) {
            document.body.classList.toggle('mono-flat-mode');
            e.preventDefault();
            return;
        }

        // Section navigation with J / K / ArrowDown / ArrowUp
        if (!isEditable && !this.isModalOpen && (e.key === 'j' || e.key === 'J' || e.key === 'ArrowDown' || e.key === 'k' || e.key === 'K' || e.key === 'ArrowUp')) {
            if (this.virtualSlides.length > 1) {
                let nextIndex = this.activeSlideIndex;
                if (e.key === 'j' || e.key === 'J' || e.key === 'ArrowDown') {
                    nextIndex = Math.min(this.activeSlideIndex + 1, this.virtualSlides.length - 1);
                } else {
                    nextIndex = Math.max(this.activeSlideIndex - 1, 0);
                }

                if (nextIndex !== this.activeSlideIndex) {
                    this.activeSlideIndex = nextIndex;
                    const targetEl = this.virtualSlides[nextIndex][0];
                    if (targetEl) {
                        targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        this.updateActiveVirtualSlide();
                    }
                    e.preventDefault();
                    return;
                }
            }
        }

        if (!this.isModalOpen) return;

        if (e.key === 'Escape') {
            this.closeModal();
            e.preventDefault();
            return;
        }
        
        // Focus trap
        if (e.key === 'Tab') {
            const shadowFocusables = Array.from(this.overlay.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'));
            const lightFocusables = Array.from(this.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'));
            const focusableElements = [...shadowFocusables, ...lightFocusables];
            if (focusableElements.length === 0) return;
            
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];
            const currentActive = this.shadowRoot.activeElement || document.activeElement;
            
            if (e.shiftKey) {
                if (currentActive === firstElement || currentActive === this) {
                    lastElement.focus();
                    e.preventDefault();
                }
            } else {
                if (currentActive === lastElement) {
                    firstElement.focus();
                    e.preventDefault();
                }
            }
        }
    }
}

if (!customElements.get('mono-zoom')) {
    customElements.define('mono-zoom', MonoZoom);
}

// Automatically inject into page
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (!document.querySelector('mono-zoom')) {
            document.body.appendChild(document.createElement('mono-zoom'));
        }
    });
} else {
    if (!document.querySelector('mono-zoom')) {
        document.body.appendChild(document.createElement('mono-zoom'));
    }
}
