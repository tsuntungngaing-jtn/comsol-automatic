"""Offline source-ledger to auditable candidate simulation inputs. No COMSOL imports.

Never execute spreadsheet expressions, infer absent physical values, or promote
figure/engineering evidence to reported paper facts.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

FIELDS = ("文章ID/DOI", "项目", "原始值", "单位", "来源类别", "页码/图表定位",
          "证据链接或本机路径", "提取/计算方式", "不确定度", "采用版本", "说明/冲突", "核验状态")
SOURCE_TYPES = {
    "1.": ("paper", "reported"),
    "2.": ("figure", "digitized_estimate"),
    "3.": ("supplement", "missing"),
    "4.": ("engineering_assumption", "assumption"),
}
MISSING = {"", "—", "-", "none", "null", "n/a", "na", "unknown"}
UNITS = {
    "m": ("length_m", 1.0, 0.0), "mm": ("length_m", 1e-3, 0.0),
    "um": ("length_m", 1e-6, 0.0), "µm": ("length_m", 1e-6, 0.0),
    "μm": ("length_m", 1e-6, 0.0),
    "pa": ("pressure_pa", 1.0, 0.0), "kpa": ("pressure_pa", 1e3, 0.0),
    "k": ("temperature_k", 1.0, 0.0), "°c": ("temperature_k", 1.0, 273.15),
    "1": ("dimensionless", 1.0, 0.0),
}


def _text(value):
    return "" if value is None else str(value).strip()


def _absent(value):
    return _text(value).lower() in MISSING


def _read_rows(source: Path):
    """Accept a 12-column Chinese source ledger CSV, JSON or ZIP JSON, without unpacking."""
    suffix = source.suffix.lower()
    if suffix == ".zip":
        with ZipFile(source) as archive:
            members = [x for x in archive.infolist() if x.filename == "source_rows.json"]
            if len(members) != 1 or members[0].file_size > 10_000_000:
                raise ValueError("ZIP requires one source_rows.json of <=10 MB")
            raw = archive.read(members[0]).decode("utf-8-sig")
        content = json.loads(raw)
    elif suffix == ".json":
        content = json.loads(source.read_text(encoding="utf-8-sig"))
    elif suffix == ".csv":
        with source.open(encoding="utf-8-sig", newline="") as stream:
            content = list(csv.DictReader(stream))
    else:
        raise ValueError("Only CSV, JSON or ZIP containing source_rows.json are supported")
    if isinstance(content, dict):
        content = content.get("rows", [])
    if not isinstance(content, list):
        raise ValueError("Source rows must be a list")
    if content and isinstance(content[0], list):
        header = [str(h) for h in content[0]]
        content = [dict(zip(header, row)) for row in content[1:]]
    for field in FIELDS[:5]:
        if content and field not in content[0]:
            raise ValueError(f"Missing required source column: {field}")
    if len(content) > 50_000:
        raise ValueError("Source ledger exceeds 50,000 rows")
    if not all(isinstance(row, dict) for row in content):
        raise ValueError("Each source row must be an object")
    return content


def _scalar(value):
    raw = _text(value)
    if _absent(raw):
        return "missing", None
    try:
        result = float(raw)
        if math.isfinite(result):
            return "number", result
    except ValueError:
        pass
    if raw.startswith("["):
        try:
            obj = json.loads(raw)
            if isinstance(obj, list):
                return "array", None
        except ValueError:
            pass
    if any(x in raw for x in ("*", "/", "^", "[mm]", "[m]", "=", "rho", "mu")):
        return "expression_or_label", None
    return "text", None


def _unit(value):
    raw = _text(value)
    if _absent(raw):
        return {"status": "MISSING", "dimension": None}
    normalized = raw.lower().replace(" ", "")
    if normalized in UNITS:
        dim, scale, offset = UNITS[normalized]
        return {"status": "RECOGNIZED", "dimension": dim, "factor": scale,
                "offset": offset}
    return {"status": "UNREVIEWED", "dimension": None}


def _source(row):
    code = _text(row.get("来源类别"))
    for prefix, category in SOURCE_TYPES.items():
        if code.startswith(prefix):
            return category
    return "unknown", "missing"


def _unavailable(row, category):
    if category != "supplement":
        return False
    state = _text(row.get("核验状态")) + " " + _text(row.get("说明/冲突"))
    return _absent(row.get("原始值")) or any(s in state for s in
        ("未取得", "未定位", "未找到", "未发现", "未获得", "待核", "未核实"))


def _sha(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()


def create_audit(rows: list[dict], aliases: dict | None = None, decisions: dict | None = None,
                 mode: str = "paper_faithful") -> dict:
    """Create an input plan; only explicit, reviewed selections can be admitted."""
    if mode not in ("paper_faithful", "engineering_completed"):
        raise ValueError("mode must be paper_faithful or engineering_completed")
    aliases = aliases or {}
    decisions = decisions or {}
    if not isinstance(aliases, dict) or not isinstance(decisions, dict):
        raise ValueError("aliases and decisions must be JSON objects")
    candidates, groups = [], defaultdict(list)
    for i, row in enumerate(rows, 1):
        paper, parameter = _text(row.get("文章ID/DOI")), _text(row.get("项目"))
        key = f"{paper}::{parameter}"
        canonical = aliases.get(key, key)
        if not isinstance(canonical, str) or "::" not in canonical:
            raise ValueError("Alias target must be a 'paper::parameter' identifier")
        if canonical.split("::", 1)[0] != paper:
            raise ValueError("Cross-paper aliases are not permitted")
        source, origin = _source(row)
        unavailable = _unavailable(row, source)
        kind, numeric = _scalar(row.get("原始值"))
        unit = _unit(row.get("单位"))
        usable = kind == "number" and unit["status"] == "RECOGNIZED" and not unavailable
        if source == "supplement" and not unavailable:
            # Supplement category alone is not evidence of an actual supplement being held.
            usable = False
        value_base = (numeric * unit["factor"] + unit["offset"]) if usable else None
        entry = {
            "candidate_id": f"row-{i:05d}", "key": canonical, "original_key": key,
            "paper_id": paper, "parameter": parameter, "raw_value": _text(row.get("原始值")),
            "unit": _text(row.get("单位")), "unit_status": unit["status"],
            "value_kind": kind, "base_dimension": unit["dimension"],
            "value_in_base_units": value_base,
            "source_category": source, "origin": origin if not unavailable else "missing",
            "source_location": _text(row.get("页码/图表定位")),
            "source_reference": _text(row.get("证据链接或本机路径")),
            "extraction_method": _text(row.get("提取/计算方式")),
            "uncertainty_raw": _text(row.get("不确定度")),
            "adopted_version_raw": _text(row.get("采用版本")),
            "notes": _text(row.get("说明/冲突")),
            "verification_raw": _text(row.get("核验状态")),
            "availability": "NOT_OBTAINED_OR_UNVERIFIED" if unavailable else "UNVERIFIED_BY_TOOL",
            "eligible_scalar": usable,
        }
        candidates.append(entry)
        groups[canonical].append(entry)
    conflicts = []
    for key, items in sorted(groups.items()):
        numeric = [v for v in items if v["eligible_scalar"]]
        if len(numeric) >= 2:
            dims = {v["base_dimension"] for v in numeric}
            if len(dims) > 1:
                conflicts.append({"key": key, "kind": "UNIT_DIMENSION_MISMATCH",
                                  "candidate_ids": [v["candidate_id"] for v in numeric]})
            elif not all(math.isclose(numeric[0]["value_in_base_units"], v["value_in_base_units"], rel_tol=1e-9, abs_tol=1e-12) for v in numeric[1:]):
                conflicts.append({"key": key, "kind": "NUMERIC_DISAGREEMENT",
                                  "candidate_ids": [v["candidate_id"] for v in numeric]})
        elif len(items) > 1 and len(numeric) < len(items):
            conflicts.append({"key": key, "kind": "MIXED_OR_NONSCALAR_REPRESENTATIONS",
                              "candidate_ids": [v["candidate_id"] for v in items]})
    conflict_keys = {c["key"] for c in conflicts}
    admitted, blocked = [], []
    for key, items in sorted(groups.items()):
        decision = decisions.get(key)
        if not isinstance(decision, dict) or decision.get("approved") is not True:
            blocked.append({"key": key, "reason": "CONFLICT_REQUIRES_SELECTION" if key in conflict_keys else "REQUIRES_EXPLICIT_REVIEW"})
            continue
        chosen = next((v for v in items if v["candidate_id"] == decision.get("candidate_id")), None)
        reason = _text(decision.get("reason"))
        if not chosen or not reason:
            blocked.append({"key": key, "reason": "INVALID_OR_UNEXPLAINED_SELECTION"})
            continue
        if not chosen["eligible_scalar"] or chosen["origin"] == "missing":
            blocked.append({"key": key, "reason": "MISSING_OR_UNSUPPORTED_NUMERIC_INPUT"})
            continue
        if mode == "paper_faithful" and chosen["origin"] != "reported":
            blocked.append({"key": key, "reason": "NON_REPORTED_INPUT_IN_PAPER_FAITHFUL_MODE"})
            continue
        admitted.append({"key": key, "candidate_id": chosen["candidate_id"],
                         "value_base": chosen["value_in_base_units"],
                         "base_dimension": chosen["base_dimension"], "origin": chosen["origin"],
                         "review_reason": reason, "admission": "INPUT_DRAFT_ONLY"})
    return {
        "format_version": 1, "mode": mode,
        "status": "OFFLINE_REVIEW_ONLY", "scientific_validation": "NOT_RUN",
        "simulation_execution": "NOT_RUN", "may_claim_paper_reproduction": False,
        "summary": {"source_rows": len(rows), "candidate_count": len(candidates),
                    "source_types": dict(Counter(x["source_category"] for x in candidates)),
                    "unit_missing": sum(x["unit_status"] == "MISSING" for x in candidates),
                    "unit_unreviewed": sum(x["unit_status"] == "UNREVIEWED" for x in candidates),
                    "uncertainty_empty": sum(not x["uncertainty_raw"] for x in candidates),
                    "potential_conflicts": len(conflicts), "admitted_drafts": len(admitted),
                    "blocked_groups": len(blocked)},
        "candidates": candidates, "potential_conflicts": conflicts,
        "admitted_input_drafts": admitted, "blocked_input_groups": blocked,
    }


def audit_file(source: str | Path, output_root: str | Path, *, aliases=None,
               decisions=None, mode="paper_faithful") -> dict:
    """Local-only, no data upload, no overwrite; returns actual output file path."""
    source = Path(source).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    result = create_audit(_read_rows(source), aliases=aliases, decisions=decisions, mode=mode)
    result["input_source"] = {"filename": source.name, "sha256": _sha(source)}
    directory = Path(output_root).expanduser().resolve() / "offline-input-audit" / uuid4().hex
    directory.mkdir(parents=True, exist_ok=False)
    target = directory / "input_audit.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    return {"status": result["status"], "path": str(target), "summary": result["summary"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline paper-to-input evidence audit; COMSOL never starts")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--aliases", type=Path, help="Reviewed paper::parameter alias mapping in JSON")
    parser.add_argument("--decisions", type=Path, help="Explicit reviewed candidate decisions in JSON")
    parser.add_argument("--mode", choices=["paper_faithful", "engineering_completed"], default="paper_faithful")
    args = parser.parse_args(argv)
    aliases = json.loads(args.aliases.read_text(encoding="utf-8")) if args.aliases else None
    decisions = json.loads(args.decisions.read_text(encoding="utf-8")) if args.decisions else None
    print(json.dumps(audit_file(args.source, args.output_root, aliases=aliases,
                               decisions=decisions, mode=args.mode), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
