from memory.database import MemoryDatabase


class MemoryManager:
    def __init__(self):
        self.db = MemoryDatabase()

    def remember(
        self,
        content: str,
        category: str = "Other",
        memory_key: str = None,
        value: str = None,
        confidence: float = 1.0,
        source: str = "conversation",
    ):
        """Create or update a long-term memory."""
        if not content or not content.strip():
            return None
        return self.db.add_memory(
            content,
            category=category,
            memory_key=memory_key,
            value=value,
            confidence=confidence,
            source=source,
        )

    def recall(self, limit: int = None, category: str = None):
        return self.db.get_memories(limit, category=category)

    def search(self, query: str, limit: int = 8):
        return self.db.search_memories(query, limit=limit)

    def get_count(self) -> int:
        return self.db.get_memory_count()

    def forget(self, memory_id: int):
        self.db.delete_memory(memory_id)

    def update(self, memory_id: int, **fields):
        return self.db.update_memory(memory_id, **fields)

    def clear(self):
        self.db.clear_memory()

    def get_context(self, query: str = "", limit: int = 6):
        """Build a small relevant-memory context for the current request."""
        memories = self.search(query, limit=limit) if query else self.recall(limit)

        if not memories:
            return ""

        lines = [
            "Relevant long-term information about the user:",
            "Only use these facts when they are relevant to the current request.",
            "",
        ]
        for memory in memories:
            category = memory.get("category") or "Other"
            lines.append(f"- [{category}] {memory['content']}")

        return "\n".join(lines)
