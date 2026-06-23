# `graph/nodes/discover.py`

## Purpose
The DISCOVER node scans the target project tree to produce a comprehensive `project_context` artifact. This context feeds into DEFINE so the spec-writing phase has awareness of existing code, routes, models, deployment state, and dependencies. It covers project type detection, file tree inventory, route/module discovery, template/view discovery, git status, docker health, dependency inventory, and existing spec inventory. If no project path exists (greenfield mode), it records a placeholder context.

## Public API

### Functions
#### `discover_node(state: dict) -> dict`
- **Parameters**: - `state` (dict): WorkflowState containing `project_path`
- **Returns**: dict — updated WorkflowState with `artifacts.project_context` (JSON string), `phase="DISCOVER"`, `next_phase="DEFINE"`
- **Behavior**: Orchestrates 9 discovery sub-tasks and serializes the result as a JSON string. If `project_path` is empty or the directory doesn't exist, produces a greenfield-mode placeholder and proceeds.

#### `_detect_project_type(project_path: str) -> str`
- **Parameters**: - `project_path` (str): path to the project root
- **Returns**: str — project type identifier (e.g., "python-fastapi", "python-pyproject", "node", "rust", "go", "ruby", "unknown")
- **Behavior**: Checks for manifest files in priority order (pyproject.toml, requirements.txt, package.json, Cargo.toml, go.mod, Gemfile), then scans for FastAPI in main.py files.

#### `_inventory_tree(project_path: str) -> dict`
- **Parameters**: - `project_path` (str): path to the project root
- **Returns**: dict — `{"directories": [{"name": ..., "file_count": ...}], "total_top_level": int}`
- **Behavior**: Lightweight inventory of top-level directories (excludes dotfiles). Counts total files recursively within each directory.

#### `_discover_routes(project_path: str, project_type: str) -> list[dict]`
- **Parameters**: - `project_path` (str): project root — `project_type` (str): detected project type
- **Returns**: list[dict] — each dict has `method`, `path`, and `file` keys
- **Behavior**: Delegates to `_discover_fastapi_routes` for Python projects and `_discover_express_routes` for Node.js projects.

#### `_discover_fastapi_routes(project_path: str) -> list[dict]`
- **Parameters**: - `project_path` (str): project root
- **Returns**: list[dict] — FastAPI endpoints with method, path, and file
- **Behavior**: Scans routers/api/routes directories and main.py for `@router.(get|post|put|delete|patch)` decorators using regex.

#### `_discover_express_routes(project_path: str) -> list[dict]`
- **Parameters**: - `project_path` (str): project root
- **Returns**: list[dict] — Express.js endpoints with method, path, and file
- **Behavior**: Scans all .js/.ts files for `.method(path)` patterns.

#### `_discover_models(project_path: str, project_type: str) -> list[dict]`
- **Parameters**: - `project_path` (str): project root — `project_type` (str): detected project type
- **Returns**: list[dict] — each dict has `name` and `file` keys
- **Behavior**: For Python, scans models/ directories for classes inheriting from Base/Model/DeclarativeBase. For Node.js, stub for Mongoose/Prisma.

#### `_discover_templates(project_path: str, project_type: str) -> list[dict]`
- **Parameters**: - `project_path` (str): project root — `project_type` (str): detected project type
- **Returns**: list[dict] — each dict has `name` and `file` keys
- **Behavior**: For Python, finds *.html files (Jinja2). For Node.js, finds *.ejs, *.pug, *.hbs files.

#### `_discover_dependencies(project_path: str) -> dict`
- **Parameters**: - `project_path` (str): project root
- **Returns**: dict — map of manifest filename to dependency list or "present"
- **Behavior**: Reads requirements.txt (lines), pyproject.toml (presence), and package.json (parsed dependencies + devDependencies).

#### `_get_git_status(project_path: str) -> dict`
- **Parameters**: - `project_path` (str): project root
- **Returns**: dict — branch, modified count, untracked count, ahead, behind, last_commit, last_message
- **Behavior**: Runs git commands to collect branch name, porcelain status, ahead/behind count, and last commit info. Gracefully handles missing git or timeouts.

#### `_get_docker_status(project_path: str) -> dict`
- **Parameters**: - `project_path` (str): project root
- **Returns**: dict — compose_file, project_dir, services (list), healthy/unhealthy counts
- **Behavior**: Finds docker-compose.yml, runs `docker compose ps --format json`, parses service state. Falls back with error message if Docker unavailable.

#### `_discover_specs(project_path: str) -> dict`
- **Parameters**: - `project_path` (str): project root
- **Returns**: dict — map of spec subdirectory name to file entries
- **Behavior**: Scans `specs/` directory for subdirectories and their file contents. Returns empty dict if `specs/` doesn't exist.

## Dependencies / Used By
- **Imports**: `os`, `json`, `subprocess`, `pathlib.Path`, `re` (imported inline in route/model parsers)
- **Used By**: `graph/main.py` (wires `discover_node` into LangGraph), `graph/nodes/define.py` (consumes `project_context` artifact)

## Notes / Caveats
- **Greenfield mode**: If `project_path` is missing or invalid, produces `{"mode": "greenfield", "note": "..."}` and proceeds to DEFINE.
- **Route discovery**: Uses regex pattern matching on file contents, not AST parsing — may produce false positives on comments or strings.
- **Node.js model discovery**: Currently a stub (glob calls without processing); only Python model detection is fully implemented.
- **Error handling**: All discovery sub-functions catch and silently pass on exceptions, ensuring the node never crashes on individual failures.
- **Output format**: The `project_context` is serialized to a JSON string (not a dict) for artifact storage, requiring downstream consumers to parse it.
