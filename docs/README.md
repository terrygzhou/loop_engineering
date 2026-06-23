# Loop Engineering Documentation

## Overview

**Loop Engineering** is an AI-driven autonomous development workflow engine built on LangGraph. It implements a cyclic pipeline that iteratively refines software projects through eight phases:

```
DISCOVER → DEFINE → PLAN → BUILD → SEED_DATA → VERIFY → SHIP → REFLECT
```

Each cycle runs through these phases, with the **REFLECT** node analyzing feedback and metrics to self-improve the engine's configuration, prompt templates, and quality thresholds for the next cycle. This creates a closed-loop feedback system where the development process continuously optimizes itself.

### How It Works

1. **DISCOVER** — Gathers initial context about the project, technology stack, and requirements.
2. **DEFINE** — Conducts structured interviews with the user and produces actionable specifications.
3. **PLAN** — Designs the architecture, breaking the work into implementable steps.
4. **BUILD** — Generates code based on the plan, with automated review and revision loops.
5. **SEED_DATA** — Creates test data, fixtures, and seed records for verification.
6. **VERIFY** — Runs tests, checks quality gates, and validates against guardrails.
7. **SHIP** — Packages and prepares the output for deployment or handoff.
8. **REFLECT** — Analyzes cycle metrics, generates config diffs, and proposes improvements for the next iteration.

### Configuration Resolution

All settings follow a three-tier priority: **Environment Variables** > **`config.yaml`** > **Built-in Defaults**, making it easy to override behavior without changing source code.

## Documented Modules

| # | File | Description |
|---|------|-------------|
| 1 | [`main.py`](main.md) | CLI entry point. Parses args, delegates to `WorkflowRunner.run_interactive()`. |
| 2 | [`graph/executor.py`](graph/executor.md) | Shared workflow core — `WorkflowRunner` used by both CLI and Web UI. |
| 3 | [`graph/state.py`](graph/state.md) | `WorkflowState` (TypedDict) and `CycleMetrics` (Pydantic model) definitions. |
| 4 | [`graph/main.py`](graph/main.md) | Graph construction: wires nodes and edges into the LangGraph state machine. |
| 5 | [`graph/edges.py`](graph/edges.md) | Conditional routing: uses `guardrails.py` for dynamic thresholds from YAML. |
| 6 | [`graph/nodes/discover.py`](graph/nodes/discover.md) | DISCOVER node: scans existing codebase for context, tech stack, and requirements. |
| 7 | [`graph/nodes/define.py`](graph/nodes/define.md) | DEFINE node: runs `interview-me` → `speckit-specify` → `api-and-interface-design`. Injects ChromaDB feedback. |
| 8 | [`graph/nodes/plan.py`](graph/nodes/plan.md) | PLAN node: architecture design and task breakdown with historical feedback injection. |
| 9 | [`graph/nodes/build.py`](graph/nodes/build.md) | BUILD node: iterative code generation with review gates and revision tracking. |
| 10 | [`graph/nodes/seed_data.py`](graph/nodes/seed_data.md) | SEED_DATA node: test data and fixture generation. |
| 11 | [`graph/nodes/verify.py`](graph/nodes/verify.md) | VERIFY node: UAT (browser-level), performance testing, and dynamic quality gates. |
| 12 | [`graph/nodes/ship.py`](graph/nodes/ship.md) | SHIP node: deployment packaging and Docker compose preparation. |
| 13 | [`graph/nodes/reflect.py`](graph/nodes/reflect.md) | REFLECT node: cycle analysis, diff generation, and self-improvement proposals. |
| 14 | [`config/loader.py`](config/loader.md) | Three-tier config resolution (env > YAML > defaults). Manages project name and path. |
| 15 | [`config/guardrails.py`](config/guardrails.md) | Runtime threshold loader — reads `guardrails.yaml` with fallback defaults. |
| 16 | [`config/prompt_templates.py`](config/prompt_templates.md) | Externalized ToT+CoT prompt templates for DEFINE phase (interview, spec, API design). |
| 17 | [`config/config.yaml`](config/config.yaml) | Default configuration with workspace_dir, LLM settings, and path templates. |
| 18 | [`config/guardrails.yaml`](config/guardrails.yaml) | Quality thresholds by phase — spec_confidence, arch_uncertainty, latency, flakiness, etc. |
| 19 | [`tools/llm.py`](tools/llm.md) | LLM invocation with skill content injection. Supports OpenAI-compatible providers. |
| 20 | [`tools/loader.py`](tools/loader.md) | Skill registry builder — scans `skills/` for `.md` files, indexes by trigger keywords. |
| 21 | [`feedback/aggregator.py`](feedback/aggregator.md) | Records cycles, lists past cycles, and queries feedback patterns from ChromaDB. |
| 22 | [`feedback/chroma_client.py`](feedback/chroma_client.md) | ChromaDB client — pattern embeddings, similarity search, and historical feedback retrieval. |
| 23 | [`feedback/diff_engine.py`](feedback/diff_engine.md) | Generates config diffs from past cycles, applies YAML and prompt template updates. |
| 24 | [`frontend/backend/app.py`](frontend/backend/app.md) | FastAPI web server — REST endpoints, WebSocket streaming, and static file serving. |
| 25 | [`frontend/backend/workflow_bridge.py`](frontend/backend/workflow_bridge.md) | Bridges LangGraph to the Web UI — supports real workflow mode and simulated fallback. |

## How to Navigate

- **Start with [`main.md`](main.md)** for the high-level entry point and workflow initialization.
- **Read the graph modules** (`graph/state.md` → `graph/main.md` → `graph/executor.md` → `graph/edges.md`) to understand the pipeline structure.
- **Follow the node docs** in pipeline order: discover → define → plan → build → seed_data → verify → ship → reflect.
- **Review config modules** to understand how settings, thresholds, and templates are managed.
- **Study feedback modules** to understand the self-improvement loop and pattern storage.
- **Check frontend modules** to understand how the Web UI bridges to the shared LangGraph workflow.

Each module doc follows a consistent template: Purpose, Public API (with signatures, parameters, return types, side effects), Dependencies, and Notes/Caveats.
