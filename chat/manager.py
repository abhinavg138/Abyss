import json
import re
from datetime import datetime, timezone
from pathlib import Path


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChatManager:

    def __init__(self):

        self.folder = Path("data/chats")
        self.state_path = Path("data/chat_state.json")

        self.folder.mkdir(parents=True, exist_ok=True)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        # chats whose name means "not yet given a real name"
        self.auto_named_chats = {"default", "new chat", "untitled", "untitled chat"}

        self.current_chat = self.load_last_opened()

        # Ensure at least one chat exists on startup
        if not list(self.folder.glob("*.json")):
            self.new("default")
            self.current_chat = "default"
        elif not (self.folder / f"{self.current_chat}.json").exists():
            self.current_chat = "default"
            if not (self.folder / "default.json").exists():
                self.new("default")

    # ── path helpers ──────────────────────────────────────────────

    @property
    def path(self):
        return self.folder / f"{self.current_chat}.json"

    def is_auto_name_candidate(self):
        name = self.current_chat.strip().lower()
        if name in self.auto_named_chats:
            return True
        return re.fullmatch(r"(new chat|untitled|untitled chat) \d+", name) is not None

    # ── load / save ───────────────────────────────────────────────

    def load(self):
        """Return the messages list, handling both old and new formats."""
        if not self.path.exists():
            return []

        with open(self.path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                return []

        # Old format: plain list of messages
        if isinstance(data, list):
            return data

        # New format: dict with metadata
        return data.get("messages", [])

    def load_meta(self) -> dict:
        """Return the full chat dict (with metadata). Creates defaults if missing."""
        if not self.path.exists():
            return self._empty_meta()

        with open(self.path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                return self._empty_meta()

        if isinstance(data, list):
            # Migrate old flat-list format on the fly
            return {
                "title": self.current_chat,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
                "provider": "",
                "auto_named": False,
                "messages": data,
            }

        # Ensure all expected keys exist (backward compat)
        meta = self._empty_meta()
        meta.update(data)
        return meta

    def save(self, conversation: list, provider: str = ""):
        """Save conversation using the new metadata schema."""
        meta = self.load_meta()

        # Keep original title / created_at; update the rest
        if not meta.get("title"):
            meta["title"] = self.current_chat

        meta["updated_at"] = _now_iso()
        meta["messages"] = conversation

        if provider:
            meta["provider"] = provider

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4, ensure_ascii=False)

        self.save_last_opened()

    def has_title(self) -> bool:
        """Returns True if this chat already has a non-default AI-generated title."""
        meta = self.load_meta()
        title = meta.get("title", "")
        return bool(title) and title.lower() not in self.auto_named_chats and title != self.current_chat

    def set_title(self, title: str, provider: str = "", auto_named: bool = False):
        """Rename the JSON file and update the title field inside it."""
        title = title.strip()
        if not title:
            return

        new_name = self.unique_name(self.clean_name(title))
        old_path = self.path

        # Load current data before renaming
        meta = self.load_meta()
        meta["title"] = title
        meta["updated_at"] = _now_iso()
        meta["auto_named"] = auto_named
        if provider:
            meta["provider"] = provider

        # Write to old path first, then rename
        with open(old_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4, ensure_ascii=False)

        # Rename the file
        new_path = self.folder / f"{new_name}.json"
        if old_path != new_path:
            old_path.rename(new_path)

        self.current_chat = new_name
        self.save_last_opened()

    # ── chat lifecycle ────────────────────────────────────────────

    def new(self, name: str):
        """Create a new chat and save it immediately."""
        unique_name = self.unique_name(name)
        self.current_chat = unique_name
        self.save_last_opened()

        # Write a fresh metadata file right away
        meta = self._empty_meta()
        meta["title"] = self.current_chat

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4, ensure_ascii=False)

    def switch(self, name: str):
        self.current_chat = self.clean_name(name)
        self.save_last_opened()
        return self.load()

    def list(self):
        files = list(self.folder.glob("*.json"))
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return [f.stem for f in files]

    def rename(self, old_name: str, new_title: str) -> str:
        old_name = self.clean_name(old_name)
        new_title = new_title.strip()
        if not new_title:
            return old_name

        orig_current = self.current_chat
        self.current_chat = old_name

        meta = self.load_meta()
        meta["title"] = new_title
        meta["updated_at"] = _now_iso()
        meta["auto_named"] = True  # Manually named chats should not be auto-named by AI

        new_name = self.unique_name(self.clean_name(new_title))

        old_path = self.folder / f"{old_name}.json"
        new_path = self.folder / f"{new_name}.json"

        if old_path.exists():
            with open(old_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=4, ensure_ascii=False)
            if old_path != new_path:
                old_path.rename(new_path)

        if orig_current == old_name:
            self.current_chat = new_name
        else:
            self.current_chat = orig_current

        self.save_last_opened()
        return new_name

    def delete(self, name: str):
        chat_name = self.clean_name(name)
        file = self.folder / f"{chat_name}.json"

        if file.exists():
            file.unlink()

        if chat_name == self.current_chat:
            self.current_chat = "default"
            self.save_last_opened()

    # ── name helpers ──────────────────────────────────────────────

    def clean_name(self, name: str) -> str:
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name.strip())
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
        return cleaned[:60] or "New Chat"

    def unique_name(self, name: str) -> str:
        candidate = self.clean_name(name)

        if candidate == self.current_chat or not (self.folder / f"{candidate}.json").exists():
            return candidate

        index = 2
        while True:
            suffixed = f"{candidate} {index}"
            if not (self.folder / f"{suffixed}.json").exists():
                return suffixed
            index += 1

    # ── state persistence ─────────────────────────────────────────

    def load_last_opened(self) -> str:
        if not self.state_path.exists():
            return "default"

        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (OSError, json.JSONDecodeError):
            return "default"

        current_chat = self.clean_name(state.get("current_chat", "default"))

        if not (self.folder / f"{current_chat}.json").exists():
            return "default"

        return current_chat

    def save_last_opened(self):
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump({"current_chat": self.current_chat}, f, indent=4)

    # ── internal helpers ──────────────────────────────────────────

    def _empty_meta(self) -> dict:
        return {
            "title": "",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "provider": "",
            "auto_named": False,
            "messages": [],
        }
