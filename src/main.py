"""Main orchestration script for the debate-based synthesis pipeline."""

from __future__ import annotations

import asyncio
import time

from core.critic import evaluate_differences
from core.debate import run_debate_round
from core.engine import run_initial_models
from core.synthesizer import generate_divergence_synthesis, generate_final_answer


def _truncate(text: str, max_len: int = 150) -> str:
    """Truncate text to max_len characters for clean terminal output."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _display_responses(responses: dict[str, str], title: str) -> None:
    """Display model responses with truncation."""
    print(f"=== {title} ===")
    for model, response in responses.items():
        print(f"\n{model}:")
        print(f"{_truncate(response)}\n")
    print("=" * 80 + "\n")


def _display_discrepancies(critic_eval, pass_num: int, previous_eval=None) -> None:
    """Display critic evaluation results, highlighting resolved claims."""
    print(f"[✓] Critic Pass {pass_num} completed")
    print(f"[✓] Consensus reached: {critic_eval.consensus_reached}")
    print(f"[✓] Identified {len(critic_eval.discrepancies)} discrepancies\n")

    # Show resolved claims if we have a previous evaluation
    if previous_eval and pass_num > 0:
        prev_claims = {disc.claim for disc in previous_eval.discrepancies}
        curr_claims = {disc.claim for disc in critic_eval.discrepancies}
        resolved_claims = prev_claims - curr_claims

        if resolved_claims:
            print(f"=== ✅ RESOLVED CLAIMS (Pass {pass_num}) ===")
            print(
                f"[+] {len(resolved_claims)} claim(s) now agreed upon by all models:\n"
            )
            for i, claim in enumerate(sorted(resolved_claims), 1):
                print(f"{i}. {claim}")
            print("\n")

    if critic_eval.discrepancies:
        print(f"=== DISCREPANCIES (Pass {pass_num}) ===")
        for i, disc in enumerate(critic_eval.discrepancies, 1):
            print(f"\n{i}. Claim: {disc.claim}")
            print(
                f"   Models with claim: {', '.join(disc.models_with_claim) or 'None'}"
            )
            print(
                f"   Models missing claim: {', '.join(disc.models_missing_claim) or 'None'}"
            )
        print("\n")
    else:
        print("[i] No material discrepancies found.\n")


async def run_debate_pipeline(prompt: str) -> str:
    """
    Execute the two-layer bounded debate loop with fast path and circuit breaker.

    State Machine:
    1. Initial Pass & Fast Path (Gate 0)
       - Generate initial responses and run Critic Pass 0
       - If consensus_reached -> Consensus Synthesizer -> EXIT
       - If not -> Store initial_count, proceed to Debate 1

    2. Debate Loop 1 & Circuit Breaker (Gate 1)
       - Run Debate 1, then Critic Pass 1
       - If consensus_reached -> Consensus Synthesizer -> EXIT
       - If len(discrepancies) >= initial_count -> Divergence Synthesizer -> EXIT
       - If 0 < len(discrepancies) < initial_count -> Proceed to Debate 2

    3. Debate Loop 2 - Final Attempt (Gate 2)
       - Run Debate 2, then Critic Pass 2
       - If consensus_reached -> Consensus Synthesizer -> EXIT
       - If not -> Divergence Synthesizer -> EXIT

    Args:
        prompt: The user's original question

    Returns:
        The final synthesized answer
    """
    start_time = time.time()

    # Initialize logger for this run
    from core.logger import DebateLogger

    logger = DebateLogger(prompt)

    # ========== Step 1: Initial Responses ==========
    print("[+] Fetching initial responses from 3 models...")
    initial_responses = await run_initial_models(prompt)
    logger.log_initial_responses(initial_responses)
    print(f"[✓] Initial responses received in {time.time() - start_time:.2f}s\n")
    _display_responses(initial_responses, "INITIAL RESPONSES")

    # ========== Step 2: Critic Pass 0 ==========
    print("[+] Critic Pass 0: Analyzing initial responses...")
    critic_eval_0 = await evaluate_differences(initial_responses)
    logger.log_critic_pass(0, critic_eval_0)
    _display_discrepancies(critic_eval_0, 0)

    # ========== Gate 0: Fast Path Check ==========
    if critic_eval_0.consensus_reached:
        logger.log_gate_decision(
            0, "fast_path_consensus", "Consensus reached at Pass 0, skipping debates"
        )
        print("[🚀 FAST PATH] Consensus reached at Pass 0. Skipping debates.\n")
        print("[+] Synthesizing final answer (consensus mode)...")
        final_answer = await generate_final_answer(prompt, initial_responses)
        logger.log_final_synthesis("consensus", final_answer)
        log_file = logger.save()
        print(f"[✓] Log saved to: {log_file}")
        print(f"[✓] Total pipeline time: {time.time() - start_time:.2f}s\n")
        return final_answer

    # Gate 0: No consensus - proceed to Debate Loop 1
    initial_count = len(critic_eval_0.discrepancies)
    logger.log_gate_decision(
        0,
        "proceed_to_debate_1",
        f"No consensus, {initial_count} discrepancies detected",
    )
    print(
        f"[→] No consensus. Proceeding to Debate Loop 1 (baseline: {initial_count} discrepancies)\n"
    )

    # ========== Step 3: Debate Round 1 ==========
    print("[+] Running Debate Round 1 with targeted re-prompts...")
    debate_responses_1 = await run_debate_round(
        prompt, initial_responses, critic_eval_0
    )
    logger.log_debate_round(1, debate_responses_1)
    print("[✓] Debate Round 1 completed\n")
    _display_responses(debate_responses_1, "DEBATE ROUND 1 RESPONSES")

    # ========== Step 4: Critic Pass 1 ==========
    print("[+] Critic Pass 1: Re-evaluating after Debate 1...")
    critic_eval_1 = await evaluate_differences(
        debate_responses_1, previous_eval=critic_eval_0
    )
    logger.log_critic_pass(1, critic_eval_1, previous_eval=critic_eval_0)
    _display_discrepancies(critic_eval_1, 1, previous_eval=critic_eval_0)

    # ========== Gate 1: Check Consensus or Circuit Breaker ==========
    if critic_eval_1.consensus_reached:
        logger.log_gate_decision(
            1, "consensus_after_debate_1", "Models converged after Debate 1"
        )
        print("[✅ CONSENSUS] Models converged after Debate 1.\n")
        print("[+] Synthesizing final answer (consensus mode)...")
        final_answer = await generate_final_answer(prompt, debate_responses_1)
        logger.log_final_synthesis("consensus", final_answer)
        log_file = logger.save()
        print(f"[✓] Log saved to: {log_file}")
        print(f"[✓] Total pipeline time: {time.time() - start_time:.2f}s\n")
        return final_answer

    current_count = len(critic_eval_1.discrepancies)
    if current_count >= initial_count:
        logger.log_gate_decision(
            1,
            "circuit_breaker_triggered",
            f"Discrepancies did not decrease ({current_count} >= {initial_count})",
        )
        print(
            f"[🔴 CIRCUIT BREAKER] Discrepancies did not decrease ({current_count} >= {initial_count})."
        )
        print("[!] Models are diverging or digging in. Terminating debate.\n")
        print("[+] Synthesizing final answer (divergence mode)...")
        final_answer = await generate_divergence_synthesis(
            prompt, debate_responses_1, critic_eval_1
        )
        logger.log_final_synthesis("divergence", final_answer)
        log_file = logger.save()
        print(f"[✓] Log saved to: {log_file}")
        print(f"[✓] Total pipeline time: {time.time() - start_time:.2f}s\n")
        return final_answer

    # Gate 1: Progress made - proceed to Debate Loop 2
    logger.log_gate_decision(
        1,
        "proceed_to_debate_2",
        f"Progress detected: {current_count} < {initial_count} discrepancies",
    )
    print(
        f"[→] Progress detected ({current_count} < {initial_count}). Proceeding to Debate Loop 2.\n"
    )

    # ========== Step 5: Debate Round 2 ==========
    print("[+] Running Debate Round 2 (Final Attempt)...")
    debate_responses_2 = await run_debate_round(
        prompt, debate_responses_1, critic_eval_1
    )
    logger.log_debate_round(2, debate_responses_2)
    print("[✓] Debate Round 2 completed\n")
    _display_responses(debate_responses_2, "DEBATE ROUND 2 RESPONSES")

    # ========== Step 6: Critic Pass 2 ==========
    print("[+] Critic Pass 2: Final evaluation...")
    critic_eval_2 = await evaluate_differences(
        debate_responses_2, previous_eval=critic_eval_1
    )
    logger.log_critic_pass(2, critic_eval_2, previous_eval=critic_eval_1)
    _display_discrepancies(critic_eval_2, 2, previous_eval=critic_eval_1)

    # ========== Gate 2: Terminal Decision ==========
    if critic_eval_2.consensus_reached:
        logger.log_gate_decision(
            2, "consensus_after_debate_2", "Models converged after Debate 2"
        )
        print("[✅ CONSENSUS] Models converged after Debate 2.\n")
        print("[+] Synthesizing final answer (consensus mode)...")
        final_answer = await generate_final_answer(prompt, debate_responses_2)
        logger.log_final_synthesis("consensus", final_answer)
    else:
        logger.log_gate_decision(
            2,
            "final_divergence",
            "Models could not reach consensus after 2 debate rounds",
        )
        print(
            "[🔴 DIVERGENCE] Models could not reach consensus after 2 debate rounds.\n"
        )
        print("[+] Synthesizing final answer (divergence mode)...")
        final_answer = await generate_divergence_synthesis(
            prompt, debate_responses_2, critic_eval_2
        )
        logger.log_final_synthesis("divergence", final_answer)

    log_file = logger.save()
    print(f"[✓] Log saved to: {log_file}")
    print(f"[✓] Total pipeline time: {time.time() - start_time:.2f}s\n")
    return final_answer


async def main():
    """Entry point for the debate pipeline."""
    # Example prompt
    prompt = "Considering I have hypothyroidism, what are the best dietary choices I can make to manage my condition effectively?"

    print("=" * 80)
    print("DEBATE-BASED SYNTHESIS PIPELINE")
    print("=" * 80)
    print(f"\nPrompt: {prompt}\n")
    print("=" * 80 + "\n")

    final_answer = await run_debate_pipeline(prompt)

    # Display final result
    print("=" * 80)
    print("FINAL SYNTHESIZED ANSWER")
    print("=" * 80)
    print(f"\n{final_answer}\n")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
