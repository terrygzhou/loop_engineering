# `graph/nodes/plan.py`

## Purpose
The PLAN node generates an implementation plan from the refined spec, breaks it into actionable tasks, analyzes cross-artifact consistency, challenges assumptions via doubt-driven development, and produces a feature-specific checklist. It also queries ChromaDB for historical planning lessons and computes an `arch_uncertainty` metric (0.0–1.0) derived from actual artifact quality to inform downstream routing decisions.

## Public API

### Functions
#### `_load_feedback_context(state: dict) -> str`
- **Parameters**: - `state` (dict): WorkflowState containing project_name
- **Returns**: str — formatted text block of historical planning lessons, or empty string
- **Behavior**: Queries ChromaDB for 3 most similar historical patterns tagged for the plan phase. Formats as `[Past Cycle N]` entries with distance scores. Gracefully degrades on error.

#### `_estimate_arch_uncertainty(artifacts: dict) -> float`
- **Parameters**: - `artifacts` (dict): dict of named artifacts (plan, tasks, analysis, doubt_resolution, checklist)
- **Returns**: float (0.0–1.0) — architectural uncertainty score; lower = more confident
- **Behavior**: Starts at 0.6, then adjusts based on artifact quality:
  - Plan > 200 chars: −0.15
  - Tasks ≥ 5 items: −0.15 (≥ 1 item: −0.1)
  - Analysis > 50 chars: −0.1
  - Doubt resolution > 50 chars: −0.1
  - Checklist > 50 chars: −0.05
  - Analysis mentions "low risk"/"solid": −0.05
  - Analysis mentions "unclear"/"unknown"/"high risk": +0.15
  - Clamped to [0.0, 1.0]

#### `plan_node(state: dict) -> dict`
- **Parameters**: - `state` (dict): WorkflowState containing spec_refined, spec_path, and project context
- **Returns**: dict — updated WorkflowState with artifacts (plan, tasks, analysis, doubt_resolution, checklist), metrics (task_count, arch_uncertainty), phase="PLAN", next_phase="BUILD"
- **Behavior**:
  1. Loads skill registry from state or builds from disk.
  2. Loads historical feedback from ChromaDB.
  3. Runs writing-plans to generate implementation plan from spec.
  4. Runs speckit-tasks to break plan into dependency-ordered tasks.
  5. Runs speckit-analyze for cross-artifact consistency check.
  6. Runs doubt-driven-development to challenge architectural assumptions.
  7. Runs speckit-checklist to generate a custom feature checklist.
  8. Derives `arch_uncertainty` and `task_count` metrics from artifacts.

## Dependencies / Used By
- **Imports**: `os`, `tools.loader.build_skill_registry`, `tools.llm.invoke_skill`, `feedback.chroma_client.get_chroma_client`, `feedback.chroma_client.query_patterns`
- **Used By**: `graph/main.py` (wires `plan_node` into LangGraph)

## Notes / Caveats
- **Architectural uncertainty**: Used by `graph/edges.py` as a quality gate — if above `max_arch_uncertainty` threshold, PLAN loops back.
- **Task counting**: Uses heuristic pattern matching (`- [`, `1.`, `2.`, `3.`) to count task items; may overcount in edge cases.
- **Historical feedback**: Non-blocking — ChromaDB failures are caught and logged as warnings.
- **Skill chaining**: Each step feeds into the next (plan → tasks → analysis → doubt resolution), but checklist is derived from spec_refined independently.
