# `graph/nodes/reflect.py`

## Purpose
The REFLECT node is the self-improvement loop closure point. It analyzes the completed cycle, compares against historical patterns from ChromaDB and file-based storage, generates proposed skill configuration updates via a meta-agent, requests human approval via CLI, and archives feedback for future cycles. If changes are approved, it applies config diffs and commits via git-workflow.

## Public API

### Functions
#### `reflect_node(state: dict) -> dict`
- **Parameters**: - `state` (dict): WorkflowState containing cycle_id, metrics, artifacts, and feedback
- **Returns**: dict — updated WorkflowState with proposed_diffs, optional git_commit, config_version, phase="REFLECT", next_phase="END"
- **Behavior**: Executes the full reflection pipeline:
  1. **Record cycle**: Saves cycle data via `FeedbackAggregator`.
  2. **Load guardrails**: Reads `guardrails.yaml` for change constraints.
  3. **Query historical patterns**: ChromaDB first, with file-based fallback via `FeedbackAggregator`.
  4. **Store current pattern**: Archives the completed cycle in ChromaDB for future reflection.
  5. **Generate diffs**: Uses meta-agent (via `generate_config_diffs`) to propose skill config changes based on cycle analysis.
  6. **Dry-run validation**: Validates proposed diffs before presenting to human.
  7. **Human approval gate**: Prompts via CLI (`input()`) for approval; applies changes and runs git-workflow if approved.
  8. **Update config version**: Sets `config_version` to `{cycle_id}-reflected`.

## Dependencies / Used By
- **Imports**: `os`, `json`, `yaml`, `tools.loader.build_skill_registry`, `tools.llm.get_llm`, `tools.llm.invoke_skill`, `feedback.aggregator.FeedbackAggregator`, `feedback.diff_engine.generate_config_diffs`, `feedback.diff_engine.dry_run_validation`, `feedback.diff_engine.apply_yaml_diff` (imported inline), `feedback.chroma_client.get_chroma_client`, `feedback.chroma_client.store_pattern`, `feedback.chroma_client.query_patterns`
- **Used By**: `graph/main.py` (wires `reflect_node` into LangGraph)

## Notes / Caveats
- **Human-in-the-loop (HIL)**: Supports two modes via `HIL_MODE` env var — "cli" (default, uses `input()`) and "telegram" (stubs poll-based approval, not fully implemented).
- **EOFError/KeyboardInterrupt**: Caught during CLI approval and treated as rejection.
- **Dry-run validation**: Blocks changes if `dry_run_validation(diffs)` fails.
- **Git workflow**: If `git-workflow` skill is not available, logs a warning but does not block.
- **Guardrails**: Loaded from `GUARDRAILS_PATH` env var (default `./config/guardrails.yaml`); if missing, proceeds with empty guardrails.
- **ChromaDB fallback**: If ChromaDB is unavailable, falls back to file-based historical pattern query.
- **Loop closure**: This is always the last node before END in the graph; SHIP → REFLECT → END.
