from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import shutil
import uuid
from pathlib import Path

from assistant.manager import AssistantManager

router = APIRouter()
assistant = AssistantManager()


class Attachment(BaseModel):
    filename: str
    temp_path: str
    size: int


class ChatRequest(BaseModel):
    message: str
    attachments: List[Attachment] = []


class RenameRequest(BaseModel):
    name: str
    title: str


class MemoryRequest(BaseModel):
    content: str
    category: str = "Other"
    key: Optional[str] = None
    value: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class MemoryUpdateRequest(BaseModel):
    content: Optional[str] = None
    category: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


@router.post("/chat")
async def chat(request: ChatRequest):
    attachments_dict = [att.model_dump() for att in request.attachments]
    response = assistant.chat(request.message, attachments=attachments_dict)
    return {"response": response}


@router.post("/stream")
async def stream(request: ChatRequest):
    attachments_dict = [att.model_dump() for att in request.attachments]

    def generate():
        for token in assistant.stream(request.message, attachments=attachments_dict):
            yield token

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
        }
    )


@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    metadata = []
    for file in files:
        unique_id = uuid.uuid4().hex[:8]
        temp_filename = f"{unique_id}_{file.filename}"
        temp_path = upload_dir / temp_filename

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        metadata.append({
            "filename": file.filename,
            "temp_path": str(temp_path).replace("\\", "/"),
            "size": temp_path.stat().st_size
        })

    return {"success": True, "files": metadata}


@router.get("/chats")
async def list_chats():
    return assistant.chat_manager.list()


@router.get("/active-chat")
async def active_chat():
    meta = assistant.chat_manager.load_meta()
    return {
        "name": assistant.chat_manager.current_chat,
        "title": meta.get("title") or assistant.chat_manager.current_chat,
        "messages": assistant.conversation,
    }


@router.post("/chats/new")
async def new_chat(request: ChatRequest):
    name = request.message.strip() or "New Chat"
    assistant.chat_manager.new(name)
    assistant.conversation = [assistant.system_prompt]
    provider = assistant.router.get_provider()
    assistant.chat_manager.save(assistant.conversation, provider=provider)
    return {"success": True, "name": assistant.chat_manager.current_chat}


@router.post("/chats/load")
async def load_chat(request: ChatRequest):
    conversation = assistant.chat_manager.switch(request.message)
    assistant.conversation = conversation if conversation else [assistant.system_prompt]
    meta = assistant.chat_manager.load_meta()
    saved_provider = meta.get("provider", "")
    if saved_provider:
        assistant.router.set_provider(saved_provider)
    return {"success": True, "messages": assistant.conversation}


@router.post("/chats/rename")
async def rename_chat(request: RenameRequest):
    new_name = assistant.chat_manager.rename(request.name, request.title)
    return {"success": True, "name": new_name}


@router.delete("/chats/{name}")
async def delete_chat(name: str):
    old_current = assistant.chat_manager.current_chat
    assistant.chat_manager.delete(name)

    if name == old_current or not assistant.chat_manager.list():
        conversation = assistant.chat_manager.load()
        assistant.conversation = conversation if conversation else [assistant.system_prompt]
        if not conversation:
            provider = assistant.router.get_provider()
            assistant.chat_manager.save(assistant.conversation, provider=provider)

    return {"success": True}


@router.post("/provider")
async def set_provider(request: ChatRequest):
    success = assistant.router.set_provider(request.message.strip().lower())
    return {"success": success, "provider": assistant.router.get_provider()}


@router.get("/provider")
async def get_provider():
    return {"provider": assistant.router.get_provider()}


# ── Memory 2.0 ───────────────────────────────────────────────────
@router.get("/memories")
async def get_memories(q: str = "", category: Optional[str] = None, limit: int = 100):
    memories = (
        assistant.memory.search(q, limit=min(limit, 100))
        if q.strip()
        else assistant.memory.recall(limit=min(limit, 100), category=category)
    )
    return {
        "memories": memories,
        "count": assistant.memory.get_count(),
        "categories": ["Personal", "Preferences", "Projects", "Goals", "Skills", "Other"],
    }


@router.post("/memories")
async def create_memory(request: MemoryRequest):
    memory_id = assistant.memory.remember(
        request.content,
        category=request.category,
        memory_key=request.key,
        value=request.value,
        confidence=request.confidence,
        source="manual",
    )
    return {"success": True, "id": memory_id}


@router.patch("/memories/{memory_id}")
async def update_memory(memory_id: int, request: MemoryUpdateRequest):
    fields = {
        "content": request.content,
        "category": request.category,
        "memory_key": request.key,
        "value": request.value,
        "confidence": request.confidence,
    }
    fields = {key: value for key, value in fields.items() if value is not None}
    success = assistant.memory.update(memory_id, **fields)
    return {"success": success}


@router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: int):
    assistant.memory.forget(memory_id)
    return {"success": True}
