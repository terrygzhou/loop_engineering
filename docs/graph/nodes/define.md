# `graph/nodes/define.py`

## Purpose
The DEFINE node elicits requirements, generates a structured specification, and designs API contracts. It runs three LLM-driven skills in sequence (interview-me → speckit-specify → api-and-interface-design), each building on the previous output. It also queries ChromaDB for historical lessons learned from past cycles and feeds them into the context. At the end, it computes a `spec_confidence` metric (0.0–1.0) derived from the actual quality of the generated artifacts rather than a hardcoded value.

## Public API

### Functions
#### `_load_feedback_context(state: dict) -> str`
- **Parameters**: - `state` (dict): WorkflowState containing project_name and project_context
- **Returns**: str — formatted text block of historical lessons learned, or empty string if unavailable
- **Behavior**: Queries ChromaDB for the 3 most similar historical patterns. Formats results as `[Past Cycle N]` entries with similarity distance. Gracefully degrades to empty string if ChromaDB is unavailable or throws an exception.

#### `_estimate_spec_confidence(artifacts: dict) -> float`
- **Parameters**: - `artifacts` (dict): dict of named artifacts (spec_refined, api_contract, interview_notes)
- **Returns**: float (0.0–1.0) — confidence score derived from artifact quality
- **Behavior**: Scores based on artifact presence and content:
  - Refined spec > 100 chars: +0.3
  - API contract > 50 chars: +0.2
  - Interview notes > 50 chars: +0.15
  - Spec mentions acceptance criteria keywords: +0.15
  - Spec mentions edge case keywords: +0.1
  - Spec mentions error handling keywords: +0.1
  - Capped at 1.0

#### `define_node(state: dict) -> dict`
- **Parameters**: - `state` (dict): WorkflowState containing project_name, spec_path, and project_context from DISCOVER
- **Returns**: dict — updated WorkflowState with artifacts (interview_notes, spec_refined, api_contract), metrics (spec_confidence), phase="DEFINE", next_phase="PLAN"
- **Behavior**:
  1. Captures and sanitizes project_name, persists to config.
  2. Loads skill registry from state or builds from disk.
  3. Loads project_context from DISCOVER (if available) and historical feedback from ChromaDB.
  4. Runs interview-me skill for adaptive requirement elicitation.
  5. Runs speckit-specify to generate structured spec with traceability.
  6. Runs api-and-interface-design for contract-first interface design.
  7. Derives `spec_confidence` from actual artifact quality.

## Dependencies / Used By
- **Imports**: `os`, `re`, `tools.loader.build_skill_registry`, `tools.loader.find_skills_by_trigger`, `tools.llm.invoke_skill`, `config.loader.config`, `config.prompt_templates`, `feedback.chroma_client.get_chroma_client`, `feedback.chroma_client.query_patterns`
- **Used By**: `graph/main.py` (wires `define_node` into LangGraph)

## Notes / Caveats
- **Project name sanitization**: Rejects names with characters outside `[a-zA-Z0-9_-]`, replacing them with underscores.
- **Greenfield mode**: If DISCOVER was skipped, `project_context` will be empty; the node logs a warning but proceeds.
- **Spec confidence**: Used by `graph/edges.py` as a quality gate — if below `min_spec_confidence` threshold, DEFINE loops back.
- **Historical feedback**: Non-blocking — failures to connect to ChromaDB are caught and logged as warnings.
- **Prompt templates**: Task prompts for `interview_me` and `speckit_specify` are imported from `config.prompt_templates`.
