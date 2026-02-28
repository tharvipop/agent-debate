"""Agreement detection for debate rounds."""

from __future__ import annotations

from core.openrouter import fetch_llm_response

AGREEMENT_MODEL = "openai/gpt-4o-mini"


async def is_agreement(response: str) -> bool:
    """
    Use a fast model to determine if a response is a simple agreement.
    """
    prompt = f"""You are a text classification model. Your task is to determine if the following text is a simple agreement with a previous statement.

A simple agreement is a response that does not add any new information or claims, but simply confirms that the previous response was good.

Respond with "true" if the text is a simple agreement, and "false" otherwise.

---

Text:
{response}

---

Is this a simple agreement? (true/false)
"""
    result = await fetch_llm_response(model=AGREEMENT_MODEL, prompt=prompt)
    if not result.get("ok"):
        return False

    content = result.get("content", "").strip().lower()
    return content == "true"
