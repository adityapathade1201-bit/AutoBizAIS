"""
services/llm.py
===============
Single reusable helper for calling OpenRouter.

Usage (inside any agent):

    from services.llm import generate_response

    reply = await generate_response(
        system_prompt="You are a finance expert...",
        history=memory.build_conversation_messages(),
        user_message="What is my monthly burn rate?",
    )

OpenRouter is OpenAI-compatible, so we use httpx to POST to their endpoint.
The model is configurable via the LLM_MODEL env var (defaults to a fast,
cost-effective model suitable for SME business tasks).
"""

import os
import httpx
from dotenv import load_dotenv

# Load .env from the backend directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# ── Config ────────────────────────────────────────────────────────────────────
_API_KEY   = os.getenv("OPENROUTER_API_KEY", "")
_MODEL     = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
_BASE_URL  = "https://openrouter.ai/api/v1/chat/completions"
_TIMEOUT   = 30.0  # seconds

# Headers required by OpenRouter
_HEADERS = {
    "Authorization": f"Bearer {_API_KEY}",
    "HTTP-Referer":  "http://localhost:5173",   # identifies your app
    "X-Title":       "AutoBiz AI",
    "Content-Type":  "application/json",
}


async def generate_response(
    system_prompt: str,
    history: list[dict],
    user_message: str,
) -> str:
    """
    Call OpenRouter and return the assistant's reply as a plain string.

    Parameters
    ----------
    system_prompt : str
        The agent's personality / role instructions.
    history : list[dict]
        Prior messages in OpenAI format: [{"role": "user"|"assistant", "content": "..."}]
        These come from shared memory and give the agent full cross-agent context.
    user_message : str
        The current user message to respond to.

    Returns
    -------
    str
        The assistant's reply, or a friendly error string on failure.
    """
    if not _API_KEY or _API_KEY == "your_openrouter_api_key_here":
        return (
            "⚠️ OpenRouter API key is not configured. "
            "Please add OPENROUTER_API_KEY to backend/.env and restart the server."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": user_message},
    ]

    payload = {
        "model": _MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(_BASE_URL, json=payload, headers=_HEADERS)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    except httpx.HTTPStatusError as exc:
        # OpenRouter returned a 4xx / 5xx
        status = exc.response.status_code
        try:
            detail = exc.response.json().get("error", {}).get("message", str(exc))
        except Exception:
            detail = str(exc)
        return f"⚠️ OpenRouter error ({status}): {detail}"

    except httpx.TimeoutException:
        return "⚠️ The request to OpenRouter timed out. Please try again."

    except Exception as exc:  # noqa: BLE001
        return f"⚠️ Unexpected error: {exc}"
