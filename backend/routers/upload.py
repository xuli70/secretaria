import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from backend.auth import get_current_user
from backend.config import settings
from backend.database import get_db
from backend.models import User, Conversation, File
from backend.services.file_handler import (
    sanitize_filename,
    classify_file,
    validate_file,
    save_file,
    extract_text,
)

router = APIRouter(prefix="/api/upload", tags=["upload"])


class FileOut(BaseModel):
    id: int
    filename: str
    file_type: str | None
    mime_type: str | None
    size_bytes: int | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post(
    "/conversations/{conv_id}/files",
    response_model=FileOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    conv_id: int,
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify conversation belongs to user
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conv_id, Conversation.user_id == user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    # Read file bytes
    data = await file.read()
    original_name = file.filename or "archivo"
    size = len(data)

    # Validate
    error = validate_file(original_name, size)
    if error:
        raise HTTPException(status_code=400, detail=error)

    ext = os.path.splitext(original_name)[1].lower()
    file_type = classify_file(ext)
    safe_name = sanitize_filename(original_name)
    mime_type = settings.MIME_TYPES.get(ext, "application/octet-stream")

    # Save to disk
    filepath = save_file(data, safe_name, file_type)

    # Extract text for documents
    extracted = extract_text(filepath, ext)

    # Create DB record
    db_file = File(
        conversation_id=conv_id,
        filename=original_name,
        filepath=filepath,
        file_type=file_type,
        mime_type=mime_type,
        size_bytes=size,
        extracted_text=extracted or None,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return db_file


@router.get("/files/{file_id}")
def serve_file(
    file_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_file = (
        db.query(File)
        .join(Conversation)
        .filter(File.id == file_id, Conversation.user_id == user.id)
        .first()
    )
    if not db_file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    if not os.path.exists(db_file.filepath):
        # Attempt to recover from extracted_text (applies to uploaded text files)
        if db_file.extracted_text and db_file.filepath:
            os.makedirs(os.path.dirname(db_file.filepath), exist_ok=True)
            with open(db_file.filepath, "w", encoding="utf-8") as wf:
                wf.write(db_file.extracted_text)
        if not os.path.exists(db_file.filepath):
            raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")

    # Images inline, documents as download
    if db_file.file_type == "image":
        return FileResponse(
            db_file.filepath,
            media_type=db_file.mime_type,
            headers={"Content-Disposition": f'inline; filename="{db_file.filename}"'},
        )
    else:
        return FileResponse(
            db_file.filepath,
            media_type=db_file.mime_type,
            filename=db_file.filename,
        )


@router.get("/conversations/{conv_id}/files", response_model=list[FileOut])
def list_files(
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

    return db.query(File).filter(File.conversation_id == conv_id).all()
