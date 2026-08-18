/* Code-block actions for Abyss. Keeps chat rendering logic in app.js untouched. */
(function () {
  "use strict";

  function injectStyles() {
    if (document.getElementById("abyssCodeActionStyles")) return;
    const style = document.createElement("style");
    style.id = "abyssCodeActionStyles";
    style.textContent = `
      .abyss-code-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        padding: 6px 9px;
        background: rgba(255,255,255,.025);
        border-bottom: 1px solid var(--border, #30363D);
        color: var(--text-muted, #4B5563);
        font: 10px 'Inter', sans-serif;
      }
      .abyss-code-language { text-transform: lowercase; opacity: .9; }
      .abyss-copy-code {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        border: 1px solid var(--border, #30363D);
        background: var(--surface2, #1a2233);
        color: var(--text-secondary, #9CA3AF);
        border-radius: 5px;
        padding: 3px 8px;
        font: 10px 'Inter', sans-serif;
        cursor: pointer;
        transition: background .15s, color .15s, border-color .15s;
      }
      .abyss-copy-code:hover {
        background: var(--surface, #1F2937);
        color: var(--text, #F3F4F6);
      }
      .abyss-copy-code.copied {
        color: #86efac;
        border-color: rgba(34,197,94,.35);
      }
      .ai-body pre.abyss-code-ready { margin-top: 10px; }
    `;
    document.head.appendChild(style);
  }

  function languageFromCode(code) {
    const classes = Array.from(code.classList);
    const langClass = classes.find(c => c.startsWith("language-"));
    return langClass ? langClass.slice(9) : "code";
  }

  function addCopyButton(pre) {
    if (pre.dataset.abyssCodeReady === "true") return;
    const code = pre.querySelector("code");
    if (!code) return;

    pre.dataset.abyssCodeReady = "true";
    pre.classList.add("abyss-code-ready");

    const header = document.createElement("div");
    header.className = "abyss-code-header";

    const language = document.createElement("span");
    language.className = "abyss-code-language";
    language.textContent = languageFromCode(code);

    const button = document.createElement("button");
    button.type = "button";
    button.className = "abyss-copy-code";
    button.innerHTML = '<i class="ti ti-copy"></i><span>Copy</span>';
    button.title = "Copy code";

    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(code.innerText);
        button.classList.add("copied");
        button.innerHTML = '<i class="ti ti-check"></i><span>Copied</span>';
        setTimeout(() => {
          button.classList.remove("copied");
          button.innerHTML = '<i class="ti ti-copy"></i><span>Copy</span>';
        }, 1400);
      } catch (error) {
        // Fallback for browsers where Clipboard API is unavailable.
        const area = document.createElement("textarea");
        area.value = code.innerText;
        area.style.position = "fixed";
        area.style.opacity = "0";
        document.body.appendChild(area);
        area.select();
        document.execCommand("copy");
        area.remove();
        button.classList.add("copied");
        button.innerHTML = '<i class="ti ti-check"></i><span>Copied</span>';
        setTimeout(() => {
          button.classList.remove("copied");
          button.innerHTML = '<i class="ti ti-copy"></i><span>Copy</span>';
        }, 1400);
      }
    });

    header.append(language, button);
    pre.insertBefore(header, code);
  }

  function scan(root = document) {
    root.querySelectorAll?.(".ai-body pre").forEach(addCopyButton);
  }

  function boot() {
    injectStyles();
    scan();

    const observer = new MutationObserver(mutations => {
      for (const mutation of mutations) {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType !== Node.ELEMENT_NODE) return;
          if (node.matches?.("pre")) addCopyButton(node);
          scan(node);
        });
      }
    });

    const messages = document.getElementById("messages");
    if (messages) observer.observe(messages, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
