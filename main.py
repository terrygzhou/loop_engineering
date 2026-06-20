"""
Loop Engineering main entry point.
Builds and runs the state graph for autonomous feature development cycles.
"""
import asyncio
import os
import sys
from tools.loader import build_skill_registry
from graph.state import WorkflowState, CycleMetrics
from graph.main import build_graph


async def run_workflow():
    """
    Run one complete loop engineering cycle.
    Pre-builds skill registry and injects into state to avoid per-node disk scans.
    """
    # Pre-build skill registry (once, at graph build time)
    skills_dir = os.getenv("SKILLS_DIR", "~/.hermes/skills")
    print(f"→ Pre-building skill registry from {skills_dir}...")
    skill_registry = build_skill_registry(skills_dir)
    print(f"✓ Loaded {len(skill_registry)} skills: {', '.join(skill_registry.keys())}")

    # Build graph
    graph = build_graph()

    # Initialize state with pre-built skill registry
    state = WorkflowState(
        cycle_id="1",
        phase="DISCOVER",
        next_phase="DEFINE",
        metrics=CycleMetrics(
            spec_confidence=0.0,
            arch_uncertainty=0.0,
            task_count=0,
            review_revisions=0,
            security_findings=0,
            uat_pass_rate=0.0,
            latency_ms=0.0,
            test_flakiness_rate=0.0,
            launch_success=False,
        ),
        config_version="1",
        artifacts={
            "skill_registry": skill_registry,
            "loop_counts": {},  # State-based loop counters (replaces global _loop_counter)
        },
        feedback=[],
        error=None,
        spec_path="",
        project_path=os.getenv("PROJECT_PATH", ""),
    )

    # Run the graph
    result = await graph.ainvoke(state)
    return result


if __name__ == "__main__":
    print("=== Loop Engineering — Starting ===")
    try:
        result = asyncio.run(run_workflow())
        print(f"\n=== Cycle {result['cycle_id']} complete ===")
        print(f"Phase: {result['phase']}")
        print(f"Metrics: {result['metrics'].model_dump()}")
        print(f"Errors: {result['error']}")
        print(f"Feedback entries: {len(result.get('feedback', []))}")
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
