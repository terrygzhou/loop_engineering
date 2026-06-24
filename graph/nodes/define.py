"""
DEFINE node: Elicit requirements, generate spec, design API contracts.
Skills: interview-me → speckit-specify → api-and-interface-design
"""
import os
import re
from tools.loader import build_skill_registry, find_skills_by_trigger
from tools.llm import invoke_skill
from config.loader import config
from config.prompt_templates import interview_me, speckit_specify, api_and_interface_design
from feedback.chroma_client import get_chroma_client, query_patterns


def _load_feedback_context(state: dict) -> str:
    """Query ChromaDB for historical patterns relevant to this project type.
    Returns a formatted text block of lessons learned from past cycles.
    Gracefully degrades to empty string if ChromaDB unavailable.
    """
    try:
        client = get_chroma_client()
        if client is None:
            return ""

        # Build query from available context
        project_name = state.get("project_name", "unknown")
        project_ctx = state.get("artifacts", {}).get("project_context", "")
        metrics = state.get("metrics", {})
        query_text = f"project: {project_name} context: {project_ctx[:500]}"

        results = query_patterns(client, {"project": project_name, "context": query_text[:500]}, top_k=3)
        if not results:
            return ""

        # Format results as lessons learned
        parts = ["== Historical Lessons Learned =="]
        for i, pat in enumerate(results, 1):
            doc = pat.get("document", "")
            parts.append(f"\n[Past Cycle {i}] (similarity distance: {pat.get('distance', '?'):.3f})\n{doc[:400]}")
        parts.append("\n== End Historical Lessons ==")

        text = "\n".join(parts)
        print(f"  → Loaded {len(results)} historical feedback patterns")
        return text
    except Exception as e:
        print(f"  ⚠ Could not load historical feedback: {e}")
        return ""


def _estimate_spec_confidence(artifacts: dict) -> float:
    """
    Derive spec confidence from actual artifact content.

    Scoring:
    - Has refined spec text: +0.3
    - Has API contract: +0.2
    - Has interview notes: +0.15
    - Spec mentions acceptance criteria: +0.15
    - Spec mentions edge cases: +0.1
    - Spec mentions error handling: +0.1
    Cap at 1.0.
    """
    score = 0.0
    spec_text = artifacts.get("spec_refined", "")
    api_text = artifacts.get("api_contract", "")
    interview_text = artifacts.get("interview_notes", "")

    if spec_text and len(spec_text) > 100:
        score += 0.3

    if api_text and len(api_text) > 50:
        score += 0.2

    if interview_text and len(interview_text) > 50:
        score += 0.15

    spec_lower = spec_text.lower()
    if any(kw in spec_lower for kw in ["given", "when", "then", "acceptance", "criteria", "scenario"]):
        score += 0.15
    if any(kw in spec_lower for kw in ["edge case", "edge-case", "edge case", "corner case", "empty", "invalid", "error"]):
        score += 0.1
    if any(kw in spec_lower for kw in ["error handling", "exception", "failure", "rollback", "fallback"]):
        score += 0.1

    return min(score, 1.0)


