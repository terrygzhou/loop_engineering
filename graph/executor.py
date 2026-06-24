"""
Shared executor — singleton workflow core for both CLI (main.py) and Web (app.py).

Both modes import this module. Graph construction, state initialization, and
node execution are identical. Only the UX layer (CLI prompts vs WebSocket) differs.
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, Optional

# Ensure project root is on path so config.loader resolves
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from config.loader import config  # noqa: E402
from graph.main import build_graph  # noqa: E402
from graph.state import CycleMetrics, WorkflowState  # noqa: E402
from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from tools.loader import build_skill_registry  # noqa: E402


def get_skills_dir() -> str:
    """Resolve skills directory — config > Docker mount > local default."""
    sd = config.paths.skills_dir
    # Docker override: if /app/skills exists, prefer it
    if Path("/app/skills").exists():
        return "/app/skills"
    return sd


def get_project_path() -> str:
    """Resolve project output directory from config (env var > config.yaml > default)."""
    return config.paths.project_path


def build_executor_state(
    cycle_id: str = "1",
    project_name: str = "",
    spec_text: str = "",
    context_folder: str = "",
) -> WorkflowState:
    """
    Build initial WorkflowState with pre-loaded skill registry.

    Both CLI and Web call this function — identical state for both modes.
    """
    skills_dir = get_skills_dir()
    print(f"[Executor] Loading skills from {skills_dir}...")
    skill_registry = build_skill_registry(skills_dir)
    print(f"[Executor] ✓ Loaded {len(skill_registry)} skills")

    skip_discover = not bool(context_folder)

    return WorkflowState(
        cycle_id=cycle_id,
        phase="DISCOVER",
        next_phase="DEFINE",
        project_name=project_name,
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
            "loop_counts": {},
            "project_name": project_name,
        },
        feedback=[],
        error=None,
        spec_path=spec_text,
        project_path=get_project_path(),
        skip_discover=skip_discover,
        context_folder=context_folder,
        human_approval_required=False,
    )


def get_graph(checkpointer=None):
    """Build and compile the LangGraph workflow. Pass a checkpointer for interrupt support."""
    return build_graph(checkpointer=checkpointer)


class WorkflowRunner:
    """
    Shared workflow runner. Both CLI and Web use this.

    The only difference is the HIL handler:
    - CLI: asks input() on stdin/stdout
    - Web: sends WebSocket events and waits for user reply

    Each runner gets its own MemorySaver checkpointer + unique thread_id
    for proper interrupt/resume support.
    """

    HIL_PHASES = {"HUMAN_REVIEW", "PLAN", "VERIFY"}

    def __init__(self):
        import uuid as _uuid
        self.checkpointer = MemorySaver()
        self.graph = get_graph(checkpointer=self.checkpointer)
        self.thread_id = str(_uuid.uuid4())

    def run_interactive(
        self,
        project_name: str = "",
        spec_text: str = "",
        context_folder: str = "",
        auto_approve: bool = False,
    ):
        """
        Run the workflow synchronously. Collects user input via stdin/stdout.

        Args:
            project_name: Name of the project being built.
            spec_text: Initial idea / requirements text.
            context_folder: Path to existing codebase for discovery (optional).
            auto_approve: If True, skip all HIL gates (default for CI/headless).
        """
        cycle_id = "1"
        state = build_executor_state(
            cycle_id=cycle_id,
            project_name=project_name,
            spec_text=spec_text,
            context_folder=context_folder,
        )

        if state.get("skip_discover"):
            print("\n[DISCOVER] Skipped — no context folder (greenfield mode)\n")
        else:
            print(f"\n[DISCOVER] Scanning {context_folder}...")

        # Stream through each node and collect HIL input
        import asyncio

        async def _run():
            last = None
            async for chunk in self._astream_with_hil(state, auto_approve, on_hil=self._hil_cli):
                last = chunk
            return last

        result = asyncio.run(_run())
        return result

    async def _astream_with_hil(self, state: WorkflowState, auto_approve: bool, on_hil, config=None):
        """Stream graph execution with HIL gates via LangGraph interrupt_after.

        astream() raises langgraph.types.interrupt at checkpoint boundaries.
        Catch the exception, handle HIL, update state, and resume.
        """
        import uuid as _uuid
        from langgraph.errors import GraphInterrupt
        if config is None:
            config = {"configurable": {"thread_id": str(_uuid.uuid4())}}

        current_phase = None
        input_state = state  # first pass: initial state; subsequent: None to resume

        while True:
            try:
                async for chunk in self.graph.astream(
                    input_state, stream_mode="values", config=config
                ):
                    phase = chunk.get("phase", "UNKNOWN")

                    if phase != current_phase:
                        if current_phase:
                            print(f"\n[{current_phase}] Completed\n")
                        current_phase = phase
                        print(f"[{phase}] Started...")

                    yield chunk

            except GraphInterrupt as e:
                # Graph paused at interrupt_after — handle HIL gate
                print(f"  → GraphInterrupt caught: {e}")
                graph_state = await self.graph.aget_state(config)
                is_interrupted = graph_state.next is not None and len(graph_state.next) > 0

                if not is_interrupted:
                    if current_phase:
                        print(f"\n[{current_phase}] Completed\n")
                    break

                next_nodes = graph_state.next
                interrupted_phase = current_phase
                current_chunk = graph_state.values or {}

                if not current_chunk:
                    print(f"  → WARNING: graph_state.values is None for phase {interrupted_phase}")

                if interrupted_phase and interrupted_phase in self.HIL_PHASES:
                    needs_approval = current_chunk.get("human_approval_required", False)

                    if needs_approval:
                        try:
                            if auto_approve:
                                print(f"  → Auto-approved {interrupted_phase}")
                                interview_answers = self._default_interview(
                                    graph_state.values or {}
                                )
                                update = {
                                    "human_approval_required": False,
                                    "artifacts": {
                                        **(current_chunk.get("artifacts") or {}),
                                        "interview_notes": interview_answers,
                                        "user_input": {"approved": True},
                                    },
                                }
                            else:
                                input_data = await on_hil(interrupted_phase, current_chunk)
                                update = {
                                    "human_approval_required": False,
                                }
                                if input_data:
                                    existing = (current_chunk.get("artifacts") or {}).copy()
                                    existing["user_input"] = input_data
                                    if "interview_notes" in input_data:
                                        existing["interview_notes"] = input_data[
                                            "interview_notes"
                                        ]
                                    if interrupted_phase == "HUMAN_REVIEW" and input_data.get("section_feedback"):
                                        existing["human_review_feedback"] = input_data["section_feedback"]
                                        for key, feedback in input_data["section_feedback"].items():
                                            if feedback.get("edited") and feedback.get("content") is not None:
                                                existing[key] = feedback["content"]
                                    update["artifacts"] = existing
                        except Exception as e:
                            print(f"  → HIL error: {type(e).__name__}: {e}")
                            import traceback
                            traceback.print_exc()
                            update = {"human_approval_required": False}
                    else:
                        update = None

                    if update:
                        await self.graph.aupdate_state(config, update)
                        print(f"  → State updated: resuming to {next_nodes}")

                input_state = None  # resume from interrupt point
                continue  # re-enter the try/except loop

    def _default_interview(self, state: WorkflowState) -> str:
        """Generate default interview notes when auto-approving."""
        project_name = state.get("artifacts", {}).get("project_name", "Untitled")
        spec = state.get("spec_path", "") or ""
        return (
            f"Auto-generated interview for '{project_name}':\n"
            f"Core behavior: {spec}\n"
            f"Data model: Standard CRUD\n"
            f"API surface: RESTful endpoints\n"
            f"Validation: Standard input validation\n"
            f"Integration: None specified\n"
            f"Deployment: Docker Compose\n"
            f"Edge cases: Standard error handling\n"
            f"Non-functional: Standard performance targets\n"
        )

    async def _hil_cli(self, phase: str, state: WorkflowState) -> Optional[Dict[str, str]]:
        """CLI handler for HIL — collects user input via stdin/stdout."""
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._hil_cli_sync, phase, state)
        return result

    def _hil_cli_sync(self, phase: str, state: WorkflowState) -> Optional[Dict[str, str]]:
        """Synchronous part that actually blocks on input()."""
        print(f"\n  === {phase}: Human Input Required ===")

        if phase == "HUMAN_REVIEW":
            return self._cli_human_review(state)
        elif phase == "DEFINE":
            return self._cli_interview()
        else:
            answer = input(f"  Approve {phase}? (y/n): ").strip().lower()
            if answer == "y":
                return {"approved": True}
            elif answer == "n":
                feedback = input("  Feedback: ").strip()
                return {"approved": False, "feedback": feedback}
            return {"approved": True}

    def _cli_human_review(self, state: WorkflowState) -> dict:
        """Display full DEFINE output for human review with per-section approval."""
        from graph.nodes.review_contract import (
            build_review_sections,
            format_review_summary_for_cli,
            format_review_section_for_cli,
            make_review_result,
        )

        artifacts = state.get("artifacts", {})
        sections = build_review_sections(artifacts)

        # Summary
        print("\n  === Human Review: Approve Each Section ===\n")
        print(format_review_summary_for_cli(sections))

        # Show full content and collect per-section decisions
        section_feedback = {}
        for sec in sections:
            key = sec["key"]
            title = sec["label"].upper()
            content = sec["content"]

            if content:
                print(format_review_section_for_cli(title, content))
            else:
                print(f"\n  [{title}]: (not provided)")

            answer = input(f"\n  Approve {title}? (y/n/e=edit): ").strip().lower()

            if answer == "e":
                # User wants to edit — collect replacement text
                print(f"  Enter revised {title.lower()} (end with empty line):\n")
                edits = []
                while True:
                    line = input()
                    if not line:
                        break
                    edits.append(line)
                if edits:
                    new_content = "\n".join(edits)
                    # Write the edited content back to artifacts
                    artifacts[key] = new_content
                    print(f"  ✓ {title} updated with {len(edits)} lines")
                    section_feedback[key] = {"approved": True, "edited": True, "content": new_content}
                else:
                    section_feedback[key] = {"approved": True, "edited": False}
            elif answer == "y":
                section_feedback[key] = {"approved": True}
            elif answer == "n":
                comment = input(f"  Feedback for {title}: ").strip()
                section_feedback[key] = {"approved": False, "comment": comment}
            else:
                # Default to approve
                section_feedback[key] = {"approved": True}

        result = make_review_result(section_feedback)
        # Write feedback back to state
        state["artifacts"]["human_review_feedback"] = section_feedback
        return result.to_dict()

    def _cli_interview(self) -> Dict[str, str]:
        """Ask interview questions from interview-me skill."""
        questions = [
            ("core_behavior", "What does this feature do?"),
            ("data_model", "What entities and fields are involved?"),
            ("api_surface", "What HTTP methods, paths, and auth requirements?"),
            ("validation", "What input validation rules?"),
            ("ui_template", "Any Jinja2 templates or UI requirements?"),
            ("integration", "External services, databases, or APIs?"),
            ("deployment", "Docker or infrastructure implications?"),
            ("edge_cases", "Known edge cases?"),
            ("non_functional", "Performance, security, or monitoring needs?"),
        ]

        answers = {}
        for key, q in questions:
            val = input(f"  {q} (or Enter to skip): ").strip()
            if val:
                answers[key] = val

        # Format as interview notes
        lines = ["Interview answers:"]
        for key, val in answers.items():
            lines.append(f"  {key}: {val}")
        answers["interview_notes"] = "\n".join(lines)
        answers["approved"] = True

        return answers
