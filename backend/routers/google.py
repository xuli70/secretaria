from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
import httpx

from backend.auth import get_current_user
from backend.config import settings
from backend.database import get_db
from backend.services.google_auth import get_stored_token, store_token, delete_token

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
