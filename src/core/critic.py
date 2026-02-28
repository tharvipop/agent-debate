"""Critic layer for identifying discrepancies across model responses."""

from __future__ import annotations

import json
import re

from core.openrouter import fetch_llm_response
from core.schemas import CriticEvaluation

CRITIC_MODEL = "deepseek/deepseek-v3.2"


def _generate_claim_id(claim_text: str, max_len: int = 40) -> str:
    """Generate a stable, lowercase, hyphenated ID from the claim text."""
    # Remove punctuation and extra whitespace
    s = re.sub(r"[^\w\s-]", "", claim_text.lower())
    s = re.sub(r"\s+", "-", s)
    # Truncate and remove trailing hyphen
    return s[:max_len].strip("-")


async def evaluate_differences(
    responses: dict[str, str], previous_eval: CriticEvaluation | None = None
) -> CriticEvaluation:
    """
    Use a fast critic model to identify discrepancies across responses.

    Args:
        responses: Dict mapping model names to their response content
        previous_eval: Optional previous critic evaluation for claim consistency tracking

    Returns:
        CriticEvaluation object with consensus determination and structured discrepancy data
    """
    # Build the critic prompt with all responses
    responses_text = "\n\n".join(
        [f"**{model}**:\n{content}" for model, content in responses.items()]
    )

    model_names = list(responses.keys())

    # Base prompt
    critic_prompt = f"""You are an expert Technical Auditor and the core decision engine for a multi-agent AI system.
Your job is to analyze the responses of three different AI models to a specific User Prompt and determine if they have reached a functional consensus.

Your primary goal is to identify MATERIAL and FACTUAL discrepancies.

### What CONSTITUTES a Discrepancy:
* Direct contradictions in facts, math, or logic (e.g., Model A says X is True, Model B says X is False).
* Conflicting code implementations that would result in different programmatic behavior or bugs.
* A critical omission by one model that compromises the safety, accuracy, or functionality of the answer.

### What DOES NOT Constitute a Discrepancy (IGNORE THESE):
* Stylistic differences, tone, or verbosity.
* Different formatting (e.g., Markdown tables vs. bulleted lists).
* Variable naming conventions or functionally identical code structures (e.g., using a `for` loop vs. a `while` loop).
* Additive information (e.g., Model A gives the correct answer, but Model B includes a harmless "bonus tip"). This is a synthesis feature, not a discrepancy.

---

Below are responses from {len(model_names)} different models:

{responses_text}

Model names available: {model_names}
"""

    # Add previous discrepancies context for claim consistency
    if previous_eval and previous_eval.discrepancies:
        prev_disc_list = []
        for disc in previous_eval.discrepancies:
            # Ensure claim_id is generated if it's missing from a previous run
            claim_id = disc.claim_id or _generate_claim_id(disc.claim)
            prev_disc_list.append(
                f'  - claim_id: "{claim_id}"\n    claim: "{disc.claim}"'
            )
        prev_disc_text = "\n".join(prev_disc_list)

        critic_prompt += f"""

---

### IMPORTANT: Previous Discrepancies Reference

In the PREVIOUS evaluation pass, these discrepancies were identified. Your task is to determine if they still exist.

{prev_disc_text}

### Instructions for This Pass:
1.  **Analyze Previous Claims**: For each `claim_id` above, check if the discrepancy still exists in the new responses. You should look for the *semantic meaning* of the claim, not just an exact textual match. If the core idea of the claim is present, consider it a match.
2.  **Preserve Existing Claims**: If a discrepancy persists, you MUST use the exact `claim_id` and `claim` text from the reference above in your JSON output.
3.  **Identify New Claims**: If you find a completely new discrepancy not listed above, you may add it to the `discrepancies` list. For new claims, you do not need to add a `claim_id`.
4.  **Consensus**: If all previous discrepancies are resolved and no new ones are found, set `consensus_reached` to `true`.
5.  **Confidence Score**: For each discrepancy you identify (both new and existing), provide a `confidence` score (0.0 to 1.0, in increments of 0.1) indicating your certainty that it is a genuine, material discrepancy.
6.  **Note on Agreements**: If a model's response is a simple agreement with its previous response (e.g., "I stand by my previous answer"), its original claims are carried over. You will be evaluating its original response in that case.

### Output Schema
Your output MUST be a single, raw JSON object matching this schema.

```json
{{
  "consensus_reached": true or false,
  "discrepancies": [
    {{
      "claim_id": "optional-existing-id-from-reference",
      "claim": "The specific fact/logic in question. MUST match reference if `claim_id` is used.",
      "models_with_claim": ["model1", "model2"],
      "models_missing_claim": ["model3"],
      "confidence": 0.9
    }}
  ]
}}
```
"""
    else:
        # Prompt for the first pass (no previous discrepancies)
        critic_prompt += """

---

### Instructions for This Pass:
1.  **Identify All Discrepancies**: Analyze the responses and identify all material, factual discrepancies. A discrepancy exists when at least one model makes a claim that another model omits or contradicts.
2.  **Consensus**: If there are no discrepancies, set `consensus_reached` to `true`.
3.  **Output Schema**: Your output MUST be a single, raw JSON object matching this schema. Do not add a `claim_id` on this first pass.
4.  **Critical Rule**: The `models_missing_claim` array for any given discrepancy CANNOT be empty. If all models agree on a claim, it is NOT a discrepancy.

```json
{
  "consensus_reached": true or false,
  "discrepancies": [
    {
      "claim": "The specific fact/logic in question",
      "models_with_claim": ["model1", "model2"],
      "models_missing_claim": ["model3"]
    }
  ]
}
```
"""

    # Fetch critic's analysis
    result = await fetch_llm_response(model=CRITIC_MODEL, prompt=critic_prompt)

    if not result.get("ok"):
        # If critic fails, return consensus with empty discrepancies
        print(f"[!] Critic failed: {result.get('error', 'Unknown error')}")
        return CriticEvaluation(consensus_reached=True, discrepancies=[])

    raw_output = result.get("content", "")

    try:
        # Strip markdown code fences if present
        cleaned_output = _strip_markdown_fences(raw_output)

        # Parse using Pydantic
        evaluation = CriticEvaluation.model_validate_json(cleaned_output)

        # Filter out invalid discrepancies where all models agree
        valid_discrepancies = [
            d for d in evaluation.discrepancies if d.models_missing_claim
        ]
        evaluation.discrepancies = valid_discrepancies

        # Enforce consensus logic: if no discrepancies, must be consensus
        if not evaluation.discrepancies:
            evaluation.consensus_reached = True
        else:
            # Generate claim_id for any new discrepancies
            for disc in evaluation.discrepancies:
                if not disc.claim_id:
                    disc.claim_id = _generate_claim_id(disc.claim)

        return evaluation

    except (json.JSONDecodeError, ValueError) as e:
        print(f"[!] Failed to parse Critic output: {e}")
        print(f"[!] Raw output (first 500 chars): {raw_output[:500]}")
        # Return consensus with empty discrepancies on parse failure
        return CriticEvaluation(consensus_reached=True, discrepancies=[])


def _strip_markdown_fences(text: str) -> str:
    """
    Remove markdown code fences from LLM output.
    Handles patterns like ```json ... ``` or ``` ... ```
    """
    # Remove opening fence (```json or ```)
    text = re.sub(r"^```(?:json)?\s*\n?", "", text, flags=re.MULTILINE)
    # Remove closing fence
    text = re.sub(r"\n?```\s*$", "", text, flags=re.MULTILINE)
    return text.strip()
