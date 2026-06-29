"""
B-006: Workflow State Persistence

Serialize/deserialize WorkflowState to `build/workflow_state.json` so that
workflows can survive container restarts and be recovered via the API.
"""
import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

# ── Persistence directory ──
_STATE_DIR = Path("build")

# Legacy singleton file (kept for backward compatibility)
_STATE_FILE = _STATE_DIR / "workflow_state.json"


def _project_state_file(project_id: str) -> Path:
    """Return the per-project state file path: build/{project_id}/workflow_state.json"""
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_id)
    return _STATE_DIR / safe_id / "workflow_state.json"


def _project_state_dir() -> Path:
    """Return the directory holding all per-project state files."""
    return _STATE_DIR


def _list_project_files() -> list[str]:
    """List project IDs that have persisted state files under build/."""
    if not _STATE_DIR.exists():
        return []
    projects = []
    for d in _STATE_DIR.iterdir():
        if d.is_dir() and (d / "workflow_state.json").exists():
            projects.append(d.name)
    # Also pick up legacy flat files for backward compat
    for f in _STATE_DIR.glob("workflow_state_*.json"):
        name = f.stem
        if name.startswith("workflow_state_"):
            pid = name[len("workflow_state_"):]
            if pid not in projects:
                projects.append(pid)
    return projects


def _sanitize(value: Any) -> Any:
    """Recursively walk a value and make it JSON-serializable."""
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(v) for v in value]
    if hasattr(value, "model_dump"):
        # Pydantic v2 (CycleMetrics, etc.)
        return _sanitize(value.model_dump())
    if hasattr(value, "dict"):
        # Pydantic v1 fallback
        return _sanitize(value.dict())
    # Basic JSON-serializable types: str, int, float, bool, None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    # Anything else (custom objects, file handles, etc.) — drop it
    return None


def serialize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a WorkflowState dict to a plain JSON-serializable dict."""
    return _sanitize(dict(state))


def deserialize_state(data: Dict[str, Any]) -> Dict[str, Any]:
    """Restore a persisted dict back to a WorkflowState-compatible dict.

    All keys from the original TypedDict are preserved.  Missing keys
    (e.g. from schema evolution) are filled with safe defaults.
    """
    from graph.state import CycleMetrics, WorkflowState

    # Restore CycleMetrics as a proper Pydantic model
    metrics_data = data.get("metrics", {})
    if isinstance(metrics_data, dict):
        data["metrics"] = CycleMetrics(**{k: v for k, v in metrics_data.items()
                                          if k in CycleMetrics.model_fields})

    # Ensure all TypedDict keys exist with safe defaults
    defaults: Dict[str, Any] = {
        "cycle_id": data.get("cycle_id", "1"),
        "phase": data.get("phase", "DISCOVER"),
        "artifacts": data.get("artifacts", {}),
        "metrics": data.get("metrics", CycleMetrics()),
        "feedback": data.get("feedback", []),
        "feedback_context": data.get("feedback_context", ""),
        "config_version": data.get("config_version", "1"),
        "human_approval_required": data.get("human_approval_required", False),
        "next_phase": data.get("next_phase"),
        "project_name": data.get("project_name", ""),
        "project_path": data.get("project_path", ""),
        "project_folder": data.get("project_folder", ""),
        "spec_path": data.get("spec_path", ""),
        "project_description": data.get("project_description", ""),
        "skip_discover": data.get("skip_discover", False),
        "context_folder": data.get("context_folder", ""),
        "error": data.get("error"),
        # B-009
        "pending_inputs": data.get("pending_inputs", []),
        "input_responses": data.get("input_responses", {}),
        "input_timeout_s": data.get("input_timeout_s", 300),
        "auto_approve_timeout": data.get("auto_approve_timeout", True),
        # B-010
        "diagrams": data.get("diagrams", {}),
        "diagram_status": data.get("diagram_status", "pending"),
        "diagram_feedback": data.get("diagram_feedback", ""),
        "arch_review_approved": data.get("arch_review_approved", False),
        # Improve mode
        "improve_mode": data.get("improve_mode", False),
        # DISCOVER
        "interview_notes": data.get("interview_notes", ""),
        # Auto-approve
        "auto_approve": data.get("auto_approve", False),
        "discover_interview_done": data.get("discover_interview_done", False),
        # Audit
        "trace_id": data.get("trace_id", ""),
        "audit_entries": data.get("audit_entries", []),
        # B-004: Context size management
        "context_tokens_used": data.get("context_tokens_used", 0),
        "context_compression_ratio": data.get("context_compression_ratio", 1.0),
        "headroom_remaining": data.get("headroom_remaining", 0),
    }

    # Strip the skill_registry from artifacts on restore — it will be
    # re-built by build_executor_state or the caller.
    if isinstance(defaults["artifacts"], dict):
        defaults["artifacts"].pop("skill_registry", None)

    return defaults


# ── Legacy helpers (backward compat — no project_id) ──
# These delegate to the legacy _STATE_FILE path for existing callers
# that don't yet carry a project identifier.

async def save_state(state: Dict[str, Any]):
    """Atomically write state to disk (async, non-blocking). Legacy no-project path."""
    serialized = serialize_state(state)
    serialized["__saved_at"] = time.time()
    serialized["__version"] = "1"

    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file then rename for atomicity
    tmp = _STATE_FILE.with_suffix(".tmp")
    loop = asyncio.get_running_loop()

    def _write():
        with open(tmp, "w") as f:
            json.dump(serialized, f, indent=2, default=str)
        tmp.replace(_STATE_FILE)

    await loop.run_in_executor(None, _write)


def load_state() -> Optional[Dict[str, Any]]:
    """Load persisted state from legacy disk file. Returns None if no file exists."""
    if not _STATE_FILE.exists():
        return None
    try:
        with open(_STATE_FILE) as f:
            data = json.load(f)
        data.pop("__saved_at", None)
        data.pop("__version", None)
        return deserialize_state(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def clear_state():
    """Remove the legacy persisted state file."""
    if _STATE_FILE.exists():
        _STATE_FILE.unlink()


def state_file_exists() -> bool:
    """Check whether a persisted state file is on disk."""
    return _STATE_FILE.exists()


# ── B-007: Per-project state persistence ──
# Each project gets its own state file at: build/{project_id}/workflow_state.json


def save_state_for_project(project_id: str, state: Dict[str, Any]):
    """Persist state for a specific project (sync)."""
    path = _project_state_file(project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = serialize_state(state)
    serialized["__project_id"] = project_id
    with open(path, "w") as f:
        json.dump(serialized, f, indent=2, default=str)


async def save_state_for_project_async(project_id: str, state: Dict[str, Any]):
    """Persist state for a specific project (async)."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, save_state_for_project, project_id, state)


def load_state_for_project(project_id: str) -> Optional[Dict[str, Any]]:
    """Load persisted state for a specific project."""
    path = _project_state_file(project_id)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        data.pop("__project_id", None)
        return deserialize_state(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def clear_state_for_project(project_id: str):
    """Remove persisted state for a specific project."""
    path = _project_state_file(project_id)
    if path.exists():
        path.unlink()


def state_file_exists_for_project(project_id: str) -> bool:
    """Check whether a project has persisted state."""
    return _project_state_file(project_id).exists()


def list_projects() -> list[str]:
    """List all project IDs that have persisted state files."""
    return _list_project_files()


# Alias so callers using either name get the same function
list_persisted_projects = list_projects
