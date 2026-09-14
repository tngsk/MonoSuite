"use strict";

(() => {
  const frameSpace = document.getElementById("frame-space");
  const frameDoc = document.getElementById("frame-doc");
  const btnSpace = document.getElementById("btn-space");
  const btnDoc = document.getElementById("btn-doc");
  const btnExport = document.getElementById("btn-export");
  const statusDot = document.getElementById("status-dot");
  const headingDisplay = document.getElementById("current-heading-title");

  let currentView = "space";
  let lastKnownId = null;

  // Spaceビューから現在フォーカスされているセクションIDを取得
  function getSpaceActiveId() {
    try {
      const doc = frameSpace.contentDocument || frameSpace.contentWindow?.document;
      if (!doc) return null;
      const currentBtn = doc.querySelector('#section-toc button[aria-current="true"]');
      if (currentBtn?.dataset.section) {
        return currentBtn.dataset.section;
      }
      // フォールバック: データ属性から最初のID
      const firstBtn = doc.querySelector('#section-toc button[data-section]');
      return firstBtn?.dataset.section || null;
    } catch (e) {
      return null;
    }
  }

  // Docビューから現在スクロール上端にある見出しIDを取得
  function getDocActiveId() {
    try {
      const doc = frameDoc.contentDocument || frameDoc.contentWindow?.document;
      if (!doc) return null;
      const headings = Array.from(doc.querySelectorAll("h1[id], h2[id], h3[id], h4[id]"));
      if (headings.length === 0) return null;

      const scrollTop = frameDoc.contentWindow?.scrollY || doc.documentElement.scrollTop || 0;
      let closestId = headings[0].id;

      for (const h of headings) {
        const top = h.offsetTop;
        if (top <= scrollTop + 80) {
          closestId = h.id;
        } else {
          break;
        }
      }
      return closestId;
    } catch (e) {
      return null;
    }
  }

  // Spaceビューの特定セクションをフォーカス
  function setSpaceActiveId(id) {
    if (!id) return;
    try {
      const doc = frameSpace.contentDocument || frameSpace.contentWindow?.document;
      if (!doc) return;
      const targetBtn = doc.querySelector(`#section-toc button[data-section="${id}"]`);
      if (targetBtn) {
        targetBtn.click();
      }
    } catch (e) {}
  }

  // Docビューの特定セクションへスムーズスクロール
  function setDocActiveId(id) {
    if (!id) return;
    try {
      const doc = frameDoc.contentDocument || frameDoc.contentWindow?.document;
      if (!doc) return;
      const el = doc.getElementById(id);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    } catch (e) {}
  }

  // ビューの切り替え実行
  function switchView(target) {
    if (target === currentView) return;

    if (currentView === "space") {
      // Space -> Doc
      const activeId = getSpaceActiveId() || lastKnownId;
      if (activeId) {
        lastKnownId = activeId;
        setDocActiveId(activeId);
      }
      frameSpace.classList.remove("active");
      frameSpace.classList.add("hidden");
      frameDoc.classList.remove("hidden");
      frameDoc.classList.add("active");
      btnSpace.classList.remove("active");
      btnDoc.classList.add("active");
      currentView = "doc";
    } else {
      // Doc -> Space
      const activeId = getDocActiveId() || lastKnownId;
      if (activeId) {
        lastKnownId = activeId;
        setSpaceActiveId(activeId);
      }
      frameDoc.classList.remove("active");
      frameDoc.classList.add("hidden");
      frameSpace.classList.remove("hidden");
      frameSpace.classList.add("active");
      btnDoc.classList.remove("active");
      btnSpace.classList.add("active");
      currentView = "space";
    }
    updateHeadingTitle(lastKnownId);
  }

  function updateHeadingTitle(id) {
    if (!id) return;
    try {
      const doc = frameDoc.contentDocument || frameDoc.contentWindow?.document;
      const el = doc?.getElementById(id);
      if (el) {
        headingDisplay.textContent = el.textContent.trim();
      }
    } catch (e) {}
  }

  btnSpace.onclick = () => switchView("space");
  btnDoc.onclick = () => switchView("doc");

  // 完全ビルド（PDF書き出し）
  btnExport.onclick = async () => {
    btnExport.disabled = true;
    btnExport.textContent = "書き出し中...";
    statusDot.classList.add("updating");

    try {
      const res = await fetch("/api/build", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        alert("✅ 配布セット（PDF含む）の生成が完了しました！");
      } else {
        alert("❌ ビルドエラー: " + (data.error || "生成に失敗しました"));
      }
    } catch (e) {
      alert("❌ 接続エラー: " + e.message);
    } finally {
      btnExport.disabled = false;
      btnExport.textContent = "配布PDF書き出し";
      statusDot.classList.remove("updating");
    }
  };

  // SSE (Server-Sent Events) による自動リロード
  function initSSE() {
    const sse = new EventSource("/events");

    sse.onopen = () => {
      statusDot.classList.remove("updating");
    };

    sse.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.event === "reload") {
          statusDot.classList.add("updating");
          const activeId = currentView === "space" ? getSpaceActiveId() : getDocActiveId();
          lastKnownId = activeId || lastKnownId;

          // iframe をリロード
          frameSpace.src = "/space?t=" + Date.now();
          frameDoc.src = "/doc?t=" + Date.now();

          // ロード完了後に位置を復元
          let loadedCount = 0;
          const onFrameLoad = () => {
            loadedCount++;
            if (loadedCount >= 2) {
              if (currentView === "space") {
                setSpaceActiveId(lastKnownId);
              } else {
                setDocActiveId(lastKnownId);
              }
              statusDot.classList.remove("updating");
            }
          };
          frameSpace.onload = onFrameLoad;
          frameDoc.onload = onFrameLoad;
        }
      } catch (err) {}
    };

    sse.onerror = () => {
      statusDot.classList.add("updating");
    };
  }

  initSSE();
})();
