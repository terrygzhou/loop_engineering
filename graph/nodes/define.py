"""
DEFINE node: Elicit requirements, generate spec, design API contracts.
Skills: interview-me → speckit-specify → api-and-interface-design
"""
import os
from tools.loader import build_skill_registry, find_skills_by_trigger
from tools.llm import invoke_skill


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

    # Step 1: Interview (if spec is vague)
    interview_skill = skills.get("interview-me", {})
    if interview_skill:
        print("  → Running interview-me...")
        spec_path = state.get("spec_path", "")
        task = f"Elicit requirements for the feature at: {spec_path}"
        context = f"Project context: {project_context}" if project_context else ""
        result = invoke_skill(interview_skill["content"], task, context, llm=None)
        state["artifacts"]["interview_notes"] = result
        feedback.append({"skill": "interview-me", "output": result[:300]})

    # Step 2: Generate/refine spec
    specify_skill = skills.get("speckit-specify", {})
    if specify_skill:
        print("  → Running speckit-specify...")
        context = f"Spec path: {state.get('spec_path', '')}\n"
        if project_context:
            context += f"Existing project context:\n{project_context}\n"
        context += state.get("artifacts", {}).get("interview_notes", "")
        task = f"Review and refine the feature specification at: {state.get('spec_path', '')}"
        result = invoke_skill(specify_skill["content"], task, context, llm=None)
        state["artifacts"]["spec_refined"] = result
        feedback.append({"skill": "speckit-specify", "output": result[:300]})

    # Step 3: API design
    api_skill = skills.get("api-and-interface-design", {})
    if api_skill:
        print("  → Running api-and-interface-design...")
        task = "Design API contracts and interface boundaries for this feature"
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
    state["next_phase"] = "PLAN"

    print(f"  ✓ spec_confidence={spec_confidence:.2f} (derived from artifact quality)")
    return state
