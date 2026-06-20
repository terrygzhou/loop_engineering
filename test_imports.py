#!/usr/bin/env python3
"""Test all imports for loop_engineering."""
import sys
sys.path.insert(0, '/home/terry/workspace/projects/loop_engineering')

print("1. State...")
from graph.state import WorkflowState, CycleMetrics
print("   OK")

print("2. Edges...")
from graph.edges import route_phase
print("   OK")

print("3. Loader...")
from tools.loader import build_skill_registry
print("   OK")

print("4. LLM (dry-run)...")
from tools.llm import get_llm
llm = get_llm()
print(f"   OK (llm={llm})")

print("5. Aggregator...")
from feedback.aggregator import FeedbackAggregator
print("   OK")

print("6. DiffEngine...")
from feedback.diff_engine import generate_config_diffs
print("   OK")

print("7. ChromaDB (dry-run)...")
from feedback.chroma_client import get_chroma_client
client = get_chroma_client()
print(f"   OK (client={client})")

print("\nAll imports successful.")
