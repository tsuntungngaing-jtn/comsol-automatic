"""Evidence-gated Retain/Reject for agent policy candidates.

A caller's attractive metrics are *not* independent evaluation. Under this
offline design, favorable unverified metrics can only result in REVIEW_REQUIRED,
never automatic RETAIN. A trusted evaluator/approval and immutable artifact
verification must be integrated separately before any production promotion.
"""
from __future__ import annotations

import math
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
        fields = ("performance", "scientific_validity", "false_pass_rate", "regression", "cost")
        if not isinstance(old_metrics, dict) or not isinstance(new_metrics, dict):
            return self._defer("Missing evaluation records")
        try:
            if any(k not in old_metrics or k not in new_metrics for k in fields):
                return self._defer("Missing required old/new evaluation metrics")
            def value(obj, key):
                raw = obj[key]
                if type(raw) not in (int, float):
                    raise ValueError("Non-numeric metric")
                number = float(raw)
                if not math.isfinite(number):
                    raise ValueError("Nonfinite metric")
                return number
            old = {k: value(old_metrics, k) for k in fields}
            new = {k: value(new_metrics, k) for k in fields}
            if old["cost"] <= 0 or new["cost"] < 0:
                raise ValueError("Invalid cost baseline")
            if any(not 0 <= item[k] <= 1 for item in (old, new)
                   for k in ("performance", "scientific_validity", "false_pass_rate")):
                raise ValueError("Metrics outside defined [0,1] range")
            cost_ratio = new["cost"] / old["cost"]
        except (ValueError, OverflowError, TypeError) as exc:
            return self._defer(f"Metric error: {exc}")
        checks = {
            "performance_improved": new["performance"] > old["performance"],
            "scientific_validity_nondecreasing": new["scientific_validity"] >= old["scientific_validity"],
            "false_pass_rate_ok": new["false_pass_rate"] <= self.false_pass_rate_threshold,
            "regression_ok": new["regression"] <= self.regression_threshold,
            "cost_ok": cost_ratio <= self.max_cost_ratio,
        }
        favorable = all(checks.values())
        return {
            "decision": "REVIEW_REQUIRED" if favorable else "REJECT",
            "checks": checks,
            "performance_delta": new["performance"] - old["performance"],
            "scientific_validity_delta": new["scientific_validity"] - old["scientific_validity"],
            "false_pass_rate": new["false_pass_rate"],
            "regression": new["regression"],
            "cost_ratio": cost_ratio,
            "independent_evidence_verified": False,
            "promote_active_version": False,
            "reason": (
                "Self-reported metrics appear favorable, but no independently authenticated "
                "held-out evaluation artifacts are available. Requires evidence review."
                if favorable else "Rejected: " + ", ".join(k for k, v in checks.items() if not v)
            ),
        }

    @staticmethod
    def _defer(reason):
        return {
            "decision": "REVIEW_REQUIRED",
            "reason": reason,
            "checks": {},
            "independent_evidence_verified": False,
            "promote_active_version": False,
        }
