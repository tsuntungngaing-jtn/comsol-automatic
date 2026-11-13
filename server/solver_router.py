"""Offline, host-mediated multi-solver MCP routing for ComsoFlent v0.1.0.

This module never connects to a solver, launches an application, runs code,
controls a desktop, or authenticates the supplied tool inventory. The MCP
host must discover and invoke each server independently.
"""
from __future__ import annotations

import re

SCHEMA = "comsoflent-routing/0.1.0"
SOLVERS = ("comsol", "fluent")
TASKS = ("plan", "inspect", "build", "solve", "validate", "deliver")
ID = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}\Z")
TOOL = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,79}\Z")

# The official ansys/pyfluent-mcp tool surface is distinct from the
# older third-party Fluent CFD Skill's launch_fluent/run_tui interface.
REQUIRED = {
    "comsol": ("comsol_doctor", "comsol_status"),
    "fluent": ("connect", "session_status", "find_api", "get_state"),
}
OPERATIONS = {
    "comsol": {
        "inspect": (("inspect_current_model", "get_model_tree"),),
        "build": (("model_create", "comsol_model_code"),),
        "solve": (("study_solve_async", "study_solve"),),
        "validate": (("validation_gate",),),
        "deliver": (("model_save",),),
    },
    "fluent": {
        "inspect": (("get_state", "summarize_setup"),),
        "build": (("find_api",), ("validate_code",), ("run_code",)),
        "solve": (("validate_code",), ("run_code",)),
        "validate": (("mesh_quality",), ("simulation_report",)),
        "deliver": (("validate_code",), ("run_code",)),
    },
}
LEGACY_FLUENT = frozenset(("launch_fluent", "server_info", "run_tui", "iterate", "read_case", "execute_python"))
DEFAULT_STAGES = ("inspect", "build", "solve", "validate", "deliver")


class RoutingError(ValueError):
    """Invalid or ambiguous tool inventory."""


def _token(value, pattern, label):
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise RoutingError(f"{label}: invalid identifier")
    return value


def _server_items(raw):
    if not isinstance(raw, list) or len(raw) > 8:
        raise RoutingError("servers: expected a list with at most eight entries")
    items = []
    seen = set()
    for obj in raw:
        if not isinstance(obj, dict) or set(obj) != {"id", "solver", "tools", "available"}:
            raise RoutingError("each server requires exactly id, solver, tools, available")
        sid = _token(obj["id"], ID, "server.id")
        if sid in seen:
            raise RoutingError("duplicate MCP server id: connection namespace collision")
        seen.add(sid)
        if obj["solver"] not in SOLVERS:
            raise RoutingError("server.solver must be comsol or fluent")
        if type(obj["available"]) is not bool:
            raise RoutingError("server.available must be a boolean")
        tools = obj["tools"]
        if not isinstance(tools, list) or len(tools) > 160:
            raise RoutingError("server.tools: expected a bounded list")
        names = set()
        for tool in tools:
            names.add(_token(tool, TOOL, "server.tool"))
        if len(names) != len(tools):
            raise RoutingError("duplicate tool in an MCP server inventory")
        items.append({"id": sid, "solver": obj["solver"],
                      "available": obj["available"], "tools": names})
    return items


