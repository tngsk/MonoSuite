class MonoLink extends MonoBaseElement {
    constructor() {
        super();
        this.mountTemplate('mono-link-template');
    }

    connectedCallback() {
        this.render();
    }

    static get observedAttributes() {
        return ['url', 'title', 'desc', 'image', 'card-style'];
    }

    attributeChangedCallback() {
        this.render();
    }

    getDomain(urlStr) {
        try {
            const url = new URL(urlStr);
            return url.hostname;
        } catch (e) {
            return urlStr;
        }
    }

    getFavicon(urlStr) {
        try {
            const url = new URL(urlStr);
            return `${url.protocol}//${url.hostname}/favicon.ico`;
        } catch (e) {
            return '';
        }
    }

    render() {
        const container = this.shadowRoot.querySelector('.mono-link-container');
        const titleEl = this.shadowRoot.querySelector('.mono-link-title');
        const descEl = this.shadowRoot.querySelector('.mono-link-desc');
        const domainEl = this.shadowRoot.querySelector('.mono-link-domain');
        const imageEl = this.shadowRoot.querySelector('.mono-link-image');
        const placeholderEl = this.shadowRoot.querySelector('.mono-link-image-placeholder');
        const faviconEl = this.shadowRoot.querySelector('.mono-link-favicon');

        const url = this.getAttribute('url') || '';
        const title = this.getAttribute('title') || '';
        const desc = this.getAttribute('desc') || '';
        const image = this.getAttribute('image') || '';
        const cardStyle = this.getAttribute('card-style') || 'full';

        container.href = url;

        const domain = this.getDomain(url);

        // Use domain if title is empty
        titleEl.textContent = title || domain;
        descEl.textContent = desc;
        domainEl.textContent = domain;

        if (image) {
            imageEl.style.backgroundImage = `url(${image})`;
            imageEl.style.display = 'block';
            placeholderEl.style.display = 'none';

            const testImg = new Image();
            testImg.onerror = () => {
                imageEl.style.display = 'none';
                placeholderEl.style.display = 'flex';
            };
            testImg.src = image;
        } else {
            imageEl.style.display = 'none';
            placeholderEl.style.display = 'flex';
        }

        const faviconUrl = this.getFavicon(url);
        if (faviconUrl) {
            faviconEl.style.backgroundImage = `url(${faviconUrl})`;
            // If favicon fails to load, the background will just be empty or we could add error handling
        }

        // Apply style class
        container.className = `mono-link-container mono-link-style-${cardStyle}`;
    }
}

if (!customElements.get('mono-link')) {
    customElements.define('mono-link', MonoLink);
}
