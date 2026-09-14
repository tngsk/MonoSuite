"use strict";

(() => {
  const btnExport = document.getElementById("mono-export-btn");
  const exportLabel = document.getElementById("mono-export-label");
  const statusDot = document.getElementById("mono-status-dot");

  if (btnExport) {
    btnExport.onclick = async () => {
      btnExport.disabled = true;
      if (exportLabel) exportLabel.textContent = "Exporting...";
      if (statusDot) statusDot.className = "mono-nav-dot syncing";

      try {
        const res = await fetch("/api/build", { method: "POST" });
        const data = await res.json();
        if (exportLabel) {
          exportLabel.textContent = data.success ? "Exported" : "Failed";
          setTimeout(() => {
            exportLabel.textContent = "Export PDF";
          }, 2000);
        }
      } catch (e) {
        if (exportLabel) {
          exportLabel.textContent = "Error";
          setTimeout(() => {
            exportLabel.textContent = "Export PDF";
          }, 2000);
        }
      } finally {
        btnExport.disabled = false;
        if (statusDot) statusDot.className = "mono-nav-dot connected";
      }
    };
  }

  // SSE (Server-Sent Events) 自動再読み込み
  function initSSE() {
    if (!statusDot) return;
    const sse = new EventSource("/events");

    sse.onopen = () => {
      statusDot.className = "mono-nav-dot connected";
      statusDot.title = "開発サーバー接続中";
    };

    sse.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.event === "reload") {
          statusDot.className = "mono-nav-dot syncing";
          statusDot.title = "原稿更新を検知・再読み込み中";
          window.location.reload();
        }
      } catch (err) {}
    };

    sse.onerror = () => {
      statusDot.className = "mono-nav-dot";
      statusDot.title = "切断";
    };
  }

  initSSE();
})();
