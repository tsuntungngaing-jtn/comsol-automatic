"""Offline input intake tests. No COMSOL connection or license required."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from server.input_intake import audit_file, create_audit

def item(p="P008", key="height", value="1", unit="mm", kind="1. 原文提供", **extra):
    record={"文章ID/DOI":p,"项目":key,"原始值":value,"单位":unit,
            "来源类别":kind,"核验状态":"已核对来源","不确定度":None,
            "采用版本":None,"页码/图表定位":"Table 1"}
    record.update(extra)
    return record

class OfflineInputTests(unittest.TestCase):
    def test_does_not_autoadopt(self):
        result=create_audit([item()])
        self.assertEqual(result["summary"]["admitted_drafts"],0)
        self.assertEqual(result["simulation_execution"],"NOT_RUN")

    def test_reviewed_reported_unit_converts(self):
        choice={"P008::height":{"approved":True,"candidate_id":"row-00001","reason":"Verified"}}
        result=create_audit([item()],decisions=choice)
        self.assertEqual(result["admitted_input_drafts"][0]["value_base"],0.001)
        self.assertEqual(result["admitted_input_drafts"][0]["admission"],"INPUT_DRAFT_ONLY")

    def test_dimensionally_equal_values_no_conflict(self):
        result=create_audit([item(),item(value="0.001",unit="m")])
        self.assertFalse(result["potential_conflicts"])

    def test_numeric_conflict_after_reviewed_alias(self):
        rows=[item(),item(key="height_from_pixels",value="1.5",
                          kind="2. 读像素对比数据图进行提取")]
        result=create_audit(rows,aliases={"P008::height_from_pixels":"P008::height"})
        self.assertEqual(result["potential_conflicts"][0]["kind"],"NUMERIC_DISAGREEMENT")
        self.assertEqual(result["candidates"][1]["origin"],"digitized_estimate")

    def test_no_cross_paper_alias(self):
        with self.assertRaises(ValueError):
            create_audit([item()],aliases={"P008::height":"P010::height"})

    def test_supplement_not_obtained(self):
        result=create_audit([item(value="",kind="3. supplementary material 提供",
                                  核验状态="未取得补充材料")])
        self.assertEqual(result["candidates"][0]["origin"],"missing")

    def test_unknown_units_and_formulas_not_automatically_used(self):
        rows=[item(value="rho*u*D/mu",unit="1"),
              item(key="width",value="3",unit="SI；单位见参数名/原文")]
        result=create_audit(rows)
        self.assertEqual(result["summary"]["admitted_drafts"],0)

    def test_assumption_requires_engineering_mode(self):
        choice={"P008::height":{"approved":True,"candidate_id":"row-00001","reason":"Reviewed"}}
        source=[item(value="4",kind="4. 工程假设")]
        self.assertEqual(create_audit(source,decisions=choice)["summary"]["blocked_groups"],1)
        result=create_audit(source,decisions=choice,mode="engineering_completed")
        self.assertEqual(result["admitted_input_drafts"][0]["origin"],"assumption")
        self.assertEqual(result["scientific_validation"],"NOT_RUN")

    def test_dimension_mismatch(self):
        result=create_audit([item(unit="mm"),item(value="1",unit="Pa")])
        self.assertEqual(result["potential_conflicts"][0]["kind"],"UNIT_DIMENSION_MISMATCH")

    def test_deny_admission_for_unrecognized_unit(self):
        choice={"P008::height":{"approved":True,"candidate_id":"row-00001","reason":"Reviewed"}}
        result=create_audit([item(unit="按原文")],decisions=choice)
        self.assertEqual(result["summary"]["admitted_drafts"],0)

    def test_zip_json_intake_does_not_extract_or_run_comsol(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            path=root/"source.zip"
            header=list(item())
            with ZipFile(path,"w") as archive:
                archive.writestr("source_rows.json",json.dumps([header,list(item().values())],ensure_ascii=False))
            result=audit_file(path,root)
            self.assertEqual(result["summary"]["source_rows"],1)
            self.assertTrue(Path(result["path"]).is_file())
            self.assertFalse((root/"source_rows.json").exists())

if __name__=="__main__":
    unittest.main()
