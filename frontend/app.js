// ── Elements ──────────────────────────────────────────────────────
const input    = document.getElementById("chatInput");
const messages = document.getElementById("messages");
const sendBtn  = document.getElementById("sendBtn");

let messageCount = 0;
let tokenCount   = 0;
let currentProvider = "groq";
let currentChat = "New Chat";
let knownChatNames = new Set();

// ── marked config ─────────────────────────────────────────────────
marked.setOptions({ breaks: true, gfm: true });

// ── Auto-resize textarea ──────────────────────────────────────────
input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 120) + "px";
});

// ── Send on Enter (Shift+Enter = newline) ─────────────────────────
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener("click", sendMessage);

// ── Send message ──────────────────────────────────────────────────
async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  // Remove welcome screen on first message
  document.getElementById("welcomeScreen")?.remove();

  // USER BUBBLE
  appendMessage("user", "You", now, escapeHtml(text), "user", uploadedAttachments);
  const currentAttachments = [...uploadedAttachments];
  uploadedAttachments = [];
  const attachmentList = document.getElementById("attachmentList");
  if (attachmentList) attachmentList.innerHTML = "";

  input.value = "";
  input.style.height = "auto";
  messageCount++;
  updateStats();

  // THINKING INDICATOR
  const typing = document.createElement("div");
  typing.className = "msg";
  typing.id = "typing";
  typing.innerHTML = `
    <div class="avatar ai-av">A</div>
    <div class="bubble">
      <div class="bubble-header"><span class="bubble-name ai">Abyss</span></div>
      <div class="bubble-body ai-body" style="color:#4B5563">
        <span id="typing-dots">Thinking</span>
      </div>
    </div>`;
  messages.appendChild(typing);
  messages.scrollTop = messages.scrollHeight;

  let dots = 0;
  const dotInterval = setInterval(() => {
    dots = (dots + 1) % 4;
    const el = document.getElementById("typing-dots");
    if (el) el.textContent = "Thinking" + ".".repeat(dots);
  }, 400);

  try {
    const response = await fetch("/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        message: text,
        attachments: currentAttachments
      })
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Server error ${response.status}: ${errText}`);
    }

    const reader  = response.body.getReader();
    const decoder = new TextDecoder();

    clearInterval(dotInterval);
    document.getElementById("typing")?.remove();

    // AI BUBBLE
    const aiMsg = document.createElement("div");
    aiMsg.className = "msg";
    aiMsg.innerHTML = `
      <div class="avatar ai-av">A</div>
      <div class="bubble">
        <div class="bubble-header">
          <span class="bubble-name ai">Abyss</span>
          <span class="bubble-time">${now}</span>
        </div>
        <div class="bubble-body ai-body"></div>
      </div>`;
    messages.appendChild(aiMsg);

    const reply = aiMsg.querySelector(".ai-body");
    let raw = "";

    // Stream tokens in
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      raw += chunk;
      tokenCount += chunk.split(/\s+/).filter(Boolean).length;
      reply.innerHTML = marked.parse(raw);

      // Syntax-highlight code blocks without re-processing
      if (window.hljs) {
        reply.querySelectorAll("pre code:not([data-highlighted])").forEach(block => {
          window.hljs.highlightElement(block);
          block.dataset.highlighted = "true";
        });
      }
      messages.scrollTop = messages.scrollHeight;
    }

    messageCount++;
    updateStats();
    loadProvider(); // Refresh provider badge after each message (fallback may have switched it)
    await loadChats(true);  // detectRename=true handles AI-generated title renames
    await loadMemories();

  } catch (err) {
    clearInterval(dotInterval);
    document.getElementById("typing")?.remove();

    const errorMsg = document.createElement("div");
    errorMsg.className = "msg";
    errorMsg.innerHTML = `
      <div class="avatar ai-av" style="background:#EF4444">!</div>
      <div class="bubble">
        <div class="bubble-header"><span class="bubble-name ai">Abyss</span></div>
        <div class="bubble-body ai-body" style="color:#EF4444; white-space:pre-wrap">
          ❌ ${escapeHtml(err.toString())}
        </div>
      </div>`;
    messages.appendChild(errorMsg);
    messages.scrollTop = messages.scrollHeight;
  }
}

function isImageFile(filename) {
  if (!filename) return false;
  const ext = filename.split('.').pop().toLowerCase();
  return ['png', 'jpg', 'jpeg', 'webp'].includes(ext);
}

// ── Helper: append a message bubble ──────────────────────────────
function appendMessage(side, name, time, htmlContent, nameClass, attachments = []) {
  const div = document.createElement("div");
  div.className = `msg ${side}`;
  
  let attachmentHtml = "";
  if (attachments && attachments.length > 0) {
    attachmentHtml = `<div class="msg-attachments">`;
    attachments.forEach(file => {
      if (isImageFile(file.filename)) {
        attachmentHtml += `
          <div class="msg-attachment-card">
            <img src="/${file.temp_path}" class="msg-attachment-image" onclick="window.open('/${file.temp_path}', '_blank')" />
            <div class="msg-attachment-info">
              <span>${escapeHtml(file.filename)}</span>
            </div>
          </div>`;
      } else {
        attachmentHtml += `
          <div class="msg-attachment-badge" title="${escapeHtml(file.filename)}">
            <i class="ti ti-file"></i>
            <span>${escapeHtml(file.filename)}</span>
          </div>`;
      }
    });
    attachmentHtml += `</div>`;
  }

  div.innerHTML = `
    <div class="avatar ${side}-av">${side === "user" ? "YO" : "A"}</div>
    <div class="bubble">
      <div class="bubble-header">
        <span class="bubble-name ${nameClass}">${name}</span>
        <span class="bubble-time">${time}</span>
      </div>
      <div class="bubble-body ${side}-body">
        <div>${htmlContent}</div>
        ${attachmentHtml}
      </div>
    </div>`;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

// ── Escape HTML ───────────────────────────────────────────────────
function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ── Stats ─────────────────────────────────────────────────────
function updateStats() {
  // Statusbar counts
  const el = document.getElementById("statMessages");
  const te = document.getElementById("statTokens");
  // Right-panel counts (same values, different elements)
  const elP = document.getElementById("statMessagesPanel");
  const teP = document.getElementById("statTokensPanel");

  const tokenDisplay = tokenCount > 1000
    ? (tokenCount / 1000).toFixed(1) + "K"
    : tokenCount;

  if (el)  el.textContent  = messageCount;
  if (elP) elP.textContent = messageCount;
  if (te)  te.textContent  = tokenDisplay;
  if (teP) teP.textContent = tokenDisplay;
}

// ── Chat list ─────────────────────────────────────────────────────

// loadChats — single source of truth for fetching and rendering the sidebar.
// Pass detectRename=true after a streaming response so that if the backend
// renamed the current chat file (AI title generation), the active state
// tracks the new name automatically.
async function loadChats(detectRename = false) {
  const previousNames = new Set(knownChatNames);
  const previousChat  = currentChat;

  try {
    const chats = await fetchChats();

    if (detectRename) {
      // If the old name vanished and exactly one new name appeared,
      // the backend renamed the file — update the active chat name.
      const added   = chats.filter(n => !previousNames.has(n));
      const removed = [...previousNames].filter(n => !chats.includes(n));
      if (removed.includes(previousChat) && added.length === 1) {
        setCurrentChat(added[0]);
      }
    }

    renderChatList(chats);
  } catch (e) {
    console.warn("Could not load chats:", e);
  }
}

async function loadChat(name) {
  try {
    const response = await fetch("/chats/load", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: name })
    });

    if (!response.ok) {
      throw new Error(`Server error ${response.status}`);
    }

    const data = await response.json();
    if (data.success) {
      setCurrentChat(name);
      renderConversation(data.messages);
      await loadChats();
    }
  } catch (e) {
    console.warn("Could not load chat:", e);
  }
}

async function newChat() {
  try {
    const res = await fetch("/chats/new", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "New Chat" })
    });
    const data = await res.json();
    if (data.success) {
      setCurrentChat(data.name);
      renderConversation([]);
      await loadChats();
    }
  } catch (e) {
    console.warn("Could not create chat:", e);
  }
}

async function deleteChat(name) {
  if (!confirm(`Delete "${name}"?`)) return;
  try {
    await fetch("/chats/" + encodeURIComponent(name), { method: "DELETE" });
    if (name === currentChat) {
      await loadActiveChat();
    } else {
      await loadChats();
    }
  } catch (e) {
    console.warn("Could not delete chat:", e);
  }
}

// ── Fetch helpers ─────────────────────────────────────────────────
async function fetchChats() {
  const res = await fetch("/chats");
  if (!res.ok) throw new Error(`Server error ${res.status}`);
  return await res.json();
}

function renderChatList(chats) {
  const list = document.getElementById("chatList");
  knownChatNames = new Set(chats);
  list.innerHTML = "";

  if (chats.length === 0) {
    list.innerHTML = `<div style="padding:8px 16px;font-size:11px;color:#4B5563">No saved chats</div>`;
    return;
  }

  chats.forEach(name => {
    const item = document.createElement("div");
    item.className = "convo-item";
    item.dataset.name = name;           // store name as data attr, not relying on textContent

    // Chat name span — flex-fills the row
    const label = document.createElement("span");
    label.textContent = name;
    label.style.flex = "1";
    label.style.overflow = "hidden";
    label.style.textOverflow = "ellipsis";
    item.appendChild(label);

    // Rename icon
    const edit = document.createElement("i");
    edit.className = "ti ti-pencil edit-icon";
    edit.title = "Rename chat";
    edit.style.marginRight = "6px";
    edit.addEventListener("click", async (e) => {
      e.stopPropagation(); // don't trigger loadChat
      const newTitle = prompt("Rename conversation:", name);
      if (newTitle && newTitle.trim() && newTitle.trim() !== name) {
        try {
          const response = await fetch("/chats/rename", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: name, title: newTitle.trim() })
          });
          const data = await response.json();
          if (data.success) {
            if (name === currentChat) {
              setCurrentChat(data.name);
            }
            await loadChats();
          }
        } catch (err) {
          console.warn("Could not rename chat:", err);
        }
      }
    });
    item.appendChild(edit);

    // Delete icon — uses the existing .edit-icon CSS (opacity 0, shows on hover)
    const del = document.createElement("i");
    del.className = "ti ti-trash edit-icon";
    del.title = "Delete chat";
    del.addEventListener("click", (e) => {
      e.stopPropagation();              // don't trigger loadChat
      deleteChat(name);
    });
    item.appendChild(del);

    item.classList.toggle("active", name === currentChat);
    item.addEventListener("click", () => loadChat(name));
    list.appendChild(item);
  });
}

function setCurrentChat(name) {
  currentChat = name;

  // Update both title elements from the one source of truth.
  const t1 = document.getElementById("chatTitle");
  const t2 = document.getElementById("chatTopbarTitle");
  if (t1) t1.textContent = name || "New Chat";
  if (t2) t2.textContent = name || "New Chat";

  // Active-class sync: renderChatList always rebuilds the list right after
  // setCurrentChat is called, so we don't need a separate DOM walk here.
  // We still update any already-rendered items in case renderChatList is
  // NOT called immediately (e.g. a future direct title-only update).
  document.querySelectorAll(".convo-item").forEach(el =>
    el.classList.toggle("active", el.dataset.name === name)
  );
}

function renderSelectedChatState(name, subtitle = "Conversation selected.") {
  messages.innerHTML = `
    <div class="welcome-screen" id="welcomeScreen">
      <h1>${escapeHtml(name)}</h1>
      <p>${escapeHtml(subtitle)}</p>
    </div>`;

  messageCount = 0;
  tokenCount = 0;
  updateStats();
}

function renderConversation(conversation) {
  document.getElementById("welcomeScreen")?.remove();
  messages.innerHTML = "";
  messageCount = 0;
  tokenCount = 0;

  let hasVisibleMessages = false;

  conversation.forEach(msg => {
    if (msg.role === "system") {
      return;
    }
    hasVisibleMessages = true;
    const side = msg.role === "user" ? "user" : "ai";
    const name = msg.role === "user" ? "You" : "Abyss";
    const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const htmlContent = msg.role === "user" ? escapeHtml(msg.content) : marked.parse(msg.content);
    
    appendMessage(side, name, now, htmlContent, side, msg.attachments || []);
    messageCount++;
    tokenCount += msg.content.split(/\s+/).filter(Boolean).length;
  });

  if (!hasVisibleMessages) {
    const name = currentChat || "Abyss";
    messages.innerHTML = `
      <div class="welcome-screen" id="welcomeScreen">
        <h1>🌌 Welcome to ${escapeHtml(name)}</h1>
        <p>Your personal AI assistant.</p>
        <p style="margin-top:15px;color:#4B5563;">Ask me anything to get started.</p>
      </div>`;
  }
  
  if (window.hljs) {
    messages.querySelectorAll("pre code:not([data-highlighted])").forEach(block => {
      window.hljs.highlightElement(block);
      block.dataset.highlighted = "true";
    });
  }

  updateStats();
  messages.scrollTop = messages.scrollHeight;
}

async function loadProvider() {
  try {
    const res  = await fetch("/provider");
    const data = await res.json();
    currentProvider = data.provider;

    // Capitalised name used in all display elements
    const name = data.provider.charAt(0).toUpperCase() + data.provider.slice(1);

    // Titlebar badge
    const providerBadge = document.getElementById("providerBadge");
    const sbProvider    = document.getElementById("sbProvider");
    // Chat-area topbar badge
    const topbarProvider  = document.getElementById("topbarProvider");
    // Status bar
    const statusProvider  = document.getElementById("statusProvider");
    // Right-panel stats row
    const statProvider    = document.getElementById("statProvider");

    if (providerBadge)   providerBadge.textContent  = name;
    if (sbProvider)      sbProvider.textContent      = "Provider: " + data.provider;
    if (topbarProvider)  topbarProvider.textContent  = name;
    if (statusProvider)  statusProvider.textContent  = "Provider: " + data.provider;
    if (statProvider)    statProvider.textContent    = name;
  } catch (_) {}
}

// ── Memories panel ────────────────────────────────────────────────

async function deleteMemory(id) {
  try {
    await fetch(`/memories/${id}`, { method: "DELETE" });
    await loadMemories();
  } catch (_) {}
}

async function loadMemories() {
  try {
    const res  = await fetch("/memories");
    const data = await res.json();
    const memories = data.memories || [];
    const count    = memories.length;

    // Update count badge (panel header) and stats row
    const badge = document.getElementById("memoryCount");
    const stat  = document.getElementById("statMemory");
    if (badge) badge.textContent = count;
    if (stat)  stat.textContent  = count;

    // Render each memory into #memList
    const list = document.getElementById("memList");
    if (!list) return;
    list.innerHTML = "";

    if (count === 0) {
      list.innerHTML = `<div style="font-size:11px;color:var(--text-muted);padding:6px 0">No memories stored yet.</div>`;
      return;
    }

    memories.forEach(mem => {
      const item = document.createElement("div");
      item.className = "mem-item";

      // Icon
      const iconWrap = document.createElement("div");
      iconWrap.className = "mem-icon";
      iconWrap.innerHTML = `<i class="ti ti-brain"></i>`;

      // Text content
      const text = document.createElement("div");
      text.style.flex = "1";
      text.style.overflow = "hidden";
      text.innerHTML = `
        <div class="mem-label">Memory #${mem.id}</div>
        <div class="mem-sub">${escapeHtml(mem.content)}</div>`;

      // Delete button — reuses existing .edit-icon CSS (opacity 0, shows on hover)
      const del = document.createElement("i");
      del.className = "ti ti-trash edit-icon";
      del.title = "Forget this memory";
      del.addEventListener("click", (e) => {
        e.stopPropagation();
        deleteMemory(mem.id);
      });

      item.appendChild(iconWrap);
      item.appendChild(text);
      item.appendChild(del);
      list.appendChild(item);
    });

  } catch (_) {}
}

// ── Active chat on startup ────────────────────────────────────────
// Asks the backend which chat is currently loaded and applies it to
// the title bar and sidebar highlight.  Must run after loadChats()
// so the list items already exist for setCurrentChat() to mark.
async function loadActiveChat() {
  try {
    const res  = await fetch("/active-chat");
    const data = await res.json();
    const displayName = data.title || data.name;
    currentChat = data.name;
    const t1 = document.getElementById("chatTitle");
    const t2 = document.getElementById("chatTopbarTitle");
    if (t1) t1.textContent = displayName;
    if (t2) t2.textContent = displayName;
    
    document.querySelectorAll(".convo-item").forEach(el =>
      el.classList.toggle("active", el.dataset.name === data.name)
    );

    if (data.messages) {
      renderConversation(data.messages);
    }
  } catch (_) {}
}

// ── File Upload / Drag & Drop ─────────────────────────────────────
let uploadedAttachments = [];

const fileInput = document.createElement("input");
fileInput.type = "file";
fileInput.multiple = true;
fileInput.style.display = "none";
document.body.appendChild(fileInput);

const paperclipBtn = document.querySelector('.input-icon[title="Attach file"]');
if (paperclipBtn) {
  paperclipBtn.addEventListener("click", () => fileInput.click());
}

fileInput.addEventListener("change", (e) => {
  if (e.target.files && e.target.files.length > 0) {
    handleFileUpload(e.target.files);
  }
});

const chatArea = document.querySelector(".chat-area");
if (chatArea) {
  chatArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    chatArea.classList.add("drag-over");
  });

  chatArea.addEventListener("dragenter", (e) => {
    e.preventDefault();
    chatArea.classList.add("drag-over");
  });

  chatArea.addEventListener("dragleave", () => {
    chatArea.classList.remove("drag-over");
  });

  chatArea.addEventListener("drop", (e) => {
    e.preventDefault();
    chatArea.classList.remove("drag-over");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files);
    }
  });
}

async function handleFileUpload(files) {
  const attachmentList = document.getElementById("attachmentList");
  if (!attachmentList) return;

  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  const tempItems = [];
  for (let i = 0; i < files.length; i++) {
    const item = document.createElement("div");
    item.className = "attachment-item uploading";
    item.innerHTML = `
      <i class="ti ti-file file-icon"></i>
      <span class="attachment-name">${escapeHtml(files[i].name)}</span>
      <i class="ti ti-loader attachment-remove spin" style="cursor: default"></i>
    `;
    attachmentList.appendChild(item);
    tempItems.push(item);
  }

  try {
    const response = await fetch("/upload", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Upload failed ${response.status}`);
    }

    const data = await response.json();
    if (data.success) {
      tempItems.forEach(item => item.remove());
      data.files.forEach(file => {
        uploadedAttachments.push(file);
        renderAttachment(file);
      });
    }
  } catch (e) {
    console.error("Upload error:", e);
    tempItems.forEach(item => item.remove());
    alert("❌ File upload failed.");
  }
}

