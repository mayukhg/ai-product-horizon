# HorizonAI

> **Enterprise AI Product Lifecycle & Cyber Exposure Intelligence Platform for Qualys ETM (Enterprise TruRisk Management).**

---

## Problem Statement

Enterprise security teams using Qualys Enterprise TruRisk Management (ETM) face an overwhelming volume of vulnerability scan data, evolving CVE exploits, and strict compliance demands. Manually triaging thousands of assets leads to high **Mean Time to Remediate (MTTR)** and unmitigated attack surface exposure.

At the same time, product managers attempting to build AI companions or automated remediation bots encounter systemic failure modes:
1. **The "Vibe-Based" Testing Trap**: AI outputs are non-deterministic and stochastic. Relying on manual QA leads to unexpected hallucinations, off-tone responses, and unmitigated risk.
2. **The 95% Prototype Failure Rate**: AI prototypes fail to scale due to **Data Drift**, **Cost Blow-up**, **Engineering Limitations**, **Missing Safety Guardrails**, and **Collaboration Breakdown**.
3. **The "Cost Cliff"**: Relying solely on expensive frontier models creates a **10x to 25x cost penalty per query** at production scale.
4. **Silent Quality Drift**: Once deployed, LLM performance quietly degrades over time without continuous live observability.

---

## Vision

**AI product delivery as an exact, measurable, and reliable engineering discipline.** HorizonAI bridges the gap between raw probabilistic AI outputs and enterprise cybersecurity business ROI—providing unified tooling for strategic model selection, automated AI PRDs (offline evals), agent orchestration, and real-time production drift monitoring.

---

## Strategy

HorizonAI executes three strategic commitments grounded in applied AI frameworks:

1. **Licensing & Privacy Gate First**: Legal and compliance constraints precede technical model choices. Sensitive vulnerability scan topologies and IP asset data are strictly bound to on-premise open-weight models or private enterprise endpoints.
2. **Offline Evals as the "AI PRD"**: Quality gates are defined before launch using 100-case Golden Datasets. Releases are automatically blocked if Groundedness or Accuracy scores fall below baseline thresholds.
3. **Pragmatic Hybrid Routing**: High-volume, repetitive scan triage tasks are routed to right-sized open models ("Smart Interns"), while complex multi-stage attack path reasoning is routed to frontier models ("PhDs")—reducing API spend by up to 20–25x.

---

## Why and How AI

### Why AI is Used
Traditional deterministic software cannot synthesize unstructured vulnerability notes, correlate context across millions of threat signals, or reason through multi-stage exploit paths in real time. AI provides the semantic reasoning necessary to contextualize raw vulnerability data into actionable remediation workflows.

### How AI is Implemented
HorizonAI implements AI across four core architectural pillars:
- **Six-Part Agentic Anatomy**: Operates as an always-on **Resident agent** on secure servers, using a reasoning **Brain**, system tool **Hands**, **4-Tier Memory** (Working, Session Notes, Knowledge Base, Muscle Memory), iterative execution **Loops**, security **Guardrails**, and dedicated sandboxed **Workspaces**.
- **Lead-Worker Orchestration**: A **Lead Agent** breaks large-scale asset scan reports into parallel lanes, delegating sub-tasks to specialized **Worker Agents**.
- **Dynamic Model Selection**: Implements a **Four-Lens Selection Engine** (**Task Fit**, **Intelligence Required**, **Speed & Cost**, **Control & Compliance**) to dynamically route queries between fine-tuned open-source models and frontier reasoning models.
- **Dual Evaluation Engine**: Runs the **RAG Triad** (Retrieval Quality, Context Relevance, Groundedness, Answer Relevance) and **Agent Trajectory Triad** (Tool Selection, Argument Correctness, Task Completion) alongside **LLM-as-a-Judge** bias-defusing rubrics (position randomization, cross-family judging).

---

## Roadmap