def define_node(state: dict) -> dict:
    """
    DEFINE phase: Gather requirements through interview, generate spec,
    design API interfaces. Uses project_context from DISCOVER to inform
    spec creation with awareness of existing code, routes, and models.
    Derives spec_confidence from actual artifact quality.
    """
    print("\n=== DEFINE PHASE ===")

    # ── Capture project name and persist to config ──
    project_name = state.get("project_name", "") or state.get("artifacts", {}).get("project_name", "")
    if project_name:
        # Sanitize: reject path traversal and non-safe characters
        if not re.match(r'^[a-zA-Z0-9_-]+$', project_name):
            print(f"  ⚠ Invalid project name '{project_name}' — sanitizing to safe identifier")
            project_name = re.sub(r'[^a-zA-Z0-9_-]', '_', project_name).strip('_')
        try:
            config.set_project_name(project_name)
            state["project_name"] = project_name
            state["artifacts"]["project_name"] = project_name
            state["project_path"] = config.paths.project_path
            print(f"  → Project: {project_name} → {config.paths.project_path}")
        except ValueError as e:
            print(f"  ✗ {e}")
    else:
        print("  ⚠ No project_name — using config default")

    skills = state.get("artifacts", {}).get("skill_registry")
    if skills is None:
        print("  → No skill_registry in state — building from disk...")
        skills = build_skill_registry(os.getenv("SKILLS_DIR", "~/.hermes/skills"))
        state.setdefault("artifacts", {})["skill_registry"] = skills
    feedback = []

    # Load project context from DISCOVER (if available)
    project_context = state.get("artifacts", {}).get("project_context", "")
    if project_context:
        print(f"  → Using project_context from DISCOVER ({len(project_context)} chars)")
    else:
        print("  ⚠ No project_context — DISCOVER may have been skipped")

    # ── Load historical feedback context from ChromaDB ──
    feedback_context = _load_feedback_context(state)
    state["feedback_context"] = feedback_context

    # Step 1: Interview (adaptive question tree with ToT→CoT)
    # Rationale: interview-me skill already handles one-Q-at-a-time flow.
    # Task prompt frames WHAT to explore, not HOW to ask.
    interview_skill = skills.get("interview-me", {})
    if interview_skill:
        print("  → Running interview-me...")
        spec_path = state.get("spec_path", "")
        task = interview_me.format(spec_path=spec_path)
        if feedback_context:
            task += f"\n\n{feedback_context}\n"
        context = f"Project context: {project_context}" if project_context else ""
        result = invoke_skill(interview_skill["content"], task, context, llm=None)
        state["artifacts"]["interview_notes"] = result
        feedback.append({"skill": "interview-me", "output": result[:300]})

    # Step 2: Generate/refine spec (structured with traceability + ToT→CoT)
    # Rationale: spec feeds directly into PLAN→BUILD; each section maps to downstream tasks.
    # Traceability chain: user story → acceptance criteria → edge case → dependency.
    specify_skill = skills.get("speckit-specify", {})
    if specify_skill:
        print("  → Running speckit-specify...")
        context = f"Spec path: {state.get('spec_path', '')}\n"
        if project_context:
            context += f"Existing project context:\n{project_context}\n"
        context += state.get("artifacts", {}).get("interview_notes", "")
        if feedback_context:
            context += f"\n\n{feedback_context}\n"
        task = speckit_specify.format(spec_path=state.get("spec_path", ""))
        result = invoke_skill(specify_skill["content"], task, context, llm=None)
        state["artifacts"]["spec_refined"] = result
        feedback.append({"skill": "speckit-specify", "output": result[:300]})

    # Step 3: API/interface design (multi-interface, contract-first + ToT→CoT)
    # Rationale: not every feature is REST. Handle API, CLI, DB schema, event bus.
    # Contract guarantees are non-negotiable for downstream BUILD phase.
    api_skill = skills.get("api-and-interface-design", {})
    if api_skill:
        print("  → Running api-and-interface-design...")
        task = api_and_interface_design
        result = invoke_skill(api_skill["content"], task,
                             state.get("artifacts", {}).get("spec_refined", ""),
                             llm=None)
        state["artifacts"]["api_contract"] = result
        feedback.append({"skill": "api-and-interface-design", "output": result[:300]})

    # Derive spec_confidence from actual artifact quality (not hardcoded)
    spec_confidence = _estimate_spec_confidence(state["artifacts"])
    state["metrics"] = state["metrics"].model_copy(update={
        "spec_confidence": spec_confidence,
    })
    state["phase"] = "DEFINE"
    state["feedback"] = state.get("feedback", []) + feedback
    state["next_phase"] = "HUMAN_REVIEW"
    state["human_approval_required"] = False

    print(f"  ✓ spec_confidence={spec_confidence:.2f} (derived from artifact quality)")
    return state
