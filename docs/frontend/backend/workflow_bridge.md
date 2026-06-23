# `frontend/backend/workflow_bridge.py`

## Purpose
The Workflow Bridge connects the Loop Engineering LangGraph workflow engine to the UI backend. It implements a Human-In-The-Loop (HIL) flow where the engine pauses at key phases (DEFINE, PLAN, VERIFY) to solicit user input through structured, skill-driven interview questions. It streams real-time progress events over WebSocket, maintains per-phase state tracking, and gracefully falls back to a simulated workflow when the real LangGraph imports are unavailable. The bridge is the central coordination layer between the frontend UI and the backend workflow execution.

## Public API

### Classes

#### `WorkflowBridge`
- **Description**: Bridges the Loop Engineering LangGraph workflow with the UI. Provides skill-driven interviews, real-time WebSocket streaming, HIL support at DEFINE/PLAN/VERIFY phases, and a simulated fallback mode when the real workflow is unavailable. Captures node-level events from LangGraph's `astream()`.
- **Constructor**: `__init__()` — Initializes all state to defaults: `status="idle"`, empty phase list, empty event log, no WebSocket clients, and pre-populates `phase_states` for all 8 phases as `"pending"`.

- **Class Attributes**:
  - `PHASES` (List[str]): Ordered list of workflow phases: `["DISCOVER", "DEFINE", "PLAN", "BUILD", "SEED_DATA", "VERIFY", "SHIP", "REFLECT"]`.
  - `HIL_PHASES` (Set[str]): Phases that require human input: `{"DEFINE", "PLAN", "VERIFY"}`.

- **Methods**:

  #### `run(spec_text="", project_name="", project_path="", context_folder="")`
  - **Parameters**:
    - `spec_text` (str): Project requirements/specification text.
    - `project_name` (str): Name of the project.
    - `project_path` (str): Output path for project artifacts (unused in current implementation).
    - `context_folder` (str): Path to existing codebase/docs; empty skips DISCOVER.
  - **Returns**: Nothing (async)
  - **Behavior**: Main entry point. Stores parameters, calls `_try_import_real()` to check for the real workflow, then delegates to either `run_real()` or `run_simulated()` based on availability.

  #### `run_simulated()`
  - **Parameters**: None
  - **Returns**: Nothing (async)
  - **Behavior**: Simulated workflow for testing. Acquires the internal lock, increments the cycle counter, then iterates through each phase (skipping DISCOVER if no context folder). For each phase, simulates 3 steps with 0.5s delays, generates a mock artifact, sends a skill-driven interview at DEFINE, and waits for user input at DEFINE/PLAN/VERIFY via `_wait_for_user_input()`. Broadcasts events throughout.

  #### `run_real()`
  - **Parameters**: None
  - **Returns**: Nothing (async)
  - **Behavior**: Runs the actual LangGraph workflow using the shared `WorkflowRunner` from `graph.executor`. Builds state via `_build_executor_state()` (guaranteeing identical state as the CLI). Pre-emits DISCOVER skip events if `skip_discover` is set. Streams node executions from `runner.graph.astream()` in `"values"` mode, capturing artifacts and detecting phase transitions. Triggers the skill-driven interview and HIL waits at DEFINE/PLAN/VERIFY. Falls back to `run_simulated()` if the real workflow is unavailable.

  #### `_try_import_real()`
  - **Parameters**: None
  - **Returns**: Nothing
  - **Behavior**: Attempts to import `build_graph`, `WorkflowState`, `CycleMetrics`, and `build_skill_registry` from the `loop_engineering` package (resolving the parent path). If successful, stores references and sets `_use_real_workflow = True`. On failure, logs the error and keeps simulated mode.

  #### `_build_executor_state(cycle_id, project_name, spec_text, context_folder)`
  - **Parameters**:
    - `cycle_id` (str): Unique cycle identifier.
    - `project_name` (str): Project name.
    - `spec_text` (str): Specification text.
    - `context_folder` (str): Context folder path.
  - **Returns**: `Dict` — Workflow state dict built by the shared executor.
  - **Behavior**: Delegates to `graph.executor.build_executor_state()` to ensure the bridge uses the exact same state construction as the CLI.

  #### `_make_event(phase, action, message, data=None)`
  - **Parameters**:
    - `phase` (str): Phase name.
    - `action` (str): Action type (e.g., "started", "progress", "completed", "error", "artifact", "interview", "waiting").
    - `message` (str): Human-readable message.
    - `data` (Optional[Dict]): Additional structured data.
  - **Returns**: `Dict` — Event dict with timestamp, phase, action, message, and data.
  - **Behavior**: Creates a timestamped event dict. Used internally by `add_event()`.

  #### `add_event(phase, action, message, data=None)`
  - **Parameters**: Same as `_make_event()`.
  - **Returns**: `Dict` — The created event dict.
  - **Behavior**: Creates event via `_make_event()`, appends to `self.events`, and updates the corresponding phase state in `self.phase_states` (maps actions to status transitions: started→running, waiting→waiting, completed→complete, error→error).

  #### `broadcast(ev)`
  - **Parameters**: - `ev` (Dict): Event dict to broadcast.
  - **Returns**: Nothing (async)
  - **Behavior**: JSON-serializes the event and sends it to all connected WebSocket clients. Removes dead clients from the list on failure.

  #### `connect_ws(websocket)`
  - **Parameters**: - `websocket` (WebSocket): Accepted WebSocket connection.
  - **Returns**: Nothing (async)
  - **Behavior**: Accepts the connection, adds it to `websocket_clients`, and backfills the last 50 events so the new client sees recent history.

  #### `disconnect_ws(websocket)`
  - **Parameters**: - `websocket` (WebSocket): Disconnected WebSocket.
  - **Returns**: Nothing
  - **Behavior**: Removes the WebSocket from `websocket_clients` if present.

  #### `_send_interview(phase)`
  - **Parameters**: - `phase` (str): Phase name (typically "DEFINE").
  - **Returns**: Nothing (async)
  - **Behavior**: Creates an "interview" event containing the `INTERVIEW_QUESTIONS` list and broadcasts it to the UI for structured form rendering.

  #### `_wait_for_user_input(phase)`
  - **Parameters**: - `phase` (str): Phase awaiting input.
  - **Returns**: `Any` — The user's input value, or `None` on timeout.
  - **Behavior**: Sets status to "waiting" and broadcasts a "waiting" event. Polls `self.user_inputs` for up to 1800 seconds (30 minutes) at 1-second intervals. Returns the input when received or `None` on timeout (auto-approval).

