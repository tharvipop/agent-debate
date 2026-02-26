"""Async orchestration engine for parallel model execution."""

from __future__ import annotations

import asyncio

from core.openrouter import fetch_llm_response

INITIAL_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4o",
    "google/gemini-2.5-flash-lite",
]


async def run_initial_models(prompt: str) -> dict[str, str]:
    """Run the initial model set concurrently and normalize output strings."""
    results = await asyncio.gather(
        *(fetch_llm_response(model=model, prompt=prompt) for model in INITIAL_MODELS),
        return_exceptions=True,
    )

    output: dict[str, str] = {}
    for model, result in zip(INITIAL_MODELS, results):
        if isinstance(result, BaseException):
            output[model] = f"ERROR (exception): {result}"
            continue

        if result.get("ok"):
            output[model] = str(result.get("content", ""))
        else:
            err_type = result.get("type", "unknown")
            err_msg = result.get("error", "Unknown error")
            output[model] = f"ERROR ({err_type}): {err_msg}"

    return output
