class MonoExport extends MonoBaseElement {
    constructor() {
        super();
    }

    connectedCallback() {
        super.mountTemplate('mono-export-template');
        this.setupEventListeners();
    }

    collectData() {
        const data = {};
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith("mono_")) {
                try {
                    data[key] = JSON.parse(localStorage.getItem(key));
                } catch (e) {
                    data[key] = localStorage.getItem(key);
                }
            }
        }
        return data;
    }

    setupEventListeners() {
        const fab = this.shadowRoot.getElementById("mono-export-fab");
        const menu = this.shadowRoot.getElementById("mono-export-menu");
        const btnDownload = this.shadowRoot.getElementById("mono-export-download");
        const btnSync = this.shadowRoot.getElementById("mono-export-sync");

        fab.addEventListener("click", () => {
            menu.classList.toggle("hidden");
        });

        btnDownload.addEventListener("click", () => {
            const data = this.collectData();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `export_${new Date().getTime()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            menu.classList.add("hidden");
        });

        btnSync.addEventListener("click", async () => {
            const data = this.collectData();
            const apiMeta = document.querySelector('meta[name="mono-api-url"]');
            const apiUrl = apiMeta ? apiMeta.content : null;
            if (!apiUrl) {
                alert("サーバのURLが設定されていません。データを保存するには「Download JSON」を使用してください。");
                console.info("💡 [Mono] スタンドアロンモードです。手動でJSONをダウンロードしてください。");
                return;
            }

            try {
                const response = await fetch(apiUrl + "/api/data", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(data)
                });
                if (response.ok) {
                    const result = await response.json().catch(() => null);
                    if (result && result.status === "success") {
                        alert("✅ データをサーバに同期しました！");
                    } else {
                        const errMsg = (result && result.message) ? `: ${result.message}` : "";
                        alert(`❌ サーバへの同期に失敗しました${errMsg}\n\n「Download JSON」からローカルに保存してください。`);
                        console.info("💡 [Mono] サーバ処理エラー。");
                    }
                } else {
                    alert("❌ サーバへの同期に失敗しました。\n\nオフラインの可能性があります。「Download JSON」からローカルに保存してください。");
                    console.info("💡 [Mono] サーバエラー。ステータス: " + response.statusText);
                }
            } catch (error) {
                alert("❌ サーバへの同期に失敗しました。\n\nオフラインの可能性があります。「Download JSON」からローカルに保存してください。");
                console.info("💡 [Mono] オフラインまたはサーバ未起動です。");
            }
            menu.classList.add("hidden");
        });
    }
}

if (!customElements.get("mono-export")) {
    customElements.define("mono-export", MonoExport);
}