def route_plan(request: dict) -> dict:
    """Plan one solver route against host-reported tools. Never calls tools."""
    if not isinstance(request, dict):
        raise RoutingError("request must be an object")
    if set(request) - {"preferred_solver", "source_solver", "task", "servers"}:
        raise RoutingError("unrecognized routing field")
    preferred = request.get("preferred_solver", "auto")
    source = request.get("source_solver", "unspecified")
    task = request.get("task", "plan")
    if preferred not in (*SOLVERS, "auto") or source not in (*SOLVERS, "unspecified"):
        raise RoutingError("invalid solver selection")
    if task not in TASKS:
        raise RoutingError("invalid task")
    servers = _server_items(request.get("servers", []))
    active = [s for s in servers if s["available"]]
    candidates = [s for s in active if preferred == "auto" or s["solver"] == preferred]
    result = {
        "schema": SCHEMA, "requested_task": task, "preferred_solver": preferred,
        "source_solver": source, "selected_solver": None, "server_id": None,
        "status": "BLOCKED", "reason": "", "missing_tools": [],
        "qualified_tool_hints": [], "connection_verified": False,
        "execution_performed": False, "scientific_status": "NOT_RUN",
        "next_actions": [], "fallback": "NONE_EXECUTED",
    }
    if not candidates:
        result["status"] = "BLOCKED_NO_MCP_SERVER"
        result["reason"] = "No matching available host-reported MCP server."
        result["next_actions"] = [
            "Discover local COMSOL_ROOT / COMSOL_VERSION or Ansys AWP_ROOT* without launching a solver.",
            "Start each vendor MCP service in its own environment; register separate server IDs in the MCP host.",
            "Have the host list_tools again; do not switch to direct APIs or GUI automatically.",
        ]
        return result
    if len(candidates) != 1:
        result["status"] = "BLOCKED_AMBIGUOUS_MCP_ROUTE"
        result["reason"] = "Select one solver and one server explicitly; do not merge sessions."
        result["next_actions"] = [f"{s['id']} ({s['solver']})" for s in candidates]
        return result
    selected = candidates[0]
    result["selected_solver"], result["server_id"] = selected["solver"], selected["id"]
    tools = selected["tools"]
    if selected["solver"] == "fluent" and (tools & LEGACY_FLUENT) and not set(REQUIRED["fluent"]).issubset(tools):
        result["status"] = "BLOCKED_LEGACY_FLUENT_INTERFACE"
        result["reason"] = (
            "Third-party Fluent CFD Skill tool names do not match the official "
            "ansys/pyfluent-mcp tool surface. Re-discover actual server tools."
        )
        result["next_actions"] = ["Check the registered Fluent MCP package/entry point and enumerate tools; do not guess aliases."]
        return result
    missing = [name for name in REQUIRED[selected["solver"]] if name not in tools]
    if task != "plan":
        for alternatives in OPERATIONS[selected["solver"]].get(task, ()):
            if not any(item in tools for item in alternatives):
                missing.append("one_of(" + "|".join(alternatives) + ")")
    if missing:
        result["status"] = "BLOCKED_MISSING_MCP_CAPABILITIES"
        result["reason"] = "Host-reported tools do not meet the requested stage minimum."
        result["missing_tools"] = missing
        result["next_actions"] = ["Re-enumerate this exact MCP server's tools and installed-version API before action."]
        return result
    result["status"] = "HOST_DISCOVERY_REPORTED_NOT_VERIFIED"
    result["reason"] = "Tool names were supplied by the caller; no live connection or capabilities were verified."
    for tool_name in REQUIRED[selected["solver"]]:
        result["qualified_tool_hints"].append({"server_id": selected["id"], "tool": tool_name})
    result["next_actions"] = [
        "MCP host: verify server identity, transport, session ownership, and exact tool schemas.",
        "Read-only connection/installation diagnostic; do not infer a license from filesystem discovery.",
        "Freeze paper-derived inputs and uncertainty/source hierarchy before building the case.",
        "Keep the selected solver session isolated; no simultaneous GUI/direct-API mutations.",
        "Request explicit authorization before launching a license-consuming session, editing, solving, or saving.",
        "After an authorized run, check mesh quality, monitors, conservation, physical consistency and provenance.",
        "Save to a fresh workspace path; declare all non-executed physical checks NOT_RUN.",
    ]
    if source in SOLVERS and source != selected["solver"]:
        result["status"] = "CROSS_SOLVER_RECONSTRUCTION_REVIEW"
        result["reason"] = (
            "The paper's named solver differs from the target. Review model-form, "
            "numerics, boundary conventions and evidence; no solver-equivalence claim."
        )
    return result


def register_solver_routing_tools(mcp, _runtime=None):
    @mcp.tool()
    def solver_route_plan(request: dict) -> dict:
        """Offline host-inventory route planner for COMSOL and official PyFluent MCP.

        Caller supplies observed tool names per uniquely named server. This tool
        does not connect, inspect host tools, launch Fluent, or run COMSOL.
        """
        try:
            return route_plan(request)
        except RoutingError as exc:
            return {"schema": SCHEMA, "status": "INVALID_REQUEST",
                    "error": str(exc), "execution_performed": False,
                    "scientific_status": "NOT_RUN"}
