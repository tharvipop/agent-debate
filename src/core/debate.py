"""Debate layer for re-prompting models with discrepancies."""

from __future__ import annotations

import asyncio

from core.agreement import is_agreement
from core.openrouter import fetch_llm_response
from core.schemas import CriticEvaluation

# Same models as initial round
DEBATE_MODELS = [
    "google/gemini-2.5-flash-lite",
    "anthropic/claude-3-haiku",
    "openai/gpt-4o-mini",
]


async def run_debate_round(
    original_prompt: str,
    initial_responses: dict[str, str],
    critic_eval: CriticEvaluation,
) -> dict[str, str]:
    """
    Re-prompt each model with targeted feedback based on discrepancies.

    Args:
        original_prompt: The original user question
        initial_responses: Each model's initial response
        critic_eval: Critic evaluation with discrepancies

    Returns:
        Dict mapping model names to their debate round responses
    """
    # Build model-specific prompts
    tasks = []
    for model in DEBATE_MODELS:
        debate_prompt = _build_debate_prompt(
            model, original_prompt, initial_responses.get(model, ""), critic_eval
        )
        tasks.append(fetch_llm_response(model=model, prompt=debate_prompt))

    # Execute all debate round calls in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Normalize output and check for simple agreements
    output: dict[str, str] = {}
    for model, result in zip(DEBATE_MODELS, results):
        if isinstance(result, BaseException):
            output[model] = f"ERROR (exception): {result}"
            continue

        if result.get("ok"):
            content = str(result.get("content", ""))
            # If the model just agrees, use its initial response
            if await is_agreement(content):
                output[model] = initial_responses.get(model, "")
            else:
                output[model] = content
        else:
            err_type = result.get("type", "unknown")
            err_msg = result.get("error", "Unknown error")
            output[model] = f"ERROR ({err_type}): {err_msg}"

    return output


def _build_debate_prompt(
    model: str,
    original_prompt: str,
    initial_response: str,
    critic_eval: CriticEvaluation,
) -> str:
    """
    Construct a targeted debate prompt for a specific model.

    Includes the original question, their initial response, and claims they missed.
    """
    # Find claims this model missed
    missed_claims: list[str] = []
    for disc in critic_eval.discrepancies:
        if model in disc.models_missing_claim:
            missed_claims.append(disc.claim)

    if not missed_claims:
        # No missed claims - just ask them to review their answer
        return f"""Original Question: {original_prompt}

Your Initial Response:
{initial_response}

A parallel review found no significant discrepancies in your response. Please review your answer one more time and confirm or refine it if needed."""

    # Build the list of missed claims
    claims_text = "\n".join([f"- {claim}" for claim in missed_claims])

    return f"""Original Question: {original_prompt}

Your Initial Response:
{initial_response}

In a parallel review, other models mentioned the following claims/points that you did not include:
{claims_text}

Does this information change your reasoning? If so, why? Please re-evaluate your original response and provide an updated answer."""
