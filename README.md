# Loop Engineering

Self-improving AI-driven software development engine built on LangGraph.

```
DISCOVER → DEFINE → PLAN → ARCH_REVIEW → BUILD → SEED_DATA → VERIFY → SHIP → REFLECT
```

Each cycle runs through these phases with quality gates, HIL (Human-in-the-Loop) review gates, and self-improvement via ChromaDB pattern storage. CLI and Web UI share the same `WorkflowRunner` — identical node execution, different UX layers.

## Architecture

<div class="architecture-diagram">
  <style>
    .architecture-diagram { 
      background: #f8f9fa; 
      padding: 20px; 
      border-radius: 10px; 
      margin: 20px 0;
      font-family: system-ui, -apple-system, sans-serif;
    }
    .diagram-header { text-align: center; margin-bottom: 20px; }
    .diagram-header h2 { color: #1a1a2e; margin-bottom: 10px; }
    .diagram-header p { color: #666; font-size: 1.1em; }
    
    .pipeline { 
      display: flex; 
      flex-wrap: wrap; 
      justify-content: center; 
      gap: 10px; 
      margin: 20px 0;
      align-items: center;
    }
    .phase { 
      background: #e8f5e9; 
      border: 2px solid #4CAF50; 
      border-radius: 20px; 
      padding: 8px 15px; 
      font-weight: bold; 
      font-size: 0.9em;
      text-align: center;
    }
    .phase.hil { 
      background: #fff3e0; 
      border-color: #FF9800; 
    }
    .arrow { color: #666; font-size: 1.2em; }
    .decision { 
      background: #ffebee; 
      border-color: #F44336; 
      border-radius: 20px; 
      padding: 5px 10px; 
      font-size: 0.8em;
      display: inline-block;
      margin: 0 10px;
    }
    
    .diagram-grid { 
      display: grid; 
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
      gap: 15px; 
      margin: 20px 0;
    }
    .section { 
      background: white; 
      border-radius: 10px; 
      padding: 15px; 
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      border-left: 4px solid;
    }
    .section h3 { 
      color: #1a1a2e; 
      margin-bottom: 10px; 
      border-bottom: 2px solid #f8f9fa; 
      padding-bottom: 5px; 
    }
    .node { 
      background: #f8f9fa; 
      border: 1px solid #dee2e6; 
      border-radius: 6px; 
      padding: 10px; 
      margin-bottom: 8px; 
      font-size: 0.85em;
    }
    .node h4 { margin: 0 0 5px 0; color: #1a1a2e; font-size: 1em; }
    .node p { margin: 0; color: #666; font-size: 0.9em; }
    
    .entry { border-left-color: #4CAF50; }
    .workflow { border-left-color: #2196F3; }
    .phase-section { border-left-color: #9C27B0; }
    .skills { border-left-color: #FF9800; }
    .hil-section { border-left-color: #F44336; }
    .frontend { border-left-color: #00BCD4; }
    .feedback { border-left-color: #795548; }
    .docker { border-left-color: #607D8B; }
    
    .connections { margin: 20px 0; }
    .connection { 
      background: white; 
      border: 1px solid #dee2e6; 
      border-radius: 8px; 
      padding: 12px; 
      margin-bottom: 10px;
    }
    .connection h4 { margin: 0 0 8px 0; color: #1a1a2e; }
    .connection ul { list-style: none; padding: 0; margin: 0; }
    .connection li { 
      padding: 4px 0; 
      font-size: 0.85em; 
      color: #666; 
      border-bottom: 1px solid #f8f9fa;
    }
    .connection li:last-child { border-bottom: none; }
    
    .legend { 
      background: white; 
      padding: 15px; 
      border-radius: 8px; 
      margin-top: 20px;
      border: 1px solid #dee2e6;
    }
    .legend h4 { margin: 0 0 10px 0; color: #1a1a2e; }
    .legend-items { display: flex; flex-wrap: wrap; gap: 10px; }
    .legend-item { display: flex; align-items: center; gap: 5px; font-size: 0.8em; }
    .color { 
      width: 15px; 
      height: 15px; 
      border-radius: 3px; 
      border: 2px solid;
    }
  </style>

  <div class="diagram-header">
    <h2>🔄 Loop Engineering Architecture</h2>
    <p>Self-improving AI-driven software development engine built on LangGraph with Human-in-the-Loop capabilities</p>
  </div>

  <h3>📊 Pipeline Flow</h3>
  <div class="pipeline">
    <div class="phase">DISCOVER</div>
    <div class="arrow">→</div>
    <div class="phase">DEFINE</div>
    <div class="arrow">→</div>
    <div class="phase">PLAN</div>
    <div class="arrow">→</div>
    <div class="phase hil">ARCH_REVIEW</div>
    <div class="arrow">→</div>
    <div class="phase">BUILD</div>
    <div class="arrow">→</div>
    <div class="phase">SEED_DATA</div>
    <div class="arrow">→</div>
    <div class="phase">VERIFY</div>
    <div class="arrow">→</div>
    <div class="phase">SHIP</div>
    <div class="arrow">→</div>
    <div class="phase">REFLECT</div>
  </div>
  <div style="text-align: center; margin: 15px 0;">
    <span class="decision" style="background: #e8f5e9; border-color: #4CAF50;">✅ Approved → Next Phase</span>
    <span class="decision">❌ Rejected → Loop Back</span>
  </div>

  <div class="diagram-grid">
    <div class="section entry">
      <h3>📥 Entry Points</h3>
      <div class="node"><h4>main.py</h4><p>CLI Entry (headless)</p></div>
      <div class="node"><h4>app.py</h4><p>FastAPI :8011 (Web UI)</p></div>
    </div>

    <div class="section workflow">
      <h3>🔄 LangGraph Engine</h3>
      <div class="node"><h4>state.py</h4><p>WorkflowState</p></div>
      <div class="node"><h4>main.py</h4><p>StateGraph + interrupt_after</p></div>
      <div class="node"><h4>executor.py</h4><p>WorkflowRunner</p></div>
      <div class="node"><h4>edges.py</h4><p>Conditional Routing + Quality Gates</p></div>
    </div>

    <div class="section phase-section">
      <h3>📦 Phase Nodes</h3>
      <div class="node"><h4>DISCOVER</h4><p>HIL interview + codebase scan</p></div>
      <div class="node"><h4>DEFINE</h4><p>Spec + API contract</p></div>
      <div class="node"><h4>PLAN</h4><p>Architecture + tasks</p></div>
      <div class="node"><h4>ARCH_REVIEW</h4><p>Human review gate</p></div>
      <div class="node"><h4>BUILD</h4><p>Code generation + tests</p></div>
      <div class="node"><h4>SEED_DATA</h4><p>Test data fixtures</p></div>
      <div class="node"><h4>VERIFY</h4><p>UAT + performance</p></div>
      <div class="node"><h4>SHIP</h4><p>Deploy + git tag</p></div>
      <div class="node"><h4>REFLECT</h4><p>Self-improvement loop</p></div>
    </div>

    <div class="section skills">
      <h3>🛠 Skills System</h3>
      <div class="node"><h4>tools/loader.py</h4><p>~27 SKILL.md files</p></div>
      <div class="node"><h4>tools/llm.py</h4><p>invoke_skill() + context optimization</p></div>
    </div>

    <div class="section hil-section">
      <h3>👤 HIL Bridges</h3>
      <div class="node"><h4>workflow_bridge.py</h4><p>SSE Event Emission + LangGraph Resume</p></div>
      <div class="node"><h4>abort_manager.py</h4><p>Clean Shutdown + Checkpoint Cleanup</p></div>
    </div>

    <div class="section frontend">
      <h3>🖥 Web UI Frontend</h3>
      <div class="node"><h4>app.js</h4><p>SSE Client + Mermaid Rendering</p></div>
      <div class="node"><h4>index.html</h4><p>UI + Mermaid.js CDN</p></div>
    </div>

    <div class="section feedback">
      <h3>📊 Self-Improvement Loop</h3>
      <div class="node"><h4>aggregator.py</h4><p>Cycle Recording</p></div>
      <div class="node"><h4>chroma_client.py</h4><p>Pattern Embeddings + Similarity Search</p></div>
      <div class="node"><h4>diff_engine.py</h4><p>Config Diff Generation</p></div>
      <div class="node"><h4>ChromaDB</h4><p>Historical Patterns Storage</p></div>
    </div>

    <div class="section docker">
      <h3>🐳 Docker Stack</h3>
      <div class="node"><h4>loop container</h4><p>Python + FastAPI + nginx</p></div>
      <div class="node"><h4>docker-compose.yml</h4><p>loop + chroma + otel</p></div>
    </div>
  </div>

  <div class="connections">
    <h3>🔗 Data Flow Connections</h3>
    <div class="connection">
      <h4>🔄 Pipeline Flow</h4>
      <ul>
        <li>DISCOVER → DEFINE → PLAN</li>
        <li>PLAN → ARCH_REVIEW → BUILD</li>
        <li>BUILD → SEED_DATA → VERIFY</li>
        <li>VERIFY → SHIP → REFLECT</li>
      </ul>
    </div>
    <div class="connection">
      <h4>🎯 Quality Gates</h4>
      <ul>
        <li>ARCH_REVIEW approved → BUILD</li>
        <li>ARCH_REVIEW rejected → DEFINE</li>
        <li>BUILD pass → SEED_DATA</li>
        <li>BUILD fail → PLAN (retry)</li>
        <li>VERIFY pass → SHIP</li>
        <li>VERIFY fail → BUILD (retry)</li>
      </ul>
    </div>
    <div class="connection">
      <h4>👤 HIL Bridges</h4>
      <ul>
        <li>DISCOVER → interrupt() double-pause</li>
        <li>ARCH_REVIEW → interrupt_after</li>
        <li>Bridge → SSE Events → Frontend</li>
        <li>Frontend → Review Input → Bridge</li>
      </ul>
    </div>
    <div class="connection">
      <h4>🛠 Skills Wiring</h4>
      <ul>
        <li>DISCOVER → SkillReg → LLMTool</li>
        <li>DEFINE → SkillReg → LLMTool</li>
        <li>PLAN → SkillReg → LLMTool</li>
        <li>BUILD → SkillReg → LLMTool</li>
      </ul>
    </div>
    <div class="connection">
      <h4>📊 Feedback Loop</h4>
      <ul>
        <li>REFLECT → Aggregator → ChromaClient</li>
        <li>ChromaClient → ChromaDB (patterns)</li>
        <li>Aggregator → DiffEngine → git-workflow</li>
        <li>Executor → OTel traces → OpenTelemetry</li>
      </ul>
    </div>
    <div class="connection">
      <h4>🚀 Deployment</h4>
      <ul>
        <li>CLI → Executor → Graph</li>
        <li>WebUI → Bridge → Executor</li>
        <li>Bridge ↔ AbortMgr (cleanup)</li>
        <li>Docker: loop + chroma + otel</li>
      </ul>
    </div>
  </div>

  <div class="legend">
    <h4>🎨 Legend</h4>
    <div class="legend-items">
      <div class="legend-item"><div class="color" style="background: #e8f5e9; border-color: #4CAF50;"></div>Entry Points</div>
      <div class="legend-item"><div class="color" style="background: #e3f2fd; border-color: #2196F3;"></div>LangGraph Engine</div>
      <div class="legend-item"><div class="color" style="background: #f3e5f5; border-color: #9C27B0;"></div>Phase Nodes</div>
      <div class="legend-item"><div class="color" style="background: #fff3e0; border-color: #FF9800;"></div>Skills System</div>
      <div class="legend-item"><div class="color" style="background: #ffebee; border-color: #F44336;"></div>HIL Bridges</div>
      <div class="legend-item"><div class="color" style="background: #e0f7fa; border-color: #00BCD4;"></div>Frontend</div>
      <div class="legend-item"><div class="color" style="background: #fbe9e7; border-color: #795548;"></div>Feedback Loop</div>
      <div class="legend-item"><div class="color" style="background: #eceff1; border-color: #607D8B;"></div>Docker Stack</div>
    </div>
  </div>
</div>

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
