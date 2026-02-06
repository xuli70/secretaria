import asyncio
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User, Conversation, Message, File
from backend.services.minimax_ai import chat_completion_stream, SYSTEM_PROMPT
from backend.services.perplexity import search_completion_stream, SEARCH_SYSTEM_PROMPT
from backend.services.doc_generator import generate_docx, DOC_SYSTEM_PROMPT
from backend.config import settings

router = APIRouter(prefix="/api/chat", tags=["chat"])

MAX_HISTORY = 50  # max messages sent to the AI


# --- Schemas ---

class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationRename(BaseModel):
    title: str


class FileAttachment(BaseModel):
    id: int
    filename: str
    file_type: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    model_used: str | None = None
    created_at: datetime
    files: list[FileAttachment] = []

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str = ""
    file_ids: list[int] | None = None
    use_search: bool = False
    generate_doc: bool = False


# --- Conversation CRUD ---

@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    body: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = Conversation(
        user_id=user.id,
        title=body.title or "Nueva conversación",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.delete("/conversations/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conv_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conv_id, Conversation.user_id == user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    # Delete files from disk
    files = db.query(File).filter(File.conversation_id == conv_id).all()
    for f in files:
        if f.filepath and os.path.exists(f.filepath):
            try:
                os.remove(f.filepath)
            except OSError:
                pass

    # Delete DB records: files, messages, then conversation
    db.query(File).filter(File.conversation_id == conv_id).delete()
    db.query(Message).filter(Message.conversation_id == conv_id).delete()
    db.delete(conv)
    db.commit()


@router.patch("/conversations/{conv_id}", response_model=ConversationOut)
def rename_conversation(
    conv_id: int,
    body: ConversationRename,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conv_id, Conversation.user_id == user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    conv.title = body.title
    conv.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conv)
    return conv


# --- Messages ---

@router.get("/conversations/{conv_id}/messages", response_model=list[MessageOut])
def get_messages(
    conv_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conv_id, Conversation.user_id == user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    messages = (
        db.query(Message)
        .options(joinedload(Message.files))
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
        .all()
    )
    return messages


@router.post("/conversations/{conv_id}/messages")
async def send_message(
    conv_id: int,
    body: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conv_id, Conversation.user_id == user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    content = body.content.strip()
    file_ids = body.file_ids or []

    # Must have content or files
    if not content and not file_ids:
        raise HTTPException(status_code=400, detail="Mensaje vacío")

    # Build file context for AI
    file_context_parts = []
    attached_files = []
    if file_ids:
        attached_files = (
            db.query(File)
            .filter(File.id.in_(file_ids), File.conversation_id == conv_id)
            .all()
        )
        for f in attached_files:
            if f.extracted_text:
                file_context_parts.append(
                    f"[Archivo adjunto: {f.filename}]\n{f.extracted_text}"
                )
            else:
                file_context_parts.append(f"[Archivo adjunto: {f.filename} ({f.file_type})]")

    # Build the display content (what gets saved)
    display_content = content or "[Archivo adjunto]"

    # Build the AI content (with extracted text injected)
    if file_context_parts:
        ai_content = "\n\n".join(file_context_parts)
        if content:
            ai_content += f"\n\n{content}"
    else:
        ai_content = content

    # Save user message
    user_msg = Message(
        conversation_id=conv_id,
        role="user",
        content=display_content,
    )
    db.add(user_msg)
    db.flush()  # get user_msg.id

    # Link files to this message
    for f in attached_files:
        f.message_id = user_msg.id

    conv.updated_at = datetime.now(timezone.utc)
    db.commit()

    user_msg_id = user_msg.id

    # Build message history for the AI
    recent = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at.desc())
        .limit(MAX_HISTORY)
        .all()
    )
    recent.reverse()

    use_search = body.use_search
    generate_doc = body.generate_doc
    if generate_doc:
        system_prompt = DOC_SYSTEM_PROMPT
    elif use_search:
        system_prompt = SEARCH_SYSTEM_PROMPT
    else:
        system_prompt = SYSTEM_PROMPT
    ai_messages = [{"role": "system", "content": system_prompt}]
    for m in recent:
        msg_content = m.content
        # For the current user message, use the AI content with file context
        if m.id == user_msg_id:
            msg_content = ai_content
        ai_messages.append({"role": m.role, "content": msg_content})

    # Auto-title on first user message
    is_first = len(recent) == 1 and recent[0].role == "user"
    if is_first:
        title_text = content or (attached_files[0].filename if attached_files else "Archivo")
        title = title_text[:50].strip()
        if len(title_text) > 50:
            title += "..."
        conv.title = title
        db.commit()

    # Select stream function and model label
    if use_search:
        stream_fn = search_completion_stream
        model_label = f"perplexity-{settings.PERPLEXITY_MODEL}"
    else:
        stream_fn = chat_completion_stream
        model_label = settings.MINIMAX_MODEL

    # Stream response
    async def event_stream():
        full_response = ""
        async for chunk in stream_fn(ai_messages):
            full_response += chunk
            yield f"data: {chunk}\n\n"

        # Save assistant response in a new DB session
        from backend.database import SessionLocal
        import json as _json
        save_db = SessionLocal()
        try:
            assistant_msg = Message(
                conversation_id=conv_id,
                role="assistant",
                content=full_response,
                model_used=model_label,
            )
            save_db.add(assistant_msg)
            save_db.flush()

            # Generate DOCX if in document mode
            if generate_doc and full_response.strip():
                save_dir = os.path.join(settings.DATA_DIR, "generados")
                title = content[:60] if content else "Documento"
                filepath, filename = generate_docx(full_response, title, save_dir)
                size = os.path.getsize(filepath)

                doc_file = File(
                    conversation_id=conv_id,
                    message_id=assistant_msg.id,
                    filename=filename,
                    filepath=filepath,
                    file_type="document",
                    mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    size_bytes=size,
                )
                save_db.add(doc_file)
                save_db.flush()

                file_info = _json.dumps({
                    "id": doc_file.id,
                    "filename": doc_file.filename,
                    "size_bytes": doc_file.size_bytes,
                })
                yield f"data: [FILE:{file_info}]\n\n"

            save_db.query(Conversation).filter(Conversation.id == conv_id).update(
                {"updated_at": datetime.now(timezone.utc)}
            )
            save_db.commit()
        finally:
            save_db.close()

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
