"""ExperienceRecord store: prediction and observation kept separate."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import uuid


SPLITS = ("experience", "development", "held_out")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_experience(
    *,
    task_id: str,
    task_family: str,
    agent_version: str,
    parent_agent_version: str | None,
    state: dict[str, Any],
    context: dict[str, Any],
    dataset_split: str = "experience",
    unknown_parameters: list | None = None,
    parameter_beliefs: list | None = None,
    candidate_action: dict | None = None,
    prediction: dict | None = None,
) -> dict[str, Any]:
    if dataset_split not in SPLITS:
        raise ValueError(f"dataset_split must be one of {SPLITS}")
    return {
        "experience_id": "exp-" + uuid.uuid4().hex[:12],
        "task_id": task_id,
        "task_family": task_family,
        "dataset_split": dataset_split,
        "state": dict(state or {}),
        "context": dict(context or {}),
        "unknown_parameters": list(unknown_parameters or []),
        "parameter_beliefs": list(parameter_beliefs or []),
        "candidate_action": candidate_action,
        "prediction": dict(prediction) if prediction else None,
        "actual_outcome": None,  # filled later; never rewrite prediction
        "prediction_error": None,
        "failure_type": None,
        "diagnosis": None,
        "repair": None,
        "repair_result": None,
        "scientific_validation": None,
        "parameter_validation": None,
        "user_feedback": None,
        "comsol_cost": None,
        "solver_calls": 0,
        "tool_calls": 0,
        "runtime": None,
        "lesson_learned": None,
        "reusable_skill": None,
        "agent_version": agent_version,
        "parent_agent_version": parent_agent_version,
        "retention_status": "pending",
        "created_at": _now(),
        "updated_at": _now(),
    }


class ExperienceStore:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root else None
        self._records: dict[str, dict[str, Any]] = {}
        if self.root:
            self.root.mkdir(parents=True, exist_ok=True)
            self._load()

    def _path(self) -> Path | None:
        return self.root / "experience_records.jsonl" if self.root else None

    def _load(self) -> None:
        path = self._path()
        if not path or not path.exists():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            self._records[rec["experience_id"]] = rec

    def _persist(self, rec: dict[str, Any]) -> None:
        path = self._path()
        if not path:
            return
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def add(self, record: dict[str, Any]) -> dict[str, Any]:
        eid = record["experience_id"]
        self._records[eid] = dict(record)
        self._persist(self._records[eid])
        return dict(record)

    def get(self, experience_id: str) -> dict[str, Any]:
        return dict(self._records[experience_id])

    def observe(
        self,
        experience_id: str,
        actual_outcome: dict[str, Any],
        *,
        prediction_error: Any = None,
        scientific_validation: dict | None = None,
        lesson_learned: str | None = None,
        solver_calls: int | None = None,
        runtime: float | None = None,
    ) -> dict[str, Any]:
        rec = self._records[experience_id]
        if rec.get("prediction") is not None:
            # Freeze: do not allow callers to mutate prediction via observation.
            rec["prediction"] = dict(rec["prediction"])
        rec["actual_outcome"] = dict(actual_outcome)
        rec["prediction_error"] = prediction_error
        if scientific_validation is not None:
            rec["scientific_validation"] = scientific_validation
        if lesson_learned is not None:
            rec["lesson_learned"] = lesson_learned
        if solver_calls is not None:
            rec["solver_calls"] = solver_calls
        if runtime is not None:
            rec["runtime"] = runtime
        rec["updated_at"] = _now()
        # Rewrite file store simply by appending update marker (V0.1)
        self._persist({"_update": True, **rec})
        return dict(rec)

    def list(
        self,
        *,
        split: str | None = None,
        for_learning: bool = False,
    ) -> list[dict[str, Any]]:
        items = list(self._records.values())
        if for_learning:
            # Held-out must never enter long-term learning.
            items = [r for r in items if r.get("dataset_split") != "held_out"]
        if split:
            items = [r for r in items if r.get("dataset_split") == split]
        return [dict(r) for r in items]
