# Loop Engineering

Self-improving AI-driven software development engine built on LangGraph.

```
DISCOVER → DEFINE → PLAN → ARCH_REVIEW → BUILD → SEED_DATA → VERIFY → SHIP → REFLECT
```

Each cycle runs through these phases with quality gates, HIL (Human-in-the-Loop) review gates, and self-improvement via ChromaDB pattern storage. CLI and Web UI share the same `WorkflowRunner` — identical node execution, different UX layers.

## Architecture

```
┌──────────┐     ┌────────────┐     ┌────────────┐
│    CLI    │────▶│ LangGraph  │────▶│  Skills    │
│  (main.py)│     │ Executor   │     │  (27 SKILL.md)│
└──────────┘     └─────┬──────┘     └────────────┘
                        │
┌──────────┐             │         ┌──────────────┐
│  Web UI  │◀────────────┘         │   Feedback   │
│ (FastAPI)│    WebSocket          │  Aggregator  │
└──────────┘                        └──────┬───────┘
                                           │
                                      ┌──────────────┐
                                      │  ChromaDB    │
                                      │  (Patterns)  │
                                      └──────────────┘
```

## Quick Start

### Prerequisites

- **Python 3.12+**
- **Docker** + **Docker Compose**
- **LLM endpoint** (OpenAI-compatible, e.g., vLLM on `http://localhost:8080/v1`)

### Option A: CLI (host Python)

```bash
cd <project_root>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start ChromaDB for pattern storage (optional but recommended)
docker run -d --name chromadb-main -p 8000:8000 -v chroma_data:/chroma/chroma chromadb/chroma:latest

# Run workflow — DISCOVER phase will prompt interactively for project details
python3 main.py

# Or provide project name upfront (interview still collects description + basedir)
python3 main.py --project my_project
```

### Option B: Docker Compose (all-in-one, headless)

```bash
docker compose up -d --build
```

Runs ChromaDB and the orchestrator container in auto-approve mode. The LLM endpoint is external. DISCOVER generates default interview notes from the spec.

### Option C: Web UI

```bash
cd frontend && docker compose up -d --build
```

Open `http://localhost:8011`. Progress streams via WebSocket with quality gates dashboard and phase details.

### LLM Configuration

```bash
# Local vLLM
export LLM_BASE_URL="http://localhost:8080/v1"
export LLM_MODEL="qwen3.6-27b"

# OpenAI
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o"
export OPENAI_API_KEY="sk-..."
```

> ⚠️ **Token Usage**: A full cycle makes 20–35 LLM calls. Monitor your provider's usage dashboard during long runs.

## How It Works

### Pipeline Phases

1. **DISCOVER** — Interactive HIL interview: collects project name, description, and optional existing codebase path. Asks 9 structured interview questions (core behavior, data model, API surface, etc.). Scans existing codebase for context (routes, models, dependencies, Docker/git status). Generates `requirement.md` via Fabric prompt skill (or template fallback). *Requires human input.*

2. **DEFINE** — Generates a structured specification via `speckit-specify`, then produces an API contract via `api-and-interface-design`. Fully automatic — interview was already collected in DISCOVER. Incorporates user review comments if returning from ARCH_REVIEW rejection.

3. **PLAN** — Architecture and task planning: `writing-plans` → `speckit-tasks` → `speckit-analyze` → `doubt-driven-development` → `speckit-checklist`. Generates architecture diagrams via `architecture-diagram-generator`.

4. **ARCH_REVIEW** — Human-in-the-Loop gate: pauses for the user to review the specification, implementation plan, task breakdown, and architecture diagrams before BUILD begins. Can approve, reject (loops back to DEFINE with feedback), or edit sections inline.

5. **BUILD** — Iterative code generation per task item: `incremental-implementation` → `test-driven-development` (per item). Final aggregate passes: `security-and-hardening` (STRIDE model) → `requesting-code-review`. Runs Docker Compose build, health check, and pytest. Max 2 retries per cycle.

6. **SEED_DATA** — Test data and fixture generation via `ai-workflow-data-seeding`. Executes seed script inside the running Docker container.

