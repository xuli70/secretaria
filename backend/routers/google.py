from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
import httpx

from backend.auth import get_current_user
from backend.config import settings
from backend.database import get_db
from backend.services.google_auth import get_stored_token, store_token, delete_token
from backend.services.google_calendar import (
    list_events,
    get_event,
    create_event,
    delete_event,
)
from backend.services.google_gmail import (
    list_messages,
    get_message,
    send_message,
)
from backend.services.google_drive import (
    list_files as drive_list_files,
    list_recent as drive_list_recent,
    get_file as drive_get_file,
    download_file as drive_download_file,
    upload_file as drive_upload_file,
)

router = APIRouter(prefix="/api/google", tags=["google"])

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/contacts.readonly",
]


def _build_flow(redirect_uri: str | None = None) -> Flow:
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
    return flow


def _credentials_to_dict(creds: Credentials) -> dict:
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else [],
    }


def _dict_to_credentials(data: dict) -> Credentials:
    return Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes"),
    )


def get_valid_credentials(db: Session, user_id: int) -> Credentials | None:
    """Return valid Google credentials for user, refreshing if expired."""
    token_data = get_stored_token(db, user_id)
    if not token_data:
        return None
    creds = _dict_to_credentials(token_data)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        store_token(db, user_id, _credentials_to_dict(creds), " ".join(creds.scopes or []))
    return creds


@router.get("/status")
def google_status(user=Depends(get_current_user), db: Session = Depends(get_db)):
    token_data = get_stored_token(db, user.id)
    if not token_data:
        return {"connected": False, "scopes": []}
    scopes = token_data.get("scopes", [])
    return {"connected": True, "scopes": scopes}


@router.get("/auth-url")
def google_auth_url(user=Depends(get_current_user)):
    flow = _build_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=f"user_{user.id}",
    )
    return {"auth_url": auth_url}


@router.get("/callback")
def google_callback(request: Request, code: str = "", state: str = "", error: str = "", db: Session = Depends(get_db)):
    # Handle Google errors
    if error:
        return RedirectResponse(url=f"/?google_error={error}")

    # Extract user_id from state
    if not state.startswith("user_"):
        return RedirectResponse(url="/?google_error=invalid_state")
    try:
        user_id = int(state.split("_", 1)[1])
    except (ValueError, IndexError):
        return RedirectResponse(url="/?google_error=invalid_state")

    # Exchange code for tokens
    try:
        flow = _build_flow()
        flow.fetch_token(code=code)
        creds = flow.credentials
        token_data = _credentials_to_dict(creds)
        scopes_str = " ".join(creds.scopes) if creds.scopes else ""
        store_token(db, user_id, token_data, scopes_str)
    except Exception:
        return RedirectResponse(url="/?google_error=token_exchange_failed")

    return RedirectResponse(url="/?google_connected=true")


@router.post("/disconnect")
def google_disconnect(user=Depends(get_current_user), db: Session = Depends(get_db)):
    # Try to revoke token at Google (best-effort)
    token_data = get_stored_token(db, user.id)
    if token_data and token_data.get("token"):
        try:
            httpx.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": token_data["token"]},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=5,
            )
        except Exception:
            pass  # best-effort revocation

    deleted = delete_token(db, user.id)
    return {"ok": deleted}


# ── Calendar endpoints ────────────────────────────────────────────


def _require_google(db: Session, user_id: int) -> Credentials:
    creds = get_valid_credentials(db, user_id)
    if not creds:
        raise HTTPException(status_code=400, detail="Google no conectado")
    return creds


@router.get("/calendar/events")
def calendar_events_range(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
    time_min: str | None = None,
    time_max: str | None = None,
    max_results: int = 50,
):
    creds = _require_google(db, user.id)
    return list_events(creds, time_min=time_min, time_max=time_max, max_results=max_results)


@router.get("/calendar/events/today")
def calendar_events_today(user=Depends(get_current_user), db: Session = Depends(get_db)):
    creds = _require_google(db, user.id)
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return list_events(creds, time_min=start.isoformat(), time_max=end.isoformat())


@router.get("/calendar/events/week")
def calendar_events_week(user=Depends(get_current_user), db: Session = Depends(get_db)):
    creds = _require_google(db, user.id)
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    return list_events(creds, time_min=start.isoformat(), time_max=end.isoformat())


class CreateEventBody(BaseModel):
    summary: str
    start: str
    end: str
    description: str | None = None
    location: str | None = None
    attendees: list[str] | None = None


@router.post("/calendar/events")
def calendar_create_event(
    body: CreateEventBody,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    creds = _require_google(db, user.id)
    return create_event(
        creds,
        summary=body.summary,
        start=body.start,
        end=body.end,
        description=body.description,
        location=body.location,
        attendees=body.attendees,
    )


@router.delete("/calendar/events/{event_id}")
def calendar_delete_event(
    event_id: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    creds = _require_google(db, user.id)
    delete_event(creds, event_id)
    return {"ok": True}


# ── Gmail endpoints ──────────────────────────────────────────────


@router.get("/gmail/messages")
def gmail_list_messages(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
    q: str = "",
    max: int = 20,
):
    creds = _require_google(db, user.id)
    return list_messages(creds, query=q, max_results=max)


@router.get("/gmail/messages/unread")
def gmail_unread_messages(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
    max: int = 20,
):
    creds = _require_google(db, user.id)
    return list_messages(creds, query="is:unread", max_results=max)


@router.get("/gmail/messages/{message_id}")
def gmail_get_message(
    message_id: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    creds = _require_google(db, user.id)
    return get_message(creds, message_id)


class SendEmailBody(BaseModel):
    to: str
    subject: str
    body: str
    cc: str | None = None
    bcc: str | None = None


@router.post("/gmail/send")
def gmail_send_message(
    data: SendEmailBody,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    creds = _require_google(db, user.id)
    return send_message(
        creds,
        to=data.to,
        subject=data.subject,
        body=data.body,
        cc=data.cc,
        bcc=data.bcc,
    )


# ── Drive endpoints ──────────────────────────────────────────────


@router.get("/drive/files")
def drive_files(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
    q: str = "",
    folder: str = "",
    max: int = 30,
):
    creds = _require_google(db, user.id)
    return drive_list_files(creds, query=q, folder_id=folder or None, max_results=max)


@router.get("/drive/files/recent")
def drive_files_recent(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
    max: int = 20,
):
    creds = _require_google(db, user.id)
    return drive_list_recent(creds, max_results=max)


@router.get("/drive/files/{file_id}")
def drive_file_meta(
    file_id: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    creds = _require_google(db, user.id)
    return drive_get_file(creds, file_id)


@router.get("/drive/files/{file_id}/download")
def drive_file_download(
    file_id: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    creds = _require_google(db, user.id)
    content, filename, mime_type = drive_download_file(creds, file_id)
    return Response(
        content=content,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/drive/upload")
async def drive_file_upload(
    file: UploadFile = File(...),
    folder: str = "",
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    creds = _require_google(db, user.id)
    content = await file.read()
    mime = file.content_type or "application/octet-stream"
    result = drive_upload_file(
        creds,
        filename=file.filename or "upload",
        content=content,
        mime_type=mime,
        folder_id=folder or None,
    )
    return result
