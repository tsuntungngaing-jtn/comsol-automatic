"""Offline, source-aware experimental design space contracts for Paper2Simu.

Research design is NOT paper reproduction. Never infer the paper authors used
an optimized configuration, execute a solver, or promote inferred inputs to
reported facts. Pure standard-library validation; no model or host access.
"""
from __future__ import annotations

import hashlib
import json
import math
import re

SCHEMA = "paper2simu-design-space/0.1.0"
ID = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
ORIGINS = {"USER_DEFINED_DESIGN", "PAPER_REPORTED", "MANUFACTURER_SPEC",
           "LITERATURE", "INFERRED", "DEFAULT"}
NUMERIC = {"continuous", "integer"}
TYPES = NUMERIC | {"categorical"}
MAX_VARIABLES = 24


class DesignError(ValueError):
    pass


def finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DesignError(f"{name}: finite number required")
    try:
        result = float(value)
    except (ValueError, OverflowError):
        raise DesignError(f"{name}: finite number required") from None
    if not math.isfinite(result):
        raise DesignError(f"{name}: finite number required")
    return result


def ident(value, name):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise DesignError(f"{name}: invalid identifier")
    return value


def nonempty(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        raise DesignError(f"{name}: nonempty short source text required")
    return value


def keys(obj, required, optional=(), name="object"):
    if not isinstance(obj, dict) or set(required) - set(obj) or set(obj) - set(required) - set(optional):
        raise DesignError(f"{name}: expected {sorted(required)}; optional {sorted(optional)}")


def fingerprint(document):
    return hashlib.sha256(json.dumps(document, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def validate_space(space):
    """Validate a frozen research DESIGN contract, not a paper's ground truth."""
    keys(space, ("schema", "study_id", "research_question", "source_refs", "mode",
                 "variables", "fixed_inputs", "constraints", "objectives",
                 "allowed_solvers", "budget"), name="design space")
    if space["schema"] != SCHEMA or space["mode"] != "DISCOVERY":
        raise DesignError("Use DISCOVERY mode only; reproduction inputs cannot be optimized")
    ident(space["study_id"], "study_id")
    nonempty(space["research_question"], "research_question")
    refs = space["source_refs"]
    if not isinstance(refs, list) or not refs or len(refs) > 60:
        raise DesignError("At least one bounded source reference required")
    for r in refs:
        nonempty(r, "source_refs")
    names, definitions = set(), {}
    variables = space["variables"]
    if not isinstance(variables, list) or not 1 <= len(variables) <= MAX_VARIABLES:
        raise DesignError("Use 1..24 design variables")
    for var in variables:
        keys(var, ("name", "type", "unit", "source_ref", "origin"),
             ("bounds", "choices"), "variable")
        name = ident(var["name"], "variable.name")
        if name in names:
            raise DesignError("Duplicate design variable")
        names.add(name)
        nonempty(var["source_ref"], f"{name}.source_ref")
        nonempty(var["unit"], f"{name}.unit")
        if var["origin"] not in ORIGINS or var["origin"] == "PAPER_REPORTED":
            raise DesignError(f"{name}: reported paper values are fixed, not optimization variables")
        kind = var["type"]
        if kind not in TYPES:
            raise DesignError(f"{name}: unknown type")
        if kind in NUMERIC:
            if set(var) != {"name", "type", "unit", "source_ref", "origin", "bounds"}:
                raise DesignError(f"{name}: numeric variable requires only bounds")
            pair = var["bounds"]
            if not isinstance(pair, list) or len(pair) != 2:
                raise DesignError(f"{name}: bounds must be [min,max]")
            lo, hi = finite(pair[0], name), finite(pair[1], name)
            if not lo < hi or (kind == "integer" and (not lo.is_integer() or not hi.is_integer())):
                raise DesignError(f"{name}: invalid numeric bounds")
        else:
            if set(var) != {"name", "type", "unit", "source_ref", "origin", "choices"}:
                raise DesignError(f"{name}: categorical variable requires only choices")
            values = var["choices"]
            if not isinstance(values, list) or not 2 <= len(values) <= 32 or not all(
                isinstance(v, str) and 0 < len(v) <= 100 for v in values
            ) or len(set(values)) != len(values):
                raise DesignError(f"{name}: invalid choices")
        definitions[name] = var
    inputs = space["fixed_inputs"]
    if not isinstance(inputs, list) or len(inputs) > 64:
        raise DesignError("fixed_inputs list must contain <=64 items")
    for item in inputs:
        keys(item, ("name", "value", "unit", "source_ref", "origin"), name="fixed input")
        name = ident(item["name"], "fixed.name")
        if name in names:
            raise DesignError(f"fixed input {name} cannot also be a design variable")
        names.add(name)
        nonempty(item["unit"], f"{name}.unit")
        nonempty(item["source_ref"], f"{name}.source_ref")
        if item["origin"] not in ORIGINS:
            raise DesignError(f"{name}: unknown provenance")
        if isinstance(item["value"], (int, float)):
            finite(item["value"], name)
        elif not isinstance(item["value"], str) or not item["value"].strip():
            raise DesignError(f"{name}: fixed value required")
    constraints = space["constraints"]
    if not isinstance(constraints, list) or len(constraints) > 64:
        raise DesignError("constraints list must contain <=64 items")
    for constraint in constraints:
        keys(constraint, ("type", "left", "right", "source_ref"), ("left_value", "right_value"),
             "constraint")
        nonempty(constraint["source_ref"], "constraint.source_ref")
        left, right = constraint["left"], constraint["right"]
        if left not in definitions or right not in definitions or left == right:
            raise DesignError("constraints may reference only distinct design variables")
        if constraint["type"] == "less_equal":
            if set(constraint) != {"type", "left", "right", "source_ref"}:
                raise DesignError("less_equal requires just left/right/source")
            if definitions[left]["type"] not in NUMERIC or definitions[right]["type"] not in NUMERIC or definitions[left]["unit"] != definitions[right]["unit"]:
                raise DesignError("less_equal requires numeric, same-unit variables")
        elif constraint["type"] == "forbid_pair":
            if set(constraint) != {"type", "left", "right", "source_ref", "left_value", "right_value"}:
                raise DesignError("forbid_pair requires left_value/right_value")
            for name, key in ((left, "left_value"), (right, "right_value")):
                if definitions[name]["type"] != "categorical" or constraint[key] not in definitions[name]["choices"]:
                    raise DesignError("forbid_pair must reference defined categorical values")
        else:
            raise DesignError("Unknown constraint type")
    objectives = space["objectives"]
    if not isinstance(objectives, list) or not objectives or len(objectives) > 12:
        raise DesignError("At least one scientific objective required")
    objective_names = set()
    for obj in objectives:
        keys(obj, ("name", "direction", "unit", "source_ref"), name="objective")
        name = ident(obj["name"], "objective.name")
        if name in objective_names:
            raise DesignError("Duplicate objective")
        objective_names.add(name)
        if obj["direction"] not in ("minimize", "maximize"):
            raise DesignError("Invalid objective direction")
        nonempty(obj["unit"], "objective.unit")
        nonempty(obj["source_ref"], "objective.source_ref")
    solvers = space["allowed_solvers"]
    if not isinstance(solvers, list) or not solvers or len(set(solvers)) != len(solvers) or any(x not in ("COMSOL", "Fluent") for x in solvers):
        raise DesignError("Allowed solvers: nonempty unique list of COMSOL/Fluent")
    budget = space["budget"]
    keys(budget, ("max_jobs", "max_total_minutes", "max_ram_gib"), name="budget")
    jobs = budget["max_jobs"]
    if type(jobs) is not int or not 1 <= jobs <= 100:
        raise DesignError("max_jobs must be a positive bounded integer")
    if finite(budget["max_total_minutes"], "max_total_minutes") <= 0 or finite(budget["max_ram_gib"], "max_ram_gib") <= 0:
        raise DesignError("Positive time and RAM budgets required")
    return {"schema": SCHEMA, "status": "CONTRACT_REVIEWED_NOT_AUTHENTICATED",
            "design_space_hash": fingerprint(space), "variable_names": sorted(definitions),
            "scientific_status": "NOT_RUN", "execution_performed": False}


def assess_design(space, proposed):
    """Check one novel candidate against declared domain and constraints."""
    validated = validate_space(space)
    keys(proposed, ("design_space_hash", "values"), name="candidate")
    if proposed["design_space_hash"] != validated["design_space_hash"]:
        return {"status": "STALE_DESIGN_SPACE", "issues": ["Design space revision/hash differs"],
                "eligible": False}
    values = proposed["values"]
    if not isinstance(values, dict):
        raise DesignError("Candidate values must be object")
    by_name = {v["name"]: v for v in space["variables"]}
    if set(values) != set(by_name):
        return {"status": "INVALID_CANDIDATE", "issues": ["Candidate does not specify precisely all design variables"],
                "eligible": False}
    issues = []
    for name, var in by_name.items():
        value = values[name]
        if var["type"] == "categorical":
            if value not in var["choices"]:
                issues.append(f"{name}: outside declared hardware choices")
        elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            issues.append(f"{name}: invalid numerical value")
        elif not var["bounds"][0] <= value <= var["bounds"][1]:
            issues.append(f"{name}: outside bounds")
        elif var["type"] == "integer" and int(value) != value:
            issues.append(f"{name}: integer value required")
    if not issues:
        for c in space["constraints"]:
            if c["type"] == "less_equal" and values[c["left"]] > values[c["right"]]:
                issues.append(f"{c['left']} must be <= {c['right']}")
            if c["type"] == "forbid_pair" and values[c["left"]] == c["left_value"] and values[c["right"]] == c["right_value"]:
                issues.append("Forbidden hardware combination")
    return {"status": "FEASIBLE_ON_DECLARED_CONSTRAINTS" if not issues else "INVALID_CANDIDATE",
            "eligible": not issues, "issues": issues, "candidate_hash": fingerprint(values),
            "execution_performed": False, "scientific_status": "NOT_RUN"}
