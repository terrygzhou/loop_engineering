# `graph/state.py`

## Purpose
Defines the core state types for the self-improving AI loop workflow. This module establishes the data structures that flow through every phase of the LangGraph pipeline: `CycleMetrics` (a Pydantic model for quantitative metrics) and `WorkflowState` (a TypedDict carrying all phase data). Every node reads from and writes to this state, making it the single source of truth for the entire workflow lifecycle.

## Public API

### Classes
#### `CycleMetrics(BaseModel)`
- **Description**: Pydantic model collecting quantitative metrics during a workflow cycle. Used by edge routing to enforce quality gates.
- **Constructor**: `__init__()` — all fields have default values.

| Field | Type | Default | Description |
|---|---|---|---|
| `review_revisions` | `int` | `0` | Number of code review revision rounds |
| `security_findings` | `int` | `0` | Count of security issues detected |
| `test_flakiness_rate` | `float` | `0.0` | Rate of flaky tests (0.0–1.0) |
| `latency_ms` | `float` | `0.0` | End-to-end latency in milliseconds |
| `uat_pass_rate` | `float` | `0.0` | User acceptance test pass rate (0.0–1.0) |
| `spec_confidence` | `float` | `0.0` | Confidence score in the generated spec |
| `task_count` | `int` | `0` | Number of build tasks |
| `arch_uncertainty` | `float` | `0.0` | Architectural uncertainty score (0.0–1.0) |
| `launch_success` | `bool` | `False` | Whether the deploy/launch succeeded |
| `seed_executed` | `bool` | `False` | Whether seed data insertion ran |

#### `WorkflowState(TypedDict)`
- **Description**: LangGraph state type flowing through the entire workflow. Each node mutates a copy and returns it to the graph runner.
- **Fields**:

| Field | Type | Description |
|---|---|---|
| `cycle_id` | `str` | Unique identifier for this workflow cycle |
| `phase` | `str` | Current phase: `DISCOVER`, `DEFINE`, `PLAN`, `BUILD`, `SEED_DATA`, `VERIFY`, `SHIP`, `REFLECT` |
| `artifacts` | `dict[str, str]` | Key-value store for spec files, task lists, code diffs, logs, skill registry, loop counts, etc. |
| `metrics` | `CycleMetrics` | Collected metrics for this cycle |
| `feedback` | `List[dict]` | LLM review comments, debug traces, and other feedback data |
| `feedback_context` | `str` | Historical patterns from past cycles (populated by ChromaDB) |
| `config_version` | `str` | Git commit hash of the skill config files |
| `human_approval_required` | `bool` | If `True`, execution pauses for human input at the next HIL gate |
| `next_phase` | `Optional[str]` | Suggested next phase (edge routers can override) |
| `project_name` | `str` | User-provided project name (captured in DEFINE) |
| `project_path` | `str` | Filesystem path to the target project |
| `spec_path` | `str` | Path to the spec directory |
| `skip_discover` | `bool` | If `True`, skips DISCOVER phase (greenfield mode — no existing codebase) |
| `context_folder` | `str` | Path to existing codebase for the DISCOVER phase |
| `error` | `Optional[str]` | Error message if the current phase failed |

---

## Dependencies / Used By
- **Imports**: `typing.TypedDict`, `typing.List`, `typing.Optional`, `pydantic.BaseModel`
- **Used By**: `graph/main.py`, `graph/edges.py`, `graph/executor.py`, `frontend/backend/workflow_bridge.py`

## Notes / Caveats
- `WorkflowState` is a `TypedDict`, so all fields are expected to be present at runtime (no `Total=False` used).
- The `artifacts` dict serves as a flexible key-value bag — it holds the skill registry, loop counts, interview notes, and phase-specific outputs.
- `CycleMetrics` defaults make it safe to instantiate with no arguments and fill in fields incrementally.
