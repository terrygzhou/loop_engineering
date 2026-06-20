"""
DISCOVER node: Scan project tree, detect structure, check git and Docker status.
Produces a project_context artifact that feeds into DEFINE.

Runs before DEFINE to give the spec-writing phase awareness of
existing code, routes, models, and deployment state.
"""
import os
import json
import subprocess
from pathlib import Path


def discover_node(state: dict) -> dict:
    """
    DISCOVER phase: Analyze the target project to produce a comprehensive
    context artifact. Covers:

    1. Project type detection (FastAPI, Express, Rails, etc.)
    2. File tree inventory (key directories, file counts)
    3. Route/module discovery (registered endpoints, model definitions)
    4. Template/view discovery (existing UI surfaces)
    5. Git status (branch, modified files, ahead/behind)
    6. Docker health (compose services, container status)
    7. Dependency inventory (manifest files)

    Produces state["artifacts"]["project_context"] — a structured dict
    serialised to JSON string.
    """
    print("\n=== DISCOVER PHASE ===")

    project_path = state.get("project_path", "")
    if not project_path:
        print("  ⚠ No project_path — skipping DISCOVER (greenfield mode)")
        state["artifacts"]["project_context"] = json.dumps({"mode": "greenfield", "note": "no existing project to scan"})
        state["phase"] = "DISCOVER"
        state["next_phase"] = "DEFINE"
        return state

    project_dir = Path(project_path)
    if not project_dir.is_dir():
        print(f"  ⚠ Project path not found: {project_path} — skipping DISCOVER")
        state["artifacts"]["project_context"] = json.dumps({"mode": "greenfield", "note": f"path {project_path} does not exist"})
        state["phase"] = "DISCOVER"
        state["next_phase"] = "DEFINE"
        return state

    context = {"project_path": project_path}

    # --- 1. Project type detection ---
    context["project_type"] = _detect_project_type(project_path)

    # --- 2. File tree inventory ---
    context["tree"] = _inventory_tree(project_path)

    # --- 3. Route discovery ---
    context["routes"] = _discover_routes(project_path, context["project_type"])

    # --- 4. Model/schema discovery ---
    context["models"] = _discover_models(project_path, context["project_type"])

    # --- 5. Template/view discovery ---
    context["templates"] = _discover_templates(project_path, context["project_type"])

    # --- 6. Dependency inventory ---
    context["dependencies"] = _discover_dependencies(project_path)

    # --- 7. Git status ---
    context["git"] = _get_git_status(project_path)

    # --- 8. Docker health ---
    context["docker"] = _get_docker_status(project_path)

    # --- 9. Existing spec inventory ---
    context["specs"] = _discover_specs(project_path)

    # Serialise to string for artifact storage
    state["artifacts"]["project_context"] = json.dumps(context, indent=2, default=str)
    state["phase"] = "DISCOVER"
    state["next_phase"] = "DEFINE"

    # Print summary
    route_count = len(context.get("routes", []))
    model_count = len(context.get("models", []))
    print(f"  → Project type: {context['project_type']}")
    print(f"  → Routes discovered: {route_count}")
    print(f"  → Models discovered: {model_count}")
    print(f"  → Git: {context.get('git', {}).get('branch', 'unknown')} | "
          f"modified: {context.get('git', {}).get('modified', 0)} | "
          f"untracked: {context.get('git', {}).get('untracked', 0)}")
    print(f"  → Docker services: {len(context.get('docker', {}).get('services', []))}")
    print(f"  ✓ project_context artefact generated ({len(state['artifacts']['project_context'])} chars)")

    return state


# ── Helpers ──────────────────────────────────────────────────────────────

def _detect_project_type(project_path: str) -> str:
    """Detect project type from manifest files and directory structure."""
    p = Path(project_path)
    if (p / "pyproject.toml").exists():
        return "python-pyproject"
    if (p / "requirements.txt").exists():
        return "python-requirements"
    if (p / "package.json").exists():
        return "node"
    if (p / "Cargo.toml").exists():
        return "rust"
    if (p / "go.mod").exists():
        return "go"
    if (p / "Gemfile").exists():
        return "ruby"
    # Check for FastAPI specifically
    for pyfile in p.rglob("main.py"):
        text = pyfile.read_text(errors="replace")
        if "fastapi" in text.lower() or "FastAPI" in text:
            return "python-fastapi"
    return "unknown"


