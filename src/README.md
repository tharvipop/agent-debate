# Debate-Based Synthesis Pipeline

Single-layer debate architecture for multi-model consensus using standard `asyncio`.

## Architecture

### Pipeline Flow
```
1. Initial Responses (Parallel)
   ├─ google/gemini-2.5-flash-lite
   ├─ anthropic/claude-3-haiku
   └─ openai/gpt-4o-mini

2. Critic Analysis
   └─ openai/gpt-4o-mini (structured JSON via Pydantic)

3. Debate Round (Parallel)
   ├─ Targeted re-prompts with missed claims
   └─ Models re-evaluate their positions

4. Synthesis
   └─ openai/gpt-4o (gold standard answer)
```

## Core Components

### `core/schemas.py`
Pydantic models for structured Critic output:
- `Discrepancy`: Single discrepancy with claim and model attribution
- `ModelDiscrepancies`: Collection of all identified discrepancies

### `core/critic.py`
Fast LLM-based critic that:
- Analyzes initial responses for discrepancies
- Outputs strict JSON matching Pydantic schema
- Strips markdown code fences from LLM output
- Handles parsing errors gracefully

### `core/debate.py`
Orchestrates the debate round:
- Constructs model-specific prompts with missed claims
- Uses `asyncio.gather()` for parallel execution
- Handles timeouts and errors via existing `openrouter.py` wrapper

### `core/synthesizer.py`
Final synthesis layer:
- Uses GPT-4o for strong reasoning
- **Only processes post-debate responses** (not initial responses)
- Creates the authoritative "gold standard" answer

### `core/openrouter.py`
Async OpenRouter API wrapper (from MVP):
- 30-second timeouts
- Structured error handling
- Uses `httpx` for async HTTP

### `core/engine.py`
Initial parallel model execution (from MVP)

## Running the Pipeline

```bash
cd /Users/atharvakulkarni/agent-debate/src
conda activate agent-debate
python main.py
```

## Key Technical Decisions

1. **Async First**: All API calls use `asyncio` - no blocking IO
2. **Strict Timeouts**: 30-second timeout per API call (prevents hangs)
3. **Structured Output**: Pydantic validates Critic JSON (fail fast on bad parsing)
4. **Separation of Concerns**: Each layer has a single responsibility
5. **Error Resilience**: Graceful degradation on API failures
6. **Terminal Output**: Clean progress indicators with timing information

## Environment Setup

Ensure `.env` contains:
```
OPENROUTER_API_KEY=your_key_here
```

Dependencies (see `requirements.txt`):
- httpx (async HTTP)
- pydantic (structured data)
- python-dotenv (environment variables)

## Example Output

```
[+] Fetching initial responses from 3 models...
[✓] Initial responses received in 1.28s

[+] Critic analyzing discrepancies...
[✓] Critic completed in 3.93s
[✓] Identified 3 discrepancies

[+] Running debate round with targeted re-prompts...
[✓] Debate round completed in 3.49s

[+] Synthesizing final answer using GPT-4o...
[✓] Synthesis completed in 1.14s

[✓] Total pipeline time: 9.84s
```