### Module-Level Variables
- `INTERVIEW_QUESTIONS` (List[Dict]): 9 skill-driven interview question categories derived from `interview-me SKILL.md`. Each entry has `category`, `label`, `question`, `placeholder`, and `required` fields. Categories: `core_behavior`, `data_model`, `api_surface`, `validation`, `ui_template`, `integration`, `deployment`, `edge_cases`, `non_functional`.

---

## Dependencies / Used By
- **Imports**: `asyncio`, `json`, `os`, `sys`, `datetime`, `pathlib.Path`, `typing` (Any, Dict, List, Optional), `fastapi.WebSocket`
- **Used By**: `frontend/backend/app.py` (imports `WorkflowBridge` as the sole dependency)

## Notes / Caveats
- **Dual-mode operation**: The bridge tries to import the real workflow on startup and at runtime via `_try_import_real()`. If imports fail, it falls back to `run_simulated()` which mimics the same event flow with mock data. This allows the UI to be developed and tested without the full LangGraph engine installed.
- **Shared state with CLI**: `run_real()` delegates to `graph.executor.WorkflowRunner` and `build_executor_state()` to guarantee the bridge uses the identical graph and state construction as the CLI — no duplicate or divergent state logic.
- **30-minute timeout**: `_wait_for_user_input()` auto-approves after 1800 polls (30 minutes). This prevents the workflow from hanging indefinitely if the user disconnects.
- **Event backfill**: New WebSocket clients receive the last 50 events on connect, ensuring late-joining clients see recent history.
- **WebSocket cleanup**: `broadcast()` silently removes dead clients (those that throw on `send_text`) to prevent accumulating stale connections.
- **Instance-level state**: All state (events, phase_states, user_inputs) is instance-level on the `WorkflowBridge`. Since `app.py` creates a single shared instance, this works for single-user setups but would need multi-tenant isolation for concurrent users.
- **Interview questions are static**: `INTERVIEW_QUESTIONS` is a hardcoded module-level constant. The skill-driven design means these questions map to the `interview-me` skill's categories, but they are not dynamically loaded from the skill at runtime.
