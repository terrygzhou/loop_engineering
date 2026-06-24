"""
Workflow Bridge — connects Loop Engineering LangGraph workflow to the UI backend.

Skill-driven HIL flow:
- When DEFINE runs interview-me, it generates questions from the skill
- Questions stream to the UI as a structured form
- User answers → answers feed back into the workflow as interview_notes
- Workflow continues with enriched context
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import WebSocket


# ─── Skill-driven interview questions ─────────────────────────────
# Derived from interview-me SKILL.md — the 9 question categories
INTERVIEW_QUESTIONS = [
    {
        "category": "core_behavior",
        "label": "Core Behavior",
        "question": "What does this feature do? What are the inputs and outputs? What are the success and failure paths?",
        "placeholder": "e.g. Users can create an account, log in, and manage their profile...",
        "required": True,
    },
    {
        "category": "data_model",
        "label": "Data Model",
        "question": "What entities are involved? What fields do they have? Are there relationships to existing models?",
        "placeholder": "e.g. User(id, name, email, password_hash), Order(id, user_id, items, status)...",
        "required": True,
    },
    {
        "category": "api_surface",
        "label": "API Surface",
        "question": "What HTTP methods, paths, and parameters? Any authentication/authorization requirements?",
        "placeholder": "e.g. POST /api/users, GET /api/users/{id}, JWT auth required...",
        "required": True,
    },
    {
        "category": "validation",
        "label": "Validation",
        "question": "What input validation rules? What error responses?",
        "placeholder": "e.g. Email must be valid, password min 8 chars, return 422 on bad input...",
        "required": False,
    },
    {
        "category": "ui_template",
        "label": "UI / Templates",
        "question": "Are there Jinja2 templates involved? What data do they display? Any styling or component requirements?",
        "placeholder": "e.g. Login form, dashboard page, use existing CSS framework...",
        "required": False,
    },
    {
        "category": "integration",
        "label": "Integration",
        "question": "Does this feature interact with other services, databases, or external APIs?",
        "placeholder": "e.g. PostgreSQL for users, Redis for sessions, Stripe for payments...",
        "required": False,
    },
    {
        "category": "deployment",
        "label": "Deployment",
        "question": "Any Docker or infrastructure implications? Environment variables, volumes, or network configuration?",
        "placeholder": "e.g. Docker Compose with API + DB, .env for secrets...",
        "required": False,
    },
    {
        "category": "edge_cases",
        "label": "Edge Cases",
        "question": "What are the known edge cases? What should happen with invalid input, missing data, or rate limits?",
        "placeholder": "e.g. Duplicate email registration, concurrent login attempts...",
        "required": False,
    },
    {
        "category": "non_functional",
        "label": "Non-Functional",
        "question": "Performance targets, security requirements, logging/monitoring needs?",
        "placeholder": "e.g. <200ms response time, rate limiting, audit logging...",
        "required": False,
    },
]


class WorkflowBridge:
    """
    Bridges the Loop Engineering LangGraph workflow with the UI.

    Features:
    - Skill-driven interview: interview-me generates questions, UI presents them
    - Streams real-time progress via WebSocket
    - Supports HIL (Human-In-The-Loop) on DEFINE, PLAN, VERIFY phases
    - Falls back to simulated workflow if real imports fail
    - Captures node-level events from LangGraph astream()
    """

    # Phases in order
    PHASES = [
        "DISCOVER", "DEFINE", "HUMAN_REVIEW", "PLAN", "BUILD",
        "SEED_DATA", "VERIFY", "SHIP", "REFLECT",
    ]

    # Phases where we wait for user input
    HIL_PHASES = {"HUMAN_REVIEW", "PLAN", "VERIFY"}

    def __init__(self):
        self.status = "idle"
        self.current_phase = ""
        self.cycle = 0
        self.events: List[dict] = []
        self.phase_states: Dict[str, dict] = {}
        self.waiting_for: Optional[str] = None
        self.websocket_clients: List[WebSocket] = []
        self.user_inputs: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._run_task: Optional[asyncio.Task] = None
        self._aborted = False
        self._auto_approve = False
        self._seen_artifacts: Dict[str, Any] = {}
        self._use_real_workflow = False
        self._build_graph = None
        self._WorkflowState = None
        self._CycleMetrics = None
        self._build_skill_registry = None
        self._last_phase = None
        self._project_name = ""
        self._spec_text = ""
        self._context_folder = ""

        # Initialize phase tracking
        for phase in self.PHASES:
            self.phase_states[phase] = {
                "phase": phase,
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifacts": {},
                "messages": [],
            }

    def _try_import_real(self):
        """Attempt to import the real workflow modules."""
        if self._use_real_workflow:
            return

        # Resolve project root — try multiple locations for local vs Docker
        candidates = [
            Path(__file__).resolve().parent.parent.parent,  # local: ../.. from backend/
            Path("/loop_engineering"),                        # Docker volume mount
        ]
        project_root = None
        for candidate in candidates:
            if (candidate / "graph" / "main.py").exists():
                project_root = candidate
                break

        if project_root and str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            print(f"[Bridge] → Added {project_root} to sys.path")

        try:
            from graph.main import build_graph
            from graph.state import WorkflowState, CycleMetrics
            from tools.loader import build_skill_registry
            self._build_graph = build_graph
            self._WorkflowState = WorkflowState
            self._CycleMetrics = CycleMetrics
            self._build_skill_registry = build_skill_registry
            self._use_real_workflow = True
            print("[Bridge] ✓ Real workflow imported")
        except ImportError as e:
            print(f"[Bridge] ⚠ Real workflow import failed: {e} — using simulated mode")
            self._use_real_workflow = False

    def _make_event(self, phase: str, action: str, message: str, data: Optional[Dict[str, Any]] = None) -> dict:
        """Create a progress event dict."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "phase": phase,
            "action": action,
            "message": message,
            "data": data or {},
        }

    def add_event(self, phase: str, action: str, message: str, data: Optional[Dict[str, Any]] = None) -> dict:
        """Create, record, and update phase state for an event."""
        ev = self._make_event(phase, action, message, data)
        self.events.append(ev)

        if phase in self.phase_states:
            ps = self.phase_states[phase]
            if action == "started":
                ps["status"] = "running"
                ps["started_at"] = ev["timestamp"]
            elif action == "waiting":
                ps["status"] = "waiting"
            elif action == "completed":
                ps["status"] = "complete"
                ps["completed_at"] = ev["timestamp"]
            elif action == "error":
                ps["status"] = "error"
            ps["messages"].append(ev)

        return ev

    async def broadcast(self, ev: dict):
        """Send event to all WebSocket clients."""
        payload = json.dumps(ev)
        dead = []
        for ws in self.websocket_clients:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.websocket_clients.remove(ws)

    async def connect_ws(self, websocket: WebSocket):
        """Accept a WebSocket and send recent event history."""
        await websocket.accept()
        self.websocket_clients.append(websocket)
        for ev in self.events[-50:]:
            try:
                await websocket.send_text(json.dumps(ev))
            except Exception:
                pass

    def disconnect_ws(self, websocket: WebSocket):
        """Remove a WebSocket client."""
        if websocket in self.websocket_clients:
            self.websocket_clients.remove(websocket)

    async def abort(self):
        """Abort the running workflow and reset state."""
        if self._aborted:
            return {"status": "already_aborted"}
        self._aborted = True

        # Cancel the running task
        if self._run_task and not self._run_task.done():
            self._run_task.cancel()
            try:
                await self._run_task
            except (asyncio.CancelledError, Exception):
                pass

        # Reset state
        self.status = "idle"
        self.current_phase = ""
        self.waiting_for = None
        self._aborted = False

        ev = self.add_event("SYSTEM", "error", "Workflow aborted by user")
        await self.broadcast(ev)
        return {"status": "aborted"}

    async def _send_interview(self, phase: str):
        """Send skill-driven interview questions to the UI."""
        ev = self.add_event(
            phase, "interview",
            f"{phase}: skill-driven interview — answer the questions below",
            {"type": "interview", "questions": INTERVIEW_QUESTIONS},
        )
        await self.broadcast(ev)

    async def _send_review(self, phase: str, chunk: dict):
        """Send full DEFINE output to the UI for human review.

        Uses the shared review_contract to build identical section payloads
        as the CLI executor — same keys, labels, content, and word counts.
        """
        import importlib.util
        from pathlib import Path
        # Load review_contract directly, bypassing graph/nodes/__init__.py which
        # triggers human_review_node import chain that requires 'graph' as top-level pkg
        # Resolve the same way as _try_import_real — try local then Docker mount
        _rc_candidates = [
            Path(__file__).resolve().parent.parent.parent / "graph" / "nodes" / "review_contract.py",  # local
            Path("/loop_engineering/graph/nodes/review_contract.py"),                                # Docker
        ]
        _rc_path = None
        for c in _rc_candidates:
            if c.exists():
                _rc_path = c
                break
        if not _rc_path:
            raise FileNotFoundError(f"Cannot find review_contract.py in {_rc_candidates}")
        _spec = importlib.util.spec_from_file_location("review_contract", _rc_path)
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        build_review_sections = _mod.build_review_sections
        build_review_summary = _mod.build_review_summary
        build_review_metrics = _mod.build_review_metrics

        artifacts = chunk.get("artifacts", {})
        sections = build_review_sections(artifacts)
        metrics = build_review_metrics(chunk)

        ev = self.add_event(
            phase, "review",
            f"{phase}: review DEFINE output before proceeding to PLAN",
            {
                "type": "human_review",
                "summary": build_review_summary(sections),
                "sections": sections,
                "metrics": metrics,
            },
        )
        await self.broadcast(ev)

    async def _wait_for_user_input(self, phase: str):
        """Block until user provides input or times out (30 min)."""
        self.status = "waiting"
        self.waiting_for = phase

        ev = self.add_event(phase, "waiting", f"Waiting for user input — {phase} phase", {"type": "review_approval"})
        await self.broadcast(ev)

        for _ in range(1800):  # 30 minutes max
            await asyncio.sleep(1)
            if phase in self.user_inputs:
                inp = self.user_inputs.pop(phase)
                ev = self.add_event(phase, "progress", f"User input received")
                await self.broadcast(ev)
                return inp

        ev = self.add_event(phase, "progress", f"{phase} auto-approved (timeout)")
        await self.broadcast(ev)
        return None

    async def run_simulated(self):
        """Simulated workflow for testing (no real imports needed)."""
        async with self._lock:
            if self.status == "running":
                return

        self.status = "running"
        self.cycle += 1
        self.waiting_for = None

        ev = self.add_event("SYSTEM", "started", f"Cycle {self.cycle} — simulated workflow started for: {self._project_name or 'Untitled'}")
        await self.broadcast(ev)

        # If no context folder, skip DISCOVER immediately
        skip_discover = not bool(self._context_folder)
        phases_to_run = self.PHASES
        if skip_discover:
            self.current_phase = "DISCOVER"
            ev = self.add_event("DISCOVER", "started", "Entering DISCOVER phase")
            await self.broadcast(ev)
            ev = self.add_event("DISCOVER", "completed", "DISCOVER skipped — no context folder (greenfield)")
            await self.broadcast(ev)
            phases_to_run = self.PHASES[1:]  # Skip DISCOVER

        for phase in phases_to_run:
            if self._aborted:
                break
            self.current_phase = phase
            ev = self.add_event(phase, "started", f"Entering {phase} phase")
            await self.broadcast(ev)

            # Simulate work with artifacts
            for i in range(3):
                await asyncio.sleep(0.5)
                ev = self.add_event(phase, "progress", f"{phase} step {i + 1}/3 in progress")
                await self.broadcast(ev)

            # Generate simulated artifact
            artifact_name = f"{phase.lower()}_output"
            artifact_value = f"Simulated {phase} output for {self._project_name or 'Untitled'}"
            self.phase_states[phase]["artifacts"][artifact_name] = artifact_value
            ev = self.add_event(phase, "artifact", f"Generated: {artifact_name}", {"artifact_name": artifact_name, "artifact_value": artifact_value})
            await self.broadcast(ev)

            # HIL at DEFINE: send interview questions (skill-driven)
            if phase == "DEFINE":
                await self._send_interview(phase)
                # Populate simulated artifacts for the review phase
                self.phase_states["DEFINE"]["artifacts"]["spec_refined"] = (
                    f"## Simulated Specification for {self._project_name or 'Untitled'}\n\n"
                    "This feature provides a complete end-to-end workflow for managing "
                    "user requirements through automated specification, planning, and implementation.\n\n"
                    "### Key Features\n"
                    "- Requirement gathering via interview\n"
                    "- Automated specification generation\n"
                    "- Human review and approval gates\n"
                    "- Iterative build-verify-reflect cycles"
                )
                self.phase_states["DEFINE"]["artifacts"]["api_contract"] = (
                    f"### API Contract\n\n"
                    "```\n"
                    "POST /api/workflow/start\n"
                    "  Body: { project_name, spec, context_folder }\n"
                    "  Response: { status, cycle }\n\n"
                    "GET /api/status\n"
                    "  Response: { status, phase, cycle, phases, waiting_for }\n\n"
                    "POST /api/input\n"
                    "  Body: { phase, input_type, value }\n"
                    "  Response: { status, phase }\n\n"
                    "WS /ws/progress\n"
                    "  Events: { timestamp, phase, action, message, data }\n"
                    "```\n"
                )
                self.phase_states["DEFINE"]["artifacts"]["interview_notes"] = (
                    "### Interview Notes\n"
                    "- Core behavior: Full workflow automation from requirement to deployment\n"
                    "- Data model: WorkflowState with cycle tracking\n"
                    "- API surface: REST + WebSocket\n"
                    "- Deployment: Docker Compose"
                )

            # HIL at HUMAN_REVIEW: present full spec/artifacts for review before PLAN
            # Use DEFINE phase artifacts (spec_refined, api_contract, interview_notes)
            if phase == "HUMAN_REVIEW":
                define_state = self.phase_states.get("DEFINE", {"artifacts": {}, "metrics": None})
                await self._send_review(phase, define_state)
                await self._wait_for_user_input(phase)

            # HIL at PLAN / VERIFY
            if phase in ("PLAN", "VERIFY"):
                await self._wait_for_user_input(phase)

            ev = self.add_event(phase, "completed", f"{phase} phase completed successfully")
            await self.broadcast(ev)

        self.status = "complete"
        self.current_phase = ""
        self.waiting_for = None
        ev = self.add_event("SYSTEM", "completed", f"Cycle {self.cycle} complete")
        await self.broadcast(ev)

    async def run_real(self):
        """Run the actual LangGraph workflow with streaming.

        Uses the shared WorkflowRunner from graph.executor — identical graph
        and state as main.py. The bridge only adds WebSocket event streaming
        and HIL (Human-In-The-Loop) handling via the UI.
        """
        if not self._use_real_workflow:
            print("[Bridge] Real workflow unavailable — falling back to simulated")
            await self.run_simulated()
            return

        async with self._lock:
            if self.status == "running":
                return

        self.status = "running"
        self.cycle += 1
        self.waiting_for = None
        self._last_phase = None

        # ── Use shared executor for graph + state (same as CLI) ──
        from graph.executor import WorkflowRunner
        runner = WorkflowRunner()

        # Build state via shared executor — guarantees identical state for both modes
        state = self._build_executor_state(
            cycle_id=str(self.cycle),
            project_name=self._project_name,
            spec_text=self._spec_text,
            context_folder=self._context_folder,
        )

        ev = self.add_event("SYSTEM", "started", f"Cycle {self.cycle} — real workflow started for: {self._project_name or 'Untitled'}")
        await self.broadcast(ev)

        # If skipping DISCOVER (no context folder), pre-emit so UI stays in sync
        if state.get("skip_discover"):
            self.current_phase = "DISCOVER"
            ev = self.add_event("DISCOVER", "started", "Entering DISCOVER phase")
            await self.broadcast(ev)
            ev = self.add_event("DISCOVER", "completed", "DISCOVER skipped — no context folder provided")
            await self.broadcast(ev)
            self._last_phase = "DISCOVER"
        else:
            self._last_phase = None

        try:
            # Stream events from LangGraph — each iteration is a node execution
            async def on_hil_bridge(phase, chunk):
                """Bridge HIL handler — wait for user input at HIL gates.

                Auto-approve when no WS clients connected (headless).
                When WS clients are connected, wait up to 30 min for user input.
                """
                has_clients = bool(self.websocket_clients)

                if not has_clients:
                    print(f"  → Auto-approved {phase} (no WS clients)")
                    return {"approved": True}

                # Wait for user input — poll every second, timeout 30 min
                self.status = "waiting"
                self.waiting_for = phase
                ev = self.add_event(phase, "waiting", f"Waiting for user input — {phase} phase", {"type": "review_approval"})
                await self.broadcast(ev)

                for _ in range(1800):
                    await asyncio.sleep(1)
                    if phase in self.user_inputs:
                        inp = self.user_inputs.pop(phase)
                        self.waiting_for = None
                        ev = self.add_event(phase, "progress", "User input received")
                        await self.broadcast(ev)
                        return inp or {"approved": True}

                # Timeout — auto-approve
                self.waiting_for = None
                ev = self.add_event(phase, "progress", f"{phase} auto-approved (timeout)")
                await self.broadcast(ev)
                return {"approved": True}

            async for chunk in runner._astream_with_hil(state, self._auto_approve, on_hil_bridge):
                if self._aborted:
                    break

                phase = chunk.get("phase", "UNKNOWN")
                artifacts = chunk.get("artifacts", {})

                # Capture artifacts into phase state
                if artifacts and phase in self.phase_states:
                    self.phase_states[phase]["artifacts"].update(artifacts)

                # Deduplicate: only log artifacts that are new or have changed
                for artifact_name, artifact_value in artifacts.items():
                    artifact_key = f"{phase}:{artifact_name}"
                    if artifact_key not in self._seen_artifacts or self._seen_artifacts[artifact_key] != artifact_value:
                        self._seen_artifacts[artifact_key] = artifact_value
                        ev = self.add_event(phase, "artifact", f"{artifact_name}: {str(artifact_value)[:200]}", {
                            "artifact_name": artifact_name,
                            "artifact_value": artifact_value,
                        })
                        await self.broadcast(ev)

                # Detect new phase entry
                if phase != self._last_phase:
                    if self._last_phase is not None:
                        ev = self.add_event(self._last_phase, "completed", f"{self._last_phase} completed")
                        await self.broadcast(ev)

                    self.current_phase = phase
                    ev = self.add_event(phase, "started", f"Entering {phase} phase")
                    await self.broadcast(ev)
                    self._last_phase = phase

                    # Skill-driven interview at DEFINE — executor already injected user_input
                    if phase == "DEFINE":
                        await self._send_interview(phase)

                    # Human review at HUMAN_REVIEW — send full output for review
                    # Use the same data source as CLI: the full graph state artifacts
                    # (which accumulates DEFINE + HUMAN_REVIEW outputs)
                    if phase == "HUMAN_REVIEW":
                        # Merge phase state + live chunk artifacts to match CLI state
                        merged = dict(self.phase_states.get("DEFINE", {}).get("artifacts", {}))
                        merged.update(artifacts)
                        await self._send_review(phase, {"artifacts": merged, "metrics": chunk.get("metrics", {})})

                else:
                    ev = self.add_event(phase, "progress", f"{phase} processing...")
                    await self.broadcast(ev)

            # Mark final phase as completed
            if self._last_phase:
                ev = self.add_event(self._last_phase, "completed", f"{self._last_phase} completed")
                await self.broadcast(ev)

            self.status = "complete"
            self.current_phase = ""
            self.waiting_for = None
            ev = self.add_event("SYSTEM", "completed", f"Cycle {self.cycle} complete — all phases done")
            await self.broadcast(ev)

        except Exception as e:
            self.status = "error"
            ev = self.add_event("SYSTEM", "error", f"Workflow failed: {str(e)[:200]}")
            await self.broadcast(ev)
            raise

    def _build_executor_state(self, cycle_id, project_name, spec_text, context_folder):
        """Build state via shared executor — identical to what CLI uses."""
        from graph.executor import build_executor_state
        return build_executor_state(
            cycle_id=cycle_id,
            project_name=project_name,
            spec_text=spec_text,
            context_folder=context_folder,
        )

    async def run(self, spec_text: str = "", project_name: str = "", project_path: str = "", context_folder: str = ""):
        """Main entry point — tries real workflow, falls back to simulated."""
        self._spec_text = spec_text
        self._project_name = project_name
        self._context_folder = context_folder
        self._try_import_real()

        if self._use_real_workflow:
            await self.run_real()
        else:
            await self.run_simulated()
