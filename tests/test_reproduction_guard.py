"""Synthetic regression cases distilled from LAB7/P010/P011/P031 reports.

No solver session or scientific run is executed.
"""
import tempfile
import unittest
from server.reproduction_guard import (
    TaskLease, GuardError, effective_case_check, identity_check,
    threshold_audit, preflight, resource_check, progress_review,
    reproduction_gate,
)
HASH="a"*64
IDENTITY={"run_id":"p031-1","model_revision":"3","parameters_hash":HASH,
          "mesh_id":"mesh1","study_id":"study1","solver_id":"solver1"}
def scalar(value,unit="W",source="paper:page3"):
    return {"value":value,"unit":unit,"source_ref":source}
def measured(value,unit="W"):
    return {"value":value,"unit":unit,"evidence_ref":"readback:node"}
def resource(dof=2560000,available=20):
    return {"dof":dof,"available_ram_gib":available,"authorized_ram_fraction":0.75,
            "physics_signature":"coupled_heat","host_signature":"lab9",
            "reference_runs":[
                {"dof":2560000,"peak_ram_gib":12.26,"physics_signature":"coupled_heat","host_signature":"lab9"},
                {"dof":8030000,"peak_ram_gib":26.13,"physics_signature":"coupled_heat","host_signature":"lab9"},
            ]}
def payload():
    return {"solver":"COMSOL","expected_identity":IDENTITY,"observed_identity":dict(IDENTITY),
            "thresholds":[{"id":"paper_err","category":"paper","source_ref":"research scope",
                           "unit":"dimensionless","value":0.15,"hard_gate":True}],
            "expected_effective":{"heat_source":scalar(1.0),"boundary_mode":scalar("heating","category")},
            "observed_effective":{"heat_source":measured(1.0),"boundary_mode":measured("heating","category")},
            "resources":resource()}

class GuardTests(unittest.TestCase):
    def test_p031_study_name_not_evidence_of_heating(self):
        data=payload()
        data["observed_effective"]["heat_source"]["value"]=0.0
        data["observed_effective"]["boundary_mode"]["value"]="cooling"
        self.assertEqual(preflight(data)["status"],"BLOCKED_PRECHECK")
        self.assertEqual(effective_case_check(data["expected_effective"],data["observed_effective"])["status"],"BLOCKED")
    def test_threshold_without_provenance_is_not_auto_hard_gate(self):
        t=[{"id":"initial_micro_kelvin","category":"diagnostic","value":1e-6,
            "unit":"K","source_ref":"","hard_gate":True}]
        self.assertEqual(threshold_audit(t)["status"],"REVIEW_REQUIRED")
    def test_memory_screen_avoids_giant_case(self):
        result=resource_check(resource(dof=12000000,available=16))
        self.assertEqual(result["status"],"BLOCKED_RESOURCE_RISK")
        self.assertGreater(result["estimated_ram_gib"],result["budget_ram_gib"])
    def test_no_resource_proof_not_pass(self):
        self.assertEqual(resource_check(None)["status"],"NOT_VERIFIED")
        p=payload();p["resources"]=None
        self.assertEqual(preflight(p)["status"],"BLOCKED_PRECHECK")
    def test_progress_stall_not_auto_stop(self):
        s=[{"wall_seconds":0,"accepted_steps":0,"accepted_time_seconds":0},
           {"wall_seconds":700,"accepted_steps":0,"accepted_time_seconds":0}]
        r=progress_review(s,stall_watch_seconds=600)
        self.assertEqual(r["status"],"REVIEW_STALL")
        self.assertFalse(r["stop_performed"])
    def test_progressing_not_stop(self):
        s=[{"wall_seconds":0,"accepted_steps":0,"accepted_time_seconds":0},
           {"wall_seconds":700,"accepted_steps":1,"accepted_time_seconds":0.1}]
        self.assertEqual(progress_review(s,stall_watch_seconds=600)["status"],"PROGRESSING_OR_STARTING")
    def test_stale_dataset_not_current(self):
        stale=dict(IDENTITY,dataset_id="ds-old",solution_id="sol-old",artifact_sha256=HASH)
        fresh=dict(stale,dataset_id="ds-new")
        self.assertEqual(identity_check(fresh,stale,after_solve=True)["status"],"FAIL")
    def test_no_main_paper_pass_from_reference_case(self):
        result=reproduction_gate({"main_paper_claims":[],"checks":dict.fromkeys(
            ("convergence","conservation","mesh_independence","reopen","physics_consistency"),"PASS"),
            "acceptance_limit":0.15,"acceptance_source":"research protocol"})
        self.assertEqual(result["status"],"NOT_VERIFIED")
        self.assertFalse(result["eligible_next_paper"])
    def test_meeting_reported_threshold_not_scientific_certification(self):
        result=reproduction_gate({"main_paper_claims":[{
            "id":"pressure","condition":"Re200","unit":"Pa",
            "reference_source":"paper:table2","metric_definition_hash":HASH,
            "run_id":"P011","artifact_id":"run-P011","sim_value":90,"reference_value":100
        }],"checks":dict.fromkeys(("convergence","conservation","mesh_independence",
                                     "reopen","physics_consistency"),"PASS"),
          "acceptance_limit":0.15,"acceptance_source":"research protocol"})
        self.assertEqual(result["status"],"REPORTED_CANDIDATE_NEEDS_INDEPENDENT_REVIEW")
        self.assertFalse(result["eligible_next_paper"])
    def test_scope_skip_not_pass(self):
        self.assertEqual(reproduction_gate({"scope_change":"user_skipped"})["status"],"SCOPE_CHANGED_NOT_PASS")
    def test_lease_rejects_duplicate_and_stale(self):
        with tempfile.TemporaryDirectory() as d:
            task=TaskLease(d,"P031")
            task.acquire("ownerA")
            with self.assertRaises(GuardError):
                task.acquire("ownerB")
            r=task.record("ownerA",0,"op1",stage="BUILD")
            self.assertEqual(r["status"],"RECORDED")
            self.assertEqual(task.record("ownerA",0,"op1",stage="BUILD")["status"],"DUPLICATE_NOOP")
            with self.assertRaises(GuardError):
                task.record("ownerA",0,"op2",stage="BUILD")
            task.release("ownerA")
    def test_unknown_solver_submission_does_not_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            task=TaskLease(d,"P031")
            task.acquire("machine1")
            task.record("machine1",0,"submit-1",stage="SOLVE",job_id="job1")
            with self.assertRaises(GuardError):
                task.record("machine1",1,"submit-2",stage="SOLVE",job_id="job2")
            self.assertEqual(task.read()["jobs"]["job1"],"SUBMISSION_UNVERIFIED")
            task.release("machine1")
    def test_normal_preflight_is_review_only(self):
        self.assertEqual(preflight(payload())["status"],"REVIEW_READY_NOT_AUTHORIZED")

if __name__ == "__main__":
    unittest.main()
