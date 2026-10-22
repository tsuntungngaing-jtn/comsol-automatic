"""Facade MCP tools for the closed-loop controller. Existing modeling tools are unchanged."""
from __future__ import annotations

from pathlib import Path

from .orchestrator import ClosedLoopController
from .repair import RepairController


def register_controller_tools(mcp, runtime):
    root = Path(runtime.output_root) / 'workflow-cases'
    controller = ClosedLoopController(root)
    repair = RepairController(controller)

    @mcp.tool()
    async def workflow_start(case_id: str, spec: dict | None = None) -> dict:
        """Start a persistent paper-to-simulation case. Does not call COMSOL."""
        return controller.start(case_id, spec)

    @mcp.tool()
    async def workflow_status(case_id: str) -> dict:
        """Read persisted controller state. Reviewer-safe."""
        return controller.state(case_id)

    @mcp.tool()
    async def workflow_step(case_id: str, target: str) -> dict:
        """Attempt a legal state transition. Illegal transitions are rejected."""
        try:
            return controller.store.transition(case_id, target)
        except Exception as error:
            return {'success': False, 'status': 'FAIL', 'error': str(error)}

    @mcp.tool()
    async def decision_resolve(case_id: str, decision_id: str, action: str, payload: dict | None = None) -> dict:
        """Apply a user decision while preserving origin/certainty."""
        return controller.resolve_decision(case_id, decision_id, action, **(payload or {}))

    @mcp.tool()
    async def repair_propose(case_id: str, failure_id: str, hypothesis: str, repair_type: str,
                             proposed_change: str, baseline_revision: int) -> dict:
        """Record a repair plan. Epistemic repairs are not auto-admitted."""
        return repair.propose(case_id=case_id, failure_id=failure_id, hypothesis=hypothesis,
                              repair_type=repair_type, proposed_change=proposed_change,
                              baseline_revision=baseline_revision)

    @mcp.tool()
    async def repair_apply(repair_id: str, admitted: bool = False) -> dict:
        """Apply an admitted repair, creating a new model revision."""
        return repair.apply(repair_id, admitted=admitted)
