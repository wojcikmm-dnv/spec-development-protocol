"""Feature workflow: gates, artifact approvals, story availability, and the lightweight path."""

import json
import os
import shutil
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
import test_validator as tv  # noqa: E402

sdp = tv.sdp
HUMAN = tv.HUMAN
CAPS = tv.CAPS
SLUG = "f"

BACKLOG_BODY = (
    "# Backlog: Greeting\n\n## Epics\n\n| ID | Title | Priority | Security Policy | Status |\n| --- | --- | --- | --- | --- |\n"
    "| EPIC-1 | Greeting | P0 | risk-based | draft |\n\n## Stories\n\n"
    "| Story ID | Epic | Outcome | Priority | Dependencies |\n| --- | --- | --- | --- | --- |\n"
    "| STORY-1 | EPIC-1 | Blank names greet friend | P0 | none |\n"
    "| STORY-2 | EPIC-1 | Names are trimmed | P1 | STORY-1 |\n\n## Open Decisions\n\n- none\n"
)


class FeatureBase(tv.Base):
    def feature(self, *args):
        return self.repo.cli(None, *args) if False else self._feature_cli(*args)

    def _feature_cli(self, *args):
        import contextlib
        import io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sdp.main(["--repo", str(self.repo.root), "--json", *args])
        text = out.getvalue().strip()
        return code, json.loads(text) if text else {}

    def fnext(self):
        code, payload = self._feature_cli("feature-next", "--slug", SLUG)
        self.assertEqual(0, code, payload)
        return payload

    def write(self, name, status="draft", body="# Doc\n"):
        approved = status == "approved"
        head = (f"---\nstatus: {status}\napproved_by: {HUMAN if approved else 'pending'}\n"
                f"approved_at: {'2026-11-05' if approved else 'pending'}\n---\n")
        path = self.repo.root / "spec" / SLUG / name
        tv.write_lf(path, head + body)
        return f"spec/{SLUG}/{name}"

    def approve_artifact(self, relative, **extra):
        args = ["approve-artifact", "--path", relative, "--by", extra.get("by", HUMAN)]
        if "fingerprint" in extra:
            args += ["--expect-fingerprint", extra["fingerprint"]]
        return self._feature_cli(*args)

    def all_gates_approved(self):
        self.write("PRD.md", "approved")
        self.write("BACKLOG.md", "approved", BACKLOG_BODY)
        self.write("EPIC-1.md", "approved")
        self.write("DESIGN.md", "approved")

    def write_record(self, package, status, audits=()):
        record = sdp.new_record("x-DP-1", "feature", "Lean", {"profile_floor": "Lean", "epic_security_policy": "risk-based", "mandatory_stages": []})
        record["delivery_status"] = status
        record["pending_audit"] = list(audits)
        (self.repo.root / package / "DELIVERY-RUN.json").write_text(json.dumps(record))

    def accept_package(self, name, stories):
        package = self.repo.package(name, f"stories: [{', '.join(stories)}]\n")
        self.write_record(package, "accepted")
        return package


class FeatureWorkflowDefinitionTests(unittest.TestCase):
    def test_shipped_feature_workflow_is_valid_and_bug_has_no_gates(self):
        self.assertEqual([], sdp.validate_workflow(sdp.load_workflow("feature")))
        self.assertNotIn("gates", sdp.load_workflow("bug"))

    def test_gate_rules(self):
        document = sdp.load_workflow("feature")
        document["gates"] = [g for g in document["gates"] if g["artifact"] != "DESIGN"]
        self.assertTrue(any("include PRD, BACKLOG, and DESIGN" in e for e in sdp.validate_workflow(document)))
        document = sdp.load_workflow("feature")
        document["gates"].reverse()
        self.assertTrue(any("order" in e for e in sdp.validate_workflow(document)))
        document = sdp.load_workflow("feature")
        document["gates"][0]["gate"] = 3
        self.assertTrue(any("gates[0]" in e for e in sdp.validate_workflow(document)))
        document = sdp.load_workflow("feature")
        document["gates"].append(dict(document["gates"][0]))
        self.assertTrue(sdp.validate_workflow(document))

    def test_feature_keeps_the_same_assurance_rules_as_bug(self):
        feature, bug = sdp.load_workflow("feature"), sdp.load_workflow("bug")
        self.assertEqual(bug["stages"], feature["stages"])
        self.assertEqual(bug["limits"], feature["limits"])
        self.assertEqual(bug["capabilities_required"], feature["capabilities_required"])


