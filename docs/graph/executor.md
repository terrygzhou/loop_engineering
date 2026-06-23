# `graph/executor.py`

## Purpose
Provides a shared, singleton workflow core used by both the CLI (`main.py`) and the Web frontend (`app.py`). This module abstracts graph construction, state initialization, and node execution so both UX layers share identical logic — only the HIL (Human-in-the-Loop) handler differs. CLI uses `stdin`/`stdout` for prompts; Web uses WebSocket events.

## Public API

### Functions
#### `get_skills_dir() -> str`
- **Returns**: `str` — path to the skills directory.
- **Behavior**: Resolves the skills directory using a priority chain: Docker mount at `/app/skills` (if it exists) takes precedence over the configured `config.paths.skills_dir`.

#### `get_project_path() -> str`
- **Returns**: `str` — path to the project output directory.
- **Behavior**: Returns `config.paths.project_path`, which is resolved from environment variable > `config.yaml` > default.

#### `build_executor_state(cycle_id, project_name, spec_text, context_folder) -> WorkflowState`
- **Parameters**:
  - `cycle_id` (`str`, default `"1"`): Unique cycle identifier.
  - `project_name` (`str`, default `""`): Name of the project.
  - `spec_text` (`str`, default `""`): Path to spec or initial requirements text.
  - `context_folder` (`str`, default `""`): Path to existing codebase for discovery.
- **Returns**: `WorkflowState` — fully initialized state ready for graph execution.
- **Behavior**:
  1. Resolves the skills directory and builds a skill registry via `tools.loader.build_skill_registry`.
  2. Determines `skip_discover` based on whether `context_folder` is provided.
  3. Constructs and returns a `WorkflowState` with all fields populated, including pre-loaded `CycleMetrics` and `artifacts` containing the skill registry.

#### `get_graph()`
- **Returns**: Compiled LangGraph workflow.
- **Behavior**: Calls `build_graph()` and returns the compiled graph. Cached per-process.

### Classes
#### `WorkflowRunner`
- **Description**: Shared workflow runner for both CLI and Web modes. Orchestrates graph execution, streams phase transitions, and handles HIL (Human-in-the-Loop) gates at `DEFINE`, `PLAN`, and `VERIFY`.
- **Constructor**: `__init__()` — builds the graph via `get_graph()`.
- **Module-Level Attributes**:
  - `HIL_PHASES`: `{"DEFINE", "PLAN", "VERIFY"}` — phases that trigger human approval prompts.

##### `run_interactive(project_name, spec_text, context_folder, auto_approve)`
- **Parameters**:
  - `project_name` (`str`, default `""`): Name of the project being built.
  - `spec_text` (`str`, default `""`): Initial idea / requirements text.
  - `context_folder` (`str`, default `""`): Path to existing codebase for discovery.
  - `auto_approve` (`bool`, default `False`): If `True`, skip all HIL gates (CI/headless mode).
- **Behavior**:
  1. Builds initial state via `build_executor_state`.
  2. Logs whether DISCOVER is skipped (greenfield) or scanning a context folder.
  3. Runs `_astream_with_hil` in an `asyncio.run()` context, using `_hil_cli` as the HIL handler.
  4. Returns the final state chunk.

##### `_astream_with_hil(state, auto_approve, on_hil)` *(async)*
- **Parameters**:
  - `state` (`WorkflowState`): Current workflow state.
  - `auto_approve` (`bool`): If `True`, auto-approve all HIL gates.
  - `on_hil` (callable): HIL handler function called when approval is needed.
- **Behavior**:
  - Streams through the graph using `graph.astream(state, stream_mode="values")`.
  - Detects phase transitions and prints status messages.
  - When `human_approval_required` is set and the current phase is in `HIL_PHASES`:
    - If `auto_approve`: injects default interview notes and approval into state.
    - Otherwise: calls the `on_hil` handler to collect user input, then clears the flag.
  - Returns the last state chunk.

##### `_default_interview(state) -> str`
- **Parameters**:
  - `state` (`WorkflowState`): Current workflow state.
- **Returns**: `str` — auto-generated interview notes.
- **Behavior**: Produces a structured interview response with standard defaults (CRUD data model, RESTful API, Docker Compose deployment, etc.) when `auto_approve` is `True`.

##### `_hil_cli(phase, state) -> Optional[Dict[str, str]]`
- **Parameters**:
  - `phase` (`str`): Current phase name.
  - `state` (`WorkflowState`): Current state.
- **Returns**: `Optional[Dict[str, str]]` — user input data.
- **Behavior**: CLI handler for HIL. If phase is `DEFINE`, runs `_cli_interview`. Otherwise, prompts for simple `y/n` approval with optional feedback.

##### `_cli_interview() -> Dict[str, str]`
- **Returns**: `Dict[str, str]` — interview answers keyed by category plus `interview_notes` and `approved`.
- **Behavior**: Walks the user through nine interview questions (core behavior, data model, API surface, validation, UI template, integration, deployment, edge cases, non-functional requirements). Skips empty answers. Formats results as a structured dict with a joined `interview_notes` string.

---

## Dependencies / Used By
- **Imports**:
  - `sys`, `pathlib.Path`, `typing.Dict`, `typing.Optional`
  - `config.loader.config`
  - `graph.main.build_graph`
  - `graph.state.CycleMetrics`, `graph.state.WorkflowState`
  - `tools.loader.build_skill_registry`
  - `asyncio` (imported locally in `run_interactive`)
- **Used By**: `main.py`, `frontend/backend/workflow_bridge.py`

## Notes / Caveats
- The module adds the project root to `sys.path` at import time to ensure `config.loader` resolves correctly.
- `build_executor_state` is the single point of state initialization — both CLI and Web call it, ensuring identical starting conditions.
- The HIL handler is injected as a callback (`on_hil` parameter to `_astream_with_hil`), allowing the Web layer to swap in a WebSocket-based handler without duplicating execution logic.
- `auto_approve=True` produces default interview notes rather than empty values, preventing downstream nodes from blocking on missing data.
- Loop counts are managed by `graph/edges.py`, not by the executor.
