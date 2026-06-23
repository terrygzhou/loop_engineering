# `frontend/backend/app.py`

## Purpose
The FastAPI application server for the Loop Engineering UI backend. It exposes REST endpoints and a WebSocket channel for real-time progress streaming, delegates all workflow execution to a `WorkflowBridge` instance, and serves the static frontend. The app handles CORS, Pydantic model validation, and startup-time detection of whether the real LangGraph workflow is importable or whether it should fall back to simulated mode.

## Public API

### FastAPI App
#### `app` (FastAPI)
- **Description**: The root FastAPI application instance, configured with CORS middleware (all origins, methods, and headers allowed).

### Startup Event
#### `startup()`
- **Parameters**: None
- **Returns**: Nothing (async)
- **Behavior**: Prints startup confirmation. Calls `bridge._try_import_real()` to determine if the real LangGraph workflow is available. Logs whether the backend will use real or simulated mode.

### REST Endpoints

#### `serve_frontend()` → `HTMLResponse`
- **Parameters**: None
- **Returns**: `HTMLResponse` — The contents of `static/index.html`, or a fallback `<h1>Frontend not found</h1>`.
- **Behavior**: Serves the main frontend page at `GET /`. Reads the HTML file from `parent/static/index.html` relative to this module.

#### `get_status()` → `WorkflowResponse`
- **Parameters**: None
- **Returns**: `WorkflowResponse` — Current workflow status including phase, cycle, phase states, pending user input, and the last 50 events.
- **Behavior**: Returns a snapshot of the bridge's state for the UI to render its progress view.

#### `get_phases()` → `List[Dict]`
- **Parameters**: None
- **Returns**: `List[Dict]` — List of phase state dictionaries from the bridge.
- **Behavior**: Returns details for every phase (DISCOVER through REFLECT).

#### `start_workflow(req: StartRequest)` → `Dict`
- **Parameters**: - `req` (StartRequest): Contains `project_name`, `spec`, and `context_folder`.
- **Returns**: `Dict` — `{"status": "started", "cycle": int}`.
- **Behavior**: Fires off `bridge.run()` as a background `asyncio.create_task()` and returns immediately so the caller is not blocked.

#### `submit_input(user_input: UserInput)` → `Dict`
- **Parameters**: - `user_input` (UserInput): Contains `phase`, `input_type`, and `value`.
- **Returns**: `Dict` — `{"status": "received", "phase": str}`.
- **Behavior**: Stores the user input in `bridge.user_inputs[phase]` so the bridge's `_wait_for_user_input()` loop can pick it up and unblock.

### WebSocket Endpoint

#### `websocket_endpoint(websocket: WebSocket)`
- **Parameters**: - `websocket` (WebSocket): The incoming WebSocket connection.
- **Returns**: Nothing (async generator — runs until disconnect).
- **Behavior**: Calls `bridge.connect_ws()` to accept the connection and backfill recent events. Then loops with `asyncio.sleep(1)` until the client disconnects, at which point calls `bridge.disconnect_ws()`.

### Models

#### `UserInput(BaseModel)`
- **Description**: Pydantic model for user input submissions.
- **Fields**:
  - `phase` (str): The workflow phase this input targets.
  - `input_type` (str): The type of input (e.g., "review", "interview").
  - `value` (Any): The actual input value.

#### `StartRequest(BaseModel)`
- **Description**: Pydantic model for initiating a workflow cycle.
- **Fields**:
  - `project_name` (str): Name of the project (default: `""`).
  - `spec` (str): Project requirements/specification text.
  - `context_folder` (str): Path to existing codebase/docs; empty string skips DISCOVER.

#### `WorkflowResponse(BaseModel)`
- **Description**: Pydantic model for the current workflow status response.
- **Fields**:
  - `status` (str): Current status (`idle`, `running`, `waiting`, `complete`, `error`).
  - `phase` (str): Current phase name.
  - `cycle` (int): Current cycle number.
  - `phases` (List[Dict[str, Any]]): Per-phase state details.
  - `waiting_for` (Optional[str]): Phase awaiting user input, if any.
  - `messages` (List[Dict[str, Any]]): Recent event log (last 50).

### Module-Level Variables
- `bridge` (WorkflowBridge): Single shared instance of the workflow bridge, used by all endpoints.
- `static_path` (Path): Path to the `static/` directory, used for mounting static files.

---

## Dependencies / Used By
- **Imports**: `asyncio`, `sys`, `pathlib.Path`, `typing` (Any, Dict, List, Optional), `fastapi` (FastAPI, WebSocket, WebSocketDisconnect, CORSMiddleware, StaticFiles, HTMLResponse), `pydantic` (BaseModel, Field), `backend.workflow_bridge` (WorkflowBridge)
- **Used By**: Direct entry point via `uvicorn.run()`; not imported by other modules in the project.

## Notes / Caveats
- **Single bridge instance**: `bridge` is a module-level singleton shared across all connections. Concurrent workflow starts are guarded by the bridge's internal `asyncio.Lock`, but concurrent WebSocket clients all share the same event stream.
- **Fire-and-forget workflow**: `start_workflow` spawns `bridge.run()` as a background task via `asyncio.create_task()`. The HTTP response returns immediately; progress is delivered over WebSocket or via polling `/api/status`.
- **CORS is wide open**: All origins, methods, and headers are allowed. This is convenient for development but should be tightened for production.
- **Import fallback**: The module tries `from backend.workflow_bridge import WorkflowBridge` first, then falls back to adding the module's own directory to `sys.path`. This handles both package-style and direct `python app.py` execution.
- **Static file serving**: The `/static` mount only happens if the `static/` directory exists (one level above `backend/`). The root `/` handler also checks for the file before returning a fallback.
