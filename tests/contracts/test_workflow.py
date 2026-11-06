"""Workflow definition and next-action tests, driven the way a coordinator would."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
import test_validator as tv  # noqa: E402

sdp = tv.sdp
HUMAN = tv.HUMAN
CAPS = tv.CAPS


class Driver(tv.Base):
    def nxt(self, capabilities=CAPS, package=None):
        args = ["next"]
        if capabilities is not None:
            args += ["--capabilities", capabilities]
        code, payload = self.repo.cli(package or self.pkg, *args)
        self.assertEqual(0, code, payload)
        return payload

    def assertNext(self, action, **expected):
        payload = self.nxt()
        self.assertEqual(action, payload["action"], payload)
        for key, value in expected.items():
            self.assertEqual(value, payload.get(key), payload)
        return payload

    def deliver_to_awaiting(self):
        self.approve()
        self.assertNext("start-delivery")
        self.assertEqual(0, self.move("delivering", caps=CAPS)[0])
        self.assertNext("run-stage", stage="developer")
        self.repo.edit("fixed\n")
        self.assertEqual(0, self.result("developer")[0])
        self.assertNext("run-stage", stage="reviewer", isolation="independent")
        self.assertEqual(0, self.result("reviewer")[0])
        self.assertNext("request-acceptance")
        self.assertEqual(0, self.move("awaiting-acceptance")[0])


class WorkflowDefinitionTests(unittest.TestCase):
    def test_shipped_bug_workflow_is_valid(self):
        self.assertEqual([], sdp.validate_workflow(sdp.load_workflow("bug")))

    def test_workflow_requires_review_always(self):
        document = sdp.load_workflow("bug")
        document["stages"][1]["required"] = "on-trigger-or-policy"
        self.assertTrue(any("reviewer" in e for e in sdp.validate_workflow(document)))

    def test_workflow_requires_independent_assurance(self):
        document = sdp.load_workflow("bug")
        document["stages"][1]["isolation"] = "none"
        self.assertTrue(any("isolation" in e for e in sdp.validate_workflow(document)))

    def test_workflow_cannot_drop_the_isolation_capability(self):
        document = sdp.load_workflow("bug")
        document["capabilities_required"].remove("independent-context")
        self.assertTrue(any("independent-context" in e for e in sdp.validate_workflow(document)))

    def test_workflow_stage_order_and_limits_are_fixed(self):
        document = sdp.load_workflow("bug")
        document["stages"].reverse()
        self.assertTrue(any("in that order" in e for e in sdp.validate_workflow(document)))
        document = sdp.load_workflow("bug")
        document["limits"]["rejected_candidates_before_escalation"] = 5
        self.assertTrue(any("must be 2" in e for e in sdp.validate_workflow(document)))

    def test_workflow_names_capabilities_not_agents(self):
        text = json.dumps(sdp.load_workflow("bug"))
        self.assertNotIn("sdp.developer", text)
        self.assertNotIn("sdp.reviewer", text)

    def test_unknown_and_traversal_names_refused(self):
        for name in ("missing", "../bug", "bug/../bug", ""):
            with self.subTest(name=name):
                with self.assertRaises(sdp.ProtocolError):
                    sdp.load_workflow(name)

    def test_override_directory_is_validated(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "bug.json").write_text(json.dumps({"schema_version": 1, "workflow": "bug"}))
            os.environ["SDP_WORKFLOW_DIR"] = folder
            try:
                with self.assertRaises(sdp.ProtocolError) as caught:
                    sdp.load_workflow("bug")
            finally:
                del os.environ["SDP_WORKFLOW_DIR"]
        self.assertEqual("workflow_invalid", caught.exception.error)

    def test_approval_rejects_unknown_workflow(self):
        repo = tv.Repo(self)
        package = repo.package()
        code, payload = repo.cli(package, "approve", "--by", HUMAN, "--workflow", "incident")
        self.assertEqual("workflow_unknown", payload["error"])


class HostProfileTests(Driver):
    def profile(self, **capabilities):
        folder = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(folder, ignore_errors=True))
        entries = {name: {"provided": "unverified"} for name in sdp.CAPABILITY_NAMES}
        entries.update(capabilities)
        document = {"schema_version": 1, "host": "fake", "capabilities": entries}
        (Path(folder) / "fake.json").write_text(json.dumps(document))
        previous = os.environ.get("SDP_HOSTS_DIR")
        os.environ["SDP_HOSTS_DIR"] = folder

        def restore():
            if previous is None:
                os.environ.pop("SDP_HOSTS_DIR", None)
            else:
                os.environ["SDP_HOSTS_DIR"] = previous

        self.addCleanup(restore)
        return folder

    def verified(self, *names):
        return {name: {"provided": True, "evidence": ["HISTORY.md"]} for name in names}

    def test_shipped_profiles_are_valid_and_claim_no_unproven_capability(self):
        folder = sdp.DEFAULT_HOSTS_DIR
        profiles = sorted(folder.glob("*.json"))
        self.assertTrue(profiles)
        for path in profiles:
            with self.subTest(profile=path.name):
                document = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual([], sdp.validate_host_profile(document))
                self.assertEqual([], sdp.load_host_capabilities(path.stem))

    def test_unverified_host_blocks_instead_of_allowing_self_review(self):
        self.approve()
        code, payload = self.repo.cli(self.pkg, "next", "--host", "copilot-cli")
        self.assertEqual(0, code, payload)
        self.assertEqual("blocked-capability", payload["action"])
        self.assertEqual("host:copilot-cli", payload["capability_source"])
        self.assertIn("independent-context", payload["missing"])

    def test_verified_host_allows_the_workflow(self):
        self.profile(**self.verified("implement", "technical-review", "independent-context"))
        self.approve()
        code, payload = self.repo.cli(self.pkg, "next", "--host", "fake")
        self.assertEqual("start-delivery", payload["action"])
        self.assertEqual("host:fake", payload["capability_source"])

    def test_verified_capability_must_cite_evidence(self):
        self.profile(implement={"provided": True})
        code, payload = self.repo.cli(self.pkg, "next", "--host", "fake")
        self.assertEqual("host_invalid", payload["error"])
        self.assertIn("evidence", payload["message"])

    def test_unknown_and_traversal_host_names_refused(self):
        for name in ("nope", "../x", ""):
            with self.subTest(name=name):
                with self.assertRaises(sdp.ProtocolError):
                    sdp.load_host_capabilities(name)

    def test_host_and_explicit_capabilities_are_mutually_exclusive(self):
        code, payload = self.repo.cli(self.pkg, "next", "--host", "copilot-cli", "--capabilities", CAPS)
        self.assertEqual(2, code)
        self.assertEqual("usage", payload["error"])

    def test_capability_source_is_reported(self):
        self.assertEqual("unchecked", self.nxt(capabilities=None)["capability_source"])
        self.assertEqual("explicit", self.nxt()["capability_source"])

    def test_transition_with_unverified_host_is_refused(self):
        self.approve()
        code, payload = self.repo.cli(
            self.pkg, "transition", "--to", "delivering", "--expected-revision",
            str(self.repo.revision(self.pkg)), "--host", "copilot-cli")
        self.assertEqual("capability_missing", payload["error"])
        self.assertEqual("planned", self.repo.record(self.pkg)["delivery_status"])

    def test_transition_records_where_capabilities_came_from(self):
        self.profile(**self.verified("implement", "technical-review", "independent-context"))
        self.approve()
        code, payload = self.repo.cli(
            self.pkg, "transition", "--to", "delivering", "--expected-revision",
            str(self.repo.revision(self.pkg)), "--host", "fake")
        self.assertEqual(0, code, payload)
        self.assertEqual("host:fake", self.repo.record(self.pkg)["capability_source"])
        code, payload = self.repo.cli(self.pkg, "inspect")
        self.assertEqual("host:fake", payload["capability_source"])

    def test_explicit_assertion_is_recorded_as_explicit(self):
        self.approve()
        self.assertEqual(0, self.move("delivering", caps=CAPS)[0])
        self.assertEqual("explicit", self.repo.record(self.pkg)["capability_source"])

    def test_transition_host_and_capabilities_are_mutually_exclusive(self):
        self.approve()
        code, payload = self.repo.cli(
            self.pkg, "transition", "--to", "delivering", "--expected-revision",
            str(self.repo.revision(self.pkg)), "--host", "copilot-cli", "--capabilities", CAPS)
        self.assertEqual(2, code)
        self.assertEqual("usage", payload["error"])

    def test_forged_capability_source_in_record_is_rejected(self):
        self.approve()
        path = self.repo.root / self.pkg / "DELIVERY-RUN.json"
        record = json.loads(path.read_text())
        record["capability_source"] = "trust-me"
        self.assertTrue(any("capability_source" in e for e in sdp.validate_structure(record)))

    def test_profile_must_list_exactly_the_known_capabilities(self):
        document = {"schema_version": 1, "host": "x", "capabilities": {"implement": {"provided": True, "evidence": ["e"]}}}
        self.assertTrue(any("exactly" in e for e in sdp.validate_host_profile(document)))


class NextActionTests(Driver):
    def test_unapproved_plan_waits_for_human(self):
        self.assertNext("await-plan-approval", actor="human")

    def test_approved_plan_without_record_is_recorded(self):
        plan = self.repo.root / self.pkg / "PLAN.md"
        tv.write_lf(plan, plan.read_text().replace("status: draft", "status: approved")
                        .replace("approved_by: pending", f"approved_by: {HUMAN}")
                        .replace("approved_at: pending", "approved_at: 2026-11-05"))
        self.assertNext("approve-plan", actor="coordinator")

    def test_next_is_read_only(self):
        self.approve()
        record = (self.repo.root / self.pkg / "DELIVERY-RUN.json").read_text()
        for _ in range(3):
            self.nxt()
        self.assertEqual(record, (self.repo.root / self.pkg / "DELIVERY-RUN.json").read_text())

    def test_full_happy_path_ends_in_human_decision(self):
        self.deliver_to_awaiting()
        payload = self.assertNext("await-human-decision", actor="human")
        self.assertIn("accepted", payload["options"])
        self.assertEqual(0, self.move("accepted", decided_by=HUMAN)[0])
        self.assertNext("done")

    def test_failed_review_repair_and_recheck(self):
        self.approve()
        self.move("delivering", caps=CAPS)
        self.repo.edit("attempt\n")
        self.result("developer")
        code, payload = self.result("reviewer", "fail", findings=["High: wrong output"])
        self.assertEqual(1, payload["rejected_candidates"])
        self.assertNext("resume-delivery")
        self.assertEqual(0, self.move("delivering")[0])
        repair = self.assertNext("run-stage", stage="developer", repair=True)
        self.assertEqual(["High: wrong output"], repair["findings"])
        self.repo.edit("repaired\n")
        self.assertNext("run-stage", stage="developer")
        self.result("developer")
        self.assertNext("run-stage", stage="reviewer")
        self.result("reviewer")
        self.assertNext("request-acceptance")

    def test_interrupt_and_resume_reads_stored_state(self):
        self.approve()
        self.move("delivering", caps=CAPS)
        self.repo.edit("work\n")
        self.result("developer")
        first = self.nxt()
        second = self.nxt()
        self.assertEqual(first, second)
        self.assertEqual("reviewer", second["stage"])

    def test_blocked_stage_waits_then_reruns_same_stage(self):
        self.approve()
        self.move("delivering", caps=CAPS)
        self.repo.edit("work\n")
        self.result("developer", "blocked", findings=["tests cannot run: no database"])
        payload = self.assertNext("resolve-block", actor="human")
        self.assertIn("no database", payload["reason"])
        self.assertEqual(0, self.move("delivering")[0])
        self.assertNext("run-stage", stage="developer")
        self.assertEqual(0, self.repo.record(self.pkg)["rejected_candidates"])

    def test_candidate_change_after_assurance_requires_recheck(self):
        self.deliver_to_awaiting()
        self.repo.edit("changed after review\n")
        payload = self.assertNext("await-human-decision")
        self.assertIn("working tree changed", payload["warning"])
        self.assertEqual(1, self.move("accepted", decided_by=HUMAN)[0])
        code, _ = self.move("changes-requested", decided_by=HUMAN, reason="please also handle blanks")
        self.assertEqual(0, code)
        self.assertEqual(0, self.move("delivering", human_guided=True, decided_by=HUMAN)[0])
        self.assertNext("run-stage", stage="developer")
        self.result("developer")
        self.assertNext("run-stage", stage="reviewer")

    def test_second_rejection_escalates_with_options(self):
        self.approve()
        self.move("delivering", caps=CAPS)
        for attempt in ("one\n", "two\n"):
            self.repo.edit(attempt)
            self.result("developer")
            self.result("reviewer", "fail", findings=["High: still wrong"])
            if attempt == "one\n":
                self.assertEqual(0, self.move("delivering")[0])
        payload = self.assertNext("escalate-to-human", actor="human")
        self.assertTrue(any("human-guided" in option for option in payload["options"]))
        self.assertEqual(2, self.repo.record(self.pkg)["rejected_candidates"])

    def test_security_trigger_is_forwarded_to_independent_specialist(self):
        self.approve()
        self.move("delivering", caps=CAPS)
        self.repo.edit("input handling\n")
        self.result("developer")
        self.result("reviewer", triggers=["security:input"])
        self.assertNext("run-stage", stage="security", isolation="independent", skill="sdp-security-review")
        self.result("security")
        self.assertNext("request-acceptance")

    def test_waiver_does_not_skip_forwarded_trigger(self):
        self.approve(None, "--epic-security-policy", "waived")
        self.move("delivering", caps=CAPS)
        self.repo.edit("x\n")
        self.result("developer")
        self.result("reviewer", triggers=["security:secrets"])
        self.assertNext("run-stage", stage="security")

    def test_missing_independent_capability_blocks_instead_of_self_review(self):
        self.approve()
        self.move("delivering", caps=CAPS)
        self.repo.edit("x\n")
        self.result("developer")
        payload = self.nxt(capabilities="implement")
        self.assertEqual("blocked-capability", payload["action"])
        self.assertIn("self-review", payload["reason"])
        self.assertEqual("reviewer", payload["stage"])

    def test_reviewer_capability_without_isolation_still_blocks(self):
        self.approve()
        self.move("delivering", caps=CAPS)
        self.repo.edit("x\n")
        self.result("developer")
        payload = self.nxt(capabilities="implement,technical-review")
        self.assertEqual("blocked-capability", payload["action"])
        self.assertEqual(["independent-context"], payload["missing"])
        self.assertEqual("reviewer", payload["stage"])

    def test_plan_edit_mid_delivery_requires_replan_not_resume(self):
        self.approve()
        self.move("delivering", caps=CAPS)
        plan = self.repo.root / self.pkg / "PLAN.md"
        tv.write_lf(plan, plan.read_text() + "More scope.\n")
        payload = self.assertNext("replan", actor="human")
        self.assertIn("approval is stale", payload["reason"])
        self.repo.edit("work\n")
        code, payload = self.result("developer")
        self.assertEqual(1, code)
        self.assertIn("approval is stale", payload["message"])

    def test_voided_approval_waits_for_new_human_approval(self):
        self.approve()
        self.move("delivering", caps=CAPS)
        self.assertEqual(0, self.move("planned", reason="needs a new public API")[0])
        self.assertNext("await-plan-approval")

    def test_workflow_is_taken_from_the_record(self):
        self.approve()
        self.assertEqual("bug", self.repo.record(self.pkg)["workflow"])

    def test_approval_binds_to_the_plan_the_human_saw(self):
        shown = self.nxt()["plan_fingerprint"]
        plan = self.repo.root / self.pkg / "PLAN.md"
        tv.write_lf(plan, plan.read_text() + "Quietly added scope.\n")
        code, payload = self.repo.cli(
            self.pkg, "approve", "--by", HUMAN, "--expect-plan-fingerprint", shown)
        self.assertEqual("plan_changed", payload["error"])
        self.assertFalse((self.repo.root / self.pkg / "DELIVERY-RUN.json").exists())
        fresh = self.nxt()["plan_fingerprint"]
        code, payload = self.repo.cli(
            self.pkg, "approve", "--by", HUMAN, "--expect-plan-fingerprint", fresh)
        self.assertEqual(0, code, payload)

    def test_next_names_the_approver_for_an_already_approved_plan(self):
        plan = self.repo.root / self.pkg / "PLAN.md"
        tv.write_lf(plan, plan.read_text().replace("status: draft", "status: approved")
                        .replace("approved_by: pending", f"approved_by: {HUMAN}")
                        .replace("approved_at: pending", "approved_at: 2026-11-05"))
        payload = self.assertNext("approve-plan", approved_by=HUMAN)
        code, _ = self.repo.cli(self.pkg, "approve", "--by", payload["approved_by"],
                                "--expect-plan-fingerprint", payload["plan_fingerprint"])
        self.assertEqual(0, code)

    def test_missing_capability_blocks_before_delivery_starts(self):
        self.approve()
        payload = self.nxt(capabilities="implement")
        self.assertEqual("blocked-capability", payload["action"])
        self.assertEqual(["independent-context", "technical-review"], payload["missing"])
        payload = self.nxt(capabilities="")
        self.assertEqual(["implement", "independent-context", "technical-review"], payload["missing"])

    def test_compliance_reports_every_missing_capability_at_once(self):
        self.approve(None, "--profile", "Compliance")
        self.move("delivering", caps=CAPS)
        self.repo.edit("x\n")
        self.result("developer")
        self.result("reviewer")
        payload = self.nxt(capabilities="implement,technical-review,independent-context")
        self.assertEqual("blocked-capability", payload["action"])
        self.assertEqual(["acceptance-validation", "security-review"], payload["missing"])

    def test_plan_edit_after_changes_requested_is_a_replan(self):
        self.approve()
        self.move("delivering", caps=CAPS)
        self.repo.edit("attempt\n")
        self.result("developer")
        self.result("reviewer", "fail", findings=["High: wrong"])
        plan = self.repo.root / self.pkg / "PLAN.md"
        tv.write_lf(plan, plan.read_text() + "Extra.\n")
        self.assertNext("replan")

    def test_plan_edit_while_blocked_is_a_replan(self):
        self.approve()
        self.move("delivering", caps=CAPS)
        self.move("blocked", reason="waiting")
        plan = self.repo.root / self.pkg / "PLAN.md"
        tv.write_lf(plan, plan.read_text() + "Extra.\n")
        self.assertNext("replan")


if __name__ == "__main__":
    unittest.main()
