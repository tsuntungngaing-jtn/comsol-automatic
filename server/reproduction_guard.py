"""Offline, fail-closed paper-reproduction operations guard.

No COMSOL/Fluent imports, solver calls, hidden retries, GUI control, or
scientific certification. All evidence is caller-supplied and unverified.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
from uuid import uuid4

SCHEMA = "reproduction-guard/0.1.0"
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
PRE_ID = ("run_id", "model_revision", "parameters_hash", "mesh_id", "study_id", "solver_id")
POST_ID = PRE_ID + ("solution_id", "dataset_id", "artifact_sha256")
CHECKS = ("convergence", "conservation", "mesh_independence", "reopen", "physics_consistency")


class GuardError(ValueError):
    pass


def _number(value, name, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(float(value)):
        raise GuardError(f"{name}: finite number required")
    if nonnegative and value < 0:
        raise GuardError(f"{name}: must be >= 0")
    return float(value)


def _require_dict(value, name):
    if not isinstance(value, dict):
        raise GuardError(f"{name}: object required")
    return value


def _label(value, name):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise GuardError(f"{name}: invalid ID")
    return value


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                                     allow_nan=False).encode("utf-8")).hexdigest()


def identity_check(expected, observed, *, after_solve=False):
    """Compare declared provenance identifiers; no identity is authenticated."""
    expected, observed = _require_dict(expected, "expected identity"), _require_dict(observed, "observed identity")
    keys = POST_ID if after_solve else PRE_ID
    missing = [k for k in keys if not expected.get(k) or not observed.get(k)]
    mismatched = [k for k in keys if k not in missing and expected[k] != observed[k]]
    for k in ("parameters_hash", "artifact_sha256"):
        if k in keys and k not in missing and (not isinstance(expected[k], str) or not SHA.fullmatch(expected[k])):
            mismatched.append(k + ": invalid expected hash")
    return {"status": "NOT_VERIFIED" if missing else "FAIL" if mismatched else "REPORTED_MATCH",
            "missing": missing, "mismatched": mismatched, "independently_verified": False}


def threshold_audit(thresholds):
    """A numeric diagnostic warning is not an acceptance threshold."""
    if not isinstance(thresholds, list) or len(thresholds) > 100:
        raise GuardError("thresholds: bounded list required")
    issues = []
    for t in thresholds:
        _require_dict(t, "threshold")
        name = _label(t.get("id"), "threshold.id")
        if t.get("category") not in ("paper", "solver", "engineering", "diagnostic"):
            issues.append(f"{name}: unknown threshold category")
        if not isinstance(t.get("source_ref"), str) or not t["source_ref"].strip():
            issues.append(f"{name}: threshold provenance missing")
        if not isinstance(t.get("unit"), str) or not t["unit"].strip():
            issues.append(f"{name}: threshold unit missing")
        if t.get("category") == "diagnostic" and t.get("hard_gate") is True:
            issues.append(f"{name}: diagnostic-only threshold cannot block reproduction")
        try:
            _number(t.get("value"), name)
        except GuardError as exc:
            issues.append(str(exc))
    if len({t.get("id") for t in thresholds}) != len(thresholds):
        issues.append("duplicate threshold IDs")
    return {"status": "REVIEW_REQUIRED" if issues else "DECLARED_NOT_AUTHENTICATED", "issues": issues}


def effective_case_check(expected, observed):
    """Compares effective solver readback, not study labels or nominal power."""
    _require_dict(expected, "expected effective case")
    _require_dict(observed, "observed effective case")
    if not expected:
        return {"status": "NOT_VERIFIED", "issues": ["no expected effective conditions declared"]}
    issues = []
    for name, requirement in expected.items():
        _label(name, "effective condition")
        _require_dict(requirement, name)
        if not isinstance(requirement.get("source_ref"), str) or not requirement["source_ref"].strip():
            issues.append(f"{name}: expected value lacks source")
        if name not in observed:
            issues.append(f"{name}: effective readback absent")
            continue
        record = _require_dict(observed[name], f"readback.{name}")
        if not record.get("evidence_ref"):
            issues.append(f"{name}: missing solver-side readback evidence")
        if record.get("unit") != requirement.get("unit") or not requirement.get("unit"):
            issues.append(f"{name}: unit mismatch or missing")
            continue
        value, reference = record.get("value"), requirement.get("value")
        if isinstance(value, bool) or isinstance(reference, bool):
            issues.append(f"{name}: boolean not an effective physical value")
        elif isinstance(value, (int, float)) and isinstance(reference, (int, float)):
            try:
                atol = _number(requirement.get("atol", 0), "atol", nonnegative=True)
                rtol = _number(requirement.get("rtol", 0), "rtol", nonnegative=True)
                if not math.isclose(_number(value, name), _number(reference, name),
                                    abs_tol=atol, rel_tol=rtol):
                    issues.append(f"{name}: measured readback differs from expected value")
            except GuardError as exc:
                issues.append(str(exc))
        elif value != reference:
            issues.append(f"{name}: effective readback differs from expected value")
    return {"status": "BLOCKED" if issues else "REPORTED_MATCH",
            "issues": issues, "independently_verified": False}


def resource_check(resource):
    """Conservative same-physics RAM screen; cannot prove a solve will fit."""
    if resource is None:
        return {"status": "NOT_VERIFIED", "reason": "Resource readback absent; do not start an expensive solve"}
    resource = _require_dict(resource, "resource")
    try:
        dof = _number(resource["dof"], "dof", nonnegative=True)
        available = _number(resource["available_ram_gib"], "available_ram_gib", nonnegative=True)
        fraction = _number(resource["authorized_ram_fraction"], "authorized_ram_fraction")
        physics = str(resource["physics_signature"])
        host = str(resource["host_signature"])
        if not (dof > 0 and available > 0 and 0 < fraction <= 1 and physics and host):
            raise GuardError("resource configuration invalid")
        baselines = resource["reference_runs"]
        if not isinstance(baselines, list) or len(baselines) > 20:
            raise GuardError("reference_runs: bounded list required")
        relevant = [b for b in baselines if isinstance(b, dict)
                    and b.get("physics_signature") == physics and b.get("host_signature") == host]
        if len(relevant) < 2:
            return {"status": "REVIEW_REQUIRED", "reason": "Need at least two comparable measured RAM/DOF baselines"}
        peaks = [_number(b["peak_ram_gib"], "peak_ram_gib", nonnegative=True)
                 * dof / _number(b["dof"], "reference.dof", nonnegative=True) for b in relevant
                 if b.get("dof", 0) > 0]
        if len(peaks) < 2:
            return {"status": "REVIEW_REQUIRED", "reason": "Insufficient valid comparable resource baselines"}
        forecast = max(peaks)
        return {"status": "BLOCKED_RESOURCE_RISK" if forecast > available * fraction else "REVIEW_REQUIRED",
                "estimated_ram_gib": forecast, "budget_ram_gib": available * fraction,
                "reason": "Linear DOF scaling screen; heuristic only, not a measured upper bound",
                "independently_verified": False}
    except (KeyError, TypeError, ZeroDivisionError, GuardError) as exc:
        return {"status": "NOT_VERIFIED", "reason": str(exc)}


def preflight(payload):
    _require_dict(payload, "preflight")
    if payload.get("solver") not in ("COMSOL", "Fluent"):
        raise GuardError("solver must be COMSOL or Fluent")
    identity = identity_check(payload.get("expected_identity", {}), payload.get("observed_identity", {}))
    thresholds = threshold_audit(payload.get("thresholds", []))
    effective = effective_case_check(payload.get("expected_effective", {}), payload.get("observed_effective", {}))
    resources = resource_check(payload.get("resources"))
    problems = []
    if identity["status"] != "REPORTED_MATCH":
        problems.append("identity")
    if thresholds["status"] == "REVIEW_REQUIRED":
        problems.append("thresholds")
    if effective["status"] != "REPORTED_MATCH":
        problems.append("effective_case")
    if resources["status"] != "REVIEW_REQUIRED" or "estimated_ram_gib" not in resources:
        problems.append("resources")
    return {"schema": SCHEMA, "status": "BLOCKED_PRECHECK" if problems else "REVIEW_READY_NOT_AUTHORIZED",
            "issues": problems, "identity": identity, "thresholds": thresholds,
            "effective_case": effective, "resources": resources,
            "solver_execution": "NOT_RUN", "scientific_status": "NOT_RUN",
            "authorization_granted": False,
            "next": "Independent live readback and human-authorized solve required; never infer readiness from a study name"}


def progress_review(samples, *, stall_watch_seconds):
    """Report progress trends. NEVER sends cancel/stop to a solver."""
    if not isinstance(samples, list) or len(samples) < 2 or len(samples) > 5000:
        raise GuardError("Need 2..5000 chronological progress samples")
    wait = _number(stall_watch_seconds, "stall_watch_seconds", nonnegative=True)
    if wait <= 0:
        raise GuardError("Explicit positive stall watch window required")
    old, new = _require_dict(samples[0], "first sample"), _require_dict(samples[-1], "last sample")
    for obj in samples:
        for field in ("wall_seconds", "accepted_steps", "accepted_time_seconds"):
            _number(obj[field], field, nonnegative=True)
    if any(b["wall_seconds"] <= a["wall_seconds"] or
           b["accepted_steps"] < a["accepted_steps"] or
           b["accepted_time_seconds"] < a["accepted_time_seconds"]
           for a,b in zip(samples,samples[1:])):
        raise GuardError("Progress samples are stale, regressive or non-chronological")
    last_advanced = max(i for i, v in enumerate(samples) if i == 0 or
                        v["accepted_steps"] > samples[i-1]["accepted_steps"] or
                        v["accepted_time_seconds"] > samples[i-1]["accepted_time_seconds"])
    idle = new["wall_seconds"] - samples[last_advanced]["wall_seconds"]
    waiting = idle >= wait
    return {"status": "REVIEW_STALL" if waiting else "PROGRESSING_OR_STARTING",
            "accepted_steps": new["accepted_steps"], "accepted_time_seconds": new["accepted_time_seconds"],
            "wall_seconds": new["wall_seconds"], "seconds_since_last_advance": idle,
            "stop_performed": False, "root_cause": "UNKNOWN",
            "instruction": "Inspect logs, actual accepted steps and documented cancellation semantics; never force-kill or auto-restart"}


def reproduction_gate(payload):
    """Paper acceptance is reported-only; independent artifact checks remain necessary."""
    _require_dict(payload, "acceptance")
    if payload.get("scope_change") == "user_skipped":
        return {"status": "SCOPE_CHANGED_NOT_PASS", "scientific_status": "NOT_RUN",
                "eligible_next_paper": False}
    claims = payload.get("main_paper_claims", [])
    checks = payload.get("checks", {})
    threshold = payload.get("acceptance_limit")
    source = payload.get("acceptance_source")
    if not claims or not isinstance(claims, list) or len(claims) > 100 or not isinstance(checks, dict):
        return {"status": "NOT_VERIFIED", "eligible_next_paper": False}
    if not isinstance(source, str) or not source.strip() or threshold is None:
        return {"status": "NOT_VERIFIED", "eligible_next_paper": False}
    limit = _number(threshold, "acceptance_limit", nonnegative=True)
    issues = [f"check:{k}" for k in CHECKS if checks.get(k) != "PASS"]
    for claim in claims:
        _require_dict(claim, "claim")
        if not all(claim.get(k) for k in ("id","condition","unit","reference_source","metric_definition_hash","run_id","artifact_id")):
            issues.append("claim:missing provenance")
            continue
        sim, ref = _number(claim.get("sim_value"), "sim_value"), _number(claim.get("reference_value"), "reference_value")
        if ref == 0:
            issues.append(f"claim:{claim['id']}: zero denominator requires explicit non-relative comparator")
        elif abs(sim-ref)/abs(ref) >= limit:
            issues.append(f"claim:{claim['id']}: out of tolerance")
    return {"status": "BLOCKED" if issues else "REPORTED_CANDIDATE_NEEDS_INDEPENDENT_REVIEW",
            "issues": issues, "acceptance_limit": limit,
            "scientific_status": "NOT_RUN", "eligible_next_paper": False,
            "independently_verified": False}


class TaskLease:
    """Local single-writer identity and idempotent job reservation.

    Never steals a lease or retries an unknown solver submission automatically.
    Directory must be an authorized private workspace. No network-filesystem
    or multi-machine atomicity guarantee.
    """
    def __init__(self, root, task_id):
        _label(task_id, "task_id")
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise GuardError("symlink workspace forbidden")
        self.state_path = self.root / (task_id + ".json")
        self.lock_path = self.root / (task_id + ".lease")

    def acquire(self, owner):
        _label(owner, "owner")
        try:
            fd = os.open(self.lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise GuardError("Task already leased; inspect owner/job before manual recovery") from exc
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"owner": owner, "lease_id": uuid4().hex}) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        return self.lock_path.read_text(encoding="utf-8")

    def _assert_owner(self, owner):
        try:
            current = json.loads(self.lock_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError) as exc:
            raise GuardError("No valid task lease") from exc
        if current.get("owner") != owner:
            raise GuardError("Task leased to another owner")

    def read(self):
        if not self.state_path.exists():
            return {"revision": 0, "stage": "EVIDENCE_PREPARATION", "jobs": {}, "events": []}
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def record(self, owner, expected_revision, operation_id, *, stage, job_id=None, evidence_path=None):
        self._assert_owner(owner)
        _label(operation_id, "operation_id")
        if job_id is not None:
            _label(job_id, "job_id")
        if stage not in ("EVIDENCE_PREPARATION","BUILD","SOLVE","VALIDATION",
                         "DIAGNOSIS","BLOCKED","COMPLETE","SCOPE_CHANGED"):
            raise GuardError("invalid stage")
        current = self.read()
        if any(e["operation_id"] == operation_id for e in current["events"]):
            return {"status": "DUPLICATE_NOOP", "state": current}
        if current["revision"] != expected_revision:
            raise GuardError("stale state revision; read back before any further action")
        if stage == "SOLVE" and not job_id:
            raise GuardError("solve submission needs explicit job_id")
        # Unknown job status is never interpreted as an authorization to resubmit.
        if stage == "SOLVE" and any(e["stage"] == "SOLVE" and
                                    e.get("job_id") != job_id for e in current["events"]):
            raise GuardError("Existing solver job recorded; inspect/reconcile before any new submission")
        event = {"operation_id": operation_id, "stage": stage, "job_id": job_id, "evidence_path": evidence_path}
        updated = {**current, "revision": current["revision"] + 1, "stage": stage,
                   "jobs": {**current["jobs"], **({job_id: "SUBMISSION_UNVERIFIED"} if job_id else {})},
                   "events": current["events"] + [event]}
        tmp = self.root / (self.state_path.stem + "." + uuid4().hex + ".tmp")
        try:
            with tmp.open("x", encoding="utf-8") as fh:
                json.dump(updated, fh, ensure_ascii=False, sort_keys=True, indent=2)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.state_path)
        finally:
            tmp.unlink(missing_ok=True)
        if self.read()["revision"] != updated["revision"]:
            raise GuardError("state readback verification failed")
        return {"status": "RECORDED", "state": updated}

    def release(self, owner):
        self._assert_owner(owner)
        self.lock_path.unlink()


def cli(argv=None):
    """Read-only offline command: python -m server.reproduction_guard MODE FILE."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2 or args[0] not in ("preflight", "progress", "acceptance"):
        raise SystemExit("usage: python -m server.reproduction_guard preflight|progress|acceptance <snapshot.json>")
    data = json.loads(Path(args[1]).read_text(encoding="utf-8"))
    result = (preflight(data) if args[0] == "preflight" else
              progress_review(data["samples"], stall_watch_seconds=data["stall_watch_seconds"])
              if args[0] == "progress" else reproduction_gate(data))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in ("PROGRESSING_OR_STARTING", "REVIEW_READY_NOT_AUTHORIZED") else 2


if __name__ == "__main__":
    raise SystemExit(cli())