class GateDerivationTests(FeatureBase):
    def setUp(self):
        super().setUp()
        shutil.rmtree(self.repo.root / self.pkg)
        (self.repo.root / "spec/f/PRD.md").unlink()

    def test_missing_prd_asks_a_worker_to_author_it(self):
        payload = self.fnext()
        self.assertEqual("complete-gate", payload["action"])
        self.assertEqual("worker", payload["actor"])
        self.assertEqual("/create-prd", payload["entry_point"])

    def test_draft_artifact_waits_for_a_human_and_reports_its_fingerprint(self):
        self.write("PRD.md", "draft")
        payload = self.fnext()
        self.assertEqual(("await-gate-approval", "human"), (payload["action"], payload["actor"]))
        self.assertEqual("spec/f/PRD.md", payload["path"])
        self.assertTrue(payload["artifact_fingerprint"])

    def test_gates_advance_only_as_each_artifact_is_approved(self):
        relative = self.write("PRD.md", "draft")
        self.assertEqual(0, self.approve_artifact(relative)[0])
        payload = self.fnext()
        self.assertEqual(("complete-gate", 2, "BACKLOG"), (payload["action"], payload["gate"], payload["artifact"]))
        self.write("BACKLOG.md", "approved", BACKLOG_BODY)
        self.assertEqual("EPIC", self.fnext()["artifact"])
        self.write("EPIC-1.md", "approved")
        self.assertEqual(("complete-gate", "DESIGN"), (self.fnext()["action"], self.fnext()["artifact"]))
        self.write("DESIGN.md", "approved")
        self.assertEqual("plan-package", self.fnext()["action"])

    def test_every_epic_must_be_approved(self):
        self.write("PRD.md", "approved")
        self.write("BACKLOG.md", "approved", BACKLOG_BODY)
        self.write("EPIC-1.md", "approved")
        self.write("EPIC-2.md", "draft")
        payload = self.fnext()
        self.assertEqual(("await-gate-approval", "spec/f/EPIC-2.md"), (payload["action"], payload["path"]))

    def test_malformed_frontmatter_is_reported_as_an_artifact_problem(self):
        (self.repo.root / "spec/f/PRD.md").write_text("---\nstatus: approved\nowner:\n  name: x\n---\nbody\n")
        payload = self.fnext()
        self.assertEqual(("fix-artifact", "worker"), (payload["action"], payload["actor"]))

    def test_approved_status_without_a_named_approver_does_not_count(self):
        (self.repo.root / "spec/f/PRD.md").write_text(
            "---\nstatus: approved\napproved_by: pending\napproved_at: pending\n---\nbody\n")
        self.assertEqual("await-gate-approval", self.fnext()["action"])

    def test_status_is_derived_not_stored(self):
        self.all_gates_approved()
        self.fnext()
        for path in (self.repo.root / "spec/f").rglob("*"):
            if path.is_file():
                self.assertNotIn("feature_status", path.read_text(encoding="utf-8"))

    def test_unknown_or_unsafe_slug(self):
        for slug in ("missing", "../x", ""):
            code, payload = self._feature_cli("feature-next", "--slug", slug)
            self.assertNotEqual(0, code, slug)


class ArtifactApprovalTests(FeatureBase):
    def test_agent_cannot_approve_an_artifact(self):
        relative = self.write("PRD.md", "draft")
        code, payload = self.approve_artifact(relative, by="sdp.prd")
        self.assertEqual("human_required", payload["error"])
        self.assertIn("draft", (self.repo.root / relative).read_text())

    def test_only_gate_artifacts_inside_spec_can_be_approved(self):
        self.write("PRD.md", "draft")
        for bad in ("src/app.txt", "spec/f/PLAN.md", "spec/f/notes.md", "../PRD.md", "spec/f/sub/PRD.md", "PRD.md"):
            code, payload = self.approve_artifact(bad)
            self.assertEqual("artifact_invalid", payload.get("error"), bad)

    def test_fingerprint_binds_approval_to_what_the_human_saw(self):
        relative = self.write("PRD.md", "draft", "# PRD\n\nShow this.\n")
        shown = self.fnext()["artifact_fingerprint"]
        self.write("PRD.md", "draft", "# PRD\n\nQuietly changed.\n")
        code, payload = self.approve_artifact(relative, fingerprint=shown)
        self.assertEqual("artifact_changed", payload["error"])
        self.assertIn("draft", (self.repo.root / relative).read_text())

    def test_approval_is_refused_while_a_package_is_in_delivery(self):
        self.write("PRD.md", "approved")
        relative = self.write("BACKLOG.md", "draft", BACKLOG_BODY)
        package = self.repo.package()
        self.approve(package, "--gates", "x") if False else None
        self.start()
        code, payload = self.approve_artifact(relative)
        self.assertEqual("delivery_in_progress", payload["error"])

    def test_approval_after_delivery_closes_is_allowed(self):
        relative = self.write("BACKLOG.md", "draft", BACKLOG_BODY)
        self.accept_package("f-DP-9", ["STORY-1"])
        code, payload = self.approve_artifact(relative)
        self.assertEqual(0, code, payload)

    def test_symlinked_artifact_is_refused(self):
        target = self.repo.root / "elsewhere.md"
        target.write_text("---\nstatus: draft\napproved_by: pending\napproved_at: pending\n---\n")
        link = self.repo.root / "spec/f/DESIGN.md"
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        code, payload = self.approve_artifact("spec/f/DESIGN.md")
        self.assertEqual("path_escape", payload["error"])
        self.assertIn("draft", target.read_text())


