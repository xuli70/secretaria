from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def _get_service(creds: Credentials):
    return build("calendar", "v3", credentials=creds)


def list_events(
    creds: Credentials,
    time_min: str | None = None,
    time_max: str | None = None,
    max_results: int = 50,
) -> list[dict]:
    service = _get_service(creds)
    params: dict = {
        "calendarId": "primary",
        "singleEvents": True,
        "orderBy": "startTime",
        "maxResults": max_results,
    }
    if time_min:
        params["timeMin"] = time_min
    if time_max:
        params["timeMax"] = time_max

    result = service.events().list(**params).execute()
    events = result.get("items", [])
    return [_format_event(e) for e in events]


def get_event(creds: Credentials, event_id: str) -> dict:
    service = _get_service(creds)
    event = service.events().get(calendarId="primary", eventId=event_id).execute()
    return _format_event(event)


def create_event(
    creds: Credentials,
    summary: str,
    start: str,
    end: str,
    description: str | None = None,
    location: str | None = None,
    attendees: list[str] | None = None,
) -> dict:
    service = _get_service(creds)
    body: dict = {
        "summary": summary,
        "start": _parse_datetime(start),
        "end": _parse_datetime(end),
    }
    if description:
        body["description"] = description
    if location:
        body["location"] = location
    if attendees:
        body["attendees"] = [{"email": a} for a in attendees]

    event = service.events().insert(calendarId="primary", body=body).execute()
    return _format_event(event)


def delete_event(creds: Credentials, event_id: str) -> bool:
    service = _get_service(creds)
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    return True


def _parse_datetime(dt_str: str) -> dict:
    """Convert ISO datetime string to Google Calendar datetime dict."""
    # If it looks like a date-only string (YYYY-MM-DD), use 'date' field
    if len(dt_str) == 10:
        return {"date": dt_str}
    # Ensure timezone info is included for dateTime (Google API requires it)
    if "+" not in dt_str and "Z" not in dt_str and not dt_str.endswith("z"):
        return {"dateTime": dt_str, "timeZone": "Europe/Madrid"}
    return {"dateTime": dt_str}


def _format_event(event: dict) -> dict:
    start = event.get("start", {})
    end = event.get("end", {})
    return {
        "id": event.get("id"),
        "summary": event.get("summary", "(Sin titulo)"),
        "description": event.get("description", ""),
        "location": event.get("location", ""),
        "start": start.get("dateTime") or start.get("date", ""),
        "end": end.get("dateTime") or end.get("date", ""),
        "html_link": event.get("htmlLink", ""),
        "attendees": [
            {"email": a.get("email", ""), "name": a.get("displayName", "")}
            for a in event.get("attendees", [])
        ],
    }
