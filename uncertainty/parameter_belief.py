"""ParameterBelief: evidence-grounded beliefs with explicit uncertainty semantics."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

PROVENANCE_STATES = (
    "USER_SUPPLIED",
    "MEASURED",
    "MANUFACTURER_SPEC",
    "LITERATURE",
    "DATABASE",
    "VALIDATED_PRIOR_TASK",
    "INFERRED",
    "DEFAULT",
    "UNKNOWN",
)

RANGE_KINDS = (
    "none",
    "estimated_plausible_range",
    "posterior_credible_interval",
    "confidence_interval",
)

RECOMMENDED_ACTIONS = (
    "AUTO_ACCEPT",
    "RUN_SENSITIVITY",
    "SEEK_MORE_EVIDENCE",
    "ASK_USER",
    "BLOCK_FINAL_VALIDATION",
)

SAFE_FOR = (
    "screening",
    "exploratory_simulation",
    "optimization",
    "final_validation",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ParameterBelief:
    parameter: str
    symbol: str
    unit: str | None = None
    status: str = "unresolved"  # known | inferred | unresolved
    central_estimate: Any = None
    plausible_range: dict[str, Any] | None = None
    range_kind: str = "none"
    distribution: dict[str, Any] | None = None
    credible_interval: dict[str, Any] | None = None
    evidence_sources: list[dict[str, Any]] = field(default_factory=list)
    evidence_grade: str = "D"  # A|B|C|D
    coverage: str = "insufficient"  # high|moderate|low|insufficient
    epistemic_uncertainty: float | None = None
    aleatoric_uncertainty: float | None = None
    sensitivity: dict[str, Any] | None = None
    identifiability: str | None = None
    decision_impact: str | None = None  # LOW|MEDIUM|HIGH|CRITICAL
    recommended_action: str = "ASK_USER"
    safe_for: list[str] = field(default_factory=list)
    reliability: str = "INSUFFICIENT"  # RELIABLE|UNRELIABLE|INSUFFICIENT
    provenance: list[str] = field(default_factory=lambda: ["UNKNOWN"])
    agent_version: str = "A0"
    timestamp: str = field(default_factory=_now)
    why_unknown: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.status not in ("known", "inferred", "unresolved"):
            raise ValueError(f"Invalid status: {self.status}")
        if self.range_kind not in RANGE_KINDS:
            raise ValueError(f"Invalid range_kind: {self.range_kind}")
        if self.recommended_action not in RECOMMENDED_ACTIONS:
            raise ValueError(f"Invalid recommended_action: {self.recommended_action}")
        if self.reliability not in ("RELIABLE", "UNRELIABLE", "INSUFFICIENT"):
            raise ValueError(f"Invalid reliability: {self.reliability}")
        for p in self.provenance:
            if p not in PROVENANCE_STATES:
                raise ValueError(f"Invalid provenance: {p}")
        if self.coverage == "insufficient":
            # Legal scientific conclusion: do not fabricate ranges.
            if self.plausible_range is not None or self.central_estimate is not None:
                raise ValueError(
                    "coverage=insufficient forbids central_estimate and plausible_range"
                )
            if self.range_kind not in ("none",):
                raise ValueError("coverage=insufficient requires range_kind=none")
            self.reliability = "INSUFFICIENT"
        if self.range_kind == "confidence_interval" and self.credible_interval is None:
            # Formal CI requires an explicit statistical definition object.
            raise ValueError(
                "confidence_interval requires a formal definition; "
                "use estimated_plausible_range otherwise"
            )
        if (
            self.range_kind == "estimated_plausible_range"
            and self.plausible_range is None
            and self.coverage != "insufficient"
        ):
            raise ValueError("estimated_plausible_range requires plausible_range")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParameterBelief":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def is_inferred(self) -> bool:
        return self.status == "inferred" or "INFERRED" in self.provenance

    def blocks_final_scientific_pass(self) -> bool:
        return self.decision_impact in ("HIGH", "CRITICAL") and self.is_inferred()
