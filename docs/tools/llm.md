# `tools/llm.py`

## Purpose
Provides LLM integration with local vLLM (Qwen3.6-27B) using an OpenAI-compatible API through LangChain's `ChatOpenAI`. The module is designed for graceful degradation — it wraps imports in a try/except so that when `langchain-openai` is not installed, all public functions fall back to dry-run modes instead of raising import errors. This makes it safe to import from anywhere in the codebase regardless of the deployment environment.

## Public API

### Functions

#### `get_llm(model: str = None, base_url: str = None) -> ChatOpenAI | None`
- **Parameters**:
  - `model` (str, optional): LLM model name. Defaults to `LLM_MODEL` env var, then `"Qwen3.6-27B"`.
  - `base_url` (str, optional): API base URL. Defaults to `LLM_BASE_URL` env var, then `"http://localhost:8080/v1"`.
- **Returns**: `ChatOpenAI` instance or `None` — configured LLM client ready for `.invoke()`, or `None` if langchain_openai is unavailable.
- **Behavior**: Constructs a `ChatOpenAI` client using environment variables (`LLM_MODEL`, `LLM_BASE_URL`, `OPENAI_API_KEY`, `LLM_TEMPERATURE`) with sensible defaults. Returns `None` and prints a warning if the langchain_openai package is missing.

#### `invoke_skill(skill_content: str, task: str, context: str = "", llm=None) -> str`
- **Parameters**:
  - `skill_content` (str): Markdown content from a SKILL.md file containing instructions.
  - `task` (str): The specific task to execute.
  - `context` (str, optional): Additional context for the LLM. Defaults to `""`.
  - `llm` (ChatOpenAI, optional): Pre-configured LLM instance. Defaults to `None` (calls `get_llm()` internally).
- **Returns**: `str` — LLM response content, a dry-run summary, or an error message.
- **Behavior**: Combines the skill instructions (as a system prompt) with the task and context (as a user prompt), then invokes the LLM. The system prompt instructs the model to respond with actionable output including file paths, code snippets, and verification steps. Falls back to a `[DRY-RUN]` summary string when the LLM is `None`. Catches all exceptions and returns `[LLM ERROR]` prefixed messages.

### Module-Level Variables

- `_import_error` (str | None): Stores the `ImportError` message if `langchain_openai` fails to import. `None` on successful import. Used for diagnostic output when the module falls back to dry-run mode.

## Dependencies / Used By

- **Imports**: `os`, `langchain_openai.ChatOpenAI`, `langchain_core.messages.HumanMessage`, `langchain_core.messages.SystemMessage`
- **Used By**:
  - `graph/nodes/plan.py` — invokes planning skills
  - `graph/nodes/build.py` — invokes build/coding skills
  - `graph/nodes/define.py` — invokes interview and specification skills
  - `graph/nodes/seed_data.py` — invokes data seeding skills
  - `graph/nodes/reflect.py` — uses both `get_llm()` and `invoke_skill()`
  - `graph/nodes/ship.py` — invokes shipping/deployment skills
  - `graph/nodes/verify.py` — invokes verification/testing skills
  - `feedback/diff_engine.py` — generates config diffs via LLM

## Notes / Caveats

- The lazy-import pattern means `ChatOpenAI`, `HumanMessage`, and `SystemMessage` are set to `None` when the package is missing. Callers must check for `None` returns from `get_llm()` and handle dry-run mode.
- API key defaults to `"not-needed"` since local vLLM servers typically don't require authentication.
- `max_tokens` is hard-coded to `32768`; `temperature` defaults to `0.1` for deterministic output.
- `invoke_skill` accepts an `llm` parameter so callers can reuse a single client instance instead of creating a new one on each call (as seen in `graph/nodes/reflect.py`).
