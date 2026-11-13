"""Offline ComsoFlent routing tests. No COMSOL/Fluent installation needed."""
import unittest
from server.solver_router import route_plan, register_solver_routing_tools

COMSOL = ["comsol_doctor", "comsol_status", "inspect_current_model", "model_create", "study_solve_async", "validation_gate", "model_save"]
FLUENT = ["connect", "session_status", "find_api", "get_state", "validate_code", "run_code", "mesh_quality", "simulation_report"]
def entry(id, solver, tools, available=True):
    return dict(id=id, solver=solver, tools=list(tools), available=available)
def plan(preferred="comsol", task="plan", servers=None, source="unspecified"):
    return route_plan({"preferred_solver":preferred,"task":task,"source_solver":source,
                       "servers":servers if servers is not None else [entry("comsol_local","comsol",COMSOL)]})

class RoutingTests(unittest.TestCase):
    def test_comsol_plan_only_reports_discovery(self):
        r=plan()
        self.assertEqual(r["status"],"HOST_DISCOVERY_REPORTED_NOT_VERIFIED")
        self.assertFalse(r["connection_verified"])
        self.assertFalse(r["execution_performed"])
        self.assertEqual(r["scientific_status"],"NOT_RUN")
    def test_fluent_official_tools(self):
        for task in ("inspect","build","solve","validate"):
            with self.subTest(task=task):
                r=plan("fluent",task,[entry("fluent_local","fluent",FLUENT)])
                self.assertEqual(r["selected_solver"],"fluent")
                self.assertEqual(r["status"],"HOST_DISCOVERY_REPORTED_NOT_VERIFIED")
    def test_comsol_stages(self):
        for task in ("inspect","build","solve","validate","deliver"):
            self.assertEqual(plan(task=task)["status"],"HOST_DISCOVERY_REPORTED_NOT_VERIFIED")
    def test_cross_solver_requires_review(self):
        r=plan("fluent","plan",[entry("fluent_local","fluent",FLUENT)],"comsol")
        self.assertEqual(r["status"],"CROSS_SOLVER_RECONSTRUCTION_REVIEW")
    def test_ambiguity_blocks(self):
        servers=[entry("comsol_local","comsol",COMSOL),entry("fluent_local","fluent",FLUENT)]
        self.assertEqual(plan("auto",servers=servers)["status"],"BLOCKED_AMBIGUOUS_MCP_ROUTE")
    def test_duplicate_server_id_blocks(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            plan(servers=[entry("same","comsol",COMSOL),entry("same","fluent",FLUENT)])
    def test_legacy_skill_interface_does_not_impersonate_official(self):
        r=plan("fluent",servers=[entry("legacy","fluent",["server_info","launch_fluent","run_tui"])])
        self.assertEqual(r["status"],"BLOCKED_LEGACY_FLUENT_INTERFACE")
    def test_missing_tool_blocks(self):
        r=plan(servers=[entry("comsol_local","comsol",["comsol_doctor"])])
        self.assertEqual(r["status"],"BLOCKED_MISSING_MCP_CAPABILITIES")
    def test_no_server_and_not_available(self):
        self.assertEqual(plan(servers=[])["status"],"BLOCKED_NO_MCP_SERVER")
        self.assertEqual(plan(servers=[entry("comsol_local","comsol",COMSOL,False)])["status"],"BLOCKED_NO_MCP_SERVER")
    def test_validation_rejects_injection_and_unknown_solver(self):
        for case in (
            {"servers":[entry("a","comsol",COMSOL)],"extra":"ignored"},
            {"servers":[entry("a","comsol",["tool; rm -rf"]) ]},
            {"servers":[entry("a","untrusted",COMSOL)]},
            {"servers":[entry("a","comsol",COMSOL+["comsol_doctor"])]},
        ):
            with self.subTest(case=case):
                with self.assertRaises(ValueError):
                    route_plan(case)
if __name__=="__main__":
    unittest.main()
