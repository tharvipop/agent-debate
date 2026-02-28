"""Pydantic models for structured Critic output."""

from __future__ import annotations

from pydantic import BaseModel


class Discrepancy(BaseModel):
    """A single discrepancy identified by the Critic."""

    claim_id: str | None = None
    claim: str
    models_with_claim: list[str]
    models_missing_claim: list[str]
    confidence: float | None = None


class ModelDiscrepancies(BaseModel):
    """Collection of all discrepancies identified across model responses."""

    discrepancies: list[Discrepancy]


class CriticEvaluation(BaseModel):
    """
    Complete critic evaluation including consensus determination.
    Used for state machine routing in the debate loop.
    """

    consensus_reached: bool
    discrepancies: list[Discrepancy]
