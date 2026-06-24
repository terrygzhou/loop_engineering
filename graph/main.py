"""
Graph compilation: wire up the LangGraph workflow with all nodes and edges.
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from graph.state import WorkflowState
from graph.nodes.discover import discover_node
from graph.nodes.define import define_node
from graph.nodes.human_review import human_review_node
from graph.nodes.plan import plan_node
from graph.nodes.build import build_node
from graph.nodes.seed_data import seed_data_node
from graph.nodes.verify import verify_node
from graph.nodes.ship import ship_node
from graph.nodes.reflect import reflect_node
from graph.edges import route_phase


def build_graph(checkpointer=None):
    """
    Build and compile the LangGraph workflow.

    Flow: DISCOVER -> DEFINE -> HUMAN_REVIEW -> PLAN -> BUILD -> SEED_DATA -> VERIFY -> SHIP -> REFLECT -> END
    With conditional routing for quality gates.

    HUMAN_REVIEW node pauses for human approval of spec/design before proceeding to PLAN.
    Uses interrupt_after on HUMAN_REVIEW, PLAN, and VERIFY nodes so the executor can
    pause for HIL gates and resume with updated state.
    """
    workflow = StateGraph(WorkflowState)

    # Register nodes
    workflow.add_node("DISCOVER", discover_node)
    workflow.add_node("DEFINE", define_node)
    workflow.add_node("HUMAN_REVIEW", human_review_node)
    workflow.add_node("PLAN", plan_node)
    workflow.add_node("BUILD", build_node)
    workflow.add_node("SEED_DATA", seed_data_node)
    workflow.add_node("VERIFY", verify_node)
    workflow.add_node("SHIP", ship_node)
    workflow.add_node("REFLECT", reflect_node)

    # Wire edges
    workflow.add_edge(START, "DISCOVER")
    workflow.add_edge("DISCOVER", "DEFINE")
    workflow.add_edge("DEFINE", "HUMAN_REVIEW")

    # HUMAN_REVIEW -> conditional: approve → PLAN, reject → DEFINE
    workflow.add_conditional_edges("HUMAN_REVIEW", route_phase)

    # Conditional routing with quality gates
    workflow.add_conditional_edges("PLAN", route_phase)
    workflow.add_conditional_edges("BUILD", route_phase)
    workflow.add_conditional_edges("SEED_DATA", route_phase)
    workflow.add_conditional_edges("VERIFY", route_phase)

    # SHIP -> always reflect
    workflow.add_edge("SHIP", "REFLECT")

    # REFLECT -> END
    workflow.add_edge("REFLECT", END)

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_after=["HUMAN_REVIEW", "PLAN", "VERIFY"],
    )
