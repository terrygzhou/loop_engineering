"""
SEED_DATA node: Populate the database with seed data for testing.
Runs after BUILD, before VERIFY to ensure the app has data for UAT testing.

CRITICAL ORDERING: Generate seed script FIRST (LLM), write to disk,
THEN execute inside Docker. Never attempt to load/execute before
the script is generated and persisted.
"""
import os
import ast
import subprocess
import tempfile
from pathlib import Path
from tools.loader import build_skill_registry
from tools.llm import invoke_skill
from graph.nodes.build import find_docker_project


def seed_data_node(state: dict) -> dict:
    """
    SEED_DATA phase: Generate and execute seed data for the project.

    Steps (strict ordering):
    1. Resolve docker project dir (BEFORE any file writes)
    2. Generate a seed script via LLM (GENERATION phase — must complete first)
    3. Validate seed script with ast.parse (SAFETY — reject non-Python output)
    4. Write seed script to docker_proj (PERSIST to disk)
    5. Execute the seed script inside the Docker container (LOAD/EXECUTE)
    6. Verify data was populated correctly
    7. Loop back to BUILD if seeding fails
    """
    print("\n=== SEED DATA PHASE ===")
    skills = state.get("artifacts", {}).get("skill_registry")
    if skills is None:
        print("  → No skill_registry in state — building from disk...")
        skills = build_skill_registry(os.getenv("SKILLS_DIR", "~/.hermes/skills"))
        state.setdefault("artifacts", {})["skill_registry"] = skills

    project_path = state.get("project_path", "")
    if not project_path:
        print("  ⚠ No project_path specified, skipping seed data generation")
        state["phase"] = "SEED_DATA"
        state["next_phase"] = "VERIFY"
        return state

    # Step 0: Resolve docker project dir BEFORE any file writes
    docker_proj = find_docker_project(project_path)
    print(f"  → Docker project dir: {docker_proj}")

    # Step 1: Load ai-workflow-data-seeding skill
    seed_skill = skills.get("ai-workflow-data-seeding", {})
    if not seed_skill:
        print("  ⚠ ai-workflow-data-seeding skill not found, using inline generation")
        seed_skill = {
            "content": f"""Generate a seed script that:
1. Reads the project models from {docker_proj}/app/models/
2. Creates a Python script at {docker_proj}/app/seed.py that populates the database
3. Uses SQLAlchemy 2.0 async insert() with deterministic data
4. Handles UUID vs Integer primary keys appropriately
5. Seeds: vehicles, users, dealerships, bookings, orders with realistic data
6. Is idempotent (safe to run multiple times with INSERT OR IGNORE or check-first pattern)
Output ONLY valid Python code. No markdown, no explanations outside the code."""
        }

    # ── GENERATION PHASE (must complete before any load/execute) ──

    # Step 2: Generate seed script via LLM
    print("  → [GENERATION] Generating seed script via LLM...")
    task = f"Generate a data seed script for project: {project_path}"
    context = (
        state.get("artifacts", {}).get("spec_refined", "")
        + "\n\n"
        + state.get("artifacts", {}).get("implementation", "")
    )

    seed_script = invoke_skill(seed_skill["content"], task, context, llm=None)
    state["artifacts"]["seed_script"] = seed_script
    print(f"  ✓ [GENERATION] Seed script generated ({len(seed_script)} chars)")

    # ── SAFETY: AST validation ──

    # Strip markdown fences if present
    clean_script = seed_script.strip()
    if clean_script.startswith("```"):
        # Remove first ```lang and last ```
        lines = clean_script.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        clean_script = "\n".join(lines)

    try:
        ast.parse(clean_script)
        print("  ✓ [VALIDATION] Seed script is valid Python (AST parse passed)")
    except SyntaxError as e:
        print(f"  ✗ [VALIDATION] Seed script is NOT valid Python: {e}")
        print(f"  → First 200 chars: {clean_script[:200]}")
        state["artifacts"]["seed_errors"] = f"SyntaxError: {e}"
        state["error"] = f"Seed script failed AST validation: {e}"
        state["phase"] = "SEED_DATA"
        state["next_phase"] = "BUILD"
        return state

    # ── PERSIST & EXECUTE ──

    # Step 3: Write validated seed script to docker_proj
    seed_path = os.path.join(docker_proj, "app", "seed.py")
    os.makedirs(os.path.dirname(seed_path), exist_ok=True)

    with open(seed_path, "w") as f:
        f.write(clean_script)

    print(f"  ✓ [PERSIST] Seed script written to {seed_path}")

    # Step 4: Execute seed script inside Docker container
    print("  → [EXECUTION] Running seed script in Docker container...")
    try:
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "api", "python", "-m", "app.seed"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=docker_proj,
        )

        seed_output = result.stdout + result.stderr
        print(f"  Seed output:\n{seed_output[:500]}")

        if result.returncode != 0:
            print("  ✗ Seed script failed with exit code", result.returncode)
            state["artifacts"]["seed_errors"] = seed_output
            state["error"] = f"Seed script failed (exit {result.returncode}): {seed_output[:300]}"
            state["feedback"] = state.get("feedback", []) + [
                {"skill": "seed_data", "output": f"Seed failed: {seed_output[:300]}"}
            ]
            state["next_phase"] = "BUILD"
        else:
            print("  ✓ Seed data populated successfully")
            state["artifacts"]["seed_result"] = seed_output
            state["error"] = None
            state["next_phase"] = "VERIFY"

    except subprocess.TimeoutExpired:
        print("  ✗ Seed script timed out (>60s)")
        state["artifacts"]["seed_errors"] = "Seed script timed out"
        state["error"] = "Seed script timed out after 60s"
        state["next_phase"] = "BUILD"

    except Exception as e:
        print(f"  ✗ Seed execution failed: {e}")
        state["artifacts"]["seed_errors"] = str(e)
        state["error"] = f"Seed execution failed: {e}"
        state["next_phase"] = "BUILD"

    # Update phase
    state["phase"] = "SEED_DATA"
    state["metrics"] = state["metrics"].model_copy(update={
        "seed_executed": "SEED_DATA" in state.get("phase", ""),
    })

    return state
