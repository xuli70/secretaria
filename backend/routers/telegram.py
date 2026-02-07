import os
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from backend.auth import get_current_user
from backend.config import settings
from backend.database import get_db
from backend.models import User, Conversation, Message, File, TelegramContact, TelegramSend
from backend.services import telegram_bot

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


# --- Schemas ---

class ContactCreate(BaseModel):
    name: str
    chat_id: str


class ContactOut(BaseModel):
    id: int
    name: str
    chat_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class SendRequest(BaseModel):
    message_id: int
    contact_id: int


class SendBulkRequest(BaseModel):
    message_ids: list[int]
    contact_id: int


class SendResult(BaseModel):
    ok: bool
    detail: str
    send_id: int | None = None


class HistoryOut(BaseModel):
    id: int
    message_id: int
    contact_name: str
    contact_chat_id: str
    status: str
    sent_at: datetime | None = None

    class Config:
        from_attributes = True


# --- Bot Status ---

@router.get("/bot-status")
async def bot_status():
    """Check if Telegram bot token is configured and valid."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return {"configured": False, "bot": None}
    result = await telegram_bot.get_me()
    if result.get("ok"):
        bot = result["result"]
        return {
            "configured": True,
            "bot": {
                "username": bot.get("username"),
                "first_name": bot.get("first_name"),
            },
        }
    return {"configured": False, "bot": None}


# --- Contacts CRUD ---

@router.get("/contacts", response_model=list[ContactOut])
def list_contacts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(TelegramContact)
        .filter(TelegramContact.user_id == user.id)
        .order_by(TelegramContact.created_at.desc())
        .all()
    )


@router.post("/contacts", response_model=ContactOut, status_code=201)
def create_contact(
    body: ContactCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    name = body.name.strip()
    chat_id = body.chat_id.strip()
    if not name or not chat_id:
        raise HTTPException(status_code=400, detail="Nombre y chat_id requeridos")

    contact = TelegramContact(
        user_id=user.id,
        name=name,
        chat_id=chat_id,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(
    contact_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = (
        db.query(TelegramContact)
        .filter(TelegramContact.id == contact_id, TelegramContact.user_id == user.id)
        .first()
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")

    db.query(TelegramSend).filter(TelegramSend.contact_id == contact_id).delete()
    db.delete(contact)
    db.commit()


# --- Send ---

@router.post("/send", response_model=SendResult)
async def forward_message(
    body: SendRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Forward an assistant message (text + files) to a Telegram contact."""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="Telegram bot no configurado")

    # Verify contact ownership
    contact = (
        db.query(TelegramContact)
        .filter(TelegramContact.id == body.contact_id, TelegramContact.user_id == user.id)
        .first()
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")

    # Verify message ownership (through conversation)
    msg = (
        db.query(Message)
        .options(joinedload(Message.files))
        .join(Message.conversation)
        .filter(
            Message.id == body.message_id,
            Message.conversation.has(user_id=user.id),
        )
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    # Create send record
    send = TelegramSend(
        message_id=msg.id,
        contact_id=contact.id,
        status="sending",
    )
    db.add(send)
    db.commit()
    db.refresh(send)

    # Send text
    text = msg.content.strip()
    if text:
        result = await telegram_bot.send_message(contact.chat_id, text)
        if not result.get("ok"):
            send.status = "error"
            db.commit()
            return SendResult(
                ok=False,
                detail=result.get("description", "Error enviando mensaje"),
                send_id=send.id,
            )

    # Send attached files
    for f in msg.files:
        if f.filepath and os.path.exists(f.filepath):
            result = await telegram_bot.send_document(
                contact.chat_id, f.filepath, f.filename
            )
            if not result.get("ok"):
                send.status = "partial"
                db.commit()
                return SendResult(
                    ok=False,
                    detail=f"Texto enviado, error en archivo: {f.filename}",
                    send_id=send.id,
                )

    send.status = "sent"
    send.sent_at = datetime.now(timezone.utc)
    db.commit()
    return SendResult(ok=True, detail="Enviado", send_id=send.id)


# --- Bulk Send ---

def _strip_think(text: str) -> str:
    return re.sub(r"<think>[\s\S]*?</think>", "", text).strip()


def split_telegram_text(text: str, max_len: int = 4096) -> list[str]:
    """Split text into chunks of max_len, breaking at paragraph boundaries."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Find last double-newline within limit
        cut = text.rfind("\n\n", 0, max_len)
        if cut <= 0:
            # Fallback: single newline
            cut = text.rfind("\n", 0, max_len)
        if cut <= 0:
            cut = max_len
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip("\n")
    return chunks


@router.post("/send-bulk", response_model=SendResult)
async def forward_bulk(
    body: SendBulkRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Forward multiple messages (text + files) to a Telegram contact."""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="Telegram bot no configurado")

    if not body.message_ids:
        raise HTTPException(status_code=400, detail="Sin mensajes seleccionados")

    # Verify contact ownership
    contact = (
        db.query(TelegramContact)
        .filter(TelegramContact.id == body.contact_id, TelegramContact.user_id == user.id)
        .first()
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")

    # Fetch messages, verify ownership via conversation.user_id
    messages = (
        db.query(Message)
        .options(joinedload(Message.files))
        .join(Message.conversation)
        .filter(
            Message.id.in_(body.message_ids),
            Conversation.user_id == user.id,
        )
        .order_by(Message.created_at.asc())
        .all()
    )

    if not messages:
        raise HTTPException(status_code=404, detail="Mensajes no encontrados")

    # Build combined text
    blocks = []
    all_files = []
    for msg in messages:
        label = "[Tu]" if msg.role == "user" else "[Secretaria]"
        ts = msg.created_at.strftime("%H:%M") if msg.created_at else ""
        text = msg.content.strip()
        if msg.role == "assistant":
            text = _strip_think(text)
        if text and text != "[Archivo adjunto]":
            blocks.append(f"{label} {ts}\n{text}")
        # Collect files
        for f in msg.files:
            if f.filepath and os.path.exists(f.filepath):
                all_files.append(f)

    combined = "\n\n".join(blocks)

    # Create a TelegramSend record per message in the batch
    send_ids = []
    for msg in messages:
        send = TelegramSend(
            message_id=msg.id,
            contact_id=contact.id,
            status="sending",
        )
        db.add(send)
        db.flush()
        send_ids.append(send.id)
    db.commit()

    # Send text chunks
    if combined:
        for chunk in split_telegram_text(combined):
            result = await telegram_bot.send_message(contact.chat_id, chunk)
            if not result.get("ok"):
                db.query(TelegramSend).filter(TelegramSend.id.in_(send_ids)).update(
                    {"status": "error"}, synchronize_session=False
                )
                db.commit()
                return SendResult(
                    ok=False,
                    detail=result.get("description", "Error enviando mensaje"),
                )

    # Send files
    for f in all_files:
        result = await telegram_bot.send_document(contact.chat_id, f.filepath, f.filename)
        if not result.get("ok"):
            db.query(TelegramSend).filter(TelegramSend.id.in_(send_ids)).update(
                {"status": "partial"}, synchronize_session=False
            )
            db.commit()
            return SendResult(
                ok=False,
                detail=f"Texto enviado, error en archivo: {f.filename}",
            )

    # Mark all as sent
    now = datetime.now(timezone.utc)
    db.query(TelegramSend).filter(TelegramSend.id.in_(send_ids)).update(
        {"status": "sent", "sent_at": now}, synchronize_session=False
    )
    db.commit()

    return SendResult(ok=True, detail="Enviado")


# --- History ---

@router.get("/history")
def send_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sends = (
        db.query(TelegramSend)
        .join(TelegramSend.contact)
        .filter(TelegramContact.user_id == user.id)
        .order_by(TelegramSend.id.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": s.id,
            "message_id": s.message_id,
            "contact_name": s.contact.name,
            "contact_chat_id": s.contact.chat_id,
            "status": s.status,
            "sent_at": s.sent_at,
        }
        for s in sends
    ]