7. **VERIFY** — Comprehensive validation: `uat-workflow` (Playwright desktop + mobile) mandatory. Conditional passes: `performance-optimization` (if P95 latency > 500 ms) → `systematic-debugging` (if flakiness > 10%) → `code-simplification` (if review revisions exceed threshold).

8. **SHIP** — Deployment packaging: `observability-and-instrumentation` → `shipping-and-launch` → `docker-compose-deployment` (if BUILD did not deploy) → `git-workflow` (version tag).

9. **REFLECT** — Cycle analysis: aggregates metrics and feedback, queries ChromaDB for historical patterns, meta-agent generates proposed config/guardrail diffs, dry-run validation, human approval gate for changes. Approved changes committed via `git-workflow`.

### Skills System

Each node chains skills from `skills/` (27 currently registered). A skill is skipped if missing — the pipeline continues with whatever artifacts were produced.

| Phase | Skills Chained |
|---|---|
| DISCOVER | `interview-me` (CLI HIL) → Fabric Prompt Engineering → codebase scan (filesystem/git/docker) |
| DEFINE | `speckit-specify` → `api-and-interface-design` |
| PLAN | `writing-plans` → `speckit-tasks` → `speckit-analyze` → `doubt-driven-development` → `speckit-checklist` → `architecture-diagram-generator` |
| ARCH_REVIEW | HIL gate (human reviews spec + plan + diagrams — no skills called) |
| BUILD | `incremental-implementation` → `test-driven-development` (per task item) → `security-and-hardening` → `requesting-code-review` (aggregate) |
| SEED_DATA | `ai-workflow-data-seeding` |
| VERIFY | `uat-workflow` (mandatory) → `performance-optimization` (if slow) → `systematic-debugging` (if flaky) → `code-simplification` (if high revision count) |
| SHIP | `observability-and-instrumentation` → `shipping-and-launch` → `docker-compose-deployment` → `git-workflow` |
| REFLECT | Internal `diff_engine` + meta-agent → `git-workflow` (commit approved diffs) |

**Total per cycle**: ~20–35 LLM calls. BUILD loops (up to 2 retries) can increase this.

### Quality Gates

Thresholds from `config/guardrails.yaml`:

| Phase | Gate |
|---|---|
| DISCOVER | Human interview required (always HIL, no auto-approve) |
| DEFINE | `spec_confidence ≥ 0.9` or loop back |
| PLAN | `arch_uncertainty ≤ 0.8` or loop back |
| BUILD | `security_findings = 0`, `review_revisions ≤ 2`, Docker build + health check + pytest pass — or loop back |
| SEED_DATA | `seed_errors` is empty or loop back to BUILD |
| VERIFY | `uat_pass_rate ≥ 0.95` or loop back to BUILD |
| REFLECT | Human approval required for config changes (auto-apply low-risk when confidence ≥ 0.95) |

### Self-Improvement Loop

After SHIP, REFLECT:
1. Aggregates cycle metrics and feedback
2. Queries ChromaDB for historical patterns
3. Meta-agent generates proposed skill/config/guardrail diffs
4. Dry-run validation against guardrails
5. Human approval gate (CLI or Web UI)
6. Approved changes committed via `git-workflow`

Low-risk changes (confidence ≥ 0.95, zero security findings) can auto-apply.

## Project Structure

