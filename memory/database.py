import sqlite3
from pathlib import Path
from typing import Optional


class MemoryDatabase:
    """Small SQLite-backed long-term memory store.

    The schema is intentionally simple, but memories now have enough metadata
    to be updated, categorized and retrieved by relevance instead of only by
    insertion order.
    """

    CATEGORIES = {"Personal", "Preferences", "Projects", "Goals", "Skills", "Other"}

    def __init__(self):
        db_path = Path("memory.db")
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memories(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'Other',
                memory_key TEXT,
                value TEXT,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'conversation',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Migrate the original v0.1 schema without destroying existing data.
        columns = {
            row[1]
            for row in self.connection.execute("PRAGMA table_info(memories)").fetchall()
        }
        migrations = {
            "category": "ALTER TABLE memories ADD COLUMN category TEXT DEFAULT 'Other'",
            "memory_key": "ALTER TABLE memories ADD COLUMN memory_key TEXT",
            "value": "ALTER TABLE memories ADD COLUMN value TEXT",
            "confidence": "ALTER TABLE memories ADD COLUMN confidence REAL DEFAULT 1.0",
            "source": "ALTER TABLE memories ADD COLUMN source TEXT DEFAULT 'conversation'",
            "updated_at": "ALTER TABLE memories ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        }
        for column, statement in migrations.items():
            if column not in columns:
                self.connection.execute(statement)

        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(memory_key)"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)"
        )
        self.connection.commit()

    def add_memory(
        self,
        content: str,
        category: str = "Other",
        memory_key: Optional[str] = None,
        value: Optional[str] = None,
        confidence: float = 1.0,
        source: str = "conversation",
    ):
        category = category if category in self.CATEGORIES else "Other"
        confidence = max(0.0, min(float(confidence), 1.0))

        # A stable key lets new information update an existing fact instead
        # of creating contradictory duplicate memories.
        if memory_key:
            existing = self.connection.execute(
                "SELECT id FROM memories WHERE lower(memory_key)=lower(?) LIMIT 1",
                (memory_key.strip(),),
            ).fetchone()
            if existing:
                self.connection.execute(
                    """
                    UPDATE memories
                    SET content=?, category=?, value=?, confidence=?, source=?,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                    """,
                    (
                        content.strip(), category, value, confidence, source,
                        existing["id"],
                    ),
                )
                self.connection.commit()
                return existing["id"]

        # Avoid exact duplicate prose when the extractor did not provide a key.
        duplicate = self.connection.execute(
            "SELECT id FROM memories WHERE lower(content)=lower(?) LIMIT 1",
            (content.strip(),),
        ).fetchone()
        if duplicate:
            return duplicate["id"]

        cursor = self.connection.execute(
            """
            INSERT INTO memories(content, category, memory_key, value, confidence, source)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (content.strip(), category, memory_key, value, confidence, source),
        )
        self.connection.commit()
        return cursor.lastrowid

    def get_memories(self, limit=10, category: Optional[str] = None):
        query = """
            SELECT id, content, category, memory_key, value, confidence,
                   source, created_at, updated_at
            FROM memories
        """
        params = []
        if category:
            query += " WHERE category=?"
            params.append(category)
        query += " ORDER BY updated_at DESC, id DESC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        rows = self.connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def search_memories(self, query: str, limit: int = 8):
        """Return memories ranked by simple lexical relevance.

        This deliberately avoids an embedding dependency for now. It gives
        Abyss relevant-memory retrieval while keeping the project lightweight.
        """
        memories = self.get_memories(limit=None)
        if not query or not memories:
            return memories[:limit]

        tokens = {
            token.lower()
            for token in query.replace("_", " ").replace("-", " ").split()
            if len(token) >= 3
        }

        scored = []
        for memory in memories:
            haystack = " ".join(
                str(memory.get(field) or "")
                for field in ("content", "category", "memory_key", "value")
            ).lower()
            score = sum(1 for token in tokens if token in haystack)
            if score:
                scored.append((score, memory))

        scored.sort(key=lambda item: (item[0], item[1]["updated_at"]), reverse=True)
        return [memory for _, memory in scored[:limit]]

    def get_memory_count(self):
        row = self.connection.execute("SELECT COUNT(*) AS count FROM memories").fetchone()
        return row["count"]

    def delete_memory(self, memory_id):
        self.connection.execute("DELETE FROM memories WHERE id=?", (memory_id,))
        self.connection.commit()

    def update_memory(self, memory_id: int, **fields):
        allowed = {"content", "category", "memory_key", "value", "confidence"}
        updates = {key: value for key, value in fields.items() if key in allowed}
        if not updates:
            return False

        if "category" in updates and updates["category"] not in self.CATEGORIES:
            updates["category"] = "Other"
        if "confidence" in updates:
            updates["confidence"] = max(0.0, min(float(updates["confidence"]), 1.0))

        assignments = ", ".join(f"{key}=?" for key in updates)
        assignments += ", updated_at=CURRENT_TIMESTAMP"
        params = list(updates.values()) + [memory_id]
        cursor = self.connection.execute(
            f"UPDATE memories SET {assignments} WHERE id=?",
            params,
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def clear_memory(self):
        self.connection.execute("DELETE FROM memories")
        self.connection.commit()