class StoryAvailabilityTests(FeatureBase):
    def setUp(self):
        super().setUp()
        shutil.rmtree(self.repo.root / self.pkg)
        self.all_gates_approved()

    def test_only_stories_whose_dependencies_are_accepted_are_offered(self):
        payload = self.fnext()
        self.assertEqual("plan-package", payload["action"])
        self.assertEqual(["STORY-1"], payload["available_stories"])
        self.assertEqual(["STORY-2"], payload["waiting_on_dependencies"])

    def test_accepting_a_package_releases_dependent_stories(self):
        self.accept_package("f-DP-1", ["STORY-1"])
        payload = self.fnext()
        self.assertEqual(["STORY-2"], payload["available_stories"])
        self.assertEqual(["STORY-1"], payload["stories_done"])

    def test_stories_in_an_open_package_are_not_offered_again(self):
        package = self.repo.package("f-DP-1", "stories: [STORY-1]\n")
        payload = self.fnext()
        self.assertEqual("continue-packages", payload["action"])
        self.assertEqual({"STORY-1": "f-DP-1"}, payload["stories_in_open_packages"])
        self.assertEqual({"f-DP-1": "planned"}, payload["open_packages"])

    def test_rejected_package_releases_its_stories(self):
        package = self.repo.package("f-DP-1", "stories: [STORY-1]\n")
        self.write_record(package, "rejected")
        self.assertEqual(["STORY-1"], self.fnext()["available_stories"])

    def test_feature_is_complete_only_when_every_story_is_accepted(self):
        self.accept_package("f-DP-1", ["STORY-1"])
        self.accept_package("f-DP-2", ["STORY-2"])
        payload = self.fnext()
        self.assertEqual(("feature-complete", "none"), (payload["action"], payload["actor"]))

    def test_open_audit_obligation_prevents_completion(self):
        self.accept_package("f-DP-1", ["STORY-1"])
        package = self.accept_package("f-DP-2", ["STORY-2"])
        self.write_record(package, "accepted", ["epic-1-audit"])
        payload = self.fnext()
        self.assertEqual("close-audits", payload["action"])
        self.assertEqual(["epic-1-audit"], payload["pending_audit"])

    def test_circular_dependencies_are_reported_as_blocked(self):
        body = BACKLOG_BODY.replace("| P0 | none |", "| P0 | STORY-2 |")
        self.write("BACKLOG.md", "approved", body)
        payload = self.fnext()
        self.assertEqual(("blocked-stories", "human"), (payload["action"], payload["actor"]))

    def test_backlog_without_stories_is_a_problem(self):
        self.write("BACKLOG.md", "approved", "# Backlog\n\n## Stories\n\nnone yet\n")
        self.assertEqual("fix-artifact", self.fnext()["action"])


