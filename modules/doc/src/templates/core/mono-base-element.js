class MonoBaseElement extends HTMLElement {
    constructor(options = { shadowMode: 'open' }) {
        super();
        this.refs = {};
        this._isMounted = false; // 二重マウント防止用フラグ

        if (options && options.shadowMode) {
            this.attachShadow({ mode: options.shadowMode });
        }
    }

    /**
     * テンプレートをマウントし、data-ref要素をキャッシュする。
     * @param {string} templateId
     */
    mountTemplate(templateId) {
        if (this._isMounted) return;

        const template = document.getElementById(templateId);
        if (!template) {
            console.error(`[Mono] Template #${templateId} not found.`);
            return;
        }

        const root = this.shadowRoot || this;
        root.appendChild(template.content.cloneNode(true));

        // data-refのキャッシュ（セキュリティのためtextContent等の操作を想定）
        root.querySelectorAll("[data-ref]").forEach((el) => {
            this.refs[el.dataset.ref] = el;
        });

        this._isMounted = true;
    }

    /**
     * Get the Mono version from the meta tag.
     * @returns {string} The version string, or "unknown" if not found.
     */
    getMonoVersion() {
        const meta = document.querySelector('meta[name="mono-version"]');
        return meta ? meta.dataset.monoVersion || "unknown" : "unknown";
    }

    /**
     * Save data to localStorage with a version wrapper.
     * @param {string} key
     * @param {any} data
     * @throws {Error} if localStorage is not available or quota is exceeded
     */
    saveState(key, data) {
        try {
            const payload = {
                _version: this.getMonoVersion(),
                data: data
            };
            localStorage.setItem(key, JSON.stringify(payload));
        } catch (e) {
            console.warn(`Failed to save state to localStorage for key: ${key}`, e);
            throw e;
        }
    }

    /**
     * Load data from localStorage and unwrap the version wrapper.
     * Checks if the data has a _version field. If not, assumes it's legacy data.
     * @param {string} key
     * @returns {any|null} The original data, or null if not found.
     * @throws {Error} if localStorage is not available
     */
    loadState(key) {
        try {
            const raw = localStorage.getItem(key);
            if (!raw) return null;

            // mono-notebook, mono-textfield-input のテスト用キーなど、JSONでない場合への対応
            let parsed;
            try {
                parsed = JSON.parse(raw);
            } catch (e) {
                return raw;
            }

            // Wrapper check
            if (parsed && typeof parsed === 'object' && '_version' in parsed && 'data' in parsed) {
                const currentVersion = this.getMonoVersion();
                if (parsed._version !== currentVersion) {
                    // Future implementation: Version migration logic here
                    console.info(`[Mono] Version mismatch for ${key}: Data version ${parsed._version}, Current version ${currentVersion}. Proceeding to load.`);
                }
                return parsed.data;
            }

            // Legacy data (unwrapped)
            return parsed;
        } catch (e) {
            console.warn(`Failed to read state from localStorage for key: ${key}`, e);
            throw e;
        }
    }

    /**
     * Remove data from localStorage.
     * @param {string} key
     * @throws {Error} if localStorage is not available
     */
    removeState(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.warn(`Failed to remove state from localStorage for key: ${key}`, e);
            throw e;
        }
    }
}