def _inventory_tree(project_path: str) -> dict:
    """Produce a lightweight directory inventory (no deep recursion)."""
    p = Path(project_path)
    dirs = []
    for d in p.iterdir():
        if d.is_dir() and not d.name.startswith("."):
            count = len(list(d.rglob("*")))
            dirs.append({"name": d.name, "file_count": count})
    return {"directories": dirs, "total_top_level": len(dirs)}


def _discover_routes(project_path: str, project_type: str) -> list:
    """Find registered API routes in the project."""
    routes = []

    if project_type in ("python-fastapi", "python-pyproject", "python-requirements"):
        routes = _discover_fastapi_routes(project_path)

    elif project_type == "node":
        routes = _discover_express_routes(project_path)

    return routes


def _discover_fastapi_routes(project_path: str) -> list:
    """Parse FastAPI routers to extract registered endpoints."""
    routes = []
    p = Path(project_path)

    # Find all router files
    router_dirs = list(p.rglob("routers")) + list(p.rglob("api")) + list(p.rglob("routes"))
    for rd in router_dirs:
        if not rd.is_dir():
            continue
        for pyfile in rd.glob("*.py"):
            if pyfile.name.startswith("_"):
                continue
            try:
                text = pyfile.read_text(errors="replace")
                # Look for @router.get, @router.post, etc.
                import re
                patterns = re.findall(
                    r'@\w+\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                    text
                )
                for method, path in patterns:
                    routes.append({
                        "method": method.upper(),
                        "path": path,
                        "file": str(pyfile.relative_to(p)),
                    })
            except Exception:
                pass

    # Also check main.py for direct route definitions
    mainfiles = list(p.glob("*/main.py")) + [p / "main.py"]
    for mainfile in mainfiles:
        try:
            text = mainfile.read_text(errors="replace")
            matches = re.findall(
                r'@\w+\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                text
            )
            for method, path in matches:
                routes.append({
                    "method": method.upper(),
                    "path": path,
                    "file": str(mainfile.relative_to(p)),
                })
        except Exception:
            pass

    return routes


def _discover_express_routes(project_path: str) -> list:
    """Parse Express.js routes."""
    routes = []
    p = Path(project_path)
    for jsfile in list(p.rglob("*.js")) + list(p.rglob("*.ts")):
        try:
            text = jsfile.read_text(errors="replace")
            import re
            matches = re.findall(
                r'\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                text
            )
            for method, path in matches:
                routes.append({
                    "method": method.upper(),
                    "path": path,
                    "file": str(jsfile.relative_to(p)),
                })
        except Exception:
            pass
    return routes


def _discover_models(project_path: str, project_type: str) -> list:
    """Find model/entity definitions."""
    models = []
    p = Path(project_path)

    if project_type.startswith("python"):
        # Look for SQLAlchemy/SQLModel models
        model_dirs = list(p.rglob("models"))
        for md in model_dirs:
            if not md.is_dir():
                continue
            for pyfile in md.glob("*.py"):
                if pyfile.name.startswith("_"):
                    continue
                try:
                    text = pyfile.read_text(errors="replace")
                    import re
                    # Class definitions inheriting from Model/Base
                    class_matches = re.findall(
                        r'class\s+(\w+)\s*\([^)]*(?:Base|Model|DeclarativeBase)[^)]*\)',
                        text
                    )
                    for cls in class_matches:
                        models.append({
                            "name": cls,
                            "file": str(pyfile.relative_to(p)),
                        })
                except Exception:
                    pass

    elif project_type == "node":
        # Look for Mongoose schemas or Prisma models
        p.glob("models/*.js")
        p.glob("schemas/*.ts")

    return models


