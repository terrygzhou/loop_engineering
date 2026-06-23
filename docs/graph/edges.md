# `graph/edges.py`

## Purpose
Implements conditional edge routing for the LangGraph workflow. The `route_phase` function inspects the current phase, its metrics, and any errors to decide the next step: proceed forward, loop back for rework, or end the workflow. Quality gate thresholds are loaded from `guardrails.yaml` at runtime, allowing the REFLECT phase to dynamically adjust them between cycles. Loop counts are tracked per-phase in state artifacts to prevent livelock after repeated failures.

## Public API

### Functions
#### `route_phase(state: WorkflowState) -> str`
- **Parameters**:
  - `state` (`WorkflowState`): Current workflow state.
- **Returns**: `str` — the name of the next phase node, or `END` to terminate.
- **Behavior**: Central routing function used as the conditional edge for `DEFINE`, `PLAN`, `BUILD`, `SEED_DATA`, and `VERIFY`. Implements quality gates and loop-back logic:

  | Phase | Quality Gate | Action if Failed | Action if Passed |
  |---|---|---|---|
  | `DEFINE` | `spec_confidence < min_spec_confidence` | Loop back to `DEFINE` | Proceed to `PLAN` |
  | `PLAN` | `arch_uncertainty > max_arch_uncertainty` | Loop back to `PLAN` | Proceed to `BUILD` |
  | `BUILD` | `security_findings > max_security_findings` or `review_revisions > max_review_revisions` | Loop back to `BUILD` | Proceed to `SEED_DATA` |
  | `SEED_DATA` | `artifacts["seed_errors"]` is truthy | Loop back to `BUILD` | Proceed to `VERIFY` |
  | `VERIFY` | `uat_pass_rate < uat_pass_rate_threshold` | Loop back to `BUILD` | Proceed to `SHIP` |
  | `SHIP` | Always | — | Proceed to `REFLECT` |
  | Other | — | — | `END` |

  After 2 loop retries for a phase, the router forces forward progression (via `_forward_paths`) to prevent livelock, then resets the counter to 0. If an error is present and retries are exhausted, returns `END`.

### Module-Level Variables
- `END_MARKER` (`END`): Re-export of LangGraph's `END` marker for use in `main.py`.
- `_forward_paths` (`dict[str, str]`): Maps each phase to its normal forward successor, used when forcing progression after max retries.

  | Phase | Forward Target |
  |---|---|
  | `DISCOVER` | `DEFINE` |
  | `DEFINE` | `PLAN` |
  | `PLAN` | `BUILD` |
  | `BUILD` | `SEED_DATA` |
  | `SEED_DATA` | `VERIFY` |
  | `VERIFY` | `SHIP` |

---

## Dependencies / Used By
- **Imports**:
  - `langgraph.graph.END`
  - `graph.state.WorkflowState`
  - `config.guardrails.get_threshold`
- **Used By**: `graph/main.py`

## Notes / Caveats
- Loop counts are stored in `state["artifacts"]["loop_counts"]` — never as global variables — to prevent cross-cycle bleed.
- Thresholds (`min_spec_confidence`, `max_arch_uncertainty`, etc.) are loaded from `guardrails.yaml` via `get_threshold()` on every call, so the REFLECT phase can update the config file and have changes take effect immediately in the next cycle.
- The max retry count is hardcoded to 2 (i.e., a phase can loop back at most twice before being forced forward).
- The `SEED_DATA` phase is unique: if seed data insertion fails, it loops back to `BUILD` (not to `SEED_DATA`), since the assumption is that code changes are needed before retrying seed data.
- `VERIFY` on failure also loops back to `BUILD` rather than to `VERIFY`, as the expectation is that code must be fixed to pass UAT.
