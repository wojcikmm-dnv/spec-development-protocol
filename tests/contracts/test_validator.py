"""Contract tests for the SDP validator. Each name maps to docs/PROTOCOL.md."""

import contextlib
import copy
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / ".apm/skills/sdp-core/scripts/sdp.py"
sys.dont_write_bytecode = True  # keep generated files out of the packaged skill
SCHEMA = SCRIPT.parent.parent / "schemas/run-record.schema.json"
spec = importlib.util.spec_from_file_location("sdp", SCRIPT)
sdp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sdp)

PLAN = "# Plan\n\nOutcome: fix the greeting.\n"
HUMAN = "Ada Lovelace"
CAPS = "implement,technical-review,security-review,acceptance-validation"


def run_git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


_TEMPLATE = {}


def template_repo():
    """Build one initial repository per run and copy it for each test."""
    if "path" not in _TEMPLATE:
        holder = tempfile.TemporaryDirectory()
        _TEMPLATE["holder"] = holder
        root = Path(holder.name)
        run_git(root, "init", "-q")
        run_git(root, "config", "user.email", "t@example.com")
        run_git(root, "config", "user.name", "Tester")
        run_git(root, "config", "commit.gpgsign", "false")
        (root / "src").mkdir()
        (root / "src/app.txt").write_text("v0\n")
        (root / "spec/f").mkdir(parents=True)
        (root / "spec/f/PRD.md").write_text("prd\n")
        run_git(root, "add", "-A")
        run_git(root, "commit", "-q", "-m", "init")
        _TEMPLATE["path"] = root
    return _TEMPLATE["path"]


