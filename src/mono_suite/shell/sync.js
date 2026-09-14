"use strict";

(() => {
  const frameSpace = document.getElementById("frame-space");
  const frameDoc = document.getElementById("frame-doc");
  const btnSpace = document.getElementById("btn-space");
  const btnDoc = document.getElementById("btn-doc");
  const btnExport = document.getElementById("btn-export");
  const exportLabel = document.getElementById("export-label");
  const statusDot = document.getElementById("status-dot");

  let currentView = "space";

  // ビューの切り替え（位置同期を行わず、純粋な表示切替のみ実施）
  function switchView(target) {
    if (target === currentView) return;
    currentView = target;

    if (target === "space") {
      frameDoc.className = "view-frame hidden";
      frameSpace.className = "view-frame active";
      btnDoc.classList.remove("active");
      btnSpace.classList.add("active");
    } else {
      frameSpace.className = "view-frame hidden";
      frameDoc.className = "view-frame active";
      btnSpace.classList.remove("active");
      btnDoc.classList.add("active");
    }
  }

  btnSpace.onclick = () => switchView("space");
  btnDoc.onclick = () => switchView("doc");

  // 完全ビルド（PDF書き出し）
  btnExport.onclick = async () => {
    btnExport.disabled = true;
    exportLabel.textContent = "Exporting...";
    statusDot.className = "status-dot syncing";

    try {
      const res = await fetch("/api/build", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        exportLabel.textContent = "Exported";
        setTimeout(() => {
          exportLabel.textContent = "Export PDF";
        }, 2000);
      } else {
        exportLabel.textContent = "Failed";
        setTimeout(() => {
          exportLabel.textContent = "Export PDF";
        }, 2000);
      }
    } catch (e) {
      exportLabel.textContent = "Error";
      setTimeout(() => {
        exportLabel.textContent = "Export PDF";
      }, 2000);
    } finally {
      btnExport.disabled = false;
      statusDot.className = "status-dot connected";
    }
  };

  // SSE (Server-Sent Events) による自動リロード
  function initSSE() {
    const sse = new EventSource("/events");

    sse.onopen = () => {
      statusDot.className = "status-dot connected";
    };

    sse.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.event === "reload") {
          statusDot.className = "status-dot syncing";
          const timestamp = Date.now();
          frameSpace.src = "/space?t=" + timestamp;
          frameDoc.src = "/doc?t=" + timestamp;
          setTimeout(() => {
            statusDot.className = "status-dot connected";
          }, 300);
        }
      } catch (err) {}
    };

    sse.onerror = () => {
      statusDot.className = "status-dot";
    };
  }

  initSSE();
})();
