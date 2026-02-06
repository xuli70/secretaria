import json
from typing import AsyncGenerator

import httpx

from backend.config import settings

SYSTEM_PROMPT = "Eres Secretaria, un asistente personal eficiente y amable."


async def chat_completion_stream(
    messages: list[dict], model: str | None = None
) -> AsyncGenerator[str, None]:
    """Stream chat completion from MINIMAX AI (OpenAI-compatible API)."""
    if not settings.MINIMAX_API_KEY:
        yield "Error: No se ha configurado MINIMAX_API_KEY. Configura tu API key de MINIMAX."
        return

    model = model or settings.MINIMAX_MODEL
    url = f"{settings.MINIMAX_API_URL}/chat/completions"

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }

    headers = {
        "Authorization": f"Bearer {settings.MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST", url, json=payload, headers=headers
        ) as response:
            if response.status_code != 200:
                body = await response.aread()
                try:
                    detail = json.loads(body).get("error", {}).get("message", body.decode())
                except Exception:
                    detail = body.decode()
                yield f"Error de MINIMAX AI ({response.status_code}): {detail}"
                return

            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
