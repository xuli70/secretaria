import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from backend.auth import get_current_user
from backend.config import settings
from backend.database import get_db
from backend.models import User, Message, File, TelegramContact, TelegramSend
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
