from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
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


# ── /chat (non-streaming) ────────────────────────────────────────
@router.post("/chat")
async def chat(request: ChatRequest):
    attachments_dict = [att.model_dump() for att in request.attachments]
    response = assistant.chat(request.message, attachments=attachments_dict)
    return {"response": response}


# ── /stream ──────────────────────────────────────────────────────
# Bug fix: the old code called assistant.stream() incorrectly;
# AssistantManager.stream() is a generator — we must iterate it.
# Also removed the duplicate command_handler.handle() call that
# was causing garbled output (the manager already handles commands).
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
            # Disable buffering so tokens arrive immediately
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
        }
    )


# ── /upload ──────────────────────────────────────────────────────
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
            "filename":  file.filename,
            "temp_path":  str(temp_path).replace("\\", "/"),
            "size":       temp_path.stat().st_size
        })

    return {"success": True, "files": metadata}


# ── /chats ───────────────────────────────────────────────────────
@router.get("/chats")
async def list_chats():
    return assistant.chat_manager.list()


# ── /active-chat ─────────────────────────────────────────────────
# Returns which chat is currently loaded on the backend so the
# frontend can highlight the correct sidebar item and set the title
# bar on startup without a separate round-trip per chat.
@router.get("/active-chat")
async def active_chat():
    meta = assistant.chat_manager.load_meta()
    return {
        "name":     assistant.chat_manager.current_chat,
        "title":    meta.get("title") or assistant.chat_manager.current_chat,
        "messages": assistant.conversation,
    }


# ── /chats/new  (was MISSING — caused newChat() to always fail) ──
@router.post("/chats/new")
async def new_chat(request: ChatRequest):
    name = request.message.strip() or "New Chat"

    assistant.chat_manager.new(name)
    assistant.conversation = [assistant.system_prompt]

    # Save immediately so the file contains the system prompt and the
    # current provider — never leaves the chat file with messages: [].
    provider = assistant.router.get_provider()
    assistant.chat_manager.save(assistant.conversation, provider=provider)

    return {
        "success": True,
        "name": assistant.chat_manager.current_chat
    }


# ── /chats/load ──────────────────────────────────────────────────
@router.post("/chats/load")
async def load_chat(request: ChatRequest):
    conversation = assistant.chat_manager.switch(request.message)
    assistant.conversation = conversation if conversation else [assistant.system_prompt]

    # Restore the provider that was active when this chat was last saved.
    meta = assistant.chat_manager.load_meta()
    saved_provider = meta.get("provider", "")
    if saved_provider:
        assistant.router.set_provider(saved_provider)

    return {
        "success": True,
        "messages": assistant.conversation
    }


# ── /chats/rename ────────────────────────────────────────────────
@router.post("/chats/rename")
async def rename_chat(request: RenameRequest):
    new_name = assistant.chat_manager.rename(request.name, request.title)
    return {
        "success": True,
        "name": new_name
    }


# ── /chats/{name} ────────────────────────────────────────────────
@router.delete("/chats/{name}")
async def delete_chat(name: str):
    old_current = assistant.chat_manager.current_chat
    assistant.chat_manager.delete(name)
    
    # If the active chat was deleted, load the new active one
    if name == old_current or not assistant.chat_manager.list():
        conversation = assistant.chat_manager.load()
        assistant.conversation = conversation if conversation else [assistant.system_prompt]
        if not conversation:
            provider = assistant.router.get_provider()
            assistant.chat_manager.save(assistant.conversation, provider=provider)
            
    return {"success": True}


# ── /provider ────────────────────────────────────────────────────
@router.post("/provider")
async def set_provider(request: ChatRequest):
    success = assistant.router.set_provider(request.message.strip().lower())
    return {"success": success, "provider": assistant.router.get_provider()}


@router.get("/provider")
async def get_provider():
    return {"provider": assistant.router.get_provider()}


# ── /memories ────────────────────────────────────────────────────
@router.get("/memories")
async def get_memories():
    memories = assistant.memory.recall(limit=None)
    return {
        "memories": memories,
        "count":    assistant.memory.get_count(),
    }


@router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: int):
    assistant.memory.forget(memory_id)
    return {"success": True}
