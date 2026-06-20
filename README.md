# Self-Improving AI Loop Engine

Hybrid orchestrator implementing DISCOVER → DEFINE → PLAN → BUILD → SEED_DATA → VERIFY → SHIP → REFLECT workflow with self-improving feedback loop.

## Architecture

```
┌─────────────┐     ┌────────────┐     ┌───────────┐
│    CLI      │────▶│ LangGraph  │────▶│  Skills    │
│  (Typer)    │     │ Orchestrator│     │ (SKILL.md) │
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

| Phase | Skills |
|-------|--------|
| DISCOVER | none (filesystem/git/docker scans — **skipped for greenfield**) |
| DEFINE | interview-me → speckit-specify → api-and-interface-design |
| PLAN | writing-plans → speckit-tasks → speckit-analyze → doubt-driven-development → speckit-checklist |
| BUILD | incremental-implementation → fastapi-jinja2-feature-build → test-driven-development → security-and-hardening → requesting-code-review → **execute** (write files, Docker build, health check, pytest, bandit) |
| SEED_DATA | ai-workflow-data-seeding |
| VERIFY | uat-workflow (Playwright desktop + mobile mandatory) → performance-optimization → systematic-debugging → code-simplification |
| SHIP | observability-and-instrumentation → shipping-and-launch → docker-compose-deployment → git-workflow |
| REFLECT | meta-agent (internal) → diff_engine → human approval → git-workflow |

## Quick Start

```bash
# With Docker Compose (recommended) — requires vLLM running on localhost:8080
cd /home/terry/workspace/projects/loop_engineering
docker compose up -d chromadb
docker compose run orchestrator python main.py run --spec ../GloryEV_CustomerApp/specs/012-dashboard --project ../GloryEV_CustomerApp

# Local (requires vLLM + ChromaDB running)
python main.py run --spec ../GloryEV_CustomerApp/specs/012-dashboard
```

**Prerequisites:**
- vLLM serving Qwen3.6-27B on `localhost:8080`
- `pip install -r requirements.txt` (for local mode)

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
