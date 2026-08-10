/* Abyss UI polish layer. Keeps the application logic in app.js intact. */
(function () {
  "use strict";

  function injectStyles() {
    if (document.getElementById("abyssPolishStyles")) return;
    const style = document.createElement("style");
    style.id = "abyssPolishStyles";
    style.textContent = `
      .sidebar-brand{display:flex;align-items:center;gap:9px;padding:15px 16px 4px;color:#f5f5f7;font-size:14px;font-weight:600;letter-spacing:-.02em}
      .sidebar-brand .app-icon{width:23px!important;height:23px!important;border-radius:7px!important;font-size:13px}
      .new-chat-shortcut{margin-left:auto;color:#626571;font-size:11px}
      .chat-group-label{padding:15px 16px 6px;color:#555963;font-size:9px;font-weight:600;letter-spacing:.12em}
      .chat-group-label:first-child{padding-top:8px}
      .sidebar-search-hint{position:absolute;right:9px;top:50%;transform:translateY(-50%);font-size:9px;color:#555963;pointer-events:none}
      .convo-search-container{position:relative}
      .convo-search-container input{padding-right:38px!important}

      .chat-topbar{display:flex!important;align-items:center!important}
      .chat-title{position:absolute!important;left:50%!important;transform:translateX(-50%)!important}
      .chat-topbar .topbar-model{margin-left:auto!important;margin-right:42px!important}
      .topbar-model .code-tag{display:none!important}
      .abyss-more-btn{position:absolute;right:15px;top:50%;transform:translateY(-50%);width:30px;height:30px;border:0;background:transparent;color:#777b86;border-radius:8px;cursor:pointer;font-size:16px}
      .abyss-more-btn:hover{background:rgba(255,255,255,.05);color:#e6e6ea}
      .abyss-secondary-menu{position:absolute;z-index:30;right:14px;top:43px;width:270px;padding:6px;background:#11151d;border:1px solid rgba(255,255,255,.10);border-radius:12px;box-shadow:0 18px 50px rgba(0,0,0,.45);opacity:0;transform:translateY(-4px) scale(.98);pointer-events:none;transition:opacity .14s ease,transform .14s ease}
      .abyss-secondary-menu.open{opacity:1;transform:none;pointer-events:auto}
      .abyss-secondary-menu button{width:100%;display:flex;align-items:center;gap:11px;padding:10px;border:0;border-radius:8px;background:transparent;color:#e8e8ed;text-align:left;cursor:pointer}
      .abyss-secondary-menu button:hover{background:rgba(255,255,255,.05)}
      .abyss-secondary-menu button>i{width:28px;height:28px;display:grid;place-items:center;border-radius:8px;background:rgba(139,92,246,.10);color:#a98cff}
      .abyss-secondary-menu b,.abyss-secondary-menu small{display:block}
      .abyss-secondary-menu b{font-size:12px;font-weight:500}
      .abyss-secondary-menu small{margin-top:2px;color:#777b86;font-size:10px}

      .messages{padding-top:42px!important;gap:30px!important}
      .msg .bubble-body.ai-body{background:transparent!important;border-color:transparent!important;padding:4px 0!important;border-radius:0!important}
      .msg .bubble-body.user-body{background:#151a22!important;border:1px solid rgba(255,255,255,.065)!important;box-shadow:none!important}
      .msg .bubble{max-width:min(76%,880px)!important}
      .msg .bubble-header{margin-bottom:5px!important}
      .msg .bubble-time{font-size:10px!important}
      .msg .bubble-name{font-weight:600!important}
      .msg.ai{align-items:flex-start!important}
      .msg.user .bubble{max-width:min(64%,720px)!important}
      .msg.user{padding-left:8%!important}
      .msg.ai{padding-right:8%!important}

      .input-area{padding-top:10px!important}
      .input-wrap{border-radius:13px!important;min-height:50px!important}
      .send-btn{width:32px!important;height:32px!important;border-radius:9px!important}
      .statusbar{height:24px!important}

      .abyss-utility-modal{position:fixed;inset:0;z-index:100;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:opacity .15s ease}
      .abyss-utility-modal.open{opacity:1;pointer-events:auto}
      .abyss-modal-backdrop{position:absolute;inset:0;background:rgba(0,0,0,.58);backdrop-filter:blur(7px)}
      .abyss-modal{position:relative;width:min(560px,calc(100vw - 36px));max-height:min(620px,calc(100vh - 70px));overflow:auto;background:#10141b;border:1px solid rgba(255,255,255,.10);border-radius:16px;box-shadow:0 30px 90px rgba(0,0,0,.55);transform:translateY(8px) scale(.98);transition:transform .16s ease}
      .abyss-utility-modal.open .abyss-modal{transform:none}
      .abyss-modal header{display:flex;align-items:center;justify-content:space-between;padding:18px 20px;border-bottom:1px solid rgba(255,255,255,.06)}
      .abyss-modal-eyebrow{display:block;color:#8170b9;font-size:9px;letter-spacing:.14em;font-weight:600;margin-bottom:4px}
      .abyss-modal h2{margin:0;color:#f2f2f5;font-size:18px;font-weight:600;letter-spacing:-.025em}
      #abyssModalClose{width:30px;height:30px;border:0;border-radius:8px;background:transparent;color:#777b86;cursor:pointer}
      #abyssModalClose:hover{background:rgba(255,255,255,.05);color:#fff}
      #abyssModalBody{padding:8px 12px 14px}
      .utility-loading,.utility-empty{padding:34px 18px;text-align:center;color:#70747f;font-size:12px}
      .memory-modal-row,.tool-modal-row{display:flex;align-items:center;gap:12px;padding:11px 8px;border-radius:10px}
      .memory-modal-row:hover,.tool-modal-row:hover{background:rgba(255,255,255,.035)}
      .memory-modal-icon,.tool-modal-icon{width:34px;height:34px;flex:none;display:grid;place-items:center;border-radius:9px;background:rgba(139,92,246,.10);color:#a88cff}
      .memory-modal-copy,.tool-modal-row>div:last-child{min-width:0;flex:1}
      .memory-modal-copy strong,.tool-modal-row strong{display:block;color:#e7e7eb;font-size:12px;font-weight:500}
      .memory-modal-copy span,.tool-modal-row span{display:block;margin-top:3px;color:#777b86;font-size:11px;line-height:1.45;white-space:normal}
      .memory-forget{width:28px;height:28px;border:0;border-radius:7px;background:transparent;color:#5f626c;cursor:pointer}
      .memory-forget:hover{background:rgba(239,68,68,.08);color:#f87171}

      @media(max-width:800px){
        .sidebar{width:220px!important;min-width:220px!important}
        .msg.user{padding-left:2%!important}.msg.ai{padding-right:2%!important}
      }
    `;
    document.head.appendChild(style);
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function groupChats() {
    const list = document.getElementById("chatList");
    if (!list || list.dataset.grouped === "true") return;

    const items = Array.from(list.querySelectorAll(":scope > .convo-item"));
    if (!items.length) return;

    const current = items.find(i => i.classList.contains("active")) || items[0];
    const recent = items.filter(i => i !== current).slice(0, 3);
    const earlier = items.filter(i => i !== current && !recent.includes(i));

    list.innerHTML = "";
    list.dataset.grouped = "true";

    const appendGroup = (label, group) => {
      if (!group.length) return;
      list.appendChild(el("div", "chat-group-label", label));
      group.forEach(item => list.appendChild(item));
    };

    appendGroup("CURRENT", [current]);
    appendGroup("RECENT", recent);
    appendGroup("EARLIER", earlier);
  }

  function addSecondaryMenu() {
    if (document.getElementById("abyssSecondaryMenu")) return;
    const trigger = el("button", "abyss-more-btn");
    trigger.id = "abyssMoreBtn";
    trigger.type = "button";
    trigger.title = "Abyss tools";
    trigger.innerHTML = '<i class="ti ti-dots"></i>';
    const topbar = document.querySelector(".chat-topbar");
    if (!topbar) return;
    topbar.appendChild(trigger);

    const menu = el("div", "abyss-secondary-menu");
    menu.id = "abyssSecondaryMenu";
    menu.innerHTML = `
      <button type="button" data-panel="memory"><i class="ti ti-brain"></i><span><b>Memory</b><small>Saved things Abyss remembers</small></span></button>
      <button type="button" data-panel="tools"><i class="ti ti-tool"></i><span><b>Tools</b><small>Calculator, files, terminal & search</small></span></button>`;
    topbar.appendChild(menu);

    trigger.addEventListener("click", e => { e.stopPropagation(); menu.classList.toggle("open"); });
    menu.querySelectorAll("button").forEach(button => button.addEventListener("click", () => openUtilityPanel(button.dataset.panel)));
    document.addEventListener("click", e => { if (!menu.contains(e.target) && e.target !== trigger) menu.classList.remove("open"); });
  }

  function openUtilityPanel(kind) {
    document.getElementById("abyssSecondaryMenu")?.classList.remove("open");
    let modal = document.getElementById("abyssUtilityModal");
    if (!modal) {
      modal = el("div", "abyss-utility-modal");
      modal.id = "abyssUtilityModal";
      modal.innerHTML = `<div class="abyss-modal-backdrop"></div><section class="abyss-modal" role="dialog" aria-modal="true"><header><div><span class="abyss-modal-eyebrow">ABYSS</span><h2 id="abyssModalTitle">Memory</h2></div><button id="abyssModalClose" type="button" aria-label="Close"><i class="ti ti-x"></i></button></header><div id="abyssModalBody"></div></section>`;
      document.body.appendChild(modal);
      modal.querySelector(".abyss-modal-backdrop").addEventListener("click", closeUtilityPanel);
      modal.querySelector("#abyssModalClose").addEventListener("click", closeUtilityPanel);
    }
    modal.classList.add("open");
    const title = document.getElementById("abyssModalTitle");
    const body = document.getElementById("abyssModalBody");
    if (kind === "memory") { title.textContent = "Memory"; renderMemoryModal(body); }
    else { title.textContent = "Tools"; renderToolsModal(body); }
  }

  function closeUtilityPanel() { document.getElementById("abyssUtilityModal")?.classList.remove("open"); }

  async function renderMemoryModal(body) {
    body.innerHTML = '<div class="utility-loading">Loading memories…</div>';
    try {
      const response = await fetch("/memories");
      const data = await response.json();
      const memories = data.memories || [];
      if (!memories.length) { body.innerHTML = '<div class="utility-empty">Abyss has not saved any memories yet.</div>'; return; }
      body.innerHTML = '<div class="memory-modal-list"></div>';
      const list = body.querySelector(".memory-modal-list");
      memories.forEach(memory => {
        const row = el("div", "memory-modal-row");
        row.innerHTML = `<div class="memory-modal-icon"><i class="ti ti-brain"></i></div><div class="memory-modal-copy"><strong>Memory #${memory.id}</strong><span>${escapeHtml(memory.content)}</span></div><button class="memory-forget" title="Forget memory"><i class="ti ti-trash"></i></button>`;
        row.querySelector(".memory-forget").addEventListener("click", async () => {
          await fetch(`/memories/${memory.id}`, { method: "DELETE" });
          renderMemoryModal(body);
          if (typeof loadMemories === "function") loadMemories();
        });
        list.appendChild(row);
      });
    } catch (_) { body.innerHTML = '<div class="utility-empty">Could not load memories.</div>'; }
  }

  function renderToolsModal(body) {
    const tools = [["ti-math", "Calculator", "Calculate expressions and conversions."],["ti-folder", "Filesystem", "Inspect and work with project files."],["ti-terminal", "Terminal", "Run commands in the Abyss environment."],["ti-search", "Search", "Search the web through Abyss tools."]];
    body.innerHTML = '<div class="tools-modal-list"></div>';
    const list = body.querySelector(".tools-modal-list");
    tools.forEach(([icon,name,description]) => {
      const row = el("div", "tool-modal-row");
      row.innerHTML = `<div class="tool-modal-icon"><i class="ti ${icon}"></i></div><div><strong>${name}</strong><span>${description}</span></div>`;
      list.appendChild(row);
    });
  }

  function escapeHtml(value) {
    return String(value).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\"/g,"&quot;").replace(/'/g,"&#039;");
  }

  function refineStaticChrome() {
    document.querySelector(".titlebar-right .model-badge")?.remove();
    const status = document.querySelector(".statusbar .sb-left");
    if (status) status.innerHTML = '<span class="sb-dot"></span><span>Status: Connected</span>';
  }

  function boot() {
    injectStyles();
    refineStaticChrome();
    addSecondaryMenu();

    const list = document.getElementById("chatList");
    if (list) {
      const observer = new MutationObserver(() => {
        if (list.dataset.polishing === "true") return;
        list.dataset.polishing = "true";
        list.dataset.grouped = "false";
        requestAnimationFrame(() => { groupChats(); list.dataset.polishing = "false"; });
      });
      observer.observe(list, { childList: true });
      requestAnimationFrame(groupChats);
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
  else boot();
})();
