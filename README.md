# Loop Engineering

Self-improving AI-driven software development engine built on LangGraph.

```
DISCOVER → DEFINE → PLAN → ARCH_REVIEW → BUILD → SEED_DATA → VERIFY → SHIP → REFLECT
```

Each cycle runs through these phases with quality gates, HIL (Human-in-the-Loop) review gates, and self-improvement via ChromaDB pattern storage. CLI and Web UI share the same `WorkflowRunner` — identical node execution, different UX layers.

## Architecture

```mermaid
flowchart TB
    subgraph entry["📥 Entry Points"]
        CLI[\"main.py\nCLI Entry\"]
        WebUI[\"frontend/backend/app.py\nFastAPI :8011\"]
    end

    subgraph workflow["🔄 LangGraph Engine"]
        State[\"state.py\nWorkflowState\"]
        Graph[\"main.py\nStateGraph\"]
        Executor[\"executor.py\nWorkflowRunner\"]
        Edges[\"edges.py\nConditional Routing\n+ Quality Gates\"]
    end

    subgraph phases["📦 Phase Nodes"]
        DISCOVER[\"discover.py\nHIL Interview\n+ Codebase Scan\n+ requirement.md\"]
        DEFINE[\"define.py\nSpec + API Contract"]
        PLAN[\"plan.py\nPlan + Tasks\n+ Analysis"]
        ArchNode[\"architecture.py\nComponent/Sequence\nData Flow/Deployment\n→ .mmd files"]
        ARCH_REVIEW[\"arch_review.py\nHIL Pause\nDiagrams + Spec Review"]
        BUILD[\"build.py\nIncremental Code Gen\n+ TDD + Security"]
        SEED[\"seed_data.py\nTest Data Fixtures"]
        VERIFY[\"verify.py\nUAT + Perf\n+ Debug + Simplify"]
        SHIP[\"ship.py\nDeploy + Git Tag"]
        REFLECT[\"reflect.py\nChromaDB Patterns\n+ Config Diffs"]
    end

    subgraph skills["🛠 Skills System"]
        SkillReg[\"tools/loader.py\nSkill Registry\n~27 SKILL.md files"]
        LLMTool[\"tools/llm.py\ninvoke_skill()"]
    end

    subgraph hil["👤 HIL Bridges"]
        Bridge[\"workflow_bridge.py\nSSE Event Emission\n+ LangGraph Resume"]
        AbortMgr[\"abort_manager.py\nClean Shutdown"]
    end

    subgraph frontend["🖥 Frontend"]
        AppJS[\"app.js\nSSE Client\n+ Mermaid Rendering\n+ Phase Detail View"]
        UI[\"index.html\n+ style.css\n+ Mermaid.js CDN"]
    end

    subgraph feedback["📊 Feedback Loop"]
        Aggregator[\"feedback/aggregator.py\nCycle Recording"]
        ChromaClient[\"feedback/chroma_client.py\nPattern Embeddings"]
        DiffEngine[\"feedback/diff_engine.py\nConfig Diff Gen"]
        ChromaDB[(\"ChromaDB\nHistorical Patterns\")]
    end

    subgraph deploy["🚀 Deployment"]
        Docker[\"Dockerfile\nPython + nginx\n+ LangGraph"]
        Compose[\"docker-compose.yml\nloop + chroma + otel"]
    end

    CLI --> Executor
    WebUI --> Bridge
    Bridge --> Executor
    Bridge <--> AbortMgr
    Executor --> Graph
    Graph <--> State
    Graph --> Edges
    
    Graph --> DISCOVER
    DISCOVER --> DEFINE
    DEFINE --> PLAN
    PLAN --> ArchNode
    ArchNode --> ARCH_REVIEW
    ARCH_REVIEW -->|"approved"| BUILD
    ARCH_REVIEW -->|"rejected"| DEFINE
    BUILD -->|"pass"| SEED
    BUILD -->|"fail"| PLAN
    SEED -->|"pass"| VERIFY
    SEED -->|"fail"| BUILD
    VERIFY -->|"pass"| SHIP
    VERIFY -->|"fail"| BUILD
    SHIP --> REFLECT
    REFLECT -->|"END"| Done[("✓ Complete")]
    
    DISCOVER -.->|"HIL Pause"| Bridge
    ARCH_REVIEW -.->|"HIL Pause"| Bridge
    
    DISCOVER --> SkillReg
    DEFINE --> SkillReg
    PLAN --> SkillReg
    ArchNode --> SkillReg
    BUILD --> SkillReg
    SkillReg --> LLMTool
    
    Bridge -->|"SSE Events"| AppJS
    AppJS --> UI
    AppJS -->|"Review Input"| Bridge
    
    REFLECT --> Aggregator
    Aggregator --> ChromaClient
    ChromaClient --> ChromaDB
    Aggregator --> DiffEngine
    
    Executor -.->|"Observability"| OTEL["OpenTelemetry"]
    
    classDef node fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef hil fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef skill fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef storage fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef deploy fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    
    class DISCOVER,DEFINE,PLAN,ArchNode,BUILD,SEED,VERIFY,SHIP,REFLECT node
    class ARCH_REVIEW,Bridge,hil hil
    class SkillReg,LLMTool skill
    class ChromaDB storage
    class Docker,Compose deploy
```

