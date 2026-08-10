from memory.database import MemoryDatabase

db = MemoryDatabase()

db.add_memory("Abhinav likes Python")

print(db.get_memories())