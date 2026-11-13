"""Offline synthetic policy tests. No DOI verification, COMSOL or paper truth check."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from server.input_intake import create_audit
from server.source_precedence import (
    SCHEMA, SourceReviewError, review, review_file, validate_evidence,
)


def ledger(value="1", kind="1. 原文提供", key="height", locator="Table 1",
           verification="已核对来源"):
    return {"文章ID/DOI": "P008", "项目": key, "原始值": value,
            "单位": "mm", "来源类别": kind,
            "页码/图表定位": locator, "核验状态": verification}


def candidate(cid, kind, value=1.0):
    row = {
        "id": cid, "paper_id": "P008", "quantity": "channel_height",
        "source_type": kind, "value": value, "unit": "mm",
        "locator": "Table 1" if kind == "PAPER_TEXT_TABLE" else "Fig. 1",
        "source_ref": "reviewed source document", "source_sha256": "a" * 64,
        "verification": "OPERATOR_REVIEWED",
        "conditions": {"material": "water", "regime": "laminar",
                       "geometry": "P008 channel", "temperature": "298 K"},
    }
    if kind == "AUTHOR_SUPPLEMENT":
        row["supplement"] = {"obtained": True, "original_author": True,
                             "version_ref": "official supplement file v1"}
    if kind in ("INSTITUTIONAL_STANDARD", "PEER_REVIEWED"):
        row["authority"] = {
            "issuer": "reviewed external institution", "identifier": "doi or standard id",
            "version": "reviewed version", "applicability": "MATCHED",
            "applicability_basis": "matching material regime temperature and geometry"
        }
    return row


def pack(*records):
    return {"schema": SCHEMA, "case_id": "P008", "candidates": list(records)}


class SourcePrecedenceTests(unittest.TestCase):
    def test_direct_paper_over_schematic(self):
        result = review(pack(candidate("paper", "PAPER_TEXT_TABLE", 1),
                             candidate("schematic", "SCHEMATIC_PIXEL", 1.5)))
        selected = result["precedence_reviews"][0]
        self.assertEqual(selected["preferred_candidate_ids"], ["paper"])
        self.assertEqual(selected["lower_tier_candidate_ids"], ["schematic"])
        self.assertFalse(selected["auto_admitted"])
        self.assertEqual(result["scientific_status"], "NOT_RUN")

    def test_author_supplement_requires_real_acquisition(self):
        row = candidate("supp", "AUTHOR_SUPPLEMENT")
        row["supplement"]["obtained"] = False
        result = review(pack(row))
        self.assertEqual(result["candidates"][0]["eligibility"], "BLOCKED")
        self.assertEqual(result["precedence_reviews"][0]["status"], "INSUFFICIENT_EVIDENCE")

    def test_external_authority_requires_applicability(self):
        row = candidate("standard", "INSTITUTIONAL_STANDARD")
        row["authority"]["applicability"] = "PARTIAL"
        self.assertEqual(review(pack(row))["precedence_reviews"][0]["status"],
                         "INSUFFICIENT_EVIDENCE")
        row["authority"]["applicability"] = "MATCHED"
        self.assertEqual(review(pack(row))["precedence_reviews"][0]["preferred_candidate_ids"],
                         ["standard"])

    def test_external_does_not_supersede_original(self):
        result = review(pack(candidate("standard", "INSTITUTIONAL_STANDARD"),
                             candidate("paper", "PAPER_TEXT_TABLE")))
        self.assertEqual(result["precedence_reviews"][0]["preferred_candidate_ids"], ["paper"])

    def test_verified_supplement_over_external_reference(self):
        result = review(pack(candidate("standard", "INSTITUTIONAL_STANDARD"),
                             candidate("supp", "AUTHOR_SUPPLEMENT")))
        self.assertEqual(result["precedence_reviews"][0]["preferred_candidate_ids"], ["supp"])

    def test_external_not_misrepresented_as_author_supplement(self):
        row = candidate("standard", "INSTITUTIONAL_STANDARD")
        row["supplement"] = {"obtained": True, "original_author": True, "version_ref": "wrong"}
        with self.assertRaises(SourceReviewError):
            validate_evidence(pack(row))

    def test_same_tier_conflict_requires_review(self):
        result = review(pack(candidate("a", "PAPER_TEXT_TABLE", 1),
                             candidate("b", "PAPER_TEXT_TABLE", 1.5)))
        self.assertEqual(result["precedence_reviews"][0]["status"],
                         "SAME_TIER_CONFLICT_REQUIRES_REVIEW")

    def test_different_conditions_block_ranking(self):
        a, b = candidate("a", "PAPER_TEXT_TABLE"), candidate("b", "SCHEMATIC_PIXEL")
        b["conditions"]["geometry"] = "different region"
        self.assertEqual(review(pack(a, b))["precedence_reviews"][0]["status"],
                         "UNIT_OR_CONDITION_REVIEW_REQUIRED")

    def test_different_units_block_ranking(self):
        a, b = candidate("a", "PAPER_TEXT_TABLE"), candidate("b", "SCHEMATIC_PIXEL")
        b["unit"] = "m"
        self.assertEqual(review(pack(a, b))["precedence_reviews"][0]["status"],
                         "UNIT_OR_CONDITION_REVIEW_REQUIRED")

    def test_ml_is_never_primary_evidence(self):
        result = review(pack(candidate("virtual_sensor", "ML_ESTIMATE", 1.2)))
        self.assertEqual(result["precedence_reviews"][0]["status"], "INSUFFICIENT_EVIDENCE")

    def test_unreviewed_source_blocked(self):
        row = candidate("paper", "PAPER_TEXT_TABLE")
        row["verification"] = "UNVERIFIED"
        self.assertEqual(review(pack(row))["precedence_reviews"][0]["status"],
                         "INSUFFICIENT_EVIDENCE")

    def test_reject_nan_duplicate_id_and_missing_metadata(self):
        for val in (float("nan"), float("inf"), True):
            with self.subTest(val=val), self.assertRaises(SourceReviewError):
                review(pack(candidate("one", "PAPER_TEXT_TABLE", val)))
        with self.assertRaises(SourceReviewError):
            review(pack(candidate("same", "PAPER_TEXT_TABLE"),
                        candidate("same", "SCHEMATIC_PIXEL")))
        incomplete = candidate("std", "INSTITUTIONAL_STANDARD")
        del incomplete["authority"]
        with self.assertRaises(SourceReviewError):
            review(pack(incomplete))

    def test_workspace_reports_immutable_and_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "in.json").write_text(json.dumps(pack(candidate("a", "PAPER_TEXT_TABLE"))))
            a, b = review_file("in.json", root), review_file("in.json", root)
            self.assertTrue(a["success"])
            self.assertNotEqual(a["review_path"], b["review_path"])
            data = json.loads(Path(a["review_path"]).read_text())
            self.assertEqual(data["input_sha256"],
                             hashlib.sha256((root / "in.json").read_bytes()).hexdigest())
            self.assertEqual(review_file("../outside.json", root)["status"], "BLOCKED")

    def test_existing_ledger_direct_beats_pixel_even_in_engineering_mode(self):
        rows = [
            ledger(),
            ledger("1.5", "2. 读像素对比数据图进行提取",
                   key="height_pixels", locator="Fig. 1"),
        ]
        result = create_audit(
            rows,
            aliases={"P008::height_pixels": "P008::height"},
            decisions={"P008::height": {"approved": True, "candidate_id": "row-00002",
                                         "reason": "Try pixel read"}},
            mode="engineering_completed",
        )
        self.assertEqual(result["summary"]["admitted_drafts"], 0)
        self.assertEqual(result["blocked_input_groups"][0]["reason"],
                         "LOWER_PRIORITY_CANNOT_OVERRIDE_VERIFIED_PAPER_TEXT_TABLE")
        self.assertEqual(result["source_precedence_reviews"][0]["status"],
                         "DIRECT_PAPER_PRECEDENCE")

    def test_existing_ledger_direct_beats_assumption(self):
        result = create_audit(
            [ledger(), ledger("4", "4. 工程假设")],
            decisions={"P008::height": {"approved": True, "candidate_id": "row-00002",
                                         "reason": "Try engineering choice"}},
            mode="engineering_completed",
        )
        self.assertEqual(result["summary"]["admitted_drafts"], 0)

    def test_unverified_paper_not_automatically_promoted(self):
        result = create_audit([
            ledger(verification="待核验"),
            ledger("1.5", "2. 读像素对比数据图进行提取",
                   key="height_pixels", locator="Fig. 1")
        ], aliases={"P008::height_pixels": "P008::height"})
        self.assertEqual(result["source_precedence_reviews"][0]["status"],
                         "NO_VERIFIED_DIRECT_TEXT_TABLE")
        self.assertEqual(result["summary"]["admitted_drafts"], 0)

    def test_direct_paper_conflicts_are_visible(self):
        result = create_audit([ledger("1"), ledger("2")])
        self.assertEqual(result["source_precedence_reviews"][0]["status"],
                         "DIRECT_PAPER_CONFLICT_REQUIRES_REVIEW")
        self.assertEqual(result["summary"]["admitted_drafts"], 0)


if __name__ == "__main__":
    unittest.main()
