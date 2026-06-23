# `config/prompt_templates.py`

## Purpose
Defines the ToT (Tree of Thought) + CoT (Chain of Thought) prompt templates used during the **DEFINE** phase of the Loop Engineering workflow engine. Each template guides the LLM through a structured reasoning phase — evaluating multiple candidate approaches with scores — followed by a sequential execution phase with step-by-step actions. These templates are designed to be updated by the **REFLECT** node between cycles, enabling the engine to self-improve its prompting strategy over time.

## Public API

### Module-Level Variables
- `interview_me` (str): Prompt template for the interview sub-phase of DEFINE. Directs the LLM to conduct a structured user interview. ToT phase evaluates three angles (user-centric, system-centric, risk-centric) on a 1–5 scale. CoT execution follows five steps: persona identification, workflow mapping (one question at a time), acceptance criteria (Given/When/Then), risk probing, and success metrics. Uses `{spec_path}` as an f-string placeholder.
- `speckit_specify` (str): Prompt template for specification generation in DEFINE. ToT phase evaluates three scope interpretations (Minimal, Standard, Extended). CoT execution follows seven steps: summary, user stories with acceptance criteria, edge cases, non-functional requirements, dependencies, out-of-scope items, and open questions. Uses `{spec_path}` as an f-string placeholder.
- `api_and_interface_design` (str): Prompt template for interface and API design. ToT phase evaluates three architecture approaches (Monolithic, Modular, Distributed). CoT execution follows seven steps: REST API definition, CLI definition, database schema, event bus definition, error responses, contract guarantees (idempotency, versioning, backward-compatibility), and module ownership mapping. Emphasizes realistic data types and field names over placeholder schemas.

---

## Dependencies / Used By
- **Imports**: None (pure data module — no imports).
- **Used By**: `graph/nodes/define.py` (loads templates for the DEFINE phase), `feedback/diff_engine.py` (`apply_prompt_diff` reads and rewrites this file to apply LLM-generated template updates).

## Notes / Caveats
- Templates are stored as module-level string constants, not as functions, so they can be read and rewritten as text by the diff engine.
- Each template uses `{spec_path}` as an f-string placeholder; the DEFINE node formats this before sending to the LLM.
- The `apply_prompt_diff` function in `feedback/diff_engine.py` uses regex to locate and replace template text in the source file, so template names must not contain regex-special characters.
- No validation or versioning is applied to template content; any LLM-generated update is applied verbatim.
- Templates are intentionally opinionated (ToT + CoT pattern) and not designed to be swapped with arbitrary prompt text.
