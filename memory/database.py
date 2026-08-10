import sqlite3
from pathlib import Path


class MemoryDatabase:

    def __init__(self):

        db_path = Path("memory.db")

        self.connection = sqlite3.connect(
            db_path,
            check_same_thread=False
        )

        self.cursor = self.connection.cursor()

        self.create_tables()

    def create_tables(self):

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            content TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """)

        self.connection.commit()

    def add_memory(self, content):

        self.cursor.execute(
            "INSERT INTO memories(content) VALUES(?)",
            (content,)
        )

        self.connection.commit()

    def get_memories(self, limit=10):

        if limit is None:
            self.cursor.execute(
                """
                SELECT id, content, created_at
                FROM memories
                ORDER BY id DESC
                """
            )
        else:
            self.cursor.execute(
                """
                SELECT id, content, created_at
                FROM memories
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            )

        return [
            {
                "id":         row[0],
                "content":    row[1],
                "created_at": row[2],
            }
            for row in self.cursor.fetchall()
        ]

    def get_memory_count(self):

        self.cursor.execute("SELECT COUNT(*) FROM memories")

        return self.cursor.fetchone()[0]

    def delete_memory(self, memory_id):

        self.cursor.execute(
            "DELETE FROM memories WHERE id=?",
            (memory_id,)
        )

        self.connection.commit()

    def clear_memory(self):

        self.cursor.execute("DELETE FROM memories")

        self.connection.commit()