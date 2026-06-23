# `graph/main.py`

## Purpose
Compiles the LangGraph workflow by wiring together all phase nodes and edges into a single directed graph. This module defines the complete workflow topology: `DISCOVER → DEFINE → PLAN → BUILD → SEED_DATA → VERIFY → SHIP → REFLECT → END`, with conditional routing on most phases to support quality gates and loops. It serves as the graph construction entry point, imported by the executor layer.

## Public API

### Functions
#### `build_graph(checkpointer=None) -> CompiledGraph`
- **Parameters**:
  - `checkpointer` (optional, default `None`): A LangGraph checkpointer (e.g., `MemorySaver`) for state persistence across invocations.
- **Returns**: `CompiledGraph` — the compiled LangGraph workflow ready for execution.
- **Behavior**:
  1. Creates a `StateGraph` typed with `WorkflowState`.
  2. Registers eight nodes: `DISCOVER`, `DEFINE`, `PLAN`, `BUILD`, `SEED_DATA`, `VERIFY`, `SHIP`, `REFLECT`.
  3. Wires linear edges: `START → DISCOVER → DEFINE`.
  4. Attaches `route_phase` as a conditional edge router on `DEFINE`, `PLAN`, `BUILD`, `SEED_DATA`, and `VERIFY` — enabling loops back to earlier phases or forced forward progression.
  5. Wires linear edges: `SHIP → REFLECT → END`.
  6. Calls `workflow.compile()` with the optional checkpointer.

---

## Dependencies / Used By
- **Imports**:
  - `langgraph.graph.StateGraph`, `langgraph.graph.START`, `langgraph.graph.END`
  - `langgraph.checkpoint.memory.MemorySaver` (imported but not used directly in the function body; available if a checkpointer is needed)
  - `graph.state.WorkflowState`
  - `graph.nodes.discover.discover_node`
  - `graph.nodes.define.define_node`
  - `graph.nodes.plan.plan_node`
  - `graph.nodes.build.build_node`
  - `graph.nodes.seed_data.seed_data_node`
  - `graph.nodes.verify.verify_node`
  - `graph.nodes.ship.ship_node`
  - `graph.nodes.reflect.reflect_node`
  - `graph.edges.route_phase`
- **Used By**: `graph/executor.py`

## Notes / Caveats
- `MemorySaver` is imported but not wired by default; callers can pass a checkpointer to `build_graph()` for persistent state.
- The five phases with conditional routing (`DEFINE`, `PLAN`, `BUILD`, `SEED_DATA`, `VERIFY`) all use the same `route_phase` edge function from `graph/edges.py`, keeping routing logic centralized.
- `DISCOVER` has no conditional routing — it always proceeds to `DEFINE`.
- `SHIP` and `REFLECT` are fixed linear edges — they never loop back.
