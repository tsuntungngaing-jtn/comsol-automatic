"""Evidence-aware, read-only assessment of native solver termination.

Avoid an undocumented universal residual veto. This does not connect to,
control, or independently verify COMSOL/Fluent or certify scientific validity.
"""
from __future__ import annotations

from math import isfinite


def review_native_convergence(record: dict) -> dict:
    if not isinstance(record, dict):
        raise ValueError("solver report must be an object")
    if record.get("solver") not in ("COMSOL", "Fluent"):
        raise ValueError("unsupported or undeclared solver")
    if record.get("execution") not in ("success", "completed", "failed", "aborted", "partial"):
        raise ValueError("invalid execution status")
    if record.get("termination") not in ("converged", "not_converged", "max_iterations", "unknown"):
        raise ValueError("invalid native termination status")
    warnings = record.get("warnings", [])
    if not isinstance(warnings, list) or len(warnings) > 100 or any(not isinstance(s, str) for s in warnings):
        raise ValueError("warnings must be a bounded list of strings")
    native_ref = record.get("termination_log_ref")
    criterion = record.get("configured_criterion")
    authenticated = False  # Caller-provided logs are not independently authenticated.
    native_converged = (
        record["execution"] == "success"
        and record["termination"] == "converged"
        and isinstance(native_ref, str) and bool(native_ref.strip())
        and isinstance(criterion, str) and bool(criterion.strip())
    )
    if record["execution"] in ("failed", "aborted"):
        status = "SOLVER_EXECUTION_FAILED"
    elif record["termination"] in ("not_converged", "max_iterations"):
        status = "NATIVE_CONVERGENCE_NOT_MET"
    elif record["execution"] == "partial":
        status = "PARTIAL_RESULT_NO_CONVERGENCE_CLAIM"
    elif native_converged:
        status = "NATIVE_CONVERGENCE_REPORTED_WITH_WARNINGS" if warnings else "NATIVE_CONVERGENCE_REPORTED"
    else:
        status = "TERMINATION_NOT_VERIFIED"
    additional = record.get("extra_residual")
    diagnostic = {"status": "NOT_PROVIDED", "automatic_veto": False}
    if additional is not None:
        if not isinstance(additional, dict):
            raise ValueError("extra_residual must be an object")
        value, limit = additional.get("value"), additional.get("limit")
        if any(isinstance(v, bool) or not isinstance(v, (int, float))
               or not isfinite(v) or v < 0 for v in (value, limit)):
            raise ValueError("residual value and declared limit must be finite nonnegative")
        source = additional.get("source_ref")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("residual diagnostic needs a source reference")
        kind = additional.get("kind", "diagnostic")
        if kind not in ("diagnostic", "explicit_contract"):
            raise ValueError("unknown residual purpose")
        if kind == "explicit_contract" and (
            not additional.get("threshold_authority") or not additional.get("residual_definition")
        ):
            raise ValueError("an explicit contract needs authority and definition")
        diagnostic = {
            "status": ("BELOW_OR_EQUAL_DECLARED_LIMIT" if value <= limit else "ABOVE_DECLARED_LIMIT"),
            "kind": kind,
            "automatic_veto": False,
            "requires_contract_review": kind == "explicit_contract" and value > limit,
        }
    return {
        "status": status, "solver": record["solver"], "native_converged_reported": native_converged,
        "native_evidence_authenticated": authenticated,
        "warnings": warnings, "extra_residual": diagnostic,
        "automatic_rerun": False, "scientific_status": "NOT_RUN",
        "needs_review": bool(warnings) or not native_converged or diagnostic.get("requires_contract_review", False),
        "policy": "Native termination is distinct from mesh, conservation, model, and paper-claim validation.",
    }
