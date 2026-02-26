"""Parallel execution test harness for the MVP engine."""

import asyncio
import time

from core.engine import run_initial_models


async def main():
    """Run timing test for parallel model execution."""
    prompt = "Explain quantum computing in one sentence."
    
    print(f"Testing parallel execution with prompt: '{prompt}'")
    print(f"Models: anthropic/claude-3.5-sonnet, openai/gpt-4o, google/gemini-1.5-pro")
    print("-" * 80)
    
    start_time = time.time()
    results = await run_initial_models(prompt)
    elapsed = time.time() - start_time
    
    print("\n=== RESULTS ===")
    for model, output in results.items():
        print(f"\n[{model}]")
        if output.startswith("ERROR"):
            print(f"  {output}")
        else:
            # Truncate long responses for readability
            truncated = output[:200] + "..." if len(output) > 200 else output
            print(f"  {truncated}")
    
    print(f"\n=== TIMING ===")
    print(f"Total elapsed time: {elapsed:.2f} seconds")
    print(f"Expected: ~max(individual latencies), NOT sum of all three")
    print(f"If parallel execution is working correctly, time should be close to the slowest single model.")


if __name__ == "__main__":
    asyncio.run(main())
