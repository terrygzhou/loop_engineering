"""
Conditional edge routing for the LangGraph workflow.
Thresholds loaded from guardrails.yaml at runtime so REFLECT can update them.
"""
from langgraph.graph import END
from graph.state import WorkflowState
from config.guardrails import get_threshold

# Export END marker for use in main.py
END_MARKER = END

# Per-cycle loop counts stored in state["artifacts"]["loop_counts"] — never global.
# Forward paths for forced progression after max retries (prevents livelock).
_forward_paths = {
    "DISCOVER": "DEFINE",
    "DEFINE": "PLAN",
    "PLAN": "BUILD",
    "BUILD": "SEED_DATA",
    "SEED_DATA": "VERIFY",
    "VERIFY": "SHIP",
}


def _get_loop_count(state: WorkflowState, phase: str) -> int:
    """Thread-safe loop counter from state artifacts."""
    counts = state.get("artifacts", {}).get("loop_counts", {})
    return counts.get(phase, 0)


def _inc_loop_count(state: WorkflowState, phase: str) -> None:
    """Increment and persist loop count in state."""
    counts = state.setdefault("artifacts", {}).setdefault("loop_counts", {})
    counts[phase] = counts.get(phase, 0) + 1


def route_phase(state: WorkflowState) -> str:
    """
    Route to the next phase based on current phase and metrics.
    Implements quality gates that can loop back to earlier phases.
    Loop counts live in state to avoid cross-cycle bleed.
    """
    phase = state["phase"]
    m = state["metrics"]
    error = state.get("error")

    loop_count = _get_loop_count(state, phase)
    if loop_count >= 2:
        _inc_loop_count(state, phase)  # reset via overwrite below
        state.setdefault("artifacts", {}).setdefault("loop_counts", {})[phase] = 0
        return _forward_paths.get(phase, END)

    # If there's an error AND no more retries available, end the workflow
    if error and loop_count >= 2:
        return END

    # Load thresholds from guardrails (REFLECT can update between cycles)
    min_spec_conf = get_threshold("min_spec_confidence")
    max_arch_uncert = get_threshold("max_arch_uncertainty")
    max_sec_findings = get_threshold("max_security_findings")
    max_rev_revisions = get_threshold("max_review_revisions")
    min_uat_pass = get_threshold("uat_pass_rate")

    # DEFINE -> check spec confidence
    if phase == "DEFINE":
        if m.spec_confidence < min_spec_conf:
            _inc_loop_count(state, phase)
            return "DEFINE"  # Loop back to refine spec
        return "PLAN"

    # PLAN -> check architectural uncertainty
    if phase == "PLAN":
        if m.arch_uncertainty > max_arch_uncert:
            _inc_loop_count(state, phase)
            return "PLAN"  # Loop back to resolve doubts
        return "BUILD"

    # BUILD -> check security and review gates
    if phase == "BUILD":
        if m.security_findings > max_sec_findings:
            _inc_loop_count(state, phase)
            return "BUILD"  # Fix security issues first
        if m.review_revisions > max_rev_revisions:
            _inc_loop_count(state, phase)
            return "BUILD"  # Too many revisions, needs simplification
        return "SEED_DATA"

    # SEED_DATA -> check if seed executed successfully
    if phase == "SEED_DATA":
        if state.get("artifacts", {}).get("seed_errors"):
            _inc_loop_count(state, phase)
            return "BUILD"  # Seed failed, rebuild
        return "VERIFY"

    # VERIFY -> check UAT pass rate
    if phase == "VERIFY":
        if m.uat_pass_rate < min_uat_pass:
            _inc_loop_count(state, phase)
            return "BUILD"  # UAT failed, rebuild
        return "SHIP"

    # SHIP -> always reflect
    if phase == "SHIP":
        return "REFLECT"

    # Default: END
    return END
