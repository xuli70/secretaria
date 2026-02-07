import base64
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def _get_service(creds: Credentials):
    return build("gmail", "v1", credentials=creds)


def list_messages(
    creds: Credentials,
    query: str = "",
    max_results: int = 20,
) -> list[dict]:
    service = _get_service(creds)
    params: dict = {"userId": "me", "maxResults": max_results}
    if query:
        params["q"] = query
    result = service.users().messages().list(**params).execute()
    messages = result.get("messages", [])
    if not messages:
        return []
    # Fetch metadata for each message
    out = []
    for msg_stub in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_stub["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"])
            .execute()
        )
        out.append(_format_message_summary(msg))
    return out


def get_message(creds: Credentials, message_id: str) -> dict:
    service = _get_service(creds)
    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    return _format_message_full(msg)


def send_message(
    creds: Credentials,
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    bcc: str | None = None,
) -> dict:
    mime = MIMEText(body, "plain", "utf-8")
    mime["To"] = to
    mime["Subject"] = subject
    if cc:
        mime["Cc"] = cc
    if bcc:
        mime["Bcc"] = bcc

    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode("ascii")
    service = _get_service(creds)
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return {"id": sent.get("id"), "threadId": sent.get("threadId"), "ok": True}


def _get_header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _format_message_summary(msg: dict) -> dict:
    headers = msg.get("payload", {}).get("headers", [])
    labels = msg.get("labelIds", [])
    return {
        "id": msg.get("id", ""),
        "threadId": msg.get("threadId", ""),
        "snippet": msg.get("snippet", ""),
        "from": _get_header(headers, "From"),
        "subject": _get_header(headers, "Subject"),
        "date": _get_header(headers, "Date"),
        "unread": "UNREAD" in labels,
    }


def _extract_body(payload: dict) -> str:
    """Extract plain text body from message payload."""
    mime_type = payload.get("mimeType", "")

    # Simple single-part message
    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    # Multipart — look for text/plain first
    parts = payload.get("parts", [])
    for part in parts:
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        # Nested multipart
        nested = part.get("parts", [])
        for np in nested:
            if np.get("mimeType") == "text/plain":
                data = np.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    return ""


def _format_message_full(msg: dict) -> dict:
    headers = msg.get("payload", {}).get("headers", [])
    labels = msg.get("labelIds", [])
    body = _extract_body(msg.get("payload", {}))
    return {
        "id": msg.get("id", ""),
        "threadId": msg.get("threadId", ""),
        "snippet": msg.get("snippet", ""),
        "from": _get_header(headers, "From"),
        "to": _get_header(headers, "To"),
        "subject": _get_header(headers, "Subject"),
        "date": _get_header(headers, "Date"),
        "body": body,
        "unread": "UNREAD" in labels,
    }
