import httpx

from backend.config import settings

BASE_URL = "https://api.telegram.org/bot{token}/"


def _url(method: str) -> str:
    return BASE_URL.format(token=settings.TELEGRAM_BOT_TOKEN) + method


async def get_me() -> dict:
    """Verify bot token by calling getMe."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return {"ok": False, "description": "TELEGRAM_BOT_TOKEN no configurado"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(_url("getMe"))
        return resp.json()


async def send_message(chat_id: str, text: str) -> dict:
    """Send a text message to a Telegram chat."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return {"ok": False, "description": "TELEGRAM_BOT_TOKEN no configurado"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _url("sendMessage"),
            json={
                "chat_id": chat_id,
                "text": text,
            },
        )
        return resp.json()


async def send_document(
    chat_id: str, filepath: str, filename: str, caption: str | None = None
) -> dict:
    """Send a file as a document to a Telegram chat."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return {"ok": False, "description": "TELEGRAM_BOT_TOKEN no configurado"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        with open(filepath, "rb") as f:
            files = {"document": (filename, f)}
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption[:1024]
            resp = await client.post(_url("sendDocument"), data=data, files=files)
            return resp.json()
