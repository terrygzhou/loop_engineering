# `tools/loader.py`

## Purpose
Loads and parses Hermes SKILL.md files into structured Python dictionaries, making them usable as LangChain-compatible tools throughout the pipeline. It handles YAML frontmatter extraction, directory scanning, trigger-based lookup, and building a name-indexed registry that merges skills from multiple locations (local, environment variable, and the default `~/.hermes/skills`).

## Public API

### Functions

#### `parse_skill_md(filepath: str) -> Dict[str, Any]`
- **Parameters**:
  - `filepath` (str): Path to a SKILL.md file.
- **Returns**: `Dict[str, Any]` — dict with keys `"meta"` (parsed YAML frontmatter or `{}`), `"content"` (markdown body), and `"path"` (the input filepath).
- **Behavior**: Reads the file, splits on `---` delimiters to extract YAML frontmatter, and separates the markdown body. If no frontmatter is found, returns empty `meta` and the full file as `content`.

#### `load_skills(skills_dir: str = "~/.hermes/skills") -> List[Dict[str, Any]]`
- **Parameters**:
  - `skills_dir` (str, optional): Root directory to scan for skills. Defaults to `"~/.hermes/skills"`.
- **Returns**: `List[Dict[str, Any]]` — list of parsed skill dicts, each with `name`, `description`, `triggers`, `version`, `content`, `category`, and `path`.
- **Behavior**: Walks the directory tree looking for `SKILL.md` files. For each match, extracts the directory name as the skill name, the relative parent path as the category, and merges parsed frontmatter metadata with defaults. Prints a warning if the skills directory doesn't exist; skips individual files that fail to parse.

#### `find_skills_by_trigger(trigger_keyword: str, skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]`
- **Parameters**:
  - `trigger_keyword` (str): Keyword to match against triggers, names, and descriptions.
  - `skills` (List[Dict[str, Any]]): List of skill dicts (typically from `load_skills()` or `build_skill_registry()`).
- **Returns**: `List[Dict[str, Any]]` — filtered list of matching skills.
- **Behavior**: Performs case-insensitive matching against each skill's `triggers` list, `name`, and `description`. Returns all skills where the keyword appears in any of those fields.

#### `build_skill_registry(skills_dir: Optional[str] = None) -> Dict[str, Dict[str, Any]]`
- **Parameters**:
  - `skills_dir` (str, optional): Skills directory path. If `None`, resolved via a search order.
- **Returns**: `Dict[str, Dict[str, Any]]` — name-indexed dictionary of skill dicts for fast lookup.
- **Behavior**: Determines the skills directory using a four-step search order:
  1. Explicit `skills_dir` parameter
  2. `SKILLS_DIR` environment variable
  3. Local `./skills` directory (relative to project root)
  4. `~/.hermes/skills` (default Hermes location)

  Loads skills from the primary directory, then merges in skills from `~/.hermes/skills` if it's a different location. Skills from the primary source take precedence; duplicate names from the merge are skipped.

## Dependencies / Used By

- **Imports**: `os`, `re`, `yaml`, `pathlib.Path`, `typing.List`, `typing.Dict`, `typing.Any`, `typing.Optional`
- **Used By**:
  - `graph/nodes/define.py` — imports `build_skill_registry`, `find_skills_by_trigger`
  - `graph/nodes/plan.py` — imports `build_skill_registry`
  - `graph/nodes/build.py` — imports `build_skill_registry`
  - `graph/nodes/seed_data.py` — imports `build_skill_registry`
  - `graph/nodes/reflect.py` — imports `build_skill_registry`
  - `graph/nodes/ship.py` — imports `build_skill_registry`
  - `graph/nodes/verify.py` — imports `build_skill_registry`
  - `graph/executor.py` — imports `build_skill_registry`
  - `frontend/backend/workflow_bridge.py` — imports `build_skill_registry`

## Notes / Caveats

- The `re` module is imported but not actively used in the current implementation.
- `load_skills` uses `os.walk` for recursive traversal, meaning skills can be nested in subdirectories under the skills root. The `category` field captures the subdirectory path relative to the root.
- `build_skill_registry` handles the common case where a project has its own local skills directory but also wants access to the shared Hermes skills. The merge is non-destructive — first-seen names win.
- File read errors in `load_skills` are caught and logged as warnings, allowing the loader to continue processing remaining skills instead of failing entirely.
