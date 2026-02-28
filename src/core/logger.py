"""JSON logging system for debate pipeline execution."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.schemas import CriticEvaluation


class DebateLogger:
    """
    Structured JSON logger for debate pipeline runs.

    Each run creates a dedicated folder with separate files:
    - flow.json: Logic flow, gates, critic evaluations (no full responses)
    - initial_responses.json: Initial model responses
    - debate_round_1.json: Debate 1 responses (if applicable)
    - debate_round_2.json: Debate 2 responses (if applicable)
    - final_synthesis.json: Final synthesized answer
    """

    def __init__(self, prompt: str, log_dir: str = "logs"):
        """
        Initialize a new debate logger.

        Args:
            prompt: The original user question
            log_dir: Base directory to store log folders (relative to src/)
        """
        self.start_time = datetime.now()
        self.base_log_dir = Path(__file__).parent.parent / log_dir

        # Create timestamped folder: run_2026-02-27_18-40-17/
        timestamp_str = self.start_time.strftime("%Y-%m-%d_%H-%M-%S")
        self.run_dir = self.base_log_dir / f"run_{timestamp_str}"
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Build the flow structure (no full responses)
        self.flow_data = {
            "metadata": {
                "timestamp_start": self.start_time.isoformat(),
                "timestamp_end": None,
                "total_time_seconds": None,
                "prompt": prompt,
            },
            "critic_pass_0": {},
            "gate_0_decision": {},
            "critic_pass_1": {},
            "gate_1_decision": {},
            "critic_pass_2": {},
            "gate_2_decision": {},
            "final_synthesis": {},
        }

        # Track responses separately
        self.initial_responses = {}
        self.debate_round_1_responses = {}
        self.debate_round_2_responses = {}
        self.final_synthesis_data = {}

    def log_initial_responses(self, responses: dict[str, str]) -> None:
        """Log initial model responses (stored separately)."""
        self.initial_responses = responses

    def log_critic_pass(
        self,
        pass_num: int,
        evaluation: CriticEvaluation,
        previous_eval: CriticEvaluation | None = None,
    ) -> None:
        """
        Log critic evaluation results in the flow.

        Args:
            pass_num: Critic pass number (0, 1, or 2)
            evaluation: Current critic evaluation
            previous_eval: Previous evaluation for resolved claims tracking
        """
        key = f"critic_pass_{pass_num}"

        # Build discrepancies list
        discrepancies_list = []
        for disc in evaluation.discrepancies:
            d = {
                "claim": disc.claim,
                "models_with_claim": disc.models_with_claim,
                "models_missing_claim": disc.models_missing_claim,
            }
            if disc.confidence is not None:
                d["confidence"] = disc.confidence
            discrepancies_list.append(d)

        # Calculate resolved claims
        resolved_claims = []
        if previous_eval and pass_num > 0:
            prev_claims = {disc.claim for disc in previous_eval.discrepancies}
            curr_claims = {disc.claim for disc in evaluation.discrepancies}
            resolved_claims = sorted(list(prev_claims - curr_claims))

        self.flow_data[key] = {
            "consensus_reached": evaluation.consensus_reached,
            "discrepancies_count": len(evaluation.discrepancies),
            "discrepancies": discrepancies_list,
        }

        if resolved_claims:
            self.flow_data[key]["resolved_claims"] = resolved_claims

    def log_gate_decision(self, gate_num: int, route: str, reason: str) -> None:
        """
        Log gate routing decision.

        Args:
            gate_num: Gate number (0, 1, or 2)
            route: Routing decision (e.g., "fast_path", "proceed_to_debate_2")
            reason: Human-readable explanation of the decision
        """
        key = f"gate_{gate_num}_decision"
        self.flow_data[key] = {"route": route, "reason": reason}

    def log_debate_round(self, round_num: int, responses: dict[str, str]) -> None:
        """
        Log debate round responses (stored separately).

        Args:
            round_num: Debate round number (1 or 2)
            responses: Model responses (full text)
        """
        if round_num == 1:
            self.debate_round_1_responses = responses
        elif round_num == 2:
            self.debate_round_2_responses = responses

    def log_final_synthesis(self, mode: str, answer: str) -> None:
        """
        Log final synthesis result.

        Args:
            mode: Synthesis mode ("consensus" or "divergence")
            answer: The final synthesized answer
        """
        self.final_synthesis_data = {"mode": mode, "answer": answer}

        # Also add to flow.json for quick reference
        self.flow_data["final_synthesis"] = {"mode": mode, "answer": answer}

    def save(self) -> Path:
        """
        Save all log data to the run folder as separate JSON files.

        Returns:
            Path to the run folder
        """
        # Calculate total time
        end_time = datetime.now()
        total_seconds = (end_time - self.start_time).total_seconds()

        self.flow_data["metadata"]["timestamp_end"] = end_time.isoformat()
        self.flow_data["metadata"]["total_time_seconds"] = round(total_seconds, 2)

        # Save flow.json (main logic without full responses)
        flow_file = self.run_dir / "flow.json"
        with open(flow_file, "w") as f:
            json.dump(self.flow_data, f, indent=2, ensure_ascii=False)

        # Save initial_responses.json
        if self.initial_responses:
            with open(self.run_dir / "initial_responses.json", "w") as f:
                json.dump(self.initial_responses, f, indent=2, ensure_ascii=False)

        # Save debate_round_1.json
        if self.debate_round_1_responses:
            with open(self.run_dir / "debate_round_1.json", "w") as f:
                json.dump(
                    self.debate_round_1_responses, f, indent=2, ensure_ascii=False
                )

        # Save debate_round_2.json (only if it exists)
        if self.debate_round_2_responses:
            with open(self.run_dir / "debate_round_2.json", "w") as f:
                json.dump(
                    self.debate_round_2_responses, f, indent=2, ensure_ascii=False
                )

        # Save final_synthesis.json
        if self.final_synthesis_data:
            with open(self.run_dir / "final_synthesis.json", "w") as f:
                json.dump(self.final_synthesis_data, f, indent=2, ensure_ascii=False)

        return self.run_dir
