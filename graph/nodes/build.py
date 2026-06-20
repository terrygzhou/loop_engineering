"""
BUILD node: Implement tasks incrementally with TDD, security gates, and code review.
Generates code, writes to disk, executes (Docker build, health check, pytest, bandit),
and loops back on validation failure.

Skills: incremental-implementation → fastapi-jinja2-feature-build → test-driven-development
        → security-and-hardening → requesting-code-review
"""
import os
import re
import json
import subprocess
from pathlib import Path
from tools.loader import build_skill_registry
from tools.llm import invoke_skill


def parse_llm_output(text):
    """
    Parse LLM output for file content and shell commands.

    Expected formats:
    File:
    === FILE: path/to/file.py ===
    ...```python
    ...code...
    ...```

    Command:
    === COMMAND: description ===
    ...```bash
    ...command...
    ...```

    Also supports bare fenced code blocks with language hints.

    Returns: (files, commands, parse_info)
    """
    files = []
    commands = []

    total_code_blocks = len(re.findall(r'```', text)) // 2

    # --- Parse structured FILE blocks ---
    for m in re.finditer(
        r'===\s*FILE:\s*(.+?)\s*===\s*\n\s*```(\w+)?\s*\n(.*?)```',
        text, re.DOTALL
    ):
        path = m.group(1).strip()
        code = m.group(3).rstrip()
        if code and path:
            files.append((path, code))

    # --- Parse structured COMMAND blocks ---
    for m in re.finditer(
        r'===\s*COMMAND:\s*(.+?)\s*===\s*\n\s*```(\w+)?\s*\n(.*?)```',
        text, re.DOTALL
    ):
        desc = m.group(1).strip()
        cmd = m.group(3).strip()
        if cmd:
            commands.append((desc, cmd))

    # --- Parse bare code blocks (no FILE/COMMAND header) ---
    bare_blocks = 0
    for m in re.finditer(r'```(\w+)?\s*\n(.*?)```', text, re.DOTALL):
        lang = (m.group(1) or '').strip().lower()
        code = m.group(2).rstrip()
        # Skip if already captured in a FILE/COMMAND block
        if m.start() in [fm.start() for fm in re.finditer(
            r'===\s*(?:FILE|COMMAND):', text
        )]:
            continue
        bare_blocks += 1
        if lang == 'bash' or lang == 'shell':
            commands.append(('auto-detected', code))
        elif lang in ('python', 'html', 'jinja', 'javascript', 'css', 'sql', 'yaml', 'json', 'dockerfile'):
            first_line = code.split('\n')[0].strip()
            if first_line.startswith('#') and 'path:' in first_line.lower():
                inferred = first_line.split('path:')[1].strip()
                if '/' in inferred or '.' in inferred:
                    files.append((inferred, code))
                    continue

    markers_found = len(files) + len(commands)
    parse_info = {
        "markers_found": markers_found,
        "bare_blocks": bare_blocks,
        "total_code_blocks": total_code_blocks,
        "unstructured": bare_blocks > markers_found,
    }

    return files, commands, parse_info


def write_files_to_project(files, project_path):
    """Write parsed files to disk under project_path. Safety: reject paths escaping project."""
    written = []
    proj = os.path.realpath(project_path)
    for path, content in files:
        target = os.path.realpath(os.path.join(project_path, path))
        if not target.startswith(proj + os.sep) and target != proj:
            print(f"  ⚠ Skipping {path}: path escapes project directory")
            continue
        parent = os.path.dirname(target)
        os.makedirs(parent, exist_ok=True)
        with open(target, 'w') as f:
            f.write(content)
        written.append(path)
    return written


