import json
from typing import AsyncGenerator

import httpx

from backend.config import settings

SEARCH_SYSTEM_PROMPT = (
    "Eres Secretaria. Busca informacion actualizada en internet y "
    "responde con fuentes. Responde en español."
)


async def search_completion_stream(
    messages: list[dict], model: str | None = None
) -> AsyncGenerator[str, None]:
    """Stream search completion from Perplexity AI (OpenAI-compatible API)."""
    if not settings.PERPLEXITY_API_KEY:
        yield "Error: No se ha configurado PERPLEXITY_API_KEY. Configura tu API key de Perplexity."
        return

    model = model or settings.PERPLEXITY_MODEL
    url = f"{settings.PERPLEXITY_API_URL}/chat/completions"

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }

    headers = {
        "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
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
                yield f"Error de Perplexity ({response.status_code}): {detail}"
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
