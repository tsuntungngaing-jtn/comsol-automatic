"""Retain / Reject gate for AgentVersion candidates."""
from __future__ import annotations

from typing import Any


class RetentionGate:
    def __init__(
        self,
        *,
        false_pass_rate_threshold: float = 0.05,
        regression_threshold: float = 0.0,
        max_cost_ratio: float = 1.25,
    ) -> None:
        self.false_pass_rate_threshold = false_pass_rate_threshold
        self.regression_threshold = regression_threshold
        self.max_cost_ratio = max_cost_ratio

    def evaluate(
        self,
        *,
        old_metrics: dict[str, Any],
        new_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """
        old_metrics / new_metrics keys:
          performance (higher better),
          scientific_validity (higher better),
          false_pass_rate (lower better),
          regression (lower better; e.g. held-out drop),
          cost (lower better; e.g. solver_calls)
        """
        perf_old = float(old_metrics.get("performance", 0))
        perf_new = float(new_metrics.get("performance", 0))
        sci_old = float(old_metrics.get("scientific_validity", 0))
        sci_new = float(new_metrics.get("scientific_validity", 0))
        fpr_new = float(new_metrics.get("false_pass_rate", 1))
        reg_new = float(new_metrics.get("regression", 1))
        cost_old = float(old_metrics.get("cost", 1) or 1)
        cost_new = float(new_metrics.get("cost", 1) or 1)
        cost_ratio = cost_new / cost_old if cost_old else float("inf")

        checks = {
            "performance_improved": perf_new > perf_old,
            "scientific_validity_nondecreasing": sci_new >= sci_old,
            "false_pass_rate_ok": fpr_new <= self.false_pass_rate_threshold,
            "regression_ok": reg_new <= self.regression_threshold,
            "cost_ok": cost_ratio <= self.max_cost_ratio,
        }
        retain = all(checks.values())
        return {
            "decision": "RETAIN" if retain else "REJECT",
            "checks": checks,
            "performance_delta": perf_new - perf_old,
            "scientific_validity_delta": sci_new - sci_old,
            "false_pass_rate": fpr_new,
            "regression": reg_new,
            "cost_ratio": cost_ratio,
            "reason": (
                "All retention criteria satisfied"
                if retain
                else "Rejected: " + ", ".join(k for k, v in checks.items() if not v)
            ),
        }
