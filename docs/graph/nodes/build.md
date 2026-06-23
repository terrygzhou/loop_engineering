# `graph/nodes/build.py`

## Purpose
The BUILD node implements tasks incrementally using TDD, security gates, and code review. It orchestrates a pipeline of LLM-driven skill invocations (incremental implementation → FastAPI/Jinja2 feature build → test generation → security review → code review), parses the generated code from LLM output, writes files to disk, and then validates by running a Docker build, health check, pytest, and Bandit security scan. On validation failure, it loops back (up to 2 retries) with error context for the LLM to self-correct. Git stash rollback is used as a safety net around file writes.

## Public API

### Functions
#### `parse_llm_output(text) -> tuple[list[tuple[str, str]], list[tuple[str, str]], dict]`
- **Parameters**: - `text` (str): raw LLM output text containing structured FILE/COMMAND blocks and/or bare fenced code blocks
- **Returns**: tuple of `(files, commands, parse_info)` — files is a list of `(path, content)` tuples, commands is a list of `(description, command)` tuples, parse_info is a dict with structural metadata
- **Behavior**: Parses three formats: `=== FILE: ... ===` blocks, `=== COMMAND: ... ===` blocks, and bare fenced code blocks (auto-detected by language hint). Bare blocks with `# path:` comments in code get inferred as file writes.

#### `write_files_to_project(files, project_path) -> list[str]`
- **Parameters**: - `files` (list[tuple[str, str]]): list of `(path, content)` tuples — `project_path` (str): base directory for the project
- **Returns**: list[str] — paths of successfully written files
- **Behavior**: Writes each file under `project_path`, creating parent directories as needed. Safety: rejects any resolved path that escapes `project_path` via realpath comparison.

#### `run_command(cmd, timeout=180, workdir=None) -> tuple[int, str, str]`
- **Parameters**: - `cmd` (str): shell command to execute — `timeout` (int, default 180): max seconds before killing — `workdir` (str | None): working directory for the subprocess
- **Returns**: tuple of `(exit_code, stdout, stderr)`
- **Behavior**: Runs `cmd` via `subprocess.run(shell=True)`. Returns `-1` exit code on `TimeoutExpired` or other exceptions with error message in stderr.

#### `find_docker_project(project_path) -> str`
- **Parameters**: - `project_path` (str): base project directory
- **Returns**: str — path to the directory containing `docker-compose.yml` (or variant)
- **Behavior**: Checks `project_path` and `project_path/mvp_output` for common docker-compose filenames. Falls back to `project_path` if none found.

#### `build_node(state: dict) -> dict`
- **Parameters**: - `state` (dict): WorkflowState containing project_path, artifacts, metrics, and optional error from prior phase
- **Returns**: dict — updated WorkflowState with artifacts, metrics, phase, next_phase, and optional error
- **Behavior**: Executes the full BUILD pipeline:
  1. **Generation**: Invokes 5 skills sequentially (incremental-implementation → fastapi-jinja2-feature-build → test-driven-development → security-and-hardening → requesting-code-review), each feeding into the next.
  2. **Execution**: Parses LLM output, writes files to disk under docker project dir, runs non-build/test commands.
  3. **Validation**: Docker build → start container → health check (port 8010) → pytest → Bandit scan.
  4. **Loop-back**: On failure, stops container, restores git stash, sets `next_phase="BUILD"` with error context. On success, drops stash, writes `.build_status` marker, sets `next_phase="SEED_DATA"`.
  5. **Skip optimization**: If `.build_status` shows a prior pass and this is not a retry, skips regeneration.

## Dependencies / Used By
- **Imports**: `os`, `re`, `json`, `subprocess`, `pathlib.Path`, `tools.loader.build_skill_registry`, `tools.llm.invoke_skill`, `graph.nodes.build.find_docker_project` (internal)
- **Used By**: `graph/main.py` (wires `build_node` into LangGraph), `graph/nodes/seed_data.py` (imports `find_docker_project`)

## Notes / Caveats
- **Git rollback safety**: Creates a stash before writing files; pops on failure, drops on success. Non-fatal if stash fails.
- **Path traversal protection**: `write_files_to_project` rejects paths that escape the project directory after realpath resolution.
- **Retry limit**: Max 2 retries enforced by `graph/edges.py` loop counter, not within this module.
- **Bandit graceful skip**: If the Docker image doesn't include `bandit`, the scan is skipped with a warning.
- **Health check port**: Hardcoded to `localhost:8010`; assumes the docker-compose config exposes this port.
- **Status file**: Writes `.build_status` JSON marker in the docker project dir to enable downstream phases (VERIFY, SEED_DATA) to skip redundant work.