### Key Components

- **Entry Points**: CLI (`main.py`) for headless auto-approve, or Web UI (FastAPI `:8011`) for HIL workflow
- **LangGraph Engine**: `StateGraph` with 10 phase nodes, conditional routing via quality gates, OOTB `interrupt_after` for HIL pauses
- **Skills System**: 27 `SKILL.md` files loaded by `tools/loader.py`, invoked via `tools/llm.py` with context optimization
- **HIL Bridge**: SSE event streaming between LangGraph executor and frontend; supports double-pause DISCOVER interview and ARCH_REVIEW diagram approval
- **Feedback Loop**: ChromaDB stores historical patterns across cycles; REFLECT phase queries and generates config diff proposals
- **Deployment**: Single Docker Compose stack (`loop` container = orchestrator + frontend + nginx)

## Quick Start

### Prerequisites

- **Docker** + **Docker Compose**
- **LLM endpoint** (OpenAI-compatible, e.g., vLLM on `http://localhost:8080/v1`)

### Option A: CLI (headless, auto-approve)

```bash
docker compose up -d --build
```

Runs the orchestrator in auto-approve mode. DISCOVER generates default interview notes from the spec.

### Option B: Web UI (HIL)

```bash
docker compose up -d --build loop
```

Open `http://localhost:8011`. Progress streams via Server-Sent Events (SSE) with quality gates dashboard, phase details, and Mermaid diagram rendering at ARCH_REVIEW gates.

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

1. **DISCOVER** — HIL interview node using LangGraph OOTB `interrupt()`. Double-pause: first for project setup (name + description), then for interview questions (9 structured questions). Scans existing codebases for context. Generates `requirement.md`. In Web UI mode, pauses for user input via SSE. In auto-approve mode, generates defaults.

2. **DEFINE** — Generates a structured specification via `speckit-specify`, then produces an API contract via `api-and-interface-design`. Fully automatic — interview data collected in DISCOVER. Incorporates user review feedback if returning from ARCH_REVIEW rejection.

3. **PLAN** — Architecture and task planning: `writing-plans` → `speckit-tasks` → `speckit-analyze` → `doubt-driven-development` → `speckit-checklist`. Generates architecture diagrams via `architecture-diagram-generator`. Diagrams are stored as `plan.md` and `diagrams.md` in the project output folder.

4. **ARCH_REVIEW** — HIL gate: pauses execution so the user can review the specification, plan, and architecture diagrams before BUILD begins. Web UI renders Mermaid diagrams client-side with tabbed diagram viewer. User can approve (proceeds to BUILD) or reject with feedback (loops back to DEFINE). Max 2 retries before forced progression.

5. **BUILD** — Iterative code generation per task item: `incremental-implementation` → `test-driven-development` (per item). Final aggregate passes: `security-and-hardening` (STRIDE model) → `requesting-code-review`. Runs Docker Compose build, health check, and pytest. Max 2 retries per cycle.

6. **SEED_DATA** — Test data and fixture generation via `ai-workflow-data-seeding`. Executes seed script inside the running Docker container.

7. **VERIFY** — Comprehensive validation: `uat-workflow` (Playwright) mandatory. Conditional passes: `performance-optimization` (if P95 latency > 500 ms) → `systematic-debugging` (if flakiness > 10%) → `code-simplification` (if review revisions exceed threshold).

