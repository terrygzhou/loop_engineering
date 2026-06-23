# `config/guardrails.py`

## Purpose
Loads quality thresholds from a YAML configuration file at runtime, providing a centralized guardrails system used by edge routing, verification, and reflection logic. Falls back to built-in defaults when the YAML file is missing or keys are absent. This module enables the REFLECT node to update thresholds between cycles, allowing the engine to adapt its quality gates based on historical performance.

## Public API

### Functions

#### `load_guardrails() -> Dict[str, Any]`
- **Parameters**: None
- **Returns**: `Dict[str, Any]` — Dictionary containing `quality_thresholds` (merged with built-in defaults), `security_sensitive`, `feedback`, `reflection`, `llm`, and any extra top-level keys from the YAML file.
- **Behavior**: Calls `_resolve_path()` to locate the guardrails YAML file, reads and parses it with `yaml.safe_load()`, then merges the file's `quality_thresholds` over `_DEFAULTS` (YAML wins). Returns a dict with the merged thresholds plus all other top-level keys from the file. Silently falls back to `_DEFAULTS` for all values if the file is missing or unreadable.

#### `get_threshold(name: str, default=None) -> Any`
- **Parameters**:
  - `name` (str): The threshold key name (e.g., `"min_spec_confidence"`, `"max_latency_ms"`).
  - `default` (Any, optional): Custom fallback value if the threshold is not found. If `None`, uses the built-in default from `_DEFAULTS`.
- **Returns**: `Any` — The resolved threshold value (typically `float` or `int`).
- **Behavior**: If `default` is `None`, looks up the key in `_DEFAULTS`. Raises `KeyError` if the name is unknown (not in `_DEFAULTS` and no custom default). Calls `load_guardrails()` on every invocation (no caching) and retrieves the value from the merged `quality_thresholds` dict.

#### `_resolve_path() -> str` (private)
- **Parameters**: None
- **Returns**: `str` — Path to the guardrails YAML file.
- **Behavior**: Resolves path using priority: `GUARDRAILS_PATH` environment variable > `guardrails.yaml` alongside this module file > `./config/guardrails.yaml` as final fallback.

### Module-Level Variables
- `_DEFAULTS` (Dict[str, Any]): Built-in fallback thresholds: `min_spec_confidence` (0.9), `max_arch_uncertainty` (0.8), `max_security_findings` (0), `max_review_revisions` (2), `uat_pass_rate` (0.95), `max_latency_ms` (500), `max_test_flakiness_rate` (0.1).

---

## Dependencies / Used By
- **Imports**: `os`, `pathlib.Path`, `typing.Any`, `typing.Dict`, `yaml`
- **Used By**: `graph/edges.py` (thresholds for routing decisions), `graph/nodes/verify.py` (verification gates), `graph/nodes/reflect.py` (reads and may update thresholds between cycles), `feedback/diff_engine.py` (receives guardrails dict for diff generation)

## Notes / Caveats
- `get_threshold()` reloads the YAML on every call — no internal caching. For high-frequency access, call `load_guardrails()` once and read from the returned dict.
- The YAML merge strategy is: YAML values override `_DEFAULTS`. Keys present in YAML but absent from `_DEFAULTS` are still returned.
- The module tolerates a completely missing YAML file by falling back to `_DEFAULTS` for all threshold lookups.
