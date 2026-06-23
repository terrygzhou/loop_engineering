# `config/loader.py`

## Purpose
Central configuration loader for Loop Engineering, implementing a three-tier resolution strategy (environment variables > `config.yaml` > built-in defaults) for all settings. Manages the project name lifecycle — initially a placeholder until the DEFINE node captures a real name, then persists it to disk. Provides a singleton `config` object consumed by every node, edge, and utility module throughout the workflow engine.

## Public API

### Functions

#### `_load_yaml(path: str) -> Dict[str, Any]` (private)
- **Parameters**:
  - `path` (str): Path to the YAML file.
- **Returns**: `Dict[str, Any]` — Parsed YAML content, or `{}` on failure.
- **Behavior**: Checks if the file exists via `Path.exists()`, then reads and parses with `yaml.safe_load()`. Returns empty dict if the file is missing, invalid, or any exception occurs.

#### `_resolve(env_var: str | None, config: Dict[str, Any], key_path: str, default: str) -> str` (private)
- **Parameters**:
  - `env_var` (str | None): Environment variable name to check first. If `None`, skips env var resolution.
  - `config` (Dict[str, Any]): Dictionary to search for the nested key.
  - `key_path` (str): Dot-separated key path (e.g., `"paths.project_name"`, `"workflow.hil_mode"`).
  - `default` (str): Fallback value if neither env var nor config key exists.
- **Returns**: `str` — Resolved string value.
- **Behavior**: Checks the environment variable first (highest priority). Then walks the nested key path through the config dict using dot-notation splitting. Falls back to `default` if neither source provides a value. Returns `str` via `str()` conversion for config values.

#### `_save_yaml(path: str, data: Dict[str, Any])` (private)
- **Parameters**:
  - `path` (str): Destination file path.
  - `data` (Dict[str, Any]): Data to serialize.
- **Returns**: Nothing
- **Behavior**: Creates parent directories with `mkdir(parents=True, exist_ok=True)`, then writes the dict to YAML using `yaml.dump()` with `default_flow_style=False` and `sort_keys=False`.

### Classes

#### `Config`
- **Description**: Singleton configuration object. Read attributes directly via `config.paths.*` and `config.workflow.*`. Call `set_project_name()` after the DEFINE node captures the project name.

##### Constructor
- No explicit `__init__`; class attributes are set at class definition time using `_resolve()` with the loaded `_config` dict and built-in defaults.

##### `Config.Paths` (inner class)
- **Description**: Path-related configuration. Resolution follows env > config.yaml > default for each attribute.
  - `project_name` (str): Current project name. Defaults to `"loop_project"`.
  - `project_path_template` (str): Template for deriving the project path. Defaults to `"{{project_name}}"`.
  - `skills_dir` (str): Directory for skill definitions. Resolved via `SKILLS_DIR` env var. Defaults to `"skills"`.
  - `storage_dir` (str): Directory for storing cycle artifacts and feedback. Resolved via `STORAGE_DIR` env var. Defaults to `"./storage"`.
  - `guardrails_path` (str): Path to guardrails YAML. Resolved via `GUARDRAILS_PATH` env var. Defaults to `"./config/guardrails.yaml"`.
  - `project_path` (property → str): Resolves full project path. Checks `PROJECT_PATH` env var first, otherwise joins `_workspace_base` with `project_name` (substituting `{{project_name}}` in the template).

##### `Config.Workflow` (inner class)
- **Description**: Workflow behavior configuration.
  - `hil_mode` (str): Human-in-the-loop mode. Resolved via `HIL_MODE` env var. Defaults to `"auto"`.
  - `max_retries` (int): Maximum retry count for failed phases. Defaults to `2`.
  - `auto_approve` (bool): Whether to auto-approve changes without human confirmation. Defaults to `False`.

##### `set_project_name(name: str) -> None` (instance method)
- **Parameters**:
  - `name` (str): Project name. Must match `^[a-zA-Z0-9_-]+$` and must not start with container paths (`/var/lib/docker`, `/app`, `/container`).
- **Returns**: Nothing
- **Behavior**: Validates the name against a strict regex pattern and rejects container paths (security measure). Updates in-memory state immediately (`self.paths.project_name` and `self.paths.project_path_template`). Builds a complete `_config` dict and persists to `config.yaml` via `_save_yaml()`. Silently skips disk write on `OSError` (read-only filesystems in Docker). Prints a confirmation message with the resolved project path.

##### `reload() -> None` (static method)
- **Parameters**: None
- **Returns**: Nothing
- **Behavior**: Re-reads `config.yaml` and reassigns the module-level `_config` global. Intended for tests or development use. Note: previously instantiated `Config.Paths` and `Config.Workflow` class attributes are NOT re-evaluated after reload.

### Module-Level Variables
- `_workspace_base` (str): Base workspace directory where generated projects live. Defaults to `~/workspace/projects`, overridable via `WORKSPACE_DIR` env var.
- `_codebase_root` (str): Absolute path to the Loop Engineering codebase root (parent of the `config/` directory).
- `_config_path` (Path): Resolved path to `config.yaml`. Tries `config/config.yaml` relative to this module, falls back to `../config/config.yaml` (when imported from `graph/`).
- `_config` (Dict[str, Any]): Loaded YAML configuration dictionary, mutated by `reload()`.
- `config` (Config): Module-level singleton instance. The primary entry point for all config access.

---

## Dependencies / Used By
- **Imports**: `os`, `pathlib.Path`, `typing.Any`, `typing.Dict`, `yaml`, `re` (imported inside `set_project_name`)
- **Used By**: Virtually every module in the engine (`graph/executor.py`, all nodes in `graph/nodes/`, `graph/edges.py`, `config/guardrails.py`, `feedback/aggregator.py`). Imported as `from config.loader import config`.

## Notes / Caveats
- The `config` singleton is created at module import time. All path and workflow defaults are resolved once on import.
- `set_project_name()` persists to disk but silently ignores `OSError` for read-only filesystems (Docker containers). The in-memory update still takes effect.
- The project name validation is strict: only alphanumeric characters, hyphens, and underscores are allowed. Container paths are explicitly rejected as a security measure.
- `reload()` uses `global _config` to mutate the module-level config, which means previously resolved `Config.Paths` and `Config.Workflow` class attributes are NOT re-evaluated. Use with caution.
- Environment variables always take highest priority, making it easy to override config in production without changing files.
