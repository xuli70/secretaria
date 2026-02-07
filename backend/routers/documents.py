import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.config import settings
from backend.database import get_db
from backend.models import User, File, Message
from backend.services.doc_generator import generate_docx

router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentOut(BaseModel):
    id: int
    filename: str
    size_bytes: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[DocumentOut])
def list_documents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List generated documents for the current user."""
    docs = (
        db.query(File)
        .join(File.conversation)
        .filter(
            File.conversation.has(user_id=user.id),
            File.filepath.contains("/generados/"),
        )
        .order_by(File.created_at.desc())
        .all()
    )
    return docs


@router.get("/{file_id}")
def download_document(
    file_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download a generated document."""
    f = (
        db.query(File)
        .filter(File.id == file_id)
        .first()
    )
    if not f:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Verify ownership
    if not f.conversation or f.conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if not f.filepath or not os.path.exists(f.filepath):
        # Attempt to regenerate from message content
        if f.message_id:
            msg = db.query(Message).filter(Message.id == f.message_id).first()
            if msg and msg.content and msg.content.strip():
                save_dir = os.path.join(settings.DATA_DIR, "generados")
                os.makedirs(save_dir, exist_ok=True)
                temp_path, _ = generate_docx(msg.content, "", save_dir)
                os.makedirs(os.path.dirname(f.filepath), exist_ok=True)
                os.replace(temp_path, f.filepath)
        # If still missing after regen attempt, return error
        if not f.filepath or not os.path.exists(f.filepath):
            raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")

    return FileResponse(
        path=f.filepath,
        filename=f.filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
