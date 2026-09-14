class MonoSessionJoin extends MonoInteractiveElement {
  constructor() {
    super();
    this.mountTemplate('mono-session-join-template');
  }

  connectedCallback() {
    if (super.connectedCallback) {
        super.connectedCallback();
    }
    this.title = this.getAttribute("title") || "セッション参加";

    const titleEl = this.shadowRoot.getElementById("join-title");
    if (titleEl) titleEl.textContent = this.title;

    this.joinView = this.shadowRoot.getElementById("join-view");
    this.joinedView = this.shadowRoot.getElementById("joined-view");
    this.inputField = this.shadowRoot.getElementById("session-id-input");
    this.joinBtn = this.shadowRoot.getElementById("join-btn");
    this.leaveBtn = this.shadowRoot.getElementById("leave-btn");
    this.currentSessionSpan = this.shadowRoot.getElementById("current-session-id");
    this.errorMsg = this.shadowRoot.getElementById("error-msg");

    this.joinBtn.addEventListener("click", () => this.handleJoin());
    this.leaveBtn.addEventListener("click", () => this.handleLeave());
    this.inputField.addEventListener("keydown", (e) => {
      if (e.key === "Enter") this.handleJoin();
    });

    this.checkStatus();
  }

  checkStatus() {
    try {
      const data = this.loadState("mono_session_id");
      if (data && data.sessionId) {
        this.showJoinedView(data.sessionId);
        return;
      }
    } catch (e) {
      console.info("セッション状態の読み込みに失敗しました", e);
    }
    this.showJoinView();
  }

  generateUserId() {
    return 'user-' + Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
  }

  handleJoin() {
    const rawVal = this.inputField.value.trim();

    // バリデーション: 英数字、ハイフン許可
    const isValid = /^[a-zA-Z0-9\-]+$/.test(rawVal);

    if (!isValid || rawVal.length === 0) {
      this.errorMsg.style.display = "block";
      return;
    }
    this.errorMsg.style.display = "none";

    const sessionId = rawVal;

    // 既存のユーザーIDがあるか確認
    let userId = this.generateUserId();
    try {
      const data = this.loadState("mono_session_id");
      if (data && data.userId) userId = data.userId;
    } catch(e) {}

    const payload = {
      timestamp: new Date().toISOString(),
      sessionId: sessionId,
      userId: userId
    };

    try {
      this.saveState("mono_session_id", payload);
    } catch (e) {
      console.info("セッション情報の保存に失敗しました", e);
      alert("セッション情報の保存に失敗しました");
      return;
    }

    // mono-dataイベント発行
    const event = new CustomEvent("mono-data", {
      detail: payload,
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);

    // グローバルなカスタムイベント（他のコンポーネントが検知できるように）
    window.dispatchEvent(new CustomEvent("mono-session-changed"));

    this.showJoinedView(sessionId);
  }

  handleLeave() {
    // 変更ボタン：ここでは単にViewを戻すだけ（localStorageをクリアするかは運用次第だが、変更可能にするため）
    this.showJoinView();
  }

  showJoinView() {
    if(this.joinView) this.joinView.style.display = "block";
    if(this.joinedView) this.joinedView.style.display = "none";
  }

  showJoinedView(sessionId) {
    if(this.joinView) this.joinView.style.display = "none";
    if(this.joinedView) this.joinedView.style.display = "block";
    if(this.currentSessionSpan) this.currentSessionSpan.textContent = sessionId;
  }
}

if (!customElements.get("mono-session-join")) {
  customElements.define("mono-session-join", MonoSessionJoin);
}
