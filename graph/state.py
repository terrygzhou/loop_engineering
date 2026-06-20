"""
WorkflowState definition for the self-improving AI loop.
"""
from typing import TypedDict, List, Optional
from pydantic import BaseModel


class CycleMetrics(BaseModel):
    """Metrics collected during a workflow cycle."""
    review_revisions: int = 0
    security_findings: int = 0
    test_flakiness_rate: float = 0.0
    latency_ms: float = 0.0
    uat_pass_rate: float = 0.0
    spec_confidence: float = 0.0
    task_count: int = 0
    arch_uncertainty: float = 0.0
    launch_success: bool = False
    seed_executed: bool = False


class WorkflowState(TypedDict):
    """LangGraph state for the self-improving AI loop."""
    cycle_id: str                          # Unique ID for this cycle
    phase: str                             # Current phase: DISCOVER/DEFINE/PLAN/BUILD/SEED_DATA/VERIFY/SHIP/REFLECT
    artifacts: dict[str, str]              # spec.yaml, tasks.md, code diffs, logs, etc.
    metrics: CycleMetrics                  # Collected metrics
    feedback: List[dict]                   # LLM review comments, debug traces, etc.
    config_version: str                    # Git commit hash of skill configs
    human_approval_required: bool          # True if next action needs human approval
    next_phase: Optional[str]              # Suggested next phase (edges can override)
    project_path: str                      # Path to the target project
    spec_path: str                         # Path to the spec directory
    error: Optional[str]                   # Error message if phase failed