class PlaceholderIdentityTests(FeatureBase):
    PLACEHOLDERS = (" pending", "PENDING", "TBD", "todo", "none", "n/a", "   ", "-", "?", "unknown")

    def test_placeholder_approvers_never_count_as_approved(self):
        for value in self.PLACEHOLDERS:
            with self.subTest(value=value):
                plan = sdp.parse_plan(f'---\nstatus: approved\napproved_by: "{value}"\napproved_at: 2026-11-05\n---\nbody\n')
                self.assertFalse(sdp.plan_is_approved(plan))
                plan = sdp.parse_plan(f'---\nstatus: approved\napproved_by: Ada\napproved_at: "{value}"\n---\nbody\n')
                self.assertFalse(sdp.plan_is_approved(plan))

    def test_agent_names_in_frontmatter_never_count_as_approved(self):
        for value in ("sdp.prd", "Copilot", "ci-bot"):
            plan = sdp.parse_plan(f"---\nstatus: approved\napproved_by: {value}\napproved_at: 2026-11-05\n---\nbody\n")
            self.assertFalse(sdp.plan_is_approved(plan), value)

    def test_hand_edited_placeholder_approval_does_not_open_a_gate(self):
        (self.repo.root / "spec/f/PRD.md").write_text(
            '---\nstatus: approved\napproved_by: "TBD"\napproved_at: 2026-11-05\n---\nbody\n')
        self.assertEqual("await-gate-approval", self.fnext()["action"])

    def test_commands_refuse_placeholder_humans(self):
        relative = self.write("DESIGN.md", "draft")
        for value in ("TBD", "   ", "n/a", "pending"):
            code, payload = self.approve_artifact(relative, by=value)
            self.assertEqual("human_required", payload["error"], value)
            code, payload = self.repo.cli(self.pkg, "approve", "--by", value)
            self.assertEqual("human_required", payload["error"], value)
        self.assertIn("status: draft", (self.repo.root / relative).read_text())

    def test_acceptance_refuses_placeholder_deciders(self):
        self.reach_awaiting()
        for value in ("none", "TBD", "n/a"):
            code, payload = self.move("accepted", decided_by=value)
            self.assertEqual("human_required", payload["error"], value)


class ReviewHardeningTests(FeatureBase):
    def setUp(self):
        super().setUp()
        shutil.rmtree(self.repo.root / self.pkg)
        self.all_gates_approved()

    def test_symlinked_epic_is_reported_as_invalid_not_missing(self):
        target = self.repo.root / "elsewhere.md"
        target.write_text("---\nstatus: approved\napproved_by: Ada\napproved_at: 2026-11-05\n---\n")
        try:
            os.symlink(target, self.repo.root / "spec/f/EPIC-2.md")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        payload = self.fnext()
        self.assertEqual("fix-artifact", payload["action"])
        self.assertIn("symbolic link", payload["reason"])

    def test_dependency_on_an_unknown_story_is_reported(self):
        self.write("BACKLOG.md", "approved", BACKLOG_BODY.replace("| P1 | STORY-1 |", "| P1 | STORY-9 |"))
        payload = self.fnext()
        self.assertEqual("fix-artifact", payload["action"])
        self.assertIn("STORY-9", payload["reason"])

    def test_plan_stories_must_exist_in_the_backlog(self):
        package = self.repo.package("f-DP-4", "stories: [STORY-1, STORY-77]\n")
        code, payload = self.repo.cli(package, "approve", "--by", HUMAN, "--workflow", "feature")
        self.assertEqual("unknown_story", payload["error"])
        self.assertFalse((self.repo.root / package / "DELIVERY-RUN.json").exists())

    def test_junk_lightweight_basis_is_refused(self):
        for index, basis in enumerate(("x", "TBD", "n/a", "short", "   ")):
            package = self.repo.package(f"f-DP-{10 + index}", f'gates: lightweight\nbasis: "{basis}"\n')
            code, payload = self.repo.cli(package, "approve", "--by", HUMAN, "--workflow", "feature")
            self.assertEqual("lightweight_basis", payload["error"], basis)

    def test_malformed_record_in_another_package_is_a_clean_error(self):
        package = self.repo.package("f-DP-5", "stories: [STORY-1]\n")
        (self.repo.root / package / "DELIVERY-RUN.json").write_text("{not json")
        code, payload = self._feature_cli("feature-next", "--slug", SLUG)
        self.assertEqual(1, code)
        self.assertEqual("record_unreadable", payload["error"])

    def test_prerequisite_with_a_malformed_record_does_not_count_as_accepted(self):
        first = self.repo.package("f-DP-6", "stories: [STORY-1]\n")
        (self.repo.root / first / "DELIVERY-RUN.json").write_text(json.dumps({"invalid": "json"}))
        second = self.repo.package("f-DP-7", "sequenced_after: [f-DP-6]\nstories: [STORY-2]\n")
        code, payload = self.repo.cli(second, "approve", "--by", HUMAN, "--workflow", "feature")
        self.assertEqual(0, code, payload)
        code, payload = self.move("delivering", second, caps=CAPS)
        self.assertEqual("prerequisite_open", payload["error"])

    def test_record_missing_its_status_is_a_clean_error_not_a_traceback(self):
        package = self.repo.package("f-DP-5", "stories: [STORY-1]\n")
        (self.repo.root / package / "DELIVERY-RUN.json").write_text(json.dumps({"invalid": "json"}))
        code, payload = self._feature_cli("feature-next", "--slug", SLUG)
        self.assertNotEqual(0, code)
        self.assertFalse(payload.get("ok", False))


