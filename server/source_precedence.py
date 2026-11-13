"""Conservative offline source precedence and authority-applicability review.

No web search, DOI verification, numeric imputation, simulation, or author
supplement authentication is performed. All claims are operator-provided.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
from uuid import uuid4

SCHEMA = "source-evidence/0.7.6"
MAX_BYTES = 2 * 1024 * 1024
SOURCE_RANK = {
    "PAPER_TEXT_TABLE": 1,
    "AUTHOR_SUPPLEMENT": 2,
    "INSTITUTIONAL_STANDARD": 3,
    "PEER_REVIEWED": 4,
    "FIGURE_CURVE": 5,
    "SCHEMATIC_PIXEL": 6,
    "ENGINEERING_ASSUMPTION": 7,
    "ML_ESTIMATE": 7,
}
DIRECT = {"PAPER_TEXT_TABLE", "AUTHOR_SUPPLEMENT"}
EXTERNAL = {"INSTITUTIONAL_STANDARD", "PEER_REVIEWED"}
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")


class SourceReviewError(ValueError):
    pass


def _keys(v, required, optional=(), name="record"):
    if not isinstance(v, dict) or set(required) - set(v) or set(v) - set(required) - set(optional):
        raise SourceReviewError(f"{name}: expected keys {sorted(required)} and optional {sorted(optional)}")


def _id(v, name):
    if not isinstance(v, str) or not ID.fullmatch(v):
        raise SourceReviewError(f"{name}: invalid ID")
    return v


def _text(v, name):
    if not isinstance(v, str) or not v.strip() or len(v) > 1024:
        raise SourceReviewError(f"{name}: nonempty text <=1024 characters required")
    return v


def _num(v, name):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise SourceReviewError(f"{name}: finite number required")
    try:
        value = float(v)
    except (ValueError, OverflowError) as exc:
        raise SourceReviewError(f"{name}: finite number required") from exc
    if not math.isfinite(value):
        raise SourceReviewError(f"{name}: finite number required")
    return value


def _inside(root, path):
    root = Path(root).resolve()
    if not isinstance(path, (str, Path)):
        raise SourceReviewError("Workspace path required")
    p = Path(path)
    resolved = (p if p.is_absolute() else root / p).resolve()
    if not resolved.is_relative_to(root):
        raise SourceReviewError("Path escapes COMSOL_OUTPUT_ROOT")
    return resolved


def validate_evidence(document):
    _keys(document, ("schema", "case_id", "candidates"), name="evidence collection")
    if document["schema"] != SCHEMA:
        raise SourceReviewError("Expected source-evidence/0.7.6 schema")
    _id(document["case_id"], "case_id")
    records = document["candidates"]
    if not isinstance(records, list) or not 1 <= len(records) <= 300:
        raise SourceReviewError("Provide 1..300 candidates")
    ids = set()
    for row in records:
        _keys(row, ("id", "paper_id", "quantity", "source_type", "value",
                    "unit", "locator", "source_ref", "source_sha256",
                    "verification", "conditions"),
              ("authority", "supplement"), "candidate")
        candidate_id = _id(row["id"], "candidate id")
        if candidate_id in ids:
            raise SourceReviewError("Duplicate candidate ID")
        ids.add(candidate_id)
        _id(row["paper_id"], "paper id")
        _id(row["quantity"], "quantity")
        if row["source_type"] not in SOURCE_RANK:
            raise SourceReviewError("Unknown source_type")
        _num(row["value"], "value")
        _text(row["unit"], "unit")
        _text(row["locator"], "locator")
        _text(row["source_ref"], "source_ref")
        if not isinstance(row["source_sha256"], str) or not SHA.fullmatch(row["source_sha256"]):
            raise SourceReviewError("source_sha256 must be 64 lowercase hex characters")
        if row["verification"] not in ("OPERATOR_REVIEWED", "UNVERIFIED", "UNAVAILABLE"):
            raise SourceReviewError("Invalid verification")
        conditions = row["conditions"]
        _keys(conditions, ("material", "regime", "geometry", "temperature"), name="conditions")
        for k in ("material", "regime", "geometry", "temperature"):
            _text(conditions[k], "conditions." + k)
        kind = row["source_type"]
        if kind == "AUTHOR_SUPPLEMENT":
            if "authority" in row or "supplement" not in row:
                raise SourceReviewError("Author supplement needs supplement metadata, never external authority metadata")
            _keys(row["supplement"], ("obtained", "original_author", "version_ref"), name="supplement")
            if type(row["supplement"]["obtained"]) is not bool or type(row["supplement"]["original_author"]) is not bool:
                raise SourceReviewError("Supplement identity/availability must be booleans")
            _text(row["supplement"]["version_ref"], "supplement.version_ref")
        elif kind in EXTERNAL:
            if "supplement" in row or "authority" not in row:
                raise SourceReviewError("External sources require authority metadata and cannot claim to be author supplements")
            _keys(row["authority"], ("issuer", "identifier", "version",
                                     "applicability", "applicability_basis"), name="authority")
            for name in ("issuer", "identifier", "version", "applicability_basis"):
                _text(row["authority"][name], "authority." + name)
            if row["authority"]["applicability"] not in ("MATCHED", "PARTIAL", "UNREVIEWED"):
                raise SourceReviewError("Unknown applicability state")
        elif "authority" in row or "supplement" in row:
            raise SourceReviewError("Metadata mismatched to source type")
    return document


def review(document):
    validate_evidence(document)
    candidates = []
    for row in document["candidates"]:
        category = row["source_type"]
        defects = []
        if row["verification"] != "OPERATOR_REVIEWED":
            defects.append("SOURCE_NOT_REVIEWED")
        if category == "AUTHOR_SUPPLEMENT" and not (row["supplement"]["obtained"] and row["supplement"]["original_author"]):
            defects.append("AUTHOR_SUPPLEMENT_NOT_AUTHENTICATED")
        if category in EXTERNAL and row["authority"]["applicability"] != "MATCHED":
            defects.append("EXTERNAL_SOURCE_CONDITIONS_NOT_MATCHED")
        if category == "ML_ESTIMATE":
            defects.append("ML_NOT_PRIMARY_SCIENTIFIC_EVIDENCE")
        candidates.append({
            "id": row["id"], "paper_id": row["paper_id"], "quantity": row["quantity"],
            "source_type": category, "rank": SOURCE_RANK[category],
            "value": row["value"], "unit": row["unit"], "conditions": row["conditions"],
            "source_ref": row["source_ref"], "locator": row["locator"],
            "source_sha256": row["source_sha256"],
            "eligibility": "REVIEWED_FOR_RANKING" if not defects else "BLOCKED",
            "reasons": defects, "authenticity_verified_by_tool": False,
        })
    groups = {}
    for row in candidates:
        groups.setdefault((row["paper_id"], row["quantity"]), []).append(row)
    decisions = []
    for (paper, quantity), group in sorted(groups.items()):
        eligible = [r for r in group if r["eligibility"] == "REVIEWED_FOR_RANKING"]
        if not eligible:
            decisions.append({"paper_id": paper, "quantity": quantity, "status": "INSUFFICIENT_EVIDENCE",
                              "preferred_candidate_ids": [], "reason": "No reviewed admissible source"})
            continue
        rank = min(r["rank"] for r in eligible)
        leading = [r for r in eligible if r["rank"] == rank]
        if len({r["unit"] for r in group}) > 1:
            status, reason = "UNIT_OR_CONDITION_REVIEW_REQUIRED", "Units differ; no automatic conversion"
        elif len({json.dumps(r["conditions"], sort_keys=True) for r in group}) > 1:
            status, reason = "UNIT_OR_CONDITION_REVIEW_REQUIRED", "Physical conditions differ"
        elif len(leading) > 1 and not all(math.isclose(float(leading[0]["value"]), float(r["value"]),
                                                rel_tol=1e-9, abs_tol=1e-12) for r in leading[1:]):
            status, reason = "SAME_TIER_CONFLICT_REQUIRES_REVIEW", "Same-tier values disagree"
        else:
            status, reason = "REVIEW_REQUIRED", "Precedence candidate only, never automatically accepted"
        decisions.append({"paper_id": paper, "quantity": quantity, "status": status,
                          "preferred_candidate_ids": [r["id"] for r in leading],
                          "lower_tier_candidate_ids": [r["id"] for r in eligible if r["rank"] > rank],
                          "reason": reason,
                          "scientific_status": "NOT_RUN", "auto_admitted": False})
    return {"schema": SCHEMA, "case_id": document["case_id"],
            "status": "OFFLINE_REVIEW_ONLY", "scientific_status": "NOT_RUN",
            "candidates": candidates, "precedence_reviews": decisions,
            "limitations": ("Authority metadata and SHA strings are caller assertions; "
                            "no independent DOI/issuer/source authentication, no numeric imputation, "
                            "no physical simulation or scientific validation")}


def review_file(source_path, output_root):
    try:
        source = _inside(output_root, source_path)
        if not source.is_file() or source.stat().st_size > MAX_BYTES:
            raise SourceReviewError("Existing JSON input of <=2 MiB required")
        original = source.read_bytes()
        document = json.loads(original.decode("utf-8"))
        report = review(document)
        report["input_sha256"] = hashlib.sha256(original).hexdigest()
        dest = _inside(output_root, Path("source-precedence") / uuid4().hex / "review.json")
        dest.parent.mkdir(parents=True, exist_ok=False)
        dest.write_text(json.dumps(report, ensure_ascii=False, indent=2,
                                   sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        return {"success": True, "status": report["status"], "review_path": str(dest),
                "scientific_status": "NOT_RUN", "group_count": len(report["precedence_reviews"])}
    except (SourceReviewError, OSError, TypeError, ValueError, KeyError, OverflowError) as exc:
        return {"success": False, "status": "BLOCKED", "scientific_status": "NOT_RUN",
                "error": str(exc)}


def register_source_precedence_tools(mcp, runtime):
    @mcp.tool()
    async def source_precedence_review(source_path: str) -> dict:
        """Offline source precedence and authoritative external-evidence applicability checks. Never authenticates DOI, downloads sources, imputes data, operates COMSOL, or auto-selects."""
        return review_file(source_path, runtime.output_root)
