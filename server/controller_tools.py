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
        """Apply a user decision while preserving origin/certainty.

        Optional payload keys: autonomy_override (strict|assisted|auto) for this
        decision only; does not permanently change COMSOL_RSI_AUTONOMY.
        """
        body = dict(payload or {})
        override = body.pop("autonomy_override", None)
        result = controller.resolve_decision(case_id, decision_id, action, **body)
        if isinstance(result, dict) and override:
            result = {**result, "autonomy_override": override}
        return result

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

    @mcp.tool()
    async def workflow_admit(case_id: str, task: str) -> dict:
        """Check only dependencies of the requested task."""
        return controller.admit(case_id, task)

    @mcp.tool()
    async def workflow_record_execution(case_id: str, run_id: str, status: str, details: dict | None = None) -> dict:
        """Record caller-supplied execution outcome; does not certify reproduction."""
        return controller.record_execution(case_id, run_id, status, details)

    @mcp.tool()
    async def workflow_submit_checks(case_id: str, layers: dict, run_id: str,
                                     model_revision: int, spec_revision: int,
                                     required: list[str] | None = None) -> dict:
        """Record explicit diagnostic checks separately from paper acceptance."""
        return controller.submit_validation(case_id, layers, required, run_id=run_id,
                                            model_revision=model_revision, spec_revision=spec_revision)

    @mcp.tool()
    async def workflow_evaluate_acceptance(case_id: str, run_id: str, model_revision: int,
                                           spec_revision: int, observations: dict) -> dict:
        """Compare caller-supplied {id: {value, unit}} observations with spec.acceptance_spec.criteria.

        Each criterion requires id, metric (relative_error|absolute_error), reference,
        tolerance and unit. Relative tolerances use fractions: 0.15 means 15%.
        No default tolerance; absent acceptance_spec returns NOT_CONFIGURED.
        This comparison does not authenticate supplied data or certify general scientific validity.
        """
        return controller.evaluate_acceptance(case_id, run_id, model_revision, spec_revision, observations)

    @mcp.tool()
    async def workflow_deliver(case_id: str, artifacts: list[dict] | None = None) -> dict:
        """Deliver model/log paths even after failure; separate execution/check/comparison statuses."""
        return controller.deliver(case_id, artifacts)
