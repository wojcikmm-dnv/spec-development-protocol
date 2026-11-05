"""Tests for the skill checker and the evaluation grader."""

import copy
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / ".apm/skills"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load("check_skills", ROOT / "scripts/check-skills.py")
grader = checker.load_grader()
SCHEMA = json.loads((SKILLS / "sdp-core/schemas/skill-descriptor.schema.json").read_text(encoding="utf-8"))
DESCRIPTOR_SKILLS = sorted(p.name for p in SKILLS.iterdir() if (p / "sdp.skill.json").exists())


def cases_of(skill):
    return json.loads((SKILLS / skill / "evals/cases.json").read_text(encoding="utf-8"))["cases"]


class ShippedSkillTests(unittest.TestCase):
    def test_expected_skills_have_descriptors(self):
        expected = {
            "sdp-investigate", "sdp-plan-delivery", "sdp-implement", "sdp-technical-review",
            "sdp-security-review", "sdp-acceptance-validation", "write-tests",
        }
        self.assertTrue(expected <= set(DESCRIPTOR_SKILLS), expected - set(DESCRIPTOR_SKILLS))

    def test_every_described_skill_passes_checker(self):
        for skill in DESCRIPTOR_SKILLS:
            with self.subTest(skill=skill):
                self.assertEqual([], checker.check_skill(SKILLS / skill, SCHEMA, grader))

    def test_legacy_skills_keep_name_folder_agreement(self):
        for skill in ("create-api-endpoint", "create-ui-component", "database-migration", "error-handling"):
            with self.subTest(skill=skill):
                self.assertEqual([], checker.check_skill(SKILLS / skill, SCHEMA, grader))

    def test_reference_results_satisfy_cases(self):
        for skill in DESCRIPTOR_SKILLS:
            for case in cases_of(skill):
                with self.subTest(skill=skill, case=case["id"]):
                    self.assertEqual([], grader.grade(case, case["reference_result"]))

    def test_each_skill_has_defect_negative_or_escalation_case(self):
        for skill in DESCRIPTOR_SKILLS:
            kinds = {case["kind"] for case in cases_of(skill)}
            self.assertIn("correct", kinds, skill)
            self.assertTrue(kinds - {"correct"}, skill)

    def test_review_skills_cover_seeded_defects(self):
        for skill in ("sdp-technical-review", "sdp-security-review"):
            kinds = [case["kind"] for case in cases_of(skill)]
            self.assertGreaterEqual(kinds.count("seeded-defect"), 2, skill)

    def test_stage_result_contract_is_referenced_by_stage_skills(self):
        reference = SKILLS / "sdp-core/references/stage-result.md"
        self.assertTrue(reference.exists())
        for skill in ("sdp-technical-review", "sdp-security-review", "sdp-acceptance-validation", "sdp-investigate"):
            text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("stage-result", text, skill)


