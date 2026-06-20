#!/usr/bin/env python3
"""
Test the loop engine against the 012-dashboard spec.
Runs the full graph in dry-run mode (no LLM).
"""
import os
import sys

# Set up paths
sys.path.insert(0, '/home/terry/workspace/projects/loop_engineering')
os.chdir('/home/terry/workspace/projects/loop_engineering')

# Set environment
os.environ["SKILLS_DIR"] = "/home/terry/.hermes/skills"
os.environ["STORAGE_DIR"] = "/home/terry/workspace/projects/loop_engineering/storage"
os.environ["GUARDRAILS_PATH"] = "/home/terry/workspace/projects/loop_engineering/config/guardrails.yaml"
os.environ["HIL_MODE"] = "cli"

# Import graph builder
from graph.main import build_graph
from graph.state import CycleMetrics

# Test: build the graph
print("=" * 60)
print("TEST: Building LangGraph workflow")
print("=" * 60)

try:
    graph = build_graph()  # No checkpointer for test
    print("✓ Graph built successfully")
except Exception as e:
    print(f"✗ Graph build failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test: create initial state for 012-dashboard
print("\n" + "=" * 60)
print("TEST: Creating initial state for 012-dashboard")
print("=" * 60)

spec_path = "/home/terry/workspace/projects/GloryEV_CustomerApp/specs/012-dashboard"
project_path = "/home/terry/workspace/projects/GloryEV_CustomerApp"

initial_state = {
    "cycle_id": "test-dashboard-001",
    "phase": "DEFINE",
    "artifacts": {},
    "metrics": CycleMetrics(),
    "feedback": [],
    "config_version": "initial",
    "human_approval_required": False,
    "next_phase": "PLAN",
    "project_path": project_path,
    "spec_path": spec_path,
    "error": None,
}

print(f"✓ Spec path: {spec_path}")
print(f"✓ Project path: {project_path}")
print(f"✓ Cycle ID: {initial_state['cycle_id']}")

# Test: run the graph
print("\n" + "=" * 60)
print("TEST: Running workflow (dry-run mode)")
print("=" * 60)

try:
    result = graph.invoke(initial_state)
    print("\n" + "=" * 60)
    print("✓ Workflow completed successfully")
    print("=" * 60)
    
    # Print metrics
    print("\n--- Cycle Metrics ---")
    metrics = result.get("metrics", {})
    for field in CycleMetrics.model_fields:
        if hasattr(metrics, field):
            val = getattr(metrics, field)
            if val is not None:
                print(f"  {field}: {val}")
        elif isinstance(metrics, dict):
            val = metrics.get(field)
            if val is not None:
                print(f"  {field}: {val}")
    
    print(f"\n--- Feedback entries: {len(result.get('feedback', []))} ---")
    for fb in result.get("feedback", [])[:10]:
        print(f"  • {fb}")
    
    if len(result.get("feedback", [])) > 10:
        print(f"  ... and {len(result['feedback']) - 10} more")
    
    print(f"\n--- Artifacts: {len(result.get('artifacts', {}))} ---")
    for key, val in result.get("artifacts", {}).items():
        if isinstance(val, str):
            print(f"  • {key}: {len(val)} chars")
        else:
            print(f"  • {key}: {type(val).__name__}")
    
    print(f"\n--- Final phase: {result.get('phase')} ---")
    
except Exception as e:
    print(f"\n✗ Workflow execution failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("TEST RESULT: ALL CHECKS PASSED")
print("=" * 60)
