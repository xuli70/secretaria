from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User, File

router = APIRouter(prefix="/api/files", tags=["files"])


class FileExplorerItem(BaseModel):
    id: int
    filename: str
    file_type: str | None
    mime_type: str | None
    size_bytes: int | None
    created_at: datetime
    is_generated: bool

    class Config:
        from_attributes = True


@router.get("", response_model=list[FileExplorerItem])
def list_all_files(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all files for the current user across all conversations."""
    files = (
        db.query(File)
        .join(File.conversation)
        .filter(File.conversation.has(user_id=user.id))
        .order_by(File.created_at.desc())
        .all()
    )
    result = []
    for f in files:
        result.append(
            FileExplorerItem(
                id=f.id,
                filename=f.filename,
                file_type=f.file_type,
                mime_type=f.mime_type,
                size_bytes=f.size_bytes,
                created_at=f.created_at,
                is_generated="/generados/" in (f.filepath or ""),
            )
        )
    return result
