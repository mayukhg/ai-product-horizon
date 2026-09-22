# LLM Setup Guide

HorizonAI uses a **hybrid model stack** approved for the CyberRisk Resident pilot.

## Model tiers

| Tier | Model | Provider | Used for |
|---|---|---|---|
| **Smart Intern** | Llama 3.3 70B | Local Ollama/vLLM | CVE triage, RAG retrieval (Slices 1–2) |
| **PhD Reasoner** | Claude Sonnet 4 | OpenRouter | Exploit synthesis (Slice 3) |
| **Guardrails** | Llama Guard 3 8B | Local Ollama | Adversarial injection blocking (Slice 4) |
| **Embeddings** | nomic-embed-text | Local Ollama | Asset/CVE retrieval (`vector(384)`) |
| **Judge** | Claude Sonnet 4 | OpenRouter | Cross-family groundedness scoring |

## When do you need the OpenRouter API key?

| Scenario | OpenRouter key needed? |
|---|---|
| Default dev (`LLM_MODE=mock`) | **No** — deterministic mock responses |
| Local Smart Intern + guardrails only | **No** |
| Live PhD Reasoner (attack-chain synthesis) | **Yes** |
| Live cross-family judge evals | **Yes** |
| Full golden-dataset eval (`POST /api/v1/evals/run`) | **Yes** (15+ judge cases call OpenRouter) |

**Provide `OPENROUTER_API_KEY` in `backend/.env` when you set `LLM_MODE=live` and want PhD-tier or judge calls.**

OpenRouter is for **LLM inference only**. It does **not** authenticate users to the HorizonAI API.

## Quick start

### 1. Mock mode (no keys — works out of the box)

```bash
# backend/.env
LLM_MODE=mock
```

Run evals against mock responses:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/evals/run -H 'Content-Type: application/json' -d '{"limit": 5}'
```

### 2. Live local tier (Smart Intern + guardrails)

Install [Ollama](https://ollama.com) and pull models:

```bash
ollama pull llama3.3:70b
ollama pull llama-guard3:8b
ollama pull nomic-embed-text
```

```bash
# backend/.env
LLM_MODE=live
SMART_INTERN_BASE_URL=http://127.0.0.1:11434/v1
GUARDRAIL_BASE_URL=http://127.0.0.1:11434/v1
EMBEDDING_BASE_URL=http://127.0.0.1:11434/v1
```

### 3. Full hybrid (local + OpenRouter)

Add your OpenRouter key:

```bash
# backend/.env
LLM_MODE=live
OPENROUTER_API_KEY=sk-or-v1-...
PHD_REASONER_MODEL=anthropic/claude-sonnet-4
JUDGE_MODEL=anthropic/claude-sonnet-4
```

Get a key at [openrouter.ai/keys](https://openrouter.ai/keys).

## API authentication (separate from OpenRouter)

```bash
# backend/.env
AUTH_JWT_SECRET=<generate-a-64-char-random-secret>
AUTH_REQUIRED=false   # set true to require JWT on protected routes
```

Mint a dev token:

```bash
cd backend
AUTH_JWT_SECRET=your-secret .venv/bin/python scripts/mint_dev_token.py operator
```

Use it on protected routes:

```bash
curl -H "Authorization: Bearer <token>" -X POST http://127.0.0.1:8000/api/v1/evals/run
```

## Release gates

| Metric | Block | Warn |
|---|---|---|
| Mean groundedness | < 90% | < 92% |
| Pass rate | < 93% | < 95% |
| Adversarial Slice 4 | any failure | — |

Configured via `EVAL_GROUNDEDNESS_BLOCK_THRESHOLD` and related env vars in `backend/.env.example`.