class GraderTests(unittest.TestCase):
    def test_empty_findings_never_satisfy_a_case_that_expects_findings(self):
        for skill in DESCRIPTOR_SKILLS:
            for case in cases_of(skill):
                expect = case["expect"]
                if not (expect.get("finding_patterns") or expect["verdict"] in ("fail", "blocked")):
                    continue
                empty = {"verdict": expect["verdict"], "findings": [], "detected_triggers": list(expect.get("triggers", []))}
                with self.subTest(skill=skill, case=case["id"]):
                    self.assertTrue(grader.grade(case, empty))

    def test_wrong_verdict_with_reference_findings_never_passes(self):
        for skill in DESCRIPTOR_SKILLS:
            for case in cases_of(skill):
                wrong = next(v for v in ("pass", "fail", "blocked", "not_applicable") if v != case["expect"]["verdict"])
                with self.subTest(skill=skill, case=case["id"]):
                    self.assertTrue(grader.grade(case, {**case["reference_result"], "verdict": wrong}))

    def test_keyword_stuffing_is_a_documented_limit(self):
        case = next(c for c in cases_of("sdp-technical-review") if c["id"] == "off-by-one-drops-last-item")
        stuffed = {"verdict": "fail", "findings": ["High: last item off-by-one drops boundary"], "detected_triggers": []}
        self.assertEqual([], grader.grade(case, stuffed))

    def case(self):
        return next(c for c in cases_of("sdp-security-review") if c["id"] == "sql-built-from-input")

    def test_wrong_verdict_fails(self):
        case = self.case()
        self.assertTrue(grader.grade(case, {**case["reference_result"], "verdict": "pass"}))

    def test_missing_finding_fails(self):
        case = self.case()
        self.assertTrue(grader.grade(case, {**case["reference_result"], "findings": ["Low: style nit"]}))

    def test_severity_floor_is_enforced(self):
        case = self.case()
        weak = {**case["reference_result"], "findings": ["Low: SQL injection via concatenation, parameterize"]}
        self.assertTrue(any("severity" in item for item in grader.grade(case, weak)))

    def test_missing_trigger_fails(self):
        case = self.case()
        self.assertTrue(any("trigger" in i for i in grader.grade(case, {**case["reference_result"], "detected_triggers": []})))

    def test_forbidden_pattern_fails(self):
        case = next(c for c in cases_of("sdp-technical-review") if c["id"] == "self-review-is-blocked")
        result = {**case["reference_result"], "findings": [*case["reference_result"]["findings"], "approved, looks good"]}
        self.assertTrue(grader.grade(case, result))

    def test_fail_without_findings_fails(self):
        case = self.case()
        self.assertTrue(grader.grade(case, {"verdict": "fail", "findings": []}))

    def test_not_applicable_needs_reason(self):
        case = next(c for c in cases_of("sdp-security-review") if c["id"] == "docs-only-not-applicable")
        failures = grader.grade(case, {"verdict": "not_applicable", "findings": ["docs only"]})
        self.assertTrue(any("reason" in item for item in failures))


class CheckerNegativeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name) / "sdp-technical-review"
        shutil.copytree(SKILLS / "sdp-technical-review", self.folder)

    def errors(self):
        return checker.check_skill(self.folder, SCHEMA, grader)

    def test_unmodified_copy_is_clean(self):
        self.assertEqual([], self.errors())

    def test_name_folder_mismatch(self):
        path = self.folder / "SKILL.md"
        path.write_text(path.read_text(encoding="utf-8").replace("name: sdp-technical-review", "name: other-name", 1))
        self.assertTrue(any("must match folder" in e for e in self.errors()))

    def test_missing_description(self):
        path = self.folder / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        start = text.index("description:")
        end = text.index("\n---", start)
        path.write_text(text[:start] + text[end:])
        self.assertTrue(any("description" in e for e in self.errors()))

    def test_description_without_use_when(self):
        path = self.folder / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("Use when", "Applies if", 1))
        self.assertTrue(any("Use when" in e for e in self.errors()))

    def test_broken_link(self):
        path = self.folder / "SKILL.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nSee [guide](references/missing.md).\n")
        self.assertTrue(any("broken link" in e for e in self.errors()))

    def test_missing_evaluation_file(self):
        (self.folder / "evals/cases.json").unlink()
        self.assertTrue(any("evaluation file missing" in e for e in self.errors()))

    def test_invalid_descriptor(self):
        path = self.folder / "sdp.skill.json"
        descriptor = json.loads(path.read_text(encoding="utf-8"))
        descriptor["capability"] = "not-a-capability"
        path.write_text(json.dumps(descriptor))
        self.assertTrue(any("sdp.skill.json" in e for e in self.errors()))

    def test_reference_that_fails_its_own_case(self):
        path = self.folder / "evals/cases.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["cases"][1]["reference_result"]["verdict"] = "pass"
        path.write_text(json.dumps(document))
        self.assertTrue(any("own case" in e for e in self.errors()))

    def test_verdict_only_failing_case_is_rejected(self):
        path = self.folder / "evals/cases.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        case = next(c for c in document["cases"] if c["expect"]["verdict"] == "fail")
        case["expect"] = {"verdict": "fail"}
        path.write_text(json.dumps(document))
        self.assertTrue(any("must name the finding" in e for e in self.errors()))

    def test_too_few_cases(self):
        path = self.folder / "evals/cases.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["cases"] = document["cases"][:2]
        path.write_text(json.dumps(document))
        self.assertTrue(any("at least three" in e for e in self.errors()))

    def test_oversized_skill(self):
        path = self.folder / "SKILL.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nline\n" * 600)
        self.assertTrue(any("lines" in e for e in self.errors()))


if __name__ == "__main__":
    unittest.main()
