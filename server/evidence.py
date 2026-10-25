"""Evidence records with origin/certainty kept distinct. No certainty laundering."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

ORIGINS = (
    "reported",
    "derived",
    "library",
    "documented_default",
    "assumption",
    "user_supplied",
    "fitted",
    "missing",
    "inferred",
)
SOURCE_RANK = {
    "paper": 90,
    "supplement": 80,
    "author_code": 75,
    "author_data": 70,
    "figure": 65,
    "table": 65,
    "reference_implementation": 50,
    "installed_documentation": 40,
    "application_library": 30,
    "material_library": 20,
    "user": 10,
    "unknown": 0,
}

# ParameterBelief provenance → EvidenceRecord.origin (never launder to reported)
PROVENANCE_TO_ORIGIN = {
    "USER_SUPPLIED": "user_supplied",
    "MEASURED": "reported",
    "MANUFACTURER_SPEC": "library",
    "LITERATURE": "derived",
    "DATABASE": "library",
    "VALIDATED_PRIOR_TASK": "derived",
    "INFERRED": "inferred",
    "DEFAULT": "documented_default",
    "UNKNOWN": "missing",
}


class PromotionError(ValueError):
    """Raised when a weaker origin would be relabeled as reported."""


def _now():
    return datetime.now(timezone.utc).isoformat()


def map_provenance_to_origin(provenance: str) -> str:
    if provenance not in PROVENANCE_TO_ORIGIN:
        raise ValueError(f"Unknown provenance: {provenance}")
    return PROVENANCE_TO_ORIGIN[provenance]


class EvidenceLedger:
    def __init__(self):
        self._records: dict[str, dict[str, Any]] = {}
        self._by_quantity: dict[str, list[str]] = {}

    def add(
        self,
        *,
        quantity_id: str,
        value,
        unit: str | None,
        origin: str,
        certainty: str,
        source_type: str,
        source_document: str | None = None,
        source_location: str | None = None,
        extraction_method: str | None = None,
        affects: list[str] | None = None,
        status: str | None = None,
    ) -> dict:
        if origin not in ORIGINS:
            raise ValueError(f"Unknown origin: {origin}")
        evidence_id = "ev-" + uuid.uuid4().hex[:12]
        record = {
            "evidence_id": evidence_id,
            "quantity_id": quantity_id,
            "value": value,
            "unit": unit,
            "origin": origin,
            "certainty": certainty,
            "source_type": source_type,
            "source_document": source_document,
            "source_location": source_location,
            "extraction_method": extraction_method,
            "candidate_values": [
                {"value": value, "origin": origin, "source_type": source_type}
            ],
            "conflicts": [],
            "affects": list(affects or []),
            "status": status or ("missing" if origin == "missing" else "active"),
            "created_at": _now(),
            "revision": 1,
            "decision": None,
        }
        self._records[evidence_id] = record
        self._by_quantity.setdefault(quantity_id, []).append(evidence_id)
        return dict(record)

    def get(self, evidence_id: str) -> dict:
        return dict(self._records[evidence_id])

    def all(self) -> list[dict]:
        return [dict(r) for r in self._records.values()]

    @classmethod
    def from_records(cls, records: list[dict] | None):
        ledger = cls()
        for rec in records or []:
            copied = dict(rec)
            evidence_id = copied["evidence_id"]
            ledger._records[evidence_id] = copied
            ledger._by_quantity.setdefault(copied["quantity_id"], []).append(evidence_id)
        return ledger

    def relabel_origin(self, evidence_id: str, new_origin: str) -> dict:
        rec = self._records[evidence_id]
        if new_origin == "reported" and rec["origin"] != "reported":
            raise PromotionError("Cannot promote a non-reported origin to reported")
        if new_origin == "reported" and rec["origin"] == "inferred":
            raise PromotionError("Cannot promote inferred to reported")
        rec["origin"] = new_origin
        rec["revision"] += 1
        return dict(rec)

    def apply_user_decision(
        self,
        evidence_id: str,
        action: str,
        decision: str = "user_approved",
        value=None,
        unit=None,
        origin=None,
    ) -> dict:
        rec = self._records[evidence_id]
        rec["decision"] = decision
        rec["user_action"] = action
        if action == "supply_value":
            rec["value"] = value
            rec["unit"] = unit or rec.get("unit")
            rec["origin"] = origin or "user_supplied"
            rec["status"] = "active"
        rec["revision"] += 1
        return dict(rec)

    def conflicts(self, quantity_id: str) -> dict:
        ids = self._by_quantity.get(quantity_id, [])
        records = [self._records[i] for i in ids]
        values = [
            (r["value"], r["origin"], r["source_type"], r["source_location"])
            for r in records
        ]
        unique = {(v[0], v[2]) for v in values}
        status = "conflict" if len(unique) > 1 else "ok"
        candidates = [
            {
                "value": r["value"],
                "origin": r["origin"],
                "source_type": r["source_type"],
                "source_location": r["source_location"],
            }
            for r in records
        ]
        for rec in records:
            rec["candidate_values"] = candidates
            rec["conflicts"] = candidates if status == "conflict" else []
            rec["status"] = "conflict" if status == "conflict" else rec["status"]
        return {
            "quantity_id": quantity_id,
            "status": status,
            "candidate_values": candidates,
        }

    @staticmethod
    def stronger_source(a: str, b: str) -> str:
        return a if SOURCE_RANK.get(a, 0) >= SOURCE_RANK.get(b, 0) else b