def _discover_templates(project_path: str, project_type: str) -> list:
    """Find UI templates/views."""
    templates = []
    p = Path(project_path)

    if project_type.startswith("python"):
        # Jinja2 templates
        for html in p.rglob("*.html"):
            templates.append({
                "name": html.name,
                "file": str(html.relative_to(p)),
            })
    elif project_type == "node":
        for ejs in p.rglob("*.ejs") + p.rglob("*.pug") + p.rglob("*.hbs"):
            templates.append({
                "name": ejs.name,
                "file": str(ejs.relative_to(p)),
            })

    return templates


def _discover_dependencies(project_path: str) -> dict:
    """Read manifest files and extract key dependencies."""
    deps = {}
    p = Path(project_path)

    if (p / "requirements.txt").exists():
        lines = (p / "requirements.txt").read_text(errors="replace").strip().splitlines()
        deps["requirements.txt"] = [l.strip() for l in lines if l.strip() and not l.startswith("#")]

    if (p / "pyproject.toml").exists():
        deps["pyproject.toml"] = "present"

    if (p / "package.json").exists():
        try:
            pkg = json.loads((p / "package.json").read_text())
            deps["package.json"] = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        except Exception:
            deps["package.json"] = "present"

    return deps


def _get_git_status(project_path: str) -> dict:
    """Get git branch, status, and commit info."""
    info = {"branch": "unknown", "modified": 0, "untracked": 0, "ahead": 0, "behind": 0}
    try:
        # Branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=5, cwd=project_path,
        )
        if result.returncode == 0:
            info["branch"] = result.stdout.strip() or "detached"

        # Short status: M = modified, ?? = untracked
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=5, cwd=project_path,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                if line.startswith("??"):
                    info["untracked"] += 1
                elif line.startswith(" M") or line.startswith("M "):
                    info["modified"] += 1

        # Ahead/behind
        result = subprocess.run(
            ["git", "rev-list", "--count", "--left-right", "HEAD...@{upstream}"],
            capture_output=True, text=True, timeout=5, cwd=project_path,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split()
            if len(parts) == 2:
                info["ahead"] = int(parts[1])
                info["behind"] = int(parts[0])

        # Last commit
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h|%s"],
            capture_output=True, text=True, timeout=5, cwd=project_path,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split("|", 1)
            info["last_commit"] = parts[0]
            info["last_message"] = parts[1] if len(parts) > 1 else ""

    except (subprocess.TimeoutExpired, FileNotFoundError):
        info["error"] = "git not available or timed out"

    return info


def _get_docker_status(project_path: str) -> dict:
    """Check Docker Compose services and container health."""
    info = {"services": [], "healthy": 0, "unhealthy": 0}
    p = Path(project_path)

    compose_file = None
    for candidate in [p / "docker-compose.yml", p / "docker-compose.yaml",
                      p / "mvp_output" / "docker-compose.yml"]:
        if candidate.exists():
            compose_file = candidate
            break

    if not compose_file:
        info["error"] = "no docker-compose.yml found"
        return info

    info["compose_file"] = str(compose_file.relative_to(p))
    info["project_dir"] = str(compose_file.parent)

    try:
        # List running containers for this project
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "ps", "--format", "json"],
            capture_output=True, text=True, timeout=15,
            cwd=str(compose_file.parent),
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                try:
                    container = json.loads(line)
                    svc = {
                        "name": container.get("Name", "unknown"),
                        "state": container.get("State", "unknown"),
                        "ports": container.get("Ports", ""),
                    }
                    info["services"].append(svc)
                    if "running" in svc["state"].lower():
                        info["healthy"] += 1
                    else:
                        info["unhealthy"] += 1
                except json.JSONDecodeError:
                    pass
    except (subprocess.TimeoutExpired, FileNotFoundError):
        info["error"] = "docker compose not available or timed out"

    return info


def _discover_specs(project_path: str) -> dict:
    """Find existing spec directories and their contents."""
    specs = {}
    p = Path(project_path)
    spec_dir = p / "specs"

    if not spec_dir.exists():
        return specs

    for spec_subdir in sorted(spec_dir.iterdir()):
        if not spec_subdir.is_dir():
            continue
        entries = {f.name: str(f.relative_to(spec_dir)) for f in spec_subdir.iterdir() if f.is_file()}
        specs[spec_subdir.name] = entries

    return specs
