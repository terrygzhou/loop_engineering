# `feedback/diff_engine.py`

## Purpose
The diff engine analyzes feedback and metrics accumulated across development cycles to generate proposed configuration updates. It serves as the bridge between the **REFLECT** node's analysis and actual configuration changes, supporting both YAML config diffs and prompt template diffs. Provides LLM-driven diff generation (when an LLM is available), dry-run validation against security guardrails, and safe application of changes to config files and prompt templates.

## Public API

### Functions

#### `generate_config_diffs(cycle_records: list, guardrails: dict, llm=None) -> dict`
- **Description**: Analyzes development cycle metrics and feedback to generate proposed configuration changes. Aggregates key metrics (review revisions, security findings, spec confidence) across all cycles, then invokes an LLM to propose up to 3 config changes with rationale and risk levels. In dry-run mode (no LLM provided), returns a placeholder response.
- **Parameters**:
  - `cycle_records` (`list`): List of cycle record dictionaries, each containing a `metrics` key with sub-metrics.
  - `guardrails` (`dict`): Guardrails configuration dictionary (from `config/guardrails.py`).
  - `llm` (optional): LangChain LLM instance for analysis. If `None`, runs in dry-run mode.
- **Returns**: `dict` — Dictionary with `overall_assessment` (str), `changes` (list of change dicts with `skill`, `change`, `rationale`, `risk_level`), and `risk_level` (str: "none", "low", "medium", "high", "unknown", "error").
- **Side Effects**: Prints warnings for dry-run mode, parse failures, and LLM invocation errors. Makes LLM API calls when `llm` is provided.

#### `dry_run_validation(diffs: dict) -> bool`
- **Description**: Validates proposed changes against security guardrails before human approval. Scans change descriptions for security-sensitive keywords (`auth`, `payment`, `billing`, `secret`, `api_key`) combined with high risk level. Returns `False` if any security-sensitive high-risk change is detected.
- **Parameters**:
  - `diffs` (`dict`): Diff dictionary with a `changes` key containing a list of change dicts.
- **Returns**: `bool` — `True` if safe to proceed, `False` if security-sensitive changes are blocked.
- **Side Effects**: Prints block messages for rejected changes.

#### `apply_yaml_diff(config_path: str, diffs: dict) -> bool`
- **Description**: Applies config diffs to a YAML file. Parses change descriptions using regex patterns to detect threshold updates, key additions, removals, and generic value modifications. If the target skill is a prompt template (`interview_me`, `speckit_specify`, `api_and_interface_design`), delegates to `apply_prompt_diff`. Writes the modified YAML back to disk.
- **Parameters**:
  - `config_path` (`str`): Path to the YAML configuration file to modify.
  - `diffs` (`dict`): Diff dictionary with `changes` list. Each change has `skill`, `change` (description), and `rationale`.
- **Returns**: `bool` — `True` on success, `False` on failure.
- **Side Effects**: Reads and writes the YAML file on disk. Prints progress messages for each applied change. Stamps `_last_updated` with rationale on each modified section.

#### `apply_prompt_diff(template_name: str, diffs: dict) -> bool`
- **Description**: Applies prompt template diffs from REFLECT analysis. Reads `config/prompt_templates.py`, finds the target template by name using regex, and replaces its content with the LLM-suggested change description. Writes the modified Python file back to disk.
- **Parameters**:
  - `template_name` (`str`): Name of the template variable to update (e.g., `"interview_me"`, `"speckit_specify"`, `"api_and_interface_design"`).
  - `diffs` (`dict`): Diff dictionary with `changes` list containing the new template content.
- **Returns**: `bool` — `True` on success, `False` on failure.
- **Side Effects**: Reads and writes `config/prompt_templates.py` on disk. Uses `os.path` to locate the file relative to this module.

#### `_find_config_target(config: dict, skill_name: str)` (private)
- **Description**: Finds a config entry by name, searching top-level keys and one level of nesting.
- **Parameters**:
  - `config` (`dict`): Configuration dictionary to search.
  - `skill_name` (`str`): Name of the skill/config key to find.
- **Returns**: `dict` or value, or `None` if not found.
- **Side Effects**: None (read-only lookup).

#### `_parse_numeric(value: str)` (private)
- **Description**: Attempts to parse a string as `int` or `float`. Returns `None` if the value is not numeric.
- **Parameters**:
  - `value` (`str`): String to parse.
- **Returns**: `int`, `float`, or `None`.
- **Side Effects**: None.

### Module-Level Variables
- None (all state is passed as parameters).

---

## Dependencies / Used By
- **Imports**: `os`, `re`, `json`, `yaml`, `typing.Dict`, `typing.List`, `typing.Any`, `importlib` (inside `apply_prompt_diff`), `inspect` (inside `apply_prompt_diff`), `langchain_core.messages` (inside `generate_config_diffs`, lazy import).
- **Used By**: `graph/nodes/reflect.py` (calls `generate_config_diffs` and `dry_run_validation` as part of the REFLECT phase).

## Notes / Caveats
- `generate_config_diffs` requires a LangChain LLM to produce meaningful results. Without one, it returns a dry-run placeholder.
- The LLM is prompted to return JSON only, but the code handles parse failures gracefully.
- `apply_yaml_diff` uses regex-based parsing of LLM-generated change descriptions, so it depends on the LLM using specific phrasing patterns (e.g., "threshold X from A to B", "add X = Y", "remove X").
- `apply_prompt_diff` directly rewrites a Python source file using regex replacement. The triple-quoted string pattern `variable_name = """..."""` must be matchable by the regex `variable_name\s*=\s*"""[^"]*"""` — note this regex does not handle escaped quotes within the template.
- Both apply functions are destructive — they modify files in place with no rollback or backup mechanism.
- Security-sensitive keyword detection in `dry_run_validation` is keyword-based and case-insensitive; it may produce false positives for benign uses of words like "secret" in non-security contexts.
