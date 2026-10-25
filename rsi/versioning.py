"""AgentVersion registry: A0 → A1 → … with retain/reject provenance."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentVersionRegistry:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root else None
        self._versions: dict[str, dict[str, Any]] = {}
        self._active: str = "A0"
        if self.root:
            self.root.mkdir(parents=True, exist_ok=True)
        if "A0" not in self._versions:
            self._versions["A0"] = {
                "version_id": "A0",
                "parent_version_id": None,
                "status": "active",
                "changes": [],
                "experience_used": [],
                "gate_results": None,
                "reason": "baseline agent",
                "policies": {
                    "ask_policy": "impact_aware",
                    "evidence_ranking": "default_v0",
                    "repair_heuristics": "default_v0",
                    "parameter_priors": {},
                },
                "created_at": _now(),
            }
        self._load()

    def _path(self) -> Path | None:
        return self.root / "agent_versions.json" if self.root else None

    def _load(self) -> None:
        path = self._path()
        if not path or not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        self._versions = data.get("versions", self._versions)
        self._active = data.get("active", self._active)

    def _save(self) -> None:
        path = self._path()
        if not path:
            return
        path.write_text(
            json.dumps({"active": self._active, "versions": self._versions}, indent=2),
            encoding="utf-8",
        )

    def active(self) -> dict[str, Any]:
        return dict(self._versions[self._active])

    def active_id(self) -> str:
        return self._active

    def get(self, version_id: str) -> dict[str, Any]:
        return dict(self._versions[version_id])

    def propose_candidate(
        self,
        *,
        changes: list[dict[str, Any]],
        experience_used: list[str],
        policies: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        parent = self._active
        n = len(self._versions)
        vid = f"A{n}_candidate"
        rec = {
            "version_id": vid,
            "parent_version_id": parent,
            "status": "candidate",
            "changes": list(changes),
            "experience_used": list(experience_used),
            "gate_results": None,
            "reason": reason,
            "policies": dict(policies),
            "created_at": _now(),
        }
        self._versions[vid] = rec
        self._save()
        return dict(rec)

    def finalize(
        self,
        candidate_id: str,
        *,
        decision: str,
        gate_results: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        cand = self._versions[candidate_id]
        parent = cand["parent_version_id"]
        cand["gate_results"] = dict(gate_results)
        cand["reason"] = reason
        if decision == "RETAIN":
            # Promote to retained version id A{n}
            retained_id = f"A{len([v for v in self._versions if not v.endswith('_candidate')])}"
            retained = dict(cand)
            retained["version_id"] = retained_id
            retained["status"] = "retained"
            self._versions[retained_id] = retained
            self._versions[candidate_id]["status"] = "retained"
            self._versions[candidate_id]["promoted_to"] = retained_id
            if parent:
                self._versions[parent]["status"] = "superseded"
            self._active = retained_id
            self._save()
            return dict(retained)
        cand["status"] = "rejected"
        if parent:
            self._versions[parent]["status"] = "active"
            self._active = parent
        self._save()
        return dict(cand)

    def all(self) -> list[dict[str, Any]]:
        return [dict(v) for v in self._versions.values()]
