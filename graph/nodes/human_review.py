"""
Human review node: pause between DEFINE and PLAN for human approval.

Displays the spec, API contract, and interview notes from DEFINE output
for the human to review before proceeding to PLAN.

Uses the shared review_contract for section definitions and formatting.
"""
from graph.state import WorkflowState
from graph.nodes.review_contract import (
    build_review_sections,
    build_review_summary,
    build_review_metrics,
    format_review_section_for_cli,
    format_review_summary_for_cli,
)


def human_review_node(state: WorkflowState) -> WorkflowState:
    """
    Pause the workflow for human review of DEFINE output.

    Displays the full spec, API contract, and interview notes in a
    human-readable terminal layout. Collects per-section approval
    and structured feedback. Routes to PLAN on approval, back to
    DEFINE on rejection.
    """
    print("\n=== HUMAN REVIEW: DEFINE Output ===")

    artifacts = state.get("artifacts", {})
    sections = build_review_sections(artifacts)

    # Summary first
    print(format_review_summary_for_cli(sections))

    # Show full content for each section
    for sec in sections:
        if sec["content"]:
            print(format_review_section_for_cli(sec["label"].upper(), sec["content"]))
        else:
            print(f"\n  [{sec['label'].upper()}]: (not provided)")

    # Show metrics
    metrics = build_review_metrics(state)
    print(f"\n  spec_confidence: {metrics['spec_confidence']:.2f}")

    # Mark this node output for the HIL handler
    state["phase"] = "HUMAN_REVIEW"
    state["human_approval_required"] = True

    print("\n  → Awaiting human review...\n")
    return state