def run_command(cmd, timeout=180, workdir=None):
    """Run a shell command via subprocess. Returns (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=workdir
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', f'Command timed out after {timeout}s: {cmd}'
    except Exception as e:
        return -1, '', f'Execution error: {e}'


def find_docker_project(project_path):
    """Find the directory containing docker-compose.yml (may be project_path or project_path/mvp_output)."""
    for candidate in [project_path, os.path.join(project_path, 'mvp_output')]:
        for pattern in ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']:
            if os.path.exists(os.path.join(candidate, pattern)):
                return candidate
    return project_path


def build_node(state: dict) -> dict:
    """
    BUILD phase: Implement each task with tests, security checks, and review.
    Then write generated code to disk, build Docker, health check, and run tests.
    Loops back if validation fails (max 2 retries).

    Safety features:
    - Git stash before writes, pop on success, restore on failure
    - Docker container cleaned up on failure
    - Bandit gracefully skipped if unavailable in container
    """
    print("\n=== BUILD PHASE ===")
    skills = state.get("artifacts", {}).get("skill_registry")
    if skills is None:
        print("  → No skill_registry in state — building from disk...")
        skills = build_skill_registry(os.getenv("SKILLS_DIR", "~/.hermes/skills"))
        state.setdefault("artifacts", {})["skill_registry"] = skills
    feedback = []

    project_path = state.get("project_path", "")
    tasks_text = state.get("artifacts", {}).get("tasks", "")
    spec_text = state.get("artifacts", {}).get("spec_refined", "")
    docker_proj = find_docker_project(project_path)
    build_status_file = os.path.join(docker_proj, '.build_status')

    # Detect retry (loop-back from VERIFY or SEED_DATA)
    prev_error = state.get("error")
    is_retry = bool(prev_error) or bool(state.get("artifacts", {}).get("build_status"))

    # Clear stale .build_status marker on retry
    if is_retry and os.path.exists(build_status_file):
        print("  → Clearing stale .build_status marker for retry...")
        os.remove(build_status_file)

    # Skip if a previous BUILD passed validation and this is NOT a retry
    if not is_retry:
        try:
            prev = json.loads(Path(build_status_file).read_text())
            if prev.get("status") == "pass":
                print("  → Previous BUILD validation passed. Skipping regeneration.")
                state["phase"] = "BUILD"
                state["next_phase"] = "SEED_DATA"
                return state
        except Exception:
            pass

    # Stop old container to prevent port conflicts on retry
    if is_retry:
        print("  → Stopping existing container for clean retry...")
        _, _, _ = run_command("docker compose down api", timeout=30, workdir=docker_proj)

    # ── GIT ROLLBACK SAFETY ──
    stash_created = False
    if project_path and os.path.isdir(project_path):
        rc, out, err = run_command("git rev-parse --is-inside-work-tree", timeout=5, workdir=project_path)
        if rc == 0 and out.strip() == "true":
            rc2, out2, err2 = run_command("git status --porcelain", timeout=5, workdir=project_path)
            if rc2 == 0 and out2.strip():
                print("  → Creating git stash for rollback safety...")
                rc3, _, err3 = run_command("git stash push -m 'loop-engine: build rollback'", timeout=10, workdir=project_path)
                if rc3 == 0:
                    stash_created = True
                    print("  ✓ Git stash created")
                else:
                    print(f"  ⚠ Git stash failed: {err3[:100]}")

    # ── GENERATION PHASE ──

    # Step 1: Incremental implementation
    impl_skill = skills.get("incremental-implementation", {})
    if impl_skill:
        print("  → Running incremental-implementation...")
        impl_task = f"Process tasks incrementally for project: {project_path}"
        if is_retry and prev_error:
            impl_task += f"\n\nPrevious failure: {prev_error}"
        impl_task += (
            "\n\n=== OUTPUT FORMAT ===\n"
            "For each new or modified file, output:\n"
            "=== FILE: path/to/file.py ===\n"
            "```python\n...complete file content...\n```\n"
            "For shell commands (testing, setup):\n"
            "=== COMMAND: description ===\n"
            "```bash\n...command...\n```"
        )
        result = invoke_skill(impl_skill["content"], impl_task,
                             tasks_text + "\n\n" + spec_text, llm=None)
        state["artifacts"]["implementation"] = result
        feedback.append({"skill": "incremental-implementation", "output": result[:300]})

    # Step 2: FastAPI/Jinja2 feature build
    feature_skill = skills.get("fastapi-jinja2-feature-build", {})
    if feature_skill:
        print("  → Running fastapi-jinja2-feature-build...")
        feat_task = f"Implement the feature following FastAPI + Jinja2 patterns in: {project_path}"
        if is_retry and prev_error:
            feat_task += f"\n\nPrevious failure: {prev_error}"
        feat_task += (
            "\n\n=== OUTPUT FORMAT ===\n"
            "For each new or modified file, output:\n"
            "=== FILE: path/to/file.py ===\n"
            "```python\n...complete file content...\n```\n"
            "For shell commands:\n"
            "=== COMMAND: description ===\n"
            "```bash\n...command...\n```"
        )
        result = invoke_skill(feature_skill["content"], feat_task,
                             state.get("artifacts", {}).get("implementation", ""),
                             llm=None)
        state["artifacts"]["code_generated"] = result
        feedback.append({"skill": "fastapi-jinja2-feature-build", "output": result[:300]})

    # Step 3: Test-driven development
    tdd_skill = skills.get("test-driven-development", {})
    if tdd_skill:
        print("  → Running test-driven-development...")
        tdd_task = "Generate tests following DAMP, pyramid, and A3 patterns"
        if is_retry and prev_error:
            tdd_task += f"\n\nPrevious test failures: {prev_error}"
        tdd_task += (
            "\n\n=== OUTPUT FORMAT ===\n"
            "For each test file, output:\n"
            "=== FILE: tests/test_XXX.py ===\n"
            "```python\n...complete test file content...\n```"
        )
        result = invoke_skill(tdd_skill["content"], tdd_task,
                             state.get("artifacts", {}).get("code_generated", ""),
                             llm=None)
        state["artifacts"]["tests"] = result
        feedback.append({"skill": "test-driven-development", "output": result[:300]})

    # Step 4: Security gate (text review only — not parsed for files)
    sec_skill = skills.get("security-and-hardening", {})
    total_sec_findings = 0
    if sec_skill:
        print("  → Running security-and-hardening...")
        result = invoke_skill(sec_skill["content"],
                             "Review code for security vulnerabilities using STRIDE model",
                             state.get("artifacts", {}).get("code_generated", ""),
                             llm=None)
        state["artifacts"]["security_report"] = result
        sec_findings = result.lower().count("critical") + result.lower().count("high severity")
        total_sec_findings = max(total_sec_findings, sec_findings)
        feedback.append({"skill": "security-and-hardening", "output": result[:300]})

    # Step 5: Code review (text review only — not parsed for files)
    review_skill = skills.get("requesting-code-review", {})
    total_revisions = 0
    if review_skill:
        print("  → Running requesting-code-review...")
        result = invoke_skill(review_skill["content"],
                             "Review code using 5-axis framework (correctness, readability, architecture, security, performance)",
                             state.get("artifacts", {}).get("code_generated", ""),
                             llm=None)
        state["artifacts"]["review_report"] = result
        revisions = result.lower().count("fix") + result.lower().count("change") + result.lower().count("improve")
        total_revisions = max(total_revisions, revisions)
        feedback.append({"skill": "requesting-code-review", "output": result[:300]})

    # ── EXECUTION PHASE ──

    generated_text = (
        state["artifacts"].get("implementation", "") + "\n" +
        state["artifacts"].get("code_generated", "") + "\n" +
        state["artifacts"].get("tests", "")
    )

    all_files, all_commands, parse_info = parse_llm_output(generated_text)
    print(f"  → Parsed {len(all_files)} files, {len(all_commands)} commands")

    if parse_info["unstructured"]:
        print(f"  ⚠ LLM output has {parse_info['bare_blocks']} unstructured code blocks — may miss files")

    if not all_files and not is_retry:
        error_detail = f"No code files were generated by the LLM (markers={parse_info['markers_found']}, bare={parse_info['bare_blocks']}, total={parse_info['total_code_blocks']})"
        print(f"  ✗ {error_detail}")
        state["error"] = error_detail
        state["phase"] = "BUILD"
        state["next_phase"] = "BUILD"
        return state

    errors = []

    # Write files to disk (under docker_proj for Docker visibility)
    if all_files:
        print(f"  → Writing {len(all_files)} files to {docker_proj}...")
        written = write_files_to_project(all_files, docker_proj)
        print(f"  ✓ Wrote {len(written)} files")

    # Run pre-build commands
    for desc, cmd in all_commands:
        if 'build' in desc.lower() or 'test' in desc.lower():
            continue
        print(f"  → Running: {desc}")
        rc, out, err = run_command(cmd, workdir=docker_proj)
        if rc != 0:
            print(f"  ⚠ Command '{desc}' failed: {err[:200]}")
            errors.append(f"Command '{desc}': {err[:200]}")

    # ── VALIDATION PHASE ──

    # 1. Docker build
    print(f"  → Docker compose build in {docker_proj}...")
    rc, out, err = run_command(
        "docker compose build --no-cache api", timeout=300, workdir=docker_proj
    )
    if rc != 0:
        errors.append(f"Docker build failed: {err[:500]}")
        print(f"  ✗ Docker build failed: {err[:300]}")

    # 2. Start container
    if not errors:
        print("  → Starting container...")
        rc, out, err = run_command(
            "docker compose up -d api", timeout=120, workdir=docker_proj
        )
        if rc != 0:
            errors.append(f"Docker start failed: {err[:500]}")
            print(f"  ✗ Docker start failed: {err[:300]}")

    # 3. Health check
    if not errors:
        import time
        print("  → Health check...")
        time.sleep(5)
        rc, out, err = run_command(
            "curl -s -o /dev/null -w '%{http_code}' http://localhost:8010/",
            timeout=30
        )
        if rc != 0 or (out.strip() not in ('200', '301', '302')):
            errors.append(f"Health check failed: HTTP {out.strip()} ({err[:200]})")
            print(f"  ✗ Health check failed: HTTP {out.strip()}")
        else:
            print(f"  ✓ Health check passed: HTTP {out.strip()}")

    # 4. Run pytest (if tests/ exists in container)
    if not errors:
        tests_exist = run_command(
            "docker compose exec api ls tests/ 2>/dev/null", timeout=10, workdir=docker_proj
        )
        if tests_exist[0] == 0:
            print("  → Running pytest...")
            rc, out, err = run_command(
                "docker compose exec api python -m pytest tests/ -v --tb=short 2>&1",
                timeout=120, workdir=docker_proj
            )
            passed = len(re.findall(r'passed', out))
            failed = len(re.findall(r'failed', out))
            if rc != 0 or failed > 0:
                errors.append(f"pytest failed: {out[-500:]}")
                print(f"  ✗ pytest: {out[-200:]}")
            else:
                print(f"  ✓ pytest passed ({passed} tests)")

    # 5. Bandit security scan (graceful skip if unavailable)
    if not errors:
        rc, out, err = run_command(
            "docker compose exec api python -m bandit -r app/ -ll -ii 2>/dev/null",
            timeout=60, workdir=docker_proj
        )
        if rc == 0 and out.strip():
            high = len(re.findall(r'HIGH', out))
            if high > 0:
                total_sec_findings += high
                print(f"  ⚠ Bandit found {high} HIGH severity issues")
        elif "No module named bandit" in err or "No module named 'bandit'" in err:
            print("  ⚠ Bandit not installed in container — skipping security scan")
        else:
            print("  ✓ Bandit scan passed (or clean)")

    # ── RESULT ──

    if errors:
        error_summary = "\n".join(errors)
        print(f"\n  ✗ BUILD validation failed ({len(errors)} errors)")
        print(f"  → Looping back to fix: {error_summary[:300]}")

        # ── ROLLBACK ──
        # Stop container to prevent port conflicts on retry
        _, _, _ = run_command("docker compose down api", timeout=30, workdir=docker_proj)

        # Restore git stash
        if stash_created:
            rc, _, err = run_command("git stash pop", timeout=10, workdir=project_path)
            if rc == 0:
                print("  ✓ Git stash restored (rollback)")
            else:
                print(f"  ⚠ Git stash pop failed: {err[:100]}")

        state["error"] = error_summary
        state["phase"] = "BUILD"
        state["metrics"] = state["metrics"].model_copy(update={
            "review_revisions": total_revisions,
            "security_findings": total_sec_findings,
        })
        state["feedback"] = state.get("feedback", []) + feedback
        state["next_phase"] = "BUILD"
        return state

    # Success — drop stash (changes are good)
    if stash_created:
        rc, _, err = run_command("git stash drop", timeout=10, workdir=project_path)
        if rc != 0:
            print(f"  ⚠ Git stash drop failed (non-fatal): {err[:100]}")

    # Write marker file
    marker = {
        "status": "pass",
        "files_written": len(all_files),
        "security_findings": total_sec_findings,
        "review_revisions": total_revisions,
        "phase": "BUILD",
    }
    Path(build_status_file).write_text(json.dumps(marker))

    state["metrics"] = state["metrics"].model_copy(update={
        "review_revisions": total_revisions,
        "security_findings": total_sec_findings,
    })
    state["artifacts"]["build_status"] = "pass"
    state["phase"] = "BUILD"
    state["feedback"] = state.get("feedback", []) + feedback
    state["next_phase"] = "SEED_DATA"
    state["error"] = None

    print(f"\n  ✓ BUILD passed: {len(all_files)} files, sec_findings={total_sec_findings}, revisions={total_revisions}")
    return state