class PlanGateEnforcementTests(FeatureBase):
    def approve_feature(self, package=None, **extra):
        args = ["approve", "--by", HUMAN, "--workflow", "feature"]
        return self.repo.cli(package or self.pkg, *args)

    def test_plan_approval_is_refused_while_a_gate_is_open(self):
        code, payload = self.approve_feature()
        self.assertEqual("gate_open", payload["error"])
        self.assertFalse((self.repo.root / self.pkg / "DELIVERY-RUN.json").exists())
        self.assertIn("approved_by: pending", (self.repo.root / self.pkg / "PLAN.md").read_text())

    def test_plan_approval_succeeds_once_gates_are_approved(self):
        self.all_gates_approved()
        code, payload = self.approve_feature()
        self.assertEqual(0, code, payload)
        self.assertEqual("feature", self.repo.record(self.pkg)["workflow"])

    def test_lightweight_plan_needs_a_stated_basis(self):
        package = self.repo.package("f-DP-2", "gates: lightweight\n")
        code, payload = self.approve_feature(package)
        self.assertEqual("lightweight_basis", payload["error"])

    def test_lightweight_plan_with_a_basis_may_skip_open_gates(self):
        package = self.repo.package("f-DP-2", "gates: lightweight\nbasis: existing-greeting-contract\n")
        code, payload = self.approve_feature(package)
        self.assertEqual(0, code, payload)

    def test_unknown_gates_value_is_refused(self):
        package = self.repo.package("f-DP-2", "gates: none\n")
        code, payload = self.approve_feature(package)
        self.assertEqual("gates_invalid", payload["error"])

    def test_gates_and_basis_are_part_of_the_approval(self):
        package = self.repo.package("f-DP-2", "gates: lightweight\nbasis: existing-contract\n")
        self.assertEqual(0, self.approve_feature(package)[0])
        plan = self.repo.root / package / "PLAN.md"
        tv.write_lf(plan, plan.read_text().replace("basis: existing-contract", "basis: something-else"))
        code, payload = self.move("delivering", package, caps=CAPS)
        self.assertEqual("plan_stale", payload["error"])

    def test_switching_to_lightweight_after_approval_voids_it(self):
        self.all_gates_approved()
        self.assertEqual(0, self.approve_feature()[0])
        plan = self.repo.root / self.pkg / "PLAN.md"
        tv.write_lf(plan, plan.read_text().replace("---\n", "---\ngates: lightweight\nbasis: x\n", 1) if False else
                        plan.read_text().replace("approved_at:", "gates: lightweight\nbasis: x\napproved_at:", 1))
        code, payload = self.move("delivering", caps=CAPS)
        self.assertEqual("plan_stale", payload["error"])

    def test_stories_and_prerequisites_are_part_of_the_approval(self):
        package = self.repo.package("f-DP-3", "stories: [STORY-1]\n")
        self.all_gates_approved()
        self.assertEqual(0, self.approve_feature(package)[0])
        plan = self.repo.root / package / "PLAN.md"
        tv.write_lf(plan, plan.read_text().replace("stories: [STORY-1]", "stories: [STORY-1, STORY-2]"))
        code, payload = self.move("delivering", package, caps=CAPS)
        self.assertEqual("plan_stale", payload["error"])

    def test_bug_workflow_is_unaffected_by_missing_gates(self):
        code, payload = self.repo.cli(self.pkg, "approve", "--by", HUMAN)
        self.assertEqual(0, code, payload)

    def test_lightweight_still_requires_independent_review(self):
        package = self.repo.package("f-DP-2", "gates: lightweight\nbasis: existing-contract\n")
        self.assertEqual(0, self.approve_feature(package)[0])
        self.assertEqual(0, self.move("delivering", package, caps=CAPS)[0])
        self.repo.edit("changed\n")
        self.assertEqual(0, self.result("developer", package=package)[0])
        code, payload = self.move("awaiting-acceptance", package)
        self.assertEqual("assurance_incomplete", payload["error"])
        code, payload = self.repo.cli(package, "next", "--capabilities", CAPS)
        self.assertEqual(("run-stage", "reviewer"), (payload["action"], payload["stage"]))

    def test_feature_package_runs_the_same_assurance_loop(self):
        self.all_gates_approved()
        self.approve_feature()
        self.assertEqual(0, self.move("delivering", caps=CAPS)[0])
        self.repo.edit("done\n")
        self.result("developer")
        code, payload = self.repo.cli(self.pkg, "next", "--capabilities", CAPS)
        self.assertEqual(("run-stage", "reviewer", "independent"), (payload["action"], payload["stage"], payload["isolation"]))


if __name__ == "__main__":
    unittest.main()
