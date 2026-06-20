"""
PLAN node: Generate implementation plan, break into tasks, analyze risks.
Skills: writing-plans → speckit-tasks → speckit-analyze → doubt-driven-development → speckit-checklist
"""
import os
from tools.loader import build_skill_registry
from tools.llm import invoke_skill


def _estimate_arch_uncertainty(artifacts: dict) -> float:
    """
    Derive architectural uncertainty from actual plan artifacts.

    Lower = more confident. Scoring starts at 0.6 and reduces:
    - Has plan with >200 chars: -0.15
    - Has tasks with >5 items: -0.15
    - Has analysis: -0.1
    - Has doubt_resolution: -0.1
    - Has checklist: -0.05
    - Analysis mentions 'low risk' or 'solid': -0.05
    - Analysis mentions 'unclear' or 'unknown' or 'risk': +0.15
    Range: [0.0, 1.0]
    """
    score = 0.6

    plan_text = artifacts.get("plan", "")
    tasks_text = artifacts.get("tasks", "")
    analysis_text = artifacts.get("analysis", "")
    doubt_text = artifacts.get("doubt_resolution", "")
    checklist_text = artifacts.get("checklist", "")

    if len(plan_text) > 200:
        score -= 0.15

    task_items = tasks_text.count("- [") + tasks_text.count("1.") + tasks_text.count("2.") + tasks_text.count("3.")
    if task_items >= 5:
        score -= 0.15
    elif task_items >= 1:
        score -= 0.1

    if len(analysis_text) > 50:
        score -= 0.1

    if len(doubt_text) > 50:
        score -= 0.1

    if len(checklist_text) > 50:
        score -= 0.05

    analysis_lower = analysis_text.lower()
    if any(kw in analysis_lower for kw in ["low risk", "solid", "clear path", "straightforward"]):
        score -= 0.05
    if any(kw in analysis_lower for kw in ["unclear", "unknown", "high risk", "major concern"]):
        score += 0.15

    return max(0.0, min(1.0, score))


def plan_node(state: dict) -> dict:
    """
    PLAN phase: Generate implementation plan, break into tasks,
    analyze architectural risks, generate checklist.
    Derives arch_uncertainty from actual artifact quality.
    """
    print("\n=== PLAN PHASE ===")
    skills = state.get("artifacts", {}).get("skill_registry")
    if skills is None:
        print("  → No skill_registry in state — building from disk...")
        skills = build_skill_registry(os.getenv("SKILLS_DIR", "~/.hermes/skills"))
        state.setdefault("artifacts", {})["skill_registry"] = skills
    feedback = []

    # Step 1: Generate plan
    plan_skill = skills.get("writing-plans", {})
    if plan_skill:
        print("  → Running writing-plans...")
        spec = state.get("artifacts", {}).get("spec_refined", "")
        task = f"Create implementation plan for: {state.get('spec_path', '')}"
        result = invoke_skill(plan_skill["content"], task, spec, llm=None)
        state["artifacts"]["plan"] = result
        feedback.append({"skill": "writing-plans", "output": result[:300]})

    # Step 2: Break into tasks
    tasks_skill = skills.get("speckit-tasks", {})
    if tasks_skill:
        print("  → Running speckit-tasks...")
        task = "Break the plan into actionable, dependency-ordered tasks"
        result = invoke_skill(tasks_skill["content"], task,
                             state.get("artifacts", {}).get("plan", ""),
                             llm=None)
        state["artifacts"]["tasks"] = result
        # Count tasks for metrics
        task_count = result.count("- [") + result.count("1.") + result.count("2.") + result.count("3.")
        state["metrics"] = state["metrics"].model_copy(update={
            "task_count": max(task_count, 1),
        })
        feedback.append({"skill": "speckit-tasks", "output": result[:300]})

    # Step 3: Analyze cross-artifact consistency
    analyze_skill = skills.get("speckit-analyze", {})
    if analyze_skill:
        print("  → Running speckit-analyze...")
        task = "Analyze consistency between spec, plan, and tasks"
        result = invoke_skill(analyze_skill["content"], task,
                             state.get("artifacts", {}).get("plan", ""),
                             llm=None)
        state["artifacts"]["analysis"] = result
        feedback.append({"skill": "speckit-analyze", "output": result[:300]})

    # Step 4: Doubt-driven development (challenge assumptions)
    doubt_skill = skills.get("doubt-driven-development", {})
    if doubt_skill:
        print("  → Running doubt-driven-development...")
        task = "Challenge the architectural assumptions in the plan"
        result = invoke_skill(doubt_skill["content"], task,
                             state.get("artifacts", {}).get("plan", ""),
                             llm=None)
        state["artifacts"]["doubt_resolution"] = result
        feedback.append({"skill": "doubt-driven-development", "output": result[:300]})

    # Step 5: Generate checklist
    checklist_skill = skills.get("speckit-checklist", {})
    if checklist_skill:
        print("  → Running speckit-checklist...")
        task = "Generate a custom checklist for this feature"
        result = invoke_skill(checklist_skill["content"], task,
                             state.get("artifacts", {}).get("spec_refined", ""),
                             llm=None)
        state["artifacts"]["checklist"] = result
        feedback.append({"skill": "speckit-checklist", "output": result[:300]})

    # Derive architectural uncertainty from actual artifact quality
    arch_uncertainty = _estimate_arch_uncertainty(state["artifacts"])
    state["metrics"] = state["metrics"].model_copy(update={
        "arch_uncertainty": arch_uncertainty,
    })
    state["phase"] = "PLAN"
    state["feedback"] = state.get("feedback", []) + feedback
    state["next_phase"] = "BUILD"

    print(f"  ✓ task_count={state['metrics'].task_count}, arch_uncertainty={arch_uncertainty:.2f}")
    return state
