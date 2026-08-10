from memory.database import MemoryDatabase


class MemoryManager:
    def __init__(self):
        self.db = MemoryDatabase()

    def remember(self, content: str):
        """Store a memory."""
        self.db.add_memory(content)

    def recall(self, limit: int = None):
        """Return recent memories. If limit is None, return all."""
        return self.db.get_memories(limit)

    def get_count(self) -> int:
        """Return the total number of memories."""
        return self.db.get_memory_count()

    def forget(self, memory_id: int):
        self.db.delete_memory(memory_id)

    def clear(self):
        self.db.clear_memory()

    def get_context(self, limit: int = 10):
        memories = self.recall(limit)

        if not memories:
            return ""

        context = "Known information about the user:\n\n"

        for memory in memories:
            context += f"- {memory['content']}\n"

        return context