function renderAttachment(file) {
  const attachmentList = document.getElementById("attachmentList");
  if (!attachmentList) return;

  const item = document.createElement("div");
  item.className = "attachment-item";

  let previewHtml = `<i class="ti ti-file file-icon"></i>`;
  if (isImageFile(file.filename)) {
    previewHtml = `<img src="/${file.temp_path}" class="attachment-preview" />`;
  }

  item.innerHTML = `
    ${previewHtml}
    <span class="attachment-name" title="${escapeHtml(file.filename)}">${escapeHtml(file.filename)}</span>
    <i class="ti ti-x attachment-remove" title="Remove attachment"></i>
  `;

  item.querySelector(".attachment-remove").addEventListener("click", () => {
    uploadedAttachments = uploadedAttachments.filter(f => f.temp_path !== file.temp_path);
    item.remove();
  });

  attachmentList.appendChild(item);
}

async function renameActiveChat() {
  const newName = prompt("Rename conversation:", currentChat);
  if (newName && newName.trim() && newName.trim() !== currentChat) {
    try {
      const response = await fetch("/chats/rename", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: currentChat, title: newName.trim() })
      });
      const data = await response.json();
      if (data.success) {
        setCurrentChat(data.name);
        await loadChats();
      }
    } catch (e) {
      console.warn("Could not rename chat:", e);
    }
  }
}

// ── Init ──────────────────────────────────────────────────────────
// loadChats() must complete before loadActiveChat() so the sidebar
// items are in the DOM when we try to set the active class.
(async () => {
  await loadChats();
  await loadActiveChat();
  loadProvider();
  loadMemories();

  // Sidebar toggle
  const sidebar = document.querySelector(".sidebar");
  const toggleBtn = document.getElementById("sidebarToggle");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed");
    });
  }

  // Sidebar search
  const searchInput = document.getElementById("convoSearch");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      const query = e.target.value.toLowerCase().trim();
      document.querySelectorAll(".convo-item").forEach(item => {
        const name = item.dataset.name.toLowerCase();
        if (name.includes(query)) {
          item.style.display = "";
        } else {
          item.style.display = "none";
        }
      });
    });
  }

  // Header rename triggers
  const editTitleBtn = document.querySelector(".chat-title i.ti-pencil");
  if (editTitleBtn) {
    editTitleBtn.addEventListener("click", renameActiveChat);
  }

  const editTitlebarBtn = document.querySelector(".titlebar-center i.ti-pencil");
  if (editTitlebarBtn) {
    editTitlebarBtn.addEventListener("click", renameActiveChat);
  }
})();
