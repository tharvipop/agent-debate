"""Async OpenRouter client wrapper for the MVP."""

from __future__ import annotations

import os
from typing import Any

import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def fetch_llm_response(model: str, prompt: str) -> dict[str, Any]:
    """Fetch a single model response with strict timeout and structured errors."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        timeout = httpx.Timeout(30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
            response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return {"ok": True, "model": model, "content": content}

    except httpx.TimeoutException:
        return {
            "ok": False,
            "model": model,
            "type": "timeout",
            "error": "Request timed out after 30 seconds.",
        }
    except httpx.HTTPStatusError as exc:
        return {
            "ok": False,
            "model": model,
            "type": "http_error",
            "error": f"HTTP {exc.response.status_code}: {exc.response.text[:300]}",
        }
    except httpx.RequestError as exc:
        return {
            "ok": False,
            "model": model,
            "type": "request_error",
            "error": str(exc),
        }
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        return {
            "ok": False,
            "model": model,
            "type": "parse_error",
            "error": f"Malformed response payload: {exc}",
        }
