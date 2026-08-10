let memoryItems = [];
let memoryFilter = "";
let memoryQuery = "";

function openMemory() {
  const modal = document.getElementById("memoryModal");
  if (!modal) return;
  modal.classList.add("open");
  document.getElementById("memorySearch")?.focus();
  loadMemoryModal();
}

function closeMemory() {
  document.getElementById("memoryModal")?.classList.remove("open");
  document.getElementById("memoryForm")?.classList.remove("open");
}

async function loadMemoryModal() {
  try {
    const params = new URLSearchParams();
    if (memoryQuery) params.set("q", memoryQuery);
    if (memoryFilter) params.set("category", memoryFilter);
    const res = await fetch(`/memories?${params.toString()}`);
    const data = await res.json();
    memoryItems = data.memories || [];
    renderMemoryModal();
  } catch (error) {
    console.warn("Could not load memories:", error);
  }
}

function renderMemoryModal() {
  const list = document.getElementById("memoryModalList");
  const count = document.getElementById("memoryModalCount");
  if (!list) return;

  if (count) count.textContent = `${memoryItems.length} memor${memoryItems.length === 1 ? "y" : "ies"}`;
  list.innerHTML = "";

  if (!memoryItems.length) {
    list.innerHTML = `<div class="memory-empty">No memories match this view.</div>`;
    return;
  }

  memoryItems.forEach(memory => {
    const card = document.createElement("div");
    card.className = "memory-card";
    const date = memory.updated_at || memory.created_at || "";
    card.innerHTML = `
      <div class="memory-card-icon"><i class="ti ti-brain"></i></div>
      <div class="memory-card-main">
        <div class="memory-card-meta">
          <span class="memory-category">${escapeHtml(memory.category || "Other")}</span>
          <span class="memory-date">${escapeHtml(formatMemoryDate(date))}</span>
        </div>
        <div class="memory-card-content">${escapeHtml(memory.content || "")}</div>
        ${memory.value ? `<div class="memory-card-value">${escapeHtml(memory.key || "value")}: ${escapeHtml(memory.value)}</div>` : ""}
      </div>
      <div class="memory-card-actions">
        <button title="Edit" onclick="editMemory(${memory.id})"><i class="ti ti-pencil"></i></button>
        <button title="Forget" onclick="forgetMemory(${memory.id})"><i class="ti ti-trash"></i></button>
      </div>`;
    list.appendChild(card);
  });
}

function formatMemoryDate(value) {
  if (!value) return "";
  const date = new Date(value.replace(" ", "T") + "Z");
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString([], { month: "short", day: "numeric" });
}

function toggleMemoryForm(memory = null) {
  const form = document.getElementById("memoryForm");
  if (!form) return;
  form.classList.toggle("open", Boolean(memory) || !form.classList.contains("open"));
  document.getElementById("memoryEditId").value = memory?.id || "";
  document.getElementById("memoryContent").value = memory?.content || "";
  document.getElementById("memoryCategory").value = memory?.category || "Other";
  document.getElementById("memoryKey").value = memory?.memory_key || "";
  document.getElementById("memoryValue").value = memory?.value || "";
}

function editMemory(id) {
  const memory = memoryItems.find(item => item.id === id);
  if (memory) toggleMemoryForm(memory);
}

async function saveMemoryForm() {
  const id = document.getElementById("memoryEditId").value;
  const payload = {
    content: document.getElementById("memoryContent").value.trim(),
    category: document.getElementById("memoryCategory").value,
    key: document.getElementById("memoryKey").value.trim() || null,
    value: document.getElementById("memoryValue").value.trim() || null,
  };
  if (!payload.content) return;

  try {
    const res = await fetch(id ? `/memories/${id}` : "/memories", {
      method: id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Memory save failed: ${res.status}`);
    document.getElementById("memoryForm").classList.remove("open");
    await loadMemoryModal();
    if (typeof loadMemories === "function") await loadMemories();
  } catch (error) {
    console.warn(error);
  }
}

async function forgetMemory(id) {
  try {
    const res = await fetch(`/memories/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`Memory delete failed: ${res.status}`);
    await loadMemoryModal();
    if (typeof loadMemories === "function") await loadMemories();
  } catch (error) {
    console.warn(error);
  }
}

function initMemoryUI() {
  const more = document.getElementById("moreMenuBtn");
  const memoryOpen = document.getElementById("openMemoryBtn");
  const close = document.getElementById("memoryClose");
  const backdrop = document.getElementById("memoryModal");
  const search = document.getElementById("memorySearch");
  const filter = document.getElementById("memoryFilter");
  const add = document.getElementById("memoryAdd");
  const cancel = document.getElementById("memoryCancel");
  const save = document.getElementById("memorySave");

  more?.addEventListener("click", () => {
    const menu = document.getElementById("quickMenu");
    menu?.classList.toggle("open");
  });
  memoryOpen?.addEventListener("click", () => {
    document.getElementById("quickMenu")?.classList.remove("open");
    openMemory();
  });
  close?.addEventListener("click", closeMemory);
  backdrop?.addEventListener("click", e => {
    if (e.target === backdrop) closeMemory();
  });
  search?.addEventListener("input", e => {
    memoryQuery = e.target.value.trim();
    loadMemoryModal();
  });
  filter?.addEventListener("change", e => {
    memoryFilter = e.target.value;
    loadMemoryModal();
  });
  add?.addEventListener("click", () => toggleMemoryForm());
  cancel?.addEventListener("click", () => document.getElementById("memoryForm")?.classList.remove("open"));
  save?.addEventListener("click", saveMemoryForm);

  document.addEventListener("keydown", e => {
    if (e.key === "Escape") closeMemory();
  });
}

document.addEventListener("DOMContentLoaded", initMemoryUI);
