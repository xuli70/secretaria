import json
from typing import AsyncGenerator

import httpx

from backend.config import settings

SYSTEM_PROMPT = "Eres Secretaria, un asistente personal eficiente y amable."

THINK_OPEN = "<think>"
THINK_CLOSE = "</think>"


def _filter_think_blocks(text: str, inside_think: bool) -> tuple[str, str, bool]:
    """Remove <think>...</think> blocks from streaming text.

    Returns (output, remaining_buffer, inside_think).
    - output: clean text safe to emit
    - remaining_buffer: partial tag data to carry over to next chunk
    - inside_think: whether we're still inside a think block
    """
    output = ""
    i = 0
    while i < len(text):
        if inside_think:
            # Look for closing tag
            close_pos = text.find(THINK_CLOSE, i)
            if close_pos != -1:
                i = close_pos + len(THINK_CLOSE)
                inside_think = False
            else:
                # Check if end of text could be a partial </think>
                for plen in range(min(len(THINK_CLOSE) - 1, len(text) - i), 0, -1):
                    if THINK_CLOSE.startswith(text[i + (len(text) - i - plen):]):
                        # Keep partial match in buffer
                        return output, text[len(text) - plen:], True
                # No partial match, discard everything (still inside think)
                return output, "", True
        else:
            # Look for opening tag
            open_pos = text.find(THINK_OPEN, i)
            if open_pos != -1:
                output += text[i:open_pos]
                i = open_pos + len(THINK_OPEN)
                inside_think = True
            else:
                # Check if end of text could be a partial <think>
                remaining = text[i:]
                for plen in range(min(len(THINK_OPEN) - 1, len(remaining)), 0, -1):
                    if THINK_OPEN.startswith(remaining[len(remaining) - plen:]):
                        output += remaining[:len(remaining) - plen]
                        return output, remaining[len(remaining) - plen:], False
                output += remaining
                return output, "", False
    return output, "", inside_think


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

    inside_think = False
    buffer = ""

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
                        text = buffer + content
                        output, buffer, inside_think = _filter_think_blocks(text, inside_think)
                        if output:
                            yield output
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    # Flush any remaining buffer (only if it's not part of a think block)
    if buffer and not inside_think:
        yield buffer