class Repo:
    def __init__(self, test):
        self.tmp = tempfile.TemporaryDirectory()
        test.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        shutil.copytree(template_repo(), self.root)
        self.packages = {}

    def package(self, name="f-DP-1", frontmatter="", body=PLAN):
        folder = self.root / "spec/f/deliveries" / name
        folder.mkdir(parents=True, exist_ok=True)
        head = "---\nstatus: draft\napproved_by: pending\napproved_at: pending\n" + frontmatter + "---\n"
        (folder / "PLAN.md").write_text(head + body, newline="\n")
        return f"spec/f/deliveries/{name}"

    def cli(self, package, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sdp.main(["--repo", str(self.root), "--package", package, "--json", *args])
        text = out.getvalue().strip()
        return code, json.loads(text) if text else {}

    def record(self, package):
        return json.loads((self.root / package / "DELIVERY-RUN.json").read_text())

    def revision(self, package):
        return self.record(package)["state_revision"]

    def edit(self, text="changed\n", name="src/app.txt"):
        (self.root / name).write_text(text)


class Base(unittest.TestCase):
    def setUp(self):
        self.repo = Repo(self)
        self.pkg = self.repo.package()

    def approve(self, package=None, *extra):
        package = package or self.pkg
        code, payload = self.repo.cli(package, "approve", "--by", HUMAN, *extra)
        self.assertEqual(0, code, payload)

    def move(self, to, package=None, **options):
        package = package or self.pkg
        args = ["transition", "--to", to, "--expected-revision", str(self.repo.revision(package))]
        if "caps" in options:
            args += ["--capabilities", options["caps"]]
        for flag in ("decided_by", "reason"):
            if flag in options:
                args += ["--" + flag.replace("_", "-"), options[flag]]
        if options.get("human_guided"):
            args.append("--human-guided")
        return self.repo.cli(package, *args)

    def result(self, stage, verdict="pass", package=None, triggers=(), findings=(), reason=None):
        package = package or self.pkg
        args = ["result", "--stage", stage, "--verdict", verdict,
                "--expected-revision", str(self.repo.revision(package))]
        for item in findings:
            args += ["--finding", item]
        for item in triggers:
            args += ["--trigger", item]
        if reason:
            args += ["--reason", reason]
        return self.repo.cli(package, *args)

    def start(self, package=None):
        self.approve(package)
        code, payload = self.move("delivering", package, caps=CAPS)
        self.assertEqual(0, code, payload)

    def pass_all(self):
        self.repo.edit("done\n")
        for stage in ("developer", "reviewer"):
            self.assertEqual(0, self.result(stage)[0])

    def reach_awaiting(self):
        self.start()
        self.pass_all()
        code, payload = self.move("awaiting-acceptance")
        self.assertEqual(0, code, payload)


class ApprovalTests(Base):
    def test_unapproved_plan_blocks_delivering(self):
        code, payload = self.move("delivering", caps=CAPS) if False else self.repo.cli(
            self.pkg, "transition", "--to", "delivering", "--expected-revision", "0", "--capabilities", CAPS)
        self.assertEqual(1, code)
        self.assertEqual("plan_unapproved", payload["error"])

    def test_agent_cannot_approve(self):
        code, payload = self.repo.cli(self.pkg, "approve", "--by", "sdp.orchestrator")
        self.assertEqual(1, code)
        self.assertEqual("human_required", payload["error"])

    def test_edited_plan_body_invalidates_approval(self):
        self.approve()
        plan = self.repo.root / self.pkg / "PLAN.md"
        plan.write_text(plan.read_text() + "Extra scope.\n", newline="\n")
        code, payload = self.move("delivering", caps=CAPS)
        self.assertEqual(1, code)
        self.assertEqual("plan_stale", payload["error"])

    def test_edited_approval_metadata_detected(self):
        self.approve()
        plan = self.repo.root / self.pkg / "PLAN.md"
        plan.write_text(plan.read_text().replace(HUMAN, "Someone Else"), newline="\n")
        code, payload = self.move("delivering", caps=CAPS)
        self.assertEqual(1, code)
        self.assertIn("approval", payload["message"])

    def test_missing_independent_capability_blocks(self):
        self.approve()
        code, payload = self.move("delivering", caps="implement")
        self.assertEqual("capability_missing", payload["error"])

    def test_resume_keeps_approval_binding(self):
        self.start()
        self.assertEqual(0, self.move("blocked", reason="tool missing")[0])
        plan = self.repo.root / self.pkg / "PLAN.md"
        plan.write_text(plan.read_text() + "More.\n", newline="\n")
        code, payload = self.move("delivering")
        self.assertEqual("plan_stale", payload["error"])

    def test_frontmatter_rejects_nested_structures(self):
        with self.assertRaises(sdp.ProtocolError):
            sdp.parse_frontmatter("status: approved\nowner:\n  name: x")


class AssuranceTests(Base):
    def test_missing_review_prevents_awaiting_acceptance(self):
        self.start()
        self.repo.edit()
        self.assertEqual(0, self.result("developer")[0])
        code, payload = self.move("awaiting-acceptance")
        self.assertEqual("assurance_incomplete", payload["error"])

    def test_review_not_applicable_rejected(self):
        self.start()
        self.repo.edit()
        self.result("developer")
        code, payload = self.result("reviewer", "not_applicable", reason="skipped")
        self.assertEqual("mandatory_stage", payload["error"])

    def test_reviewer_requires_developer_first(self):
        self.start()
        code, payload = self.result("reviewer")
        self.assertEqual("developer_first", payload["error"])

    def test_waiver_does_not_suppress_undisposed_trigger(self):
        self.approve(None, "--epic-security-policy", "waived")
        self.move("delivering", caps=CAPS)
        self.repo.edit()
        self.result("developer")
        self.result("reviewer", triggers=["security:auth"])
        code, payload = self.move("awaiting-acceptance")
        self.assertEqual("assurance_incomplete", payload["error"])
        self.assertIn("security", payload["message"])

    def test_waiver_cannot_lower_project_floor(self):
        problems = sdp.validate_record(
            {**sdp.new_record("p", "bug", "Lean", {"profile_floor": "Balanced", "epic_security_policy": "waived", "mandatory_stages": []})})
        self.assertTrue(any("profile floor" in item for item in problems))

    def test_reviewer_detected_trigger_adds_security(self):
        self.start()
        self.repo.edit()
        self.result("developer")
        self.result("reviewer", triggers=["security:input"])
        code, payload = self.repo.cli(self.pkg, "inspect")
        self.assertEqual(0, code)
        self.assertIn("security", payload["required_stages"])

    def test_reviewer_cannot_dispose_trigger(self):
        self.start()
        self.repo.edit()
        self.result("developer")
        self.result("reviewer", triggers=["security:input"])
        args = ["disposition", "--trigger", "security:input", "--disposition", "not_present",
                "--by", "reviewer", "--expected-revision", str(self.repo.revision(self.pkg))]
        code, payload = self.repo.cli(self.pkg, *args)
        self.assertEqual("invalid_disposition", payload["error"])

    def test_accepted_risk_requires_human_reason(self):
        self.start()
        self.repo.edit()
        self.result("developer")
        self.result("reviewer", triggers=["security:input"])
        for by, reason in (("sdp.security", "ok"), (HUMAN, None)):
            args = ["disposition", "--trigger", "security:input", "--disposition", "accepted_risk",
                    "--by", by, "--expected-revision", str(self.repo.revision(self.pkg))]
            if reason:
                args += ["--reason", reason]
            code, payload = self.repo.cli(self.pkg, *args)
            self.assertEqual(1, code, payload)
        args = ["disposition", "--trigger", "security:input", "--disposition", "accepted_risk",
                "--by", HUMAN, "--reason", "internal tool", "--expected-revision", str(self.repo.revision(self.pkg))]
        self.assertEqual(0, self.repo.cli(self.pkg, *args)[0])
        self.assertEqual(0, self.move("awaiting-acceptance")[0])

    def test_security_pass_satisfies_trigger(self):
        self.start()
        self.repo.edit()
        self.result("developer")
        self.result("reviewer", triggers=["security:input"])
        self.assertEqual(0, self.result("security")[0])
        self.assertEqual(0, self.move("awaiting-acceptance")[0])

    def test_compliance_requires_all_specialists(self):
        self.approve(None, "--profile", "Compliance")
        self.move("delivering", caps=CAPS)
        self.repo.edit()
        self.result("developer")
        self.result("reviewer")
        code, payload = self.move("awaiting-acceptance")
        self.assertIn("security", payload["message"])
        self.assertIn("qa", payload["message"])


class CandidateTests(Base):
    def fingerprint(self):
        return sdp.compute_candidate(self.repo.root, sdp.head_revision(self.repo.root), "spec/f/deliveries/f-DP-1")["fingerprint"]

    def test_untracked_file_changes_fingerprint(self):
        before = self.fingerprint()
        self.repo.edit("new\n", "src/new.txt")
        self.assertNotEqual(before, self.fingerprint())

    def test_ignored_untracked_file_is_outside_candidate(self):
        (self.repo.root / ".gitignore").write_text("*.log\n")
        before = self.fingerprint()
        self.repo.edit("noise\n", "debug.log")
        self.assertEqual(before, self.fingerprint())

    def test_tracked_gitignored_file_in_candidate(self):
        (self.repo.root / ".gitignore").write_text("secret.env\n")
        (self.repo.root / "secret.env").write_text("a\n")
        run_git(self.repo.root, "add", "-f", "-A")
        run_git(self.repo.root, "commit", "-q", "-m", "tracked ignored")
        before = self.fingerprint()
        (self.repo.root / "secret.env").write_text("b\n")
        self.assertNotEqual(before, self.fingerprint())

    def test_deleted_file_marker(self):
        before = self.fingerprint()
        (self.repo.root / "src/app.txt").unlink()
        self.assertNotEqual(before, self.fingerprint())

    def test_package_folder_excluded_from_candidate(self):
        before = self.fingerprint()
        (self.repo.root / self.pkg / "HISTORY.md").write_text("note\n")
        (self.repo.root / self.pkg / "PLAN.md").unlink()
        self.assertEqual(before, self.fingerprint())

    def test_candidate_change_invalidates_results(self):
        self.reach_awaiting()
        self.repo.edit("later change\n")
        code, payload = self.repo.cli(self.pkg, "validate")
        self.assertEqual(1, code)
        self.assertIn("stale", payload["message"])
        code, payload = self.move("accepted", decided_by=HUMAN)
        self.assertEqual("evidence_stale", payload["error"])

    def test_filenames_with_unusual_characters(self):
        before = self.fingerprint()
        self.repo.edit("x\n", "src/na me\u00e9.txt")
        self.assertNotEqual(before, self.fingerprint())


class RepairTests(Base):
    def reject_once(self):
        self.repo.edit("attempt\n")
        self.assertEqual(0, self.result("developer")[0])
        code, payload = self.result("reviewer", "fail", findings=["High: wrong output"])
        self.assertEqual(0, code, payload)
        return payload

    def test_blocked_does_not_count_rejection(self):
        self.start()
        self.repo.edit()
        code, payload = self.result("developer", "blocked", findings=["tests cannot run"])
        self.assertEqual("blocked", payload["status"])
        self.assertEqual(0, payload["rejected_candidates"])

    def test_duplicate_failure_counts_once(self):
        self.start()
        payload = self.reject_once()
        self.assertEqual(1, payload["rejected_candidates"])
        again = self.result("reviewer", "fail", findings=["High: wrong output"])
        self.assertEqual(1, again[1]["rejected_candidates"])

    def test_second_rejection_escalates(self):
        self.start()
        self.reject_once()
        self.assertEqual(0, self.move("delivering")[0])
        self.repo.edit("second attempt\n")
        self.assertEqual(0, self.result("developer")[0])
        self.assertEqual(2, self.result("reviewer", "fail", findings=["High: still wrong"])[1]["rejected_candidates"])
        code, payload = self.move("delivering")
        self.assertEqual("escalation_required", payload["error"])
        code, payload = self.move("delivering", human_guided=True, decided_by=HUMAN)
        self.assertEqual(0, code, payload)
        self.assertEqual(1, self.repo.record(self.pkg)["human_corrections"])

    def test_unbounded_repair_returns_to_planned(self):
        self.start()
        self.reject_once()
        code, payload = self.move("planned", reason="requires a new public API")
        self.assertEqual(0, code, payload)
        self.assertIsNone(self.repo.record(self.pkg)["plan"])
        code, payload = self.move("delivering", caps=CAPS)
        self.assertEqual("plan_unapproved", payload["error"])

    def test_fail_requires_findings(self):
        self.start()
        self.repo.edit()
        self.result("developer")
        code, payload = self.result("reviewer", "fail")
        self.assertEqual("invalid_result", payload["error"])

    def test_failed_candidate_cannot_be_repassed_unchanged(self):
        self.start()
        self.reject_once()
        self.assertEqual(0, self.move("delivering")[0])
        code, payload = self.result("reviewer")
        self.assertEqual("candidate_unchanged", payload["error"])
        self.repo.edit("actually repaired\n")
        self.assertEqual(0, self.result("developer")[0])
        self.assertEqual(0, self.result("reviewer")[0])


class AcceptanceAndTransitionTests(Base):
    def test_acceptance_requires_human_decision(self):
        self.reach_awaiting()
        for who in (None, "sdp.qa", "agent"):
            kwargs = {"decided_by": who} if who else {}
            code, payload = self.move("accepted", **kwargs)
            self.assertEqual("human_required", payload["error"], who)
        code, payload = self.move("accepted", decided_by=HUMAN, reason="looks right")
        self.assertEqual(0, code, payload)
        self.assertEqual("accepted", self.repo.record(self.pkg)["delivery_status"])

    def test_terminal_states_are_final(self):
        self.reach_awaiting()
        self.move("accepted", decided_by=HUMAN)
        for target in sdp.STATUSES:
            code, payload = self.move(target)
            self.assertEqual("terminal_state", payload["error"], target)

    def test_all_invalid_transitions_rejected(self):
        plan = sdp.parse_plan("---\nstatus: approved\napproved_by: A\napproved_at: now\n---\nbody\n")
        for current in sdp.STATUSES:
            for target in sdp.STATUSES:
                if target in sdp.ALLOWED[current]:
                    continue
                record = sdp.new_record("p", "bug", "Balanced", {"profile_floor": "Lean", "epic_security_policy": "risk-based", "mandatory_stages": []})
                record["delivery_status"] = current
                with self.assertRaises(sdp.ProtocolError, msg=f"{current}->{target}"):
                    sdp.transition(record, target, {"plan": plan})

    def test_human_acceptance_cannot_be_forged_in_file(self):
        self.reach_awaiting()
        record = self.repo.record(self.pkg)
        record["delivery_status"] = "accepted"
        problems = sdp.validate_record(record)
        self.assertTrue(any("human decision" in item for item in problems))

    def test_pending_audit_survives_transitions(self):
        self.start()
        path = self.repo.root / self.pkg / "DELIVERY-RUN.json"
        record = json.loads(path.read_text())
        record["pending_audit"] = ["epic-1-audit"]
        path.write_text(json.dumps(record))
        self.pass_all()
        self.move("awaiting-acceptance")
        self.assertEqual(["epic-1-audit"], self.repo.record(self.pkg)["pending_audit"])


class SequencingTests(Base):
    def test_sequenced_package_waits_for_prerequisite(self):
        first = self.repo.package("f-DP-1", "stories: [US-1]\n")
        second = self.repo.package("f-DP-2", "sequenced_after: [f-DP-1]\nstories: [US-2]\n")
        self.approve(second)
        code, payload = self.move("delivering", second, caps=CAPS)
        self.assertEqual("prerequisite_open", payload["error"])
        record = {"delivery_status": "accepted"}
        (self.repo.root / first / "DELIVERY-RUN.json").write_text(json.dumps(record))
        code, payload = self.move("delivering", second, caps=CAPS)
        self.assertEqual(0, code, payload)

    def test_story_in_two_open_packages_rejected(self):
        self.repo.package("f-DP-1", "stories: [US-1]\n")
        second = self.repo.package("f-DP-2", "stories: [US-1, US-2]\n")
        self.approve(second)
        code, payload = self.move("delivering", second, caps=CAPS)
        self.assertEqual("story_conflict", payload["error"])


class StorageTests(Base):
    def test_stale_revision_write_refused(self):
        self.start()
        self.repo.edit()
        args = ["result", "--stage", "developer", "--verdict", "pass", "--expected-revision", "0"]
        code, payload = self.repo.cli(self.pkg, *args)
        self.assertEqual(3, code)
        self.assertEqual("stale_revision", payload["error"])

    def test_lock_conflict_reports_distinct_code(self):
        self.start()
        self.repo.edit()
        with sdp.exclusive_lock(self.repo.root / self.pkg / "DELIVERY-RUN.json"):
            code, payload = self.result("developer")
        self.assertEqual(3, code)
        self.assertEqual("lock_held", payload["error"])

    def test_released_lock_after_holder_exit(self):
        self.start()
        record = self.repo.root / self.pkg / "DELIVERY-RUN.json"
        code = ("import importlib.util as u,os,sys;"
                "s=u.spec_from_file_location('sdp',sys.argv[1]);m=u.module_from_spec(s);s.loader.exec_module(m);"
                "l=m.exclusive_lock(sys.argv[2]);l.__enter__();os._exit(0)")
        subprocess.run([sys.executable, "-B", "-c", code, str(SCRIPT), str(record)], check=True)
        self.repo.edit()
        self.assertEqual(0, self.result("developer")[0])

    def test_interrupted_write_leaves_previous_record(self):
        self.start()
        record_path = self.repo.root / self.pkg / "DELIVERY-RUN.json"
        before = record_path.read_text()
        self.repo.edit()
        original = os.replace

        def boom(*_):
            raise OSError("simulated crash")

        os.replace = boom
        try:
            with self.assertRaises(OSError):
                self.result("developer")
        finally:
            os.replace = original
        self.assertEqual(before, record_path.read_text())
        self.assertEqual([], [p.name for p in record_path.parent.glob(".run-*")])

    def test_unknown_schema_version_refused(self):
        record = sdp.new_record("p", "bug", "Lean", {"profile_floor": "Lean", "epic_security_policy": "risk-based", "mandatory_stages": []})
        record["schema_version"] = 99
        self.assertTrue(any("newer" in item for item in sdp.validate_structure(record)))
        record["schema_version"] = 3
        self.assertTrue(any("migrate" in item for item in sdp.validate_structure(record)))

    def test_path_traversal_and_symlink_escape_refused(self):
        code, payload = self.repo.cli("../outside", "validate")
        self.assertEqual(2, code)
        self.assertEqual("path_escape", payload["error"])
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(outside, ignore_errors=True))
        link = self.repo.root / "spec/f/deliveries/link"
        try:
            os.symlink(outside, link, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        code, payload = self.repo.cli("spec/f/deliveries/link", "validate")
        self.assertEqual(2, code)

    def test_oversized_record_refused(self):
        self.start()
        path = self.repo.root / self.pkg / "DELIVERY-RUN.json"
        path.write_text(" " * (sdp.MAX_RECORD_BYTES + 1))
        code, payload = self.repo.cli(self.pkg, "validate")
        self.assertEqual("file_too_large", payload["error"])

    def test_deeply_nested_record_refused(self):
        self.start()
        path = self.repo.root / self.pkg / "DELIVERY-RUN.json"
        path.write_text("[" * 100000)
        code, payload = self.repo.cli(self.pkg, "validate")
        self.assertEqual(1, code)

    def test_file_symlink_refused(self):
        self.start()
        record = self.repo.root / self.pkg / "DELIVERY-RUN.json"
        target = self.repo.root / "elsewhere.json"
        target.write_text(record.read_text())
        record.unlink()
        try:
            os.symlink(target, record)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        code, payload = self.repo.cli(self.pkg, "validate")
        self.assertEqual(2, code)
        self.assertEqual("path_escape", payload["error"])

    def test_agent_identity_heuristic(self):
        for name in ("sdp.qa", "SDP.Security", "ci-bot", "Copilot", "claude", "agent", "orchestrator"):
            self.assertTrue(sdp.is_agent_identity(name), name)
        for name in (HUMAN, "Jan Talbot", "Abbot"):
            self.assertFalse(sdp.is_agent_identity(name), name)

    def test_candidate_evaluated_inside_lock(self):
        self.start()
        self.repo.edit("first\n")
        calls = []
        original = sdp.compute_candidate

        def tracked(*args, **kwargs):
            calls.append(sdp.exclusive_lock_held)
            return original(*args, **kwargs)

        sdp.compute_candidate = tracked
        try:
            self.assertEqual(0, self.result("developer")[0])
        finally:
            sdp.compute_candidate = original
        self.assertTrue(calls and all(calls), calls)

    def test_validator_never_writes_shared_specs(self):
        shared = self.repo.root / "spec/f/PRD.md"
        before = shared.read_bytes()
        self.reach_awaiting()
        self.move("accepted", decided_by=HUMAN)
        self.assertEqual(before, shared.read_bytes())

    def test_record_matches_published_schema(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema is a development-only dependency")
        schema = json.loads(SCHEMA.read_text())
        self.reach_awaiting()
        record = self.repo.record(self.pkg)
        jsonschema.validate(record, schema)
        for mutate in (
            lambda r: r.update(schema_version=3),
            lambda r: r.update(extra=1),
            lambda r: r["acceptance"].update(decision="maybe"),
            lambda r: r["stage_results"][0].update(verdict="great"),
        ):
            broken = copy.deepcopy(record)
            mutate(broken)
            with self.assertRaises(jsonschema.ValidationError):
                jsonschema.validate(broken, schema)
            self.assertTrue(sdp.validate_structure(broken), "validator accepted what the schema rejects")


class EndToEndTests(Base):
    def test_validate_reports_planned_without_record(self):
        code, payload = self.repo.cli(self.pkg, "validate")
        self.assertEqual((0, "planned"), (code, payload["status"]))

    def test_full_delivery_path(self):
        self.reach_awaiting()
        self.assertEqual(0, self.repo.cli(self.pkg, "validate")[0])
        self.assertEqual(0, self.move("accepted", decided_by=HUMAN)[0])


if __name__ == "__main__":
    unittest.main()
