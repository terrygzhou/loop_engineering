# Self-Improving AI Loop Engine

Autonomous software engineering workflow with LangGraph: DISCOVER → DEFINE → PLAN → BUILD → SEED_DATA → VERIFY → SHIP → REFLECT.

Supports any LLM provider — local (vLLM, Ollama) or commercial APIs (OpenAI, Anthropic, Google Gemini).
While the current BUILD pipeline targets Python/FastAPI projects, the workflow is technology-agnostic and can be adapted to other stacks.

## Architecture

```
┌─────────────┐     ┌────────────┐     ┌───────────┐
│    CLI      │────▶│ LangGraph  │────▶│  Skills   │
│  (Typer)    │     │ Orchestrator│    │ (SKILL.md)│
└─────────────┘     └─────┬──────┘     └───────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │   Feedback   │
                   │  Aggregator  │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  ChromaDB    │
                   │  (Patterns)  │
                   └──────────────┘
```

## Workflow

DISCOVER (scan project) → DEFINE (spec + API) → PLAN (tasks + analysis) →
BUILD (implement) → SEED_DATA (populate DB) → VERIFY (UAT + perf) →
SHIP (deploy) → REFLECT (self-improve) → END

## Skills Per Phase

Each LangGraph node chains its skills sequentially. A skill is skipped if missing from the local `skills/` directory — the pipeline does not fail, it continues with whatever artifacts were produced.

| LangGraph Node | Skill Chain | Token Budget (est.) |
|----------------|-------------|:---|
| **DISCOVER** | none — filesystem/git/docker scans (Python only, no LLM calls) | 0 |
| **DEFINE** | `interview-me` → `speckit-specify` → `api-and-interface-design` | 3 LLM calls |
| **PLAN** | `writing-plans` → `speckit-tasks` → `speckit-analyze` → `doubt-driven-development` → `speckit-checklist` | 5 LLM calls |
| **BUILD** | `incremental-implementation` → `fastapi-jinja2-feature-build` → `test-driven-development` → `security-and-hardening` → `requesting-code-review` → **execute** (write files, Docker build, health check, pytest, bandit) | 5 LLM calls + loops (×2 max) |
| **SEED_DATA** | `ai-workflow-data-seeding` | 1 LLM call |
| **VERIFY** | `uat-workflow` (Playwright desktop+mobile) → `performance-optimization` (if slow) → `systematic-debugging` (if flaky) → `code-simplification` (if complex) | 1–4 LLM calls |
| **SHIP** | `observability-and-instrumentation` → `shipping-and-launch` → `docker-compose-deployment` → `git-workflow` | 4 LLM calls |
| **REFLECT** | internal meta-agent (diff_engine) → `git-workflow` (human approval gate) | 1–2 LLM calls |

**Total per full cycle**: ~20–35 LLM calls. BUILD loops (up to 2 retries) and conditional VERIFY sub-skills can push this higher.

## Quick Start

### Prerequisites

- **Python 3.12+** with venv support
- **Docker** + **Docker Compose** (for ChromaDB server and Web UI)
- **LLM endpoint** (OpenAI-compatible, e.g., vLLM on `http://localhost:8080/v1`)

### 1. Set up the virtual environment

```bash
cd <project_root>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

All subsequent commands should run with the venv activated (`source .venv/bin/activate`).

### 2. Start ChromaDB server (for pattern storage)

ChromaDB stores cycle feedback and historical patterns for self-improvement. The workflow degrades gracefully without it, but pattern storage requires a running server.

```bash
docker run -d --name chromadb-main -p 8000:8000 -v chroma_data:/chroma/chroma chromadb/chroma:latest
```

The container persists data in the `chroma_data` named volume. Verify connectivity:

```bash
python3 -c "import chromadb; c = chromadb.HttpClient(host='localhost', port=8000); print('OK')"
```

If no server is available, the client falls back to an embedded in-memory store (patterns are not persisted across runs).

### 3. Run the CLI workflow

```bash
# Interactive mode (stops at HIL gates for approval)
python3 main.py --project my_project --spec "Your project description"

# Auto-approve mode (runs all phases without user interaction)
python3 main.py --project my_project --spec "Your project description" --auto-approve

# With existing codebase context
python3 main.py --project my_project --spec "Update API" --context ./existing_code
```

Projects are created under `./<project_name>` relative to the current directory.

### 4. (Optional) Run the Web UI

```bash
cd frontend && docker compose up -d --build
```

The Web UI is available at `http://localhost:8011`.

> ⚠️ **Token Usage Warning**: A full cycle makes 20–35 LLM calls. Unattended runs can accumulate significant API costs. Monitor your provider's usage dashboard during long runs.

## LLM Providers

Works with any ChatOpenAI-compatible endpoint. Set via environment variables:

```bash
# Local (vLLM, Ollama, LM Studio)
export LLM_BASE_URL="http://localhost:8080/v1"
export LLM_MODEL="qwen3.6-27b"

# OpenAI
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o"
export OPENAI_API_KEY="sk-..."

# Anthropic (via ChatOpenAI-compatible proxy or direct)
export LLM_BASE_URL="https://api.anthropic.com/v1"
export LLM_MODEL="claude-sonnet-4-20250514"

# Google Gemini (via OpenAI-compatible gateway)
export LLM_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai"
export LLM_MODEL="gemini-2.5-pro"
```

## Example Specs

See `specs/` for requirements generated by the workflow itself — demonstrating the full DEFINE → BUILD → VERIFY cycle.

## Quality Gates

- **DEFINE**: spec_confidence ≥ 0.9 or loop back
- **PLAN**: arch_uncertainty ≤ 0.8 or loop back
- **BUILD**: security_findings = 0, review_revisions ≤ 2, Docker builds, health check passes, pytest passes — or loop back
- **SEED_DATA**: seed_errors is empty or loop back to BUILD
- **VERIFY**: uat_pass_rate ≥ 0.95 or loop back to BUILD
- **SHIP**: always proceeds to REFLECT
- **REFLECT**: human approval required for config changes

## BUILD Node Scope

BUILD has two phases:

**Generation** (LLM) — Skills chain produces code, tests, and review reports as structured text.

**Execution** (Python) — Generated files are written to disk, then validated:

1. `write_files_to_project` — Parse LLM output for `=== FILE: path ===` blocks, write to disk
2. `docker compose build --no-cache api` — Compile image from source
3. `docker compose up -d api` — Start container
4. `curl http://localhost:8010/` — Health check (expect 200/301/302)
5. `pytest tests/` — Run unit/integration tests inside container
6. `bandit -r app/ -ll` — Static security scan (optional)

If any step fails, BUILD loops back (max 2 retries) with error context fed to the LLM for fixes.
A `.build_status` marker file is written on success, so VERIFY can skip redundant rebuilds.

## Self-Improvement Loop

After SHIP, REFLECT:
1. Aggregates cycle metrics and feedback
2. Queries ChromaDB for historical patterns
3. Meta-agent generates proposed skill config diffs
4. Dry-run validation against guardrails
5. Human approval gate (CLI or Telegram)
6. Approved changes committed via git-workflow

## Guardrails

See `config/guardrails.yaml` for:
- Security-sensitive keywords (auth, payment, etc.)
- Quality thresholds (UAT pass rate, flakiness, latency)
- Feedback filtering (min confidence, rollback rules)
