# `graph/nodes/seed_data.py`

## Purpose
The SEED_DATA node populates the application database with seed data for testing. It runs after BUILD and before VERIFY to ensure the app has data for UAT. It follows a strict ordering: generate seed script via LLM → validate with AST parse → persist to disk → execute inside Docker → verify population. On failure at any step, it loops back to BUILD for retry.

## Public API

### Functions
#### `seed_data_node(state: dict) -> dict`
- **Parameters**: - `state` (dict): WorkflowState containing project_path, spec_refined, and implementation artifacts
- **Returns**: dict — updated WorkflowState with seed_script, seed_result or seed_errors, error, phase="SEED_DATA", next_phase="VERIFY" (or "BUILD" on failure)
- **Behavior**: Executes the seed data pipeline:
  1. **Resolve Docker project dir**: Calls `find_docker_project()` from build.py before any file writes.
  2. **Load seed skill**: Uses `ai-workflow-data-seeding` skill, or falls back to inline prompt specifying SQLAlchemy 2.0 async insert with deterministic data.
  3. **Generate seed script**: Invokes LLM to produce Python seed script.
  4. **AST validation**: Strips markdown fences, validates via `ast.parse()` — rejects non-Python output.
  5. **Persist**: Writes validated script to `{docker_proj}/app/seed.py`.
  6. **Execute**: Runs `python -m app.seed` inside the Docker container via `docker compose exec`.
  7. **Result**: On success, sets `next_phase="VERIFY"`. On failure (syntax error, execution error, timeout), sets `next_phase="BUILD"` with error context.

## Dependencies / Used By
- **Imports**: `os`, `ast`, `subprocess`, `tempfile`, `pathlib.Path`, `tools.loader.build_skill_registry`, `tools.llm.invoke_skill`, `graph.nodes.build.find_docker_project`
- **Used By**: `graph/main.py` (wires `seed_data_node` into LangGraph)

## Notes / Caveats
- **Critical ordering**: The module enforces a strict sequence — generate first, then validate, then persist, then execute. Attempting to load before generate is explicitly forbidden (documented in module docstring).
- **AST validation**: Catches LLM output that isn't valid Python (e.g., markdown-wrapped non-code, explanations mixed with code).
- **Fallback skill**: If `ai-workflow-data-seeding` skill is not found, uses an inline prompt that assumes a specific data model (vehicles, users, dealerships, bookings, orders). This may need customization for different projects.
- **Docker execution**: Runs inside the running container from BUILD phase; requires the container to still be up.
- **Timeout**: 60-second timeout for seed script execution.
- **Idempotency**: The inline fallback prompt instructs the LLM to make the script idempotent (INSERT OR IGNORE or check-first pattern).
