"""
Shared executor — singleton workflow core for both CLI (main.py) and Web (app.py).

Both modes import this module. Graph construction, state initialization, and
node execution are identical. Only the UX layer (CLI prompts vs WebSocket) differs.
"""
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


def get_graph():
    """Build and compile the LangGraph workflow. Cached per-process."""
    return build_graph()


class WorkflowRunner:
    """
    Shared workflow runner. Both CLI and Web use this.

    The only difference is the HIL handler:
    - CLI: asks input() on stdin/stdout
    - Web: sends WebSocket events and waits for user reply
    """

    HIL_PHASES = {"DEFINE", "PLAN", "VERIFY"}

    def __init__(self):
        self.graph = get_graph()

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
        result = asyncio.run(self._astream_with_hil(state, auto_approve, on_hil=self._hil_cli))
        return result

    async def _astream_with_hil(self, state: WorkflowState, auto_approve: bool, on_hil):
        """Stream graph execution, pausing at HIL gates."""
        current_phase = None

        async for chunk in self.graph.astream(state, stream_mode="values"):
            phase = chunk.get("phase", "UNKNOWN")

            # Phase transition
            if phase != current_phase:
                if current_phase:
                    print(f"\n[{current_phase}] Completed\n")
                current_phase = phase
                print(f"[{phase}] Started...")

            # HIL gate
            if chunk.get("human_approval_required") and phase in self.HIL_PHASES:
                if auto_approve:
                    print(f"  → Auto-approved {phase}")
                    # Inject approval into state so edge routing proceeds
                    chunk["human_approval_required"] = False
                    # Set default user input so downstream nodes don't block
                    interview_answers = self._default_interview(state)
                    chunk["artifacts"]["interview_notes"] = interview_answers
                    chunk["artifacts"]["user_input"] = {"approved": True}
                else:
                    input_data = on_hil(phase, chunk)
                    if input_data:
                        chunk["artifacts"]["user_input"] = input_data
                        if "interview_notes" in input_data:
                            chunk["artifacts"]["interview_notes"] = input_data["interview_notes"]
                    chunk["human_approval_required"] = False

        if current_phase:
            print(f"\n[{current_phase}] Completed\n")

        return chunk

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

    def _hil_cli(self, phase: str, state: WorkflowState) -> Optional[Dict[str, str]]:
        """CLI handler for HIL — asks questions on stdin/stdout."""
        print(f"\n  === {phase}: Human Input Required ===")

        if phase == "DEFINE":
            return self._cli_interview()
        else:
            answer = input(f"  Approve {phase}? (y/n): ").strip().lower()
            if answer == "y":
                return {"approved": True}
            elif answer == "n":
                feedback = input("  Feedback: ").strip()
                return {"approved": False, "feedback": feedback}
            return {"approved": True}

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
