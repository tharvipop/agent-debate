"""Synthesizer layer for generating the final gold standard answer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.openrouter import fetch_llm_response

if TYPE_CHECKING:
    from core.schemas import CriticEvaluation

SYNTHESIZER_MODEL = "deepseek/deepseek-v3.2"


async def generate_final_answer(
    original_prompt: str, debate_responses: dict[str, str]
) -> str:
    """
    Use a strong model to synthesize the final answer from debate responses.

    IMPORTANT: Only uses post-debate responses (after models have reviewed discrepancies).
    Initial responses are NOT included in synthesis.

    Args:
        original_prompt: The original user question
        debate_responses: Each model's response AFTER the debate round

    Returns:
        The synthesized "gold standard" answer
    """
    # Build combined text from debate responses ONLY (not initial responses)
    responses_text = "\n\n".join(
        [f"**{model}**:\n{content}" for model, content in debate_responses.items()]
    )

    synthesis_prompt = f"""You are an expert synthesizer tasked with creating the definitive "gold standard" answer to a question.

Original Question:
{original_prompt}

Below are responses from multiple AI models AFTER they completed a debate round where they:
1. Provided initial answers
2. Reviewed discrepancies identified by a critic
3. Re-evaluated their positions based on what other models mentioned

These are their FINAL refined responses:

{responses_text}

Your task:
1. Analyze all the post-debate responses carefully
2. Identify the most accurate, complete, and well-reasoned points
3. Synthesize these insights into a single, authoritative answer
4. Ensure your answer is clear, concise, and comprehensive

Provide the final synthesized answer:"""

    result = await fetch_llm_response(model=SYNTHESIZER_MODEL, prompt=synthesis_prompt)

    if result.get("ok"):
        return str(result.get("content", "Unable to generate final answer."))
    else:
        err_type = result.get("type", "unknown")
        err_msg = result.get("error", "Unknown error")
        return f"ERROR ({err_type}): {err_msg}"


async def generate_divergence_synthesis(
    original_prompt: str,
    debate_responses: dict[str, str],
    critic_eval: "CriticEvaluation",
) -> str:
    """
    Generate a synthesis when models could not reach consensus.

    This synthesis acknowledges the divergence, explains the trade-offs,
    and presents the differing approaches transparently.

    Args:
        original_prompt: The original user question
        debate_responses: Each model's final response after debate rounds
        critic_eval: The final critic evaluation showing remaining discrepancies

    Returns:
        A synthesized answer that highlights trade-offs and divergent viewpoints
    """
    # Build combined text from debate responses
    responses_text = "\n\n".join(
        [f"**{model}**:\n{content}" for model, content in debate_responses.items()]
    )

    # Format the discrepancies for the synthesizer
    discrepancies_text = "\n".join(
        [
            f"- {disc.claim}\n  (Models with: {', '.join(disc.models_with_claim)}; Models without: {', '.join(disc.models_missing_claim)})"
            for disc in critic_eval.discrepancies
        ]
    )

    synthesis_prompt = f"""You are an expert synthesizer tasked with creating a transparent, balanced answer when AI models could NOT reach consensus.

Original Question:
{original_prompt}

The models went through multiple debate rounds but still have material disagreements:

REMAINING DISCREPANCIES:
{discrepancies_text}

FINAL MODEL RESPONSES:
{responses_text}

Your task:
1. Acknowledge that the models diverged on specific material points
2. Clearly explain the TRADE-OFFS and different approaches taken by the models
3. If possible, explain WHY the models might legitimately disagree (e.g., different optimization priorities, different interpretations of requirements)
4. Provide a balanced synthesis that helps the user understand the different perspectives
5. If one approach is clearly superior, say so - but if both are valid, present them neutrally

DO NOT force a false consensus. Transparency about disagreement is valuable.

Provide the divergence-aware synthesized answer:"""

    result = await fetch_llm_response(model=SYNTHESIZER_MODEL, prompt=synthesis_prompt)

    if result.get("ok"):
        return str(result.get("content", "Unable to generate divergence synthesis."))
    else:
        err_type = result.get("type", "unknown")
        err_msg = result.get("error", "Unknown error")
        return f"ERROR ({err_type}): {err_msg}"
