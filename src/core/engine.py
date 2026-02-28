"""Async orchestration engine for parallel model execution."""

from __future__ import annotations

import asyncio

from core.openrouter import fetch_llm_response

INITIAL_MODELS = [
    "google/gemini-2.5-flash-lite",
    "anthropic/claude-3-haiku",
    "openai/gpt-4o-mini",
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


async def summarize_responses(responses: dict[str, str]) -> str:
    """Use Claude Haiku to summarize all 3 model responses into one coherent summary."""
    # Build a prompt that includes all responses
    combined_text = "\n\n".join(
        [f"**{model}**:\n{content}" for model, content in responses.items()]
    )

    summary_prompt = f"""You are a summarizer. Below are responses from 3 different AI models to the same question. 
Please synthesize these responses into a single, coherent summary that captures the key insights from all three.

{combined_text}

Provide a clear, concise summary:"""

    result = await fetch_llm_response(
        model="anthropic/claude-3-haiku", prompt=summary_prompt
    )

    if result.get("ok"):
        return str(result.get("content", "Unable to generate summary."))
    else:
        err_type = result.get("type", "unknown")
        err_msg = result.get("error", "Unknown error")
        return f"ERROR ({err_type}): {err_msg}"
