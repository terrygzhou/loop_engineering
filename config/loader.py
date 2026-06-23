"""
Configuration loader for Loop Engineering.

Resolution order for every setting:
  1. Environment variable (highest priority)
  2. config/config.yaml
  3. Built-in default (lowest priority)

Project path uses {{project_name}} as a placeholder. After DEFINE node
captures the project name, call `config.set_project_name("my_project")` to
resolve the full path. Default base_dir is the loop engineering codebase root.

Usage:
    from config.loader import config
    config.set_project_name("gloryev")           # after DEFINE captures it
    project_path = config.paths.project_path     # → ./gloryev (or env override)
"""
import os
from pathlib import Path
from typing import Any, Dict

import yaml


# ── Workspace directory: where generated projects live ──
_workspace_base = os.path.expanduser(
    os.getenv("WORKSPACE_DIR", "~/workspace/projects")
)

# ── Base directory: loop engineering codebase root (current folder) ──
_codebase_root = str(Path(__file__).resolve().parent.parent)


def _load_yaml(path: str) -> Dict[str, Any]:
    """Load a YAML config file. Returns {} on missing/invalid."""
    p = Path(path)
    if p.exists():
        try:
            return yaml.safe_load(p.read_text()) or {}
        except Exception:
            pass
    return {}


def _resolve(env_var: str | None, config: Dict[str, Any], key_path: str, default: str) -> str:
    """Resolve a setting: env var > config dict (nested key) > default."""
    if env_var:
        env_val = os.getenv(env_var)
        if env_val:
            return env_val
    # Walk nested keys
    val = config
    for k in key_path.split("."):
        if isinstance(val, dict):
            val = val.get(k)
        else:
            val = None
            break
    if val is not None:
        return str(val)
    return default


def _save_yaml(path: str, data: Dict[str, Any]):
    """Write config dict back to YAML file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# ── Load config file ──────────────────────────────────────────────
# Look in ./config/ relative to project root (parent of this module)
_config_path = Path(__file__).resolve().parent / "config.yaml"
if not _config_path.exists():
    # Fallback: try ../config/config.yaml (when imported from graph/)
    _config_path = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
_config = _load_yaml(str(_config_path))


# ── Resolved values ───────────────────────────────────────────────
class Config:
    """Config object. Read attributes directly. Call set_project_name() after DEFINE."""

    class Paths:
        project_name: str = _resolve(None, _config, "paths.project_name", "loop_project")
        project_path_template: str = _resolve(None, _config, "paths.project_path", "{{project_name}}")
        skills_dir: str = _resolve("SKILLS_DIR", _config, "paths.skills_dir", "skills")
        storage_dir: str = _resolve("STORAGE_DIR", _config, "paths.storage_dir", "./storage")
        guardrails_path: str = _resolve("GUARDRAILS_PATH", _config, "paths.guardrails_path", "./config/guardrails.yaml")

        @property
        def project_path(self) -> str:
            """Resolve project_path: env PROJECT_PATH > workspace base + project_name."""
            env_override = os.getenv("PROJECT_PATH")
            if env_override:
                return env_override
            template = self.project_path_template
            if "{{project_name}}" in template:
                return os.path.join(_workspace_base, self.project_name)
            return template

    class Workflow:
        hil_mode: str = _resolve("HIL_MODE", _config, "workflow.hil_mode", "auto")
        max_retries: int = int(_config.get("workflow", {}).get("max_retries", 2))
        auto_approve: bool = bool(_config.get("workflow", {}).get("auto_approve", False))

    paths = Paths()
    workflow = Workflow()

    def set_project_name(self, name: str):
        """Update project name and persist to config.yaml. Called by DEFINE node."""
        import re
        if not name or not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValueError(f"Invalid project name: {name!r}. Must be alphanumeric, hyphens, or underscores.")
        if name.startswith(("/var/lib/docker", "/app", "/container")):
            raise ValueError(f"Rejected container path in project name: {name!r}")

        # Update in-memory state immediately
        self.paths.project_name = name
        self.paths.project_path_template = "{{project_name}}"
        # Persist to disk — silently skip if read-only (Docker container)
        workspace = _config.get("paths", {}).get("workspace_dir", "~/workspace/projects")
        _config["paths"] = {"project_name": name, "workspace_dir": workspace,
                            "project_path": "{{project_name}}",
                            "skills_dir": self.paths.skills_dir, "storage_dir": self.paths.storage_dir,
                            "guardrails_path": self.paths.guardrails_path}
        _config.setdefault("workflow", {})["hil_mode"] = self.workflow.hil_mode
        _config["workflow"]["max_retries"] = self.workflow.max_retries
        _config["workflow"]["auto_approve"] = self.workflow.auto_approve

        # Persist to disk — silently skip if read-only (Docker container)
        try:
            _save_yaml(str(_config_path), _config)
        except OSError:
            pass  # read-only filesystem — in-memory update is sufficient

        print(f"  ✓ config.yaml updated: project_name={name}, project_path={self.paths.project_path}")

    @staticmethod
    def reload():
        """Reload from disk (for tests or dev)."""
        global _config
        _config = _load_yaml(str(_config_path))


config = Config()