```
loop_engineering/
├── main.py                    # CLI entry point (delegates all input to DISCOVER)
├── config/
│   ├── config.yaml           # Three-tier config (env > YAML > defaults)
│   ├── loader.py            # Config resolution
│   ├── guardrails.yaml       # Quality thresholds, LLM settings, security rules
│   └── guardrails.py         # Runtime threshold loader
├── graph/
│   ├── main.py               # LangGraph construction (node wiring)
│   ├── executor.py          # Shared WorkflowRunner (CLI + Web UI)
│   ├── state.py             # WorkflowState + CycleMetrics
│   ├── edges.py             # Conditional routing with quality gates
│   └── nodes/               # Phase implementations
│       ├── discover.py      # HIL interview + codebase scan + requirement generation
│       ├── define.py        # Spec + API contract generation
│       ├── plan.py          # Architecture plan + tasks + diagrams
│       ├── arch_review.py   # HIL gate (reviews spec, plan, diagrams)
│       ├── build.py         # Incremental code generation + test + security
│       ├── seed_data.py     # Test data seeding via Docker
│       ├── verify.py        # UAT, perf, debugging, simplification
│       ├── ship.py          # Observability, launch, deploy, git tag
│       ├── reflect.py       # Cycle analysis + ChromaDB + config diffs
│       ├── human_review.py  # Legacy (no longer wired into graph)
│       └── review_contract.py  # Shared HIL contract (CLI & Web UI parity)
├── feedback/
│   ├── aggregator.py        # Cycle recording, ChromaDB queries
│   ├── chroma_client.py     # Pattern embeddings, similarity search
│   └── diff_engine.py       # Config diff generation
├── tools/
│   ├── llm.py               # LLM invocation with skill injection
│   └── loader.py           # Skill registry builder
├── skills/                   # 27 SKILL.md files (one per skill)
├── frontend/                 # Web UI (FastAPI + nginx + uvicorn)
│   ├── backend/            # FastAPI app, WebSocket streaming, workflow bridge
│   └── static/             # HTML/CSS/JS frontend
├── observability/           # OpenTelemetry collector config + Promtail
│   └── otel-collector-config.yaml
├── storage/                 # Persistent cycle data (live.json, cycles/)
├── specs/                   # Example specs from the workflow
├── scripts/
│   └── uat_pipeline.sh     # UAT pipeline helper
├── docker-compose.yml       # All-in-one: ChromaDB + orchestrator + OTEL + Phoenix
├── Dockerfile               # CLI orchestrator image
└── requirements.txt        # Python dependencies
```

## Configuration

Three-tier priority: **Environment Variables** > **`config/config.yaml`** > **Built-in Defaults**.

Key settings in `config.yaml`:
```yaml
paths:
  project_name: test_discover_fix
  workspace_dir: ~/workspace/projects
  project_path: '{{project_name}}'
  skills_dir: skills
  storage_dir: ./storage
  guardrails_path: ./config/guardrails.yaml

workflow:
  hil_mode: auto
  max_retries: 2
  auto_approve: false
```

LLM settings in `config/guardrails.yaml`:
```yaml
llm:
  model: Qwen3.6-27B
  base_url: ${LLM_BASE_URL:-http://localhost:8080/v1}
  temperature: 0.1
  max_retries: 3
```

## Dependencies

```
langgraph, langchain-core, langgraph-checkpoint, langgraph-sdk
pydantic, pyyaml, httpx, aiohttp
chromadb (pattern storage)
opentelemetry-api, opentelemetry-sdk (observability)
```

Install: `pip install -r requirements.txt` (CLI mode) or baked into Docker image (Docker mode).

## Example Runs

```bash
# Interactive CLI — DISCOVER asks for project name, description, basedir, and 9 interview questions
python3 main.py

# With project name (DISCOVER still asks for description + basedir + interview)
python3 main.py --project myapp

# Auto-approve with inline spec (useful for testing/CI)
python3 main.py --project myapp --spec "Build a REST API" --auto-approve

# Scan existing codebase (basedir also asked in interview as default)
python3 main.py --project myapp --context ./existing_code

# Improve a previously deployed product
python3 main.py --project myapp --improve
```

## Guardrails

Security-sensitive keywords (`auth`, `payment`, `billing`, `credential`, `secret`, `api_key`, `token`, etc.) trigger human approval. See `config/guardrails.yaml` for full thresholds and feedback rules.

Quality thresholds enforced per phase:

| Threshold | Default | Phase |
|---|---|---|
| `min_spec_confidence` | ≥ 0.9 | DEFINE |
| `max_arch_uncertainty` | ≤ 0.8 | PLAN |
| `max_security_findings` | 0 | BUILD |
| `max_review_revisions` | ≤ 2 | BUILD |
| `min_uat_pass_rate` | ≥ 0.95 | VERIFY |
| `max_latency_ms` | ≤ 500 | VERIFY (perf) |
| `max_test_flakiness_rate` | ≤ 0.1 | VERIFY (debug) |
