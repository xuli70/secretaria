"""Google Actions — Natural language intent detection and execution for chat."""

import json
import logging
import re
from datetime import datetime, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)

from backend.config import settings
from backend.services.google_calendar import list_events, create_event
from backend.services.google_gmail import list_messages, send_message
from backend.services.google_drive import list_recent, list_files as drive_list_files

# ---------------------------------------------------------------------------
# Fast keyword filter — avoids LLM call for unrelated messages
# ---------------------------------------------------------------------------

GOOGLE_KEYWORDS = re.compile(
    r"(?:calendari|agenda|reuni[oó]n|evento|cita|programar|agendar"
    r"|correo|email|e-mail|gmail|mensaje|inbox|bandeja"
    r"|envi[aá]\s.*(?:correo|mail|email)|mandar\s.*(?:correo|mail)"
    r"|no\s*le[ií]do"
    r"|drive|subir\s.*(?:archivo|documento)"
    r"|qu[eé]\s+tengo|mis\s+evento|mis\s+correo|mis\s+archivo"
    r"|archivos?\s+recientes)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Intent detection via LLM (prompt engineering + JSON output)
# ---------------------------------------------------------------------------

INTENT_SYSTEM_PROMPT = """Eres un clasificador de intenciones. Analiza el mensaje del usuario y determina si quiere realizar una acción con Google Calendar, Gmail o Drive.

Responde SOLO con JSON válido. Sin markdown, sin backticks, sin explicaciones.

Si detectas intención Google:
{{"action": "TIPO", "params": {{...}}}}

Si NO detectas intención Google:
{{"action": null}}

Tipos de acciones:
- "calendar_today": Ver eventos de hoy. params: {{}}
- "calendar_week": Ver eventos de la semana. params: {{}}
- "calendar_create": Crear evento. params: {{"summary": "titulo", "date": "YYYY-MM-DD", "time": "HH:MM", "duration_minutes": 60, "description": null, "location": null}}
- "gmail_unread": Ver correos no leídos. params: {{}}
- "gmail_search": Buscar correos. params: {{"query": "término de búsqueda"}}
- "gmail_send": Enviar correo. params: {{"to": "email@...", "subject": "asunto", "body": "contenido"}}
- "drive_recent": Ver archivos recientes de Drive. params: {{}}
- "drive_search": Buscar archivos en Drive. params: {{"query": "término"}}

Reglas:
- Hoy es {today} ({weekday}).
- Para "mañana" usa la fecha del día siguiente.
- Para "esta semana" o "la semana" usa "calendar_week".
- Si dice solo "calendario" o "qué tengo" sin más, usa "calendar_today".
- Si no especifica hora, usa "09:00".
- Si no especifica duración, usa 60 minutos.
- Extrae destinatario, asunto y cuerpo del correo lo mejor posible.
- Si la intención no está clara o no es Google, devuelve {{"action": null}}."""

WEEKDAYS_ES = [
    "lunes", "martes", "miércoles", "jueves",
    "viernes", "sábado", "domingo",
]


def has_google_keywords(message: str) -> bool:
    """Fast check: does the message contain Google-related keywords?"""
    return bool(GOOGLE_KEYWORDS.search(message))


async def detect_intent(message: str) -> dict | None:
    """Use a quick LLM call to detect Google action intent."""
    if not settings.MINIMAX_API_KEY:
        return None

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    weekday = WEEKDAYS_ES[now.weekday()]

    system = INTENT_SYSTEM_PROMPT.replace("{today}", today).replace("{weekday}", weekday)

    url = f"{settings.MINIMAX_API_URL}/chat/completions"
    payload = {
        "model": settings.MINIMAX_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": message},
        ],
        "temperature": 0.1,
        "max_tokens": 300,
    }
    headers = {
        "Authorization": f"Bearer {settings.MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            logger.info("detect_intent status=%s", resp.status_code)
            if resp.status_code != 200:
                logger.warning("detect_intent bad status: %s %s", resp.status_code, resp.text[:200])
                return None
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            logger.info("detect_intent raw content: %s", content[:300])
            # Strip markdown code fences if present
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            result = json.loads(content)
            logger.info("detect_intent parsed: %s", result)
            if result.get("action"):
                return result
    except Exception as e:
        logger.exception("detect_intent error: %s", e)

    return None


# ---------------------------------------------------------------------------
# Action execution — calls existing Google service functions
# ---------------------------------------------------------------------------


def execute_action(intent: dict, creds) -> dict | None:
    """Execute a Google action based on detected intent. Returns structured result."""
    action = intent.get("action")
    params = intent.get("params") or {}

    try:
        if action == "calendar_today":
            now = datetime.now(timezone.utc)
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            events = list_events(creds, time_min=start.isoformat(), time_max=end.isoformat())
            return {"type": "calendar_events", "period": "hoy", "events": events}

        elif action == "calendar_week":
            now = datetime.now(timezone.utc)
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
            events = list_events(creds, time_min=start.isoformat(), time_max=end.isoformat())
            return {"type": "calendar_events", "period": "esta semana", "events": events}

        elif action == "calendar_create":
            summary = params.get("summary", "Evento")
            date_str = params.get("date")
            time_str = params.get("time", "09:00")
            duration = int(params.get("duration_minutes", 60))
            if date_str:
                start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            else:
                start_dt = datetime.now() + timedelta(hours=1)
                start_dt = start_dt.replace(minute=0, second=0, microsecond=0)
            end_dt = start_dt + timedelta(minutes=duration)
            event = create_event(
                creds,
                summary=summary,
                start=start_dt.isoformat(),
                end=end_dt.isoformat(),
                description=params.get("description"),
                location=params.get("location"),
            )
            return {"type": "calendar_created", "event": event}

        elif action == "gmail_unread":
            messages = list_messages(creds, query="is:unread", max_results=10)
            return {"type": "gmail_messages", "filter": "no leidos", "messages": messages}

        elif action == "gmail_search":
            query = params.get("query", "")
            messages = list_messages(creds, query=query, max_results=10)
            return {"type": "gmail_messages", "filter": query, "messages": messages}

        elif action == "gmail_send":
            to = params.get("to", "")
            subject = params.get("subject", "")
            body = params.get("body", "")
            if to and body:
                send_message(creds, to=to, subject=subject, body=body)
                return {"type": "gmail_sent", "to": to, "subject": subject}
            return None

        elif action == "drive_recent":
            files = list_recent(creds, max_results=10)
            return {"type": "drive_files", "filter": "recientes", "files": files}

        elif action == "drive_search":
            query = params.get("query", "")
            files = drive_list_files(creds, query=query, max_results=10)
            return {"type": "drive_files", "filter": query, "files": files}

    except Exception as e:
        return {"type": "error", "message": str(e)}

    return None


# ---------------------------------------------------------------------------
# Format action result as context for the AI response
# ---------------------------------------------------------------------------


def format_action_context(result: dict) -> str:
    """Format action result as textual context so the AI can respond naturally."""
    if not result:
        return ""

    t = result.get("type", "")

    if t == "calendar_events":
        events = result.get("events", [])
        period = result.get("period", "")
        if not events:
            return f"[Google Calendar] No hay eventos {period}."
        lines = [f"[Google Calendar — Eventos {period}]"]
        for ev in events:
            time_str = ev.get("start", "")
            if len(time_str) > 10:
                try:
                    dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M")
                except Exception:
                    pass
            summary = ev.get("summary", "Sin titulo")
            loc = f" ({ev['location']})" if ev.get("location") else ""
            lines.append(f"- {time_str} {summary}{loc}")
        return "\n".join(lines)

    elif t == "calendar_created":
        ev = result.get("event", {})
        return (
            f"[Google Calendar] Evento creado exitosamente: "
            f"{ev.get('summary', 'Evento')} — {ev.get('start', '')} a {ev.get('end', '')}"
        )

    elif t == "gmail_messages":
        messages = result.get("messages", [])
        filter_str = result.get("filter", "")
        if not messages:
            return f"[Gmail] No hay correos ({filter_str})."
        lines = [f"[Gmail — correos {filter_str}] ({len(messages)} resultados)"]
        for msg in messages[:10]:
            fr = msg.get("from", "").split("<")[0].strip()
            subj = msg.get("subject", "(Sin asunto)")
            lines.append(f"- De: {fr} | {subj}")
        return "\n".join(lines)

    elif t == "gmail_sent":
        return (
            f"[Gmail] Correo enviado exitosamente a {result.get('to', '???')} "
            f"con asunto: \"{result.get('subject', '')}\""
        )

    elif t == "drive_files":
        files = result.get("files", [])
        filter_str = result.get("filter", "")
        if not files:
            return f"[Google Drive] No hay archivos ({filter_str})."
        lines = [f"[Google Drive — archivos {filter_str}] ({len(files)} resultados)"]
        for f in files[:10]:
            lines.append(f"- {f.get('name', '???')} ({f.get('file_type', 'archivo')})")
        return "\n".join(lines)

    elif t == "error":
        return f"[Error de Google] {result.get('message', 'Error desconocido')}"

    return ""
