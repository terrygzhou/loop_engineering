"""
ARCH_REVIEW node: Pause for user review of all Plan outputs.

Uses LangGraph OOTB: interrupt_after=["ARCH_REVIEW"] handles the suspension.
Node just sets state — no manual GraphInterrupt needed.
"""


def arch_review_node(state: dict) -> dict:
    """Set phase and return. interrupt_after handles suspension natively."""
    state["phase"] = "ARCH_REVIEW"
    state["human_approval_required"] = True
    return state
