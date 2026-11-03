"""Cross-task recursive self-improvement (harness-side) for COMSOL Automatic."""

from .controller import RSIController
from .versioning import AgentVersionRegistry
from .retention_gate import RetentionGate
from .harness_heuristics import score_harness_candidate, merge_into_retention_metrics

__all__ = [
    "RSIController",
    "AgentVersionRegistry",
    "RetentionGate",
    "score_harness_candidate",
    "merge_into_retention_metrics",
]
