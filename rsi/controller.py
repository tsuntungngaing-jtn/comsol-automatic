"""
Cross-task RSI controller — outer layer around the existing closed-loop.

Does not replace ClosedLoopController. Orchestrates:
Experience → Infer → (closed-loop hooks) → Evaluate → Calibrate → Retain
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from uncertainty.calibration import PriorStore, compare_prediction_to_observation
from uncertainty.decision_gate import decide_action
from uncertainty.detector import detect_unknown_parameters, unknown_only
from uncertainty.inference import infer_parameter_belief
from uncertainty.propagation import propagate_endpoints
from uncertainty.sensitivity import plan_endpoint_runs
from uncertainty.user_report import render_disclosure_report

from .experience_store import ExperienceStore, new_experience
from .improver import synthesize_candidate
from .retention_gate import RetentionGate
from .versioning import AgentVersionRegistry


class RSIController:
    def __init__(self, root: str | Path | None = None) -> None:
        base = Path(root) if root else None
        self.versions = AgentVersionRegistry(base / "agent_versions" if base else None)
        self.experiences = ExperienceStore(base / "experiences" if base else None)
        self.priors = PriorStore()
        self.retention = RetentionGate()

    def infer_task_parameters(
        self,
        parameters: list[dict[str, Any]],
        *,
        task_context: dict[str, Any] | None = None,
        physics_interfaces: list[str] | None = None,
        evidence_by_parameter: dict[str, list[dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        agent = self.versions.active()
        findings = detect_unknown_parameters(
            parameters, physics_interfaces=physics_interfaces
        )
        unknowns = unknown_only(findings)
        beliefs = []
        reports = []
        actions = []
        for finding in unknowns:
            sources = (evidence_by_parameter or {}).get(finding["parameter"], [])
            belief = infer_parameter_belief(
                finding,
                evidence_sources=sources,
                task_context=task_context,
                agent_version=agent["version_id"],
            )
            belief = decide_action(belief)
            beliefs.append(belief)
            reports.append(render_disclosure_report(belief))
            actions.append(belief.recommended_action)

        return {
            "agent_version": agent["version_id"],
            "findings": findings,
            "beliefs": [b.to_dict() for b in beliefs],
            "belief_objects": beliefs,
            "disclosure_reports": reports,
            "recommended_actions": actions,
            "may_enter_closed_loop": all(
                a in ("AUTO_ACCEPT", "RUN_SENSITIVITY") for a in actions
            )
            or not actions,
            "requires_user": any(a in ("ASK_USER", "BLOCK_FINAL_VALIDATION") for a in actions),
        }

    def endpoint_plan_for(self, belief_dict: dict[str, Any]) -> dict[str, Any]:
        from uncertainty.parameter_belief import ParameterBelief

        belief = ParameterBelief.from_dict(belief_dict)
        return plan_endpoint_runs(belief)

    def apply_propagation(
        self, belief_dict: dict[str, Any], plan: dict[str, Any], outcomes: list[dict]
    ) -> dict[str, Any]:
        from uncertainty.parameter_belief import ParameterBelief

        result = propagate_endpoints(plan, outcomes)
        belief = ParameterBelief.from_dict(belief_dict)
        belief.sensitivity = result.get("sensitivity")
        belief = decide_action(belief, sensitivity=result.get("sensitivity"))
        return {"propagation": result, "belief": belief.to_dict(), "disclosure": render_disclosure_report(belief)}

    def start_experience(
        self,
        *,
        task_id: str,
        task_family: str,
        context: dict[str, Any],
        inference: dict[str, Any],
        dataset_split: str = "experience",
    ) -> dict[str, Any]:
        agent = self.versions.active()
        prediction = {
            "beliefs": inference.get("beliefs"),
            "recommended_actions": inference.get("recommended_actions"),
            "agent_version": agent["version_id"],
            "context": context,
        }
        rec = new_experience(
            task_id=task_id,
            task_family=task_family,
            agent_version=agent["version_id"],
            parent_agent_version=agent.get("parent_version_id"),
            state={"phase": "inferred"},
            context=context,
            dataset_split=dataset_split,
            unknown_parameters=inference.get("findings"),
            parameter_beliefs=inference.get("beliefs"),
            candidate_action={"actions": inference.get("recommended_actions")},
            prediction=prediction,
        )
        return self.experiences.add(rec)

    def complete_experience(
        self,
        experience_id: str,
        *,
        actual_outcome: dict[str, Any],
        scientific_validation: dict[str, Any] | None = None,
        lesson_learned: str | None = None,
        solver_calls: int = 0,
        runtime: float | None = None,
    ) -> dict[str, Any]:
        rec = self.experiences.get(experience_id)
        # prediction_error from first inferred belief vs observed parameter if present
        err = None
        if rec.get("prediction") and actual_outcome.get("parameter_value") is not None:
            beliefs = (rec["prediction"] or {}).get("beliefs") or []
            if beliefs:
                cal = compare_prediction_to_observation(
                    beliefs[0],
                    {
                        "value": actual_outcome["parameter_value"],
                        "provenance": actual_outcome.get("provenance", "USER_SUPPLIED"),
                    },
                )
                err = cal
                # Update priors only for non-held-out
                if rec.get("dataset_split") != "held_out":
                    self.priors.update(
                        parameter=beliefs[0].get("parameter", "param"),
                        context=rec.get("context") or {},
                        observed_value=float(actual_outcome["parameter_value"]),
                        evidence_quality=1.0,
                        context_similarity=1.0,
                    )
        return self.experiences.observe(
            experience_id,
            actual_outcome,
            prediction_error=err,
            scientific_validation=scientific_validation,
            lesson_learned=lesson_learned,
            solver_calls=solver_calls,
            runtime=runtime,
        )

    def propose_and_gate(
        self,
        *,
        old_metrics: dict[str, Any],
        new_metrics: dict[str, Any],
        reason: str = "post-task improvement",
    ) -> dict[str, Any]:
        learning = self.experiences.list(for_learning=True)
        candidate = synthesize_candidate(self.versions, learning, reason=reason)
        gate = self.retention.evaluate(old_metrics=old_metrics, new_metrics=new_metrics)
        finalized = self.versions.finalize(
            candidate["version_id"],
            decision=gate["decision"],
            gate_results=gate,
            reason=gate["reason"],
        )
        return {"candidate": candidate, "gate": gate, "result": finalized}

    def run_with_closed_loop(
        self,
        *,
        parameters: list[dict[str, Any]],
        task_id: str,
        task_family: str,
        context: dict[str, Any],
        closed_loop_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        evidence_by_parameter: dict[str, list[dict[str, Any]]] | None = None,
        physics_interfaces: list[str] | None = None,
        dataset_split: str = "experience",
    ) -> dict[str, Any]:
        """
        Outer RSI step. closed_loop_fn is optional hook (e.g. wrap ClosedLoopController).
        """
        inference = self.infer_task_parameters(
            parameters,
            task_context=context,
            physics_interfaces=physics_interfaces,
            evidence_by_parameter=evidence_by_parameter,
        )
        exp = self.start_experience(
            task_id=task_id,
            task_family=task_family,
            context=context,
            inference=inference,
            dataset_split=dataset_split,
        )
        loop_result = None
        if closed_loop_fn is not None and not inference["requires_user"]:
            loop_result = closed_loop_fn({"inference": inference, "experience": exp})
        return {
            "inference": {k: v for k, v in inference.items() if k != "belief_objects"},
            "experience": exp,
            "closed_loop": loop_result,
            "agent_version": self.versions.active_id(),
        }