| Phase | Scope | Status |
| :--- | :--- | :--- |
| **Phase 0 — Design & Spec** | System design architecture, UI specs, evaluation rubric definition, and 100-case Golden Dataset schema. | ✅ Done |
| **Phase 1 — Pilot Prototype (CyberRisk Resident)** | Interactive Lovable UI, Cursor backend API scaffold, PostgreSQL + pgvector schema, synthetic scan dataset, and Lead-Worker agent loop. | ✅ Done (Pilot) |
| **Phase 2 — Real Backend & Local Model Enclave** | Integration with local Llama/Mistral open-weight endpoints, real JWT/HMAC security, automated PHI/PII redaction, and Vitest/PyTest eval runner. | 🔄 In Progress |
| **Phase 3 — Production Routing & Live Quality Monitoring** | Live traffic sampling (1–10%), real-time Groundedness & P95/P99 latency dashboards, soft user frustration telemetry (rage clicks, overrides). | ⏳ Scheduled |
| **Phase 4 — Future Roadmap (AttackSurface & ComplianceSentinel)** | **AttackSurface Resident**: Autonomous external recon & Shadow IT discovery agent.<br>**ComplianceSentinel**: Automated CIS Benchmark auditing & policy drift copilot. | 📅 Future Roadmap |

---

## Quick Start & Installation

### Prerequisites
- [Node.js](https://nodejs.org/) 18+ & [Bun](https://bun.sh/) (optional; used automatically if `bun.lock` is present)
- [Python](https://www.python.org/) 3.12+
- [PostgreSQL](https://www.postgresql.org/) with `pgvector` extension enabled

### How to bring up the app

HorizonAI runs as two processes: a FastAPI backend (port 8000) and a TanStack Start frontend
(port 5173). The start scripts handle dependency installation, database setup, seeding, and
health checks on first run.

**Quick start (recommended):**

| Platform | Start | Stop |
|---|---|---|
| macOS / Linux | [`./start.sh`](start.sh) | [`./stop.sh`](stop.sh) |
| Windows (PowerShell) | [`./start.ps1`](start.ps1) | [`./stop.ps1`](stop.ps1) |

```bash
git clone https://github.com/mayukhg/ai-product-horizon.git
cd ai-product-horizon
./start.sh          # installs dependencies on first run, then starts API + frontend
```

Then open **http://127.0.0.1:5173**. The script writes PID files (`.horizon-ai-api.pid`,
`.horizon-ai-web.pid`) and logs (`.horizon-ai-api.log`, `.horizon-ai-web.log`) so `./stop.sh`
can find and stop the right processes, and detects if the app is already running so it won't
start a second copy.

**Flags (bash):**

| Flag | Effect |
|---|---|
| `--host` | Override bind address (default `127.0.0.1`) |
| `--port` | Frontend port (default `5173`) |
| `--api-port` | Backend API port (default `8000`) |
| `--skip-seed` | Skip database seeding on startup |

**Verifying the backend is up**, once the app is running:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/v1/triage
```

**Manual start**, if you'd rather not use the scripts:

```bash
npm install                    # or: bun install
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
bash scripts/setup-postgres.sh
backend/.venv/bin/python backend/scripts/seed_data.py
backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend &
npm run dev                    # or: bun run dev
```

### Documentation

- **[How to use the cockpit](docs/HOW_TO_USE.md)** — walkthrough of all five UI workflows
  (CyberRisk Resident monitoring, HITL remediation approval, Eval Studio, Resident Roadmap, and
  the data state simulator), each with a diagram and click-by-click steps.
- **[End-to-end workflow](docs/workflow.md)** — how a Qualys scan becomes a human-approved
  remediation action, from triage through Lead-Worker orchestration, model routing, HITL gates,
  and golden-dataset evals.
- **[LLM setup guide](docs/LLM_SETUP.md)** — OpenRouter model stack, when to provide your API key,
  eval release gates, and JWT auth configuration.

### LLM stack (OpenRouter)

| Tier | OpenRouter model ID |
|---|---|
| Smart Intern | `meta-llama/llama-3.3-70b-instruct` |
| PhD Reasoner | `anthropic/claude-sonnet-4` |
| Guardrails | `meta-llama/llama-guard-3-8b` |
| Embeddings | `openai/text-embedding-3-small` (1536-dim) |
| Judge | `anthropic/claude-sonnet-4` |

By default `LLM_MODE=mock` — no API key required. Set `LLM_MODE=live` and add
`OPENROUTER_API_KEY` to `backend/.env` for live inference across all tiers.
See **[docs/LLM_SETUP.md](docs/LLM_SETUP.md)** for the full setup sequence.
