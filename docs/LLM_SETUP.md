# LLM Setup Guide

HorizonAI routes **all model tiers through OpenRouter** using a single API key.

## Model tiers

| Tier | OpenRouter model ID | Used for |
|---|---|---|
| **Smart Intern** | `meta-llama/llama-3.3-70b-instruct` | CVE triage, RAG retrieval (Slices 1–2) |
| **PhD Reasoner** | `anthropic/claude-sonnet-4` | Exploit synthesis (Slice 3) |
| **Guardrails** | `meta-llama/llama-guard-3-8b` | Adversarial injection blocking (Slice 4) |
| **Embeddings** | `openai/text-embedding-3-small` | Asset/CVE retrieval (`vector(1536)`) |
| **Judge** | `anthropic/claude-sonnet-4` | Cross-family groundedness scoring |

## When do you need the OpenRouter API key?

| Scenario | OpenRouter key needed? |
|---|---|
| Default dev (`LLM_MODE=mock`) | **No** — deterministic mock responses |
| Any live inference (`LLM_MODE=live`) | **Yes** — all tiers use OpenRouter |

**Provide `OPENROUTER_API_KEY` in `backend/.env` when you set `LLM_MODE=live`.**

Get a key at [openrouter.ai/keys](https://openrouter.ai/keys).

OpenRouter is for **LLM inference only**. It does **not** authenticate users to the HorizonAI API.

## Quick start

### 1. Mock mode (no key — works out of the box)

```bash
# backend/.env
LLM_MODE=mock
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/evals/run -H 'Content-Type: application/json' -d '{"limit": 5}'
```

### 2. Live mode (OpenRouter)

```bash
# backend/.env
LLM_MODE=live
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Optional overrides (defaults shown)
SMART_INTERN_MODEL=meta-llama/llama-3.3-70b-instruct
GUARDRAIL_MODEL=meta-llama/llama-guard-3-8b
EMBEDDING_MODEL=openai/text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
PHD_REASONER_MODEL=anthropic/claude-sonnet-4
JUDGE_MODEL=anthropic/claude-sonnet-4
```

Restart the API after changing `.env`:

```bash
./stop.sh && ./start.sh
```

Test a live eval:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/evals/run -H 'Content-Type: application/json' -d '{"limit": 3}'
```

## API authentication (separate from OpenRouter)

```bash
AUTH_JWT_SECRET=<generate-a-64-char-random-secret>
AUTH_REQUIRED=false   # set true to require JWT on protected routes
```

Mint a dev token:

```bash
cd backend
AUTH_JWT_SECRET=your-secret .venv/bin/python scripts/mint_dev_token.py operator
```

## Release gates

| Metric | Block | Warn |
|---|---|---|
| Mean groundedness | < 90% | < 92% |
| Pass rate | < 93% | < 95% |
| Adversarial Slice 4 | any failure | — |

Configured via `EVAL_GROUNDEDNESS_BLOCK_THRESHOLD` and related env vars in `backend/.env.example`.
