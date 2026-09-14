class MonoAccount extends MonoInteractiveElement {
    constructor() {
        super();
        this.user = null;
    }

    connectedCallback() {
        if (super.connectedCallback) {
            super.connectedCallback();
        }
        this.mountTemplate();
        this.initializeAuth();
    }

    mountTemplate() {
        super.mountTemplate("mono-account-template");
        if (this.refs.actionBtn) {
            this.refs.actionBtn.addEventListener("click", () => this.toggleAuth());
        }
    }

    initializeAuth() {
        try {
            const savedAuth = this.loadState("mono_auth");
            if (savedAuth && savedAuth.user) {
                this.user = savedAuth.user;
            }
        } catch (e) {
            console.info("アカウント機能はオフラインです", e);
            this.user = null;
        }

        this.updateView();
        this.broadcastAuthState();
    }

    toggleAuth() {
        if (this.user) {
            // Logout
            this.user = null;
            try {
                this.removeState("mono_auth");
            } catch (e) {
                console.info("ログアウト時の状態保存に失敗しました", e);
            }
        } else {
            // Mock Login
            this.user = {
                id: "user-" + Math.random().toString(36).substring(2, 9),
                name: "Test User",
                token: "mock-jwt-token"
            };
            try {
                this.saveState("mono_auth", { user: this.user });
            } catch (e) {
                console.info("ログイン時の状態保存に失敗しました", e);
            }
        }

        this.updateView();
        this.broadcastAuthState();
    }

    updateView() {
        if (!this.refs.status || !this.refs.actionBtn) return;

        if (this.user) {
            this.refs.status.textContent = `Logged in as: ${this.user.name}`;
            this.refs.actionBtn.textContent = "Logout";
        } else {
            this.refs.status.textContent = "Guest Mode";
            this.refs.actionBtn.textContent = "Login";
        }
    }

    broadcastAuthState() {
        const payload = { user: this.user };
        const event = new CustomEvent("mono-auth-changed", {
            detail: payload,
            bubbles: true,
            composed: true,
        });
        window.dispatchEvent(event);
    }
}

if (!customElements.get("mono-account")) {
    customElements.define("mono-account", MonoAccount);
}
