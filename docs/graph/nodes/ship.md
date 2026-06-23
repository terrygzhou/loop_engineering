# `graph/nodes/ship.py`

## Purpose
The SHIP node handles the final deployment phase: adding observability (logging, health endpoints, RED metrics), running a pre-launch checklist (feature flags, rollback plan, staging verification), deploying via Docker Compose, and committing changes via git workflow. It skips redundant Docker rebuilds if BUILD already deployed and verified the container.

## Public API

### Functions
#### `ship_node(state: dict) -> dict`
- **Parameters**: - `state` (dict): WorkflowState containing project_path, artifacts, cycle_id, and metrics
- **Returns**: dict — updated WorkflowState with artifacts (observability, launch_checklist, deploy_logs, git_log), config_version, phase="SHIP", next_phase="REFLECT"
- **Behavior**: Executes the shipping pipeline:
  1. **Observability**: Invokes `observability-and-instrumentation` skill to add structured logging, health endpoints, and RED metrics.
  2. **Pre-launch checklist**: Invokes `shipping-and-launch` skill for feature flags, rollback plan, and staging verification.
  3. **Deploy**: If BUILD already deployed (`build_status == "pass"`), skips Docker rebuild and just does a health check. Otherwise, invokes `docker-compose-deployment` skill for full `docker compose up -d --build`.
  4. **Git workflow**: Invokes `git-workflow` skill to create atomic, conventional commits for the cycle.
  5. **Metrics**: Sets `launch_success=True` and `config_version=cycle_id`.

## Dependencies / Used By
- **Imports**: `os`, `tools.loader.build_skill_registry`, `tools.llm.invoke_skill`, `subprocess` (imported inline for health check)
- **Used By**: `graph/main.py` (wires `ship_node` into LangGraph)

## Notes / Caveats
- **Build status shortcut**: Checks `state["artifacts"]["build_status"]` to avoid redundant Docker builds. When BUILD already compiled and deployed, only a `curl` health check is performed.
- **Health check port**: Hardcoded to `localhost:8010`, matching the BUILD node's health check.
- **Git workflow**: The git-commit task includes the full cycle diff data in its prompt context.
- **No rollback**: Unlike BUILD, SHIP does not implement rollback logic — it assumes the build is stable after VERIFY passed.
- **Always goes to REFLECT**: SHIP is the last production phase before the self-improvement loop (REFLECT).