8. **SHIP** — Deployment packaging: `observability-and-instrumentation` → `shipping-and-launch` → `docker-compose-deployment` (if BUILD did not deploy) → `git-workflow` (version tag).

9. **REFLECT** — Cycle analysis: aggregates metrics and feedback, queries ChromaDB for historical patterns, meta-agent generates proposed config/guardrail diffs, dry-run validation, human approval gate for changes. Approved changes committed via `git-workflow`.

### Skills System

Each node chains skills from `skills/` (27 currently registered). A skill is skipped if missing — the pipeline continues with whatever artifacts were produced.

| Phase | Skills Chained |
|---|---|
| DISCOVER | `interview-me` → Fabric Prompt Engineering → codebase scan (filesystem/git/docker) |
| DEFINE | `speckit-specify` → `api-and-interface-design` |
| PLAN | `writing-plans` → `speckit-tasks` → `speckit-analyze` → `doubt-driven-development` → `speckit-checklist` → `architecture-diagram-generator` |
| ARCH_REVIEW | HIL gate (human reviews spec + plan + Mermaid diagrams — no skills called) |
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
| DISCOVER | HIL required in Web UI mode; auto-generates defaults in auto-approve mode |
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
5. Human approval gate (Web UI)
6. Approved changes committed via `git-workflow`

Low-risk changes (confidence ≥ 0.95, zero security findings) can auto-apply.

## Project Structure

```
loop_engineering/
├── main.py                    # CLI entry (delegates input to DISCOVER)
├── config/
│   ├── config.yaml           # Three-tier config (env > YAML > defaults)
│   ├── loader.py            # Config resolution
│   ├── guardrails.yaml       # Quality thresholds, LLM settings, security rules
│   ├── guardrails.py         # Runtime threshold loader
│   └── prompt_templates.py   # LLM prompt templates for each phase
├── graph/
│   ├── main.py               # LangGraph construction (node wiring, interrupt_after)
│   ├── executor.py          # Shared WorkflowRunner (CLI + Web UI)
│   ├── state.py             # WorkflowState + CycleMetrics
│   ├── edges.py             # Conditional routing with quality gates
│   └── nodes/               # Phase implementations
│       ├── discover.py      # HIL interview + codebase scan + requirement generation
│       ├── define.py        # Spec + API contract generation
│       ├── plan.py          # Architecture plan + tasks
│       ├── architecture.py  # Architecture diagram generation (Mermaid)
│       ├── arch_review.py   # HIL gate (diagram review via Web UI)
│       ├── build.py         # Incremental code generation + test + security
│       ├── seed_data.py     # Test data seeding via Docker
│       ├── verify.py        # UAT, perf, debugging, simplification
│       ├── ship.py          # Observability, launch, deploy, git tag
│       ├── reflect.py       # Cycle analysis + ChromaDB + config diffs
│       └── review_contract.py  # Shared HIL review contract (CLI & Web UI parity)
├── feedback/
│   ├── aggregator.py        # Cycle recording, ChromaDB queries
│   ├── chroma_client.py     # Pattern embeddings, similarity search
│   └── diff_engine.py       # Config diff generation
├── tools/
│   ├── llm.py               # LLM invocation with skill injection
│   └── loader.py           # Skill registry builder
├── skills/                   # 27 SKILL.md files (one per skill)
├── frontend/                 # Web UI (FastAPI + nginx)
│   ├── backend/            # FastAPI app, SSE streaming, workflow bridge
│   │   ├── app.py          # FastAPI entry point
│   │   ├── workflow_bridge.py  # LangGraph execution bridge + event emission
│   │   └── abort_manager.py    # Workflow abort/cleanup
│   ├── static/             # HTML/CSS/JS frontend (Mermaid.js for diagrams)
│   └── nginx/              # nginx configuration
├── observability/           # OpenTelemetry collector config + Promtail
│   └── otel-collector-config.yaml
├── output/                   # Phase artifacts (./output/<project_name>/)
├── storage/                 # Persistent cycle data (live.json, cycles/)
├── specs/                   # Example specs from the workflow
├── scripts/
│   └── uat_pipeline.sh     # UAT pipeline helper
├── docker-compose.yml       # Stack: orchestrator + ChromaDB + OTEL + Phoenix
├── Dockerfile               # Container image (Python + nginx)
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

Install: baked into Docker image via `docker compose up -d --build`.

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
