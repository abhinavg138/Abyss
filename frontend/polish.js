/* Abyss UI polish layer. Keeps the application logic in app.js intact. */
(function () {
  "use strict";

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

    // The existing /chats endpoint intentionally returns names only. Keep the
    // visual grouping honest: current/recent items first, then the remainder.
    const current = items.find(i => i.dataset.name === window.currentChat) || items[0];
    const recent = items.filter(i => i !== current).slice(0, 3);
    const earlier = items.filter(i => i !== current && !recent.includes(i));

    list.innerHTML = "";
    list.dataset.grouped = "true";

    const appendGroup = (label, group) => {
      if (!group.length) return;
      const heading = el("div", "chat-group-label", label);
      list.appendChild(heading);
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
      <button type="button" data-panel="memory">
        <i class="ti ti-brain"></i>
        <span><b>Memory</b><small>Saved things Abyss remembers</small></span>
      </button>
      <button type="button" data-panel="tools">
        <i class="ti ti-tool"></i>
        <span><b>Tools</b><small>Calculator, files, terminal & search</small></span>
      </button>`;
    topbar.appendChild(menu);

    trigger.addEventListener("click", (event) => {
      event.stopPropagation();
      menu.classList.toggle("open");
    });

    menu.querySelectorAll("button").forEach(button => {
      button.addEventListener("click", () => openUtilityPanel(button.dataset.panel));
    });

    document.addEventListener("click", (event) => {
      if (!menu.contains(event.target) && event.target !== trigger) {
        menu.classList.remove("open");
      }
    });
  }

  function openUtilityPanel(kind) {
    const menu = document.getElementById("abyssSecondaryMenu");
    menu?.classList.remove("open");

    let modal = document.getElementById("abyssUtilityModal");
    if (!modal) {
      modal = el("div", "abyss-utility-modal");
      modal.id = "abyssUtilityModal";
      modal.innerHTML = `
        <div class="abyss-modal-backdrop"></div>
        <section class="abyss-modal" role="dialog" aria-modal="true">
          <header>
            <div>
              <span class="abyss-modal-eyebrow">ABYSS</span>
              <h2 id="abyssModalTitle">Memory</h2>
            </div>
            <button id="abyssModalClose" type="button" aria-label="Close"><i class="ti ti-x"></i></button>
          </header>
          <div id="abyssModalBody"></div>
        </section>`;
      document.body.appendChild(modal);

      modal.querySelector(".abyss-modal-backdrop").addEventListener("click", closeUtilityPanel);
      modal.querySelector("#abyssModalClose").addEventListener("click", closeUtilityPanel);
    }

    modal.classList.add("open");
    const title = document.getElementById("abyssModalTitle");
    const body = document.getElementById("abyssModalBody");

    if (kind === "memory") {
      title.textContent = "Memory";
      renderMemoryModal(body);
    } else {
      title.textContent = "Tools";
      renderToolsModal(body);
    }
  }

  function closeUtilityPanel() {
    document.getElementById("abyssUtilityModal")?.classList.remove("open");
  }

  async function renderMemoryModal(body) {
    body.innerHTML = '<div class="utility-loading">Loading memories…</div>';
    try {
      const response = await fetch("/memories");
      const data = await response.json();
      const memories = data.memories || [];
      if (!memories.length) {
        body.innerHTML = '<div class="utility-empty">Abyss has not saved any memories yet.</div>';
        return;
      }
      body.innerHTML = '<div class="memory-modal-list"></div>';
      const list = body.querySelector(".memory-modal-list");
      memories.forEach(memory => {
        const row = el("div", "memory-modal-row");
        row.innerHTML = `
          <div class="memory-modal-icon"><i class="ti ti-brain"></i></div>
          <div class="memory-modal-copy">
            <strong>Memory #${memory.id}</strong>
            <span>${escapeHtml(memory.content)}</span>
          </div>
          <button class="memory-forget" title="Forget memory"><i class="ti ti-trash"></i></button>`;
        row.querySelector(".memory-forget").addEventListener("click", async () => {
          await fetch(`/memories/${memory.id}`, { method: "DELETE" });
          renderMemoryModal(body);
          if (typeof loadMemories === "function") loadMemories();
        });
        list.appendChild(row);
      });
    } catch (error) {
      body.innerHTML = '<div class="utility-empty">Could not load memories.</div>';
    }
  }

  function renderToolsModal(body) {
    const tools = [
      ["ti-math", "Calculator", "Calculate expressions and conversions."],
      ["ti-folder", "Filesystem", "Inspect and work with project files."],
      ["ti-terminal", "Terminal", "Run commands in the Abyss environment."],
      ["ti-search", "Search", "Search the web through Abyss tools."]
    ];
    body.innerHTML = '<div class="tools-modal-list"></div>';
    const list = body.querySelector(".tools-modal-list");
    tools.forEach(([icon, name, description]) => {
      const row = el("div", "tool-modal-row");
      row.innerHTML = `
        <div class="tool-modal-icon"><i class="ti ${icon}"></i></div>
        <div><strong>${name}</strong><span>${description}</span></div>`;
      list.appendChild(row);
    });
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function refineStaticChrome() {
    // One provider surface only: the chat header. The footer keeps only status.
    document.querySelector(".titlebar-right .model-badge")?.remove();
    const status = document.querySelector(".statusbar .sb-left");
    if (status) {
      status.innerHTML = '<span class="sb-dot"></span><span>Status: Connected</span>';
    }
    const stats = document.querySelector(".statusbar .sb-right");
    if (stats) stats.innerHTML = '<span id="statMessagesCompact">0 messages</span>';

    const search = document.querySelector(".convo-search-container");
    if (search && !document.getElementById("sidebarSearchHint")) {
      const hint = el("span", "sidebar-search-hint", "⌘ K");
      hint.id = "sidebarSearchHint";
      search.appendChild(hint);
    }
  }

  function boot() {
    refineStaticChrome();
    addSecondaryMenu();

    const list = document.getElementById("chatList");
    if (list) {
      const observer = new MutationObserver(() => {
        if (list.dataset.polishing === "true") return;
        list.dataset.polishing = "true";
        list.dataset.grouped = "false";
        requestAnimationFrame(() => {
          groupChats();
          list.dataset.polishing = "false";
        });
      });
      observer.observe(list, { childList: true });
      requestAnimationFrame(groupChats);
    }

    // Keep the compact message count current without touching app.js logic.
    const messageCount = document.getElementById("statMessages");
    const compact = document.getElementById("statMessagesCompact");
    if (messageCount && compact) {
      const observer = new MutationObserver(() => {
        compact.textContent = `${messageCount.textContent || 0} messages`;
      });
      observer.observe(messageCount, { childList: true, characterData: true, subtree: true });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
