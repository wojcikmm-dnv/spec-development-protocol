"""Tests for the legacy migration tool. Each scenario is built as a legacy project on disk."""

import contextlib
import hashlib
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
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".apm/skills/sdp-migrate/scripts/migrate.py"
spec = importlib.util.spec_from_file_location("sdp_migrate", SCRIPT)
migrate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migrate)
migrate.core = migrate.load_core()
core = migrate.core

PLAN = "---\nstatus: approved\napproved_by: Ada Lovelace\napproved_at: 2026-01-01\n---\n# Plan\n\nBody text.\n"


def have_tag(tag):
    done = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet", f"{tag}^{{commit}}"], capture_output=True)
    return done.returncode == 0


def legacy_record(status="accepted", delivery_id="f-DP-1", audits=(), decided_by="Ada Lovelace", version=3):
    record = {
        "schema_version": version, "run_id": "run-1", "delivery_id": delivery_id, "profile": "Balanced",
        "current_stage": "closed", "completed_stages": ["developer"], "changed_paths": ["src/app.py"],
        "stage_results": [{"stage": "developer", "result": "pass"}], "autonomous_rejection_count": 0,
        "pending_audit": list(audits),
        "acceptance": {"decision": status if status in ("accepted", "rejected") else "pending", "decided_by": decided_by,
                       "decided_at": "2026-01-02T00:00:00Z", "feedback": "ok"},
        "compliance": None,
    }
    if version == 3:
        record.update({"delivery_status": status, "branch": None})
    return record


def tree(root):
    snapshot = {}
    for path in sorted(Path(root).rglob("*")):
        relative = path.relative_to(root).as_posix()
        if relative.startswith(".git/") or relative == ".git" or relative.startswith(".sdp-backup"):
            continue
        snapshot[relative] = None if path.is_dir() else hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


class Project(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        (self.repo / ".git").mkdir(parents=True)

    def write(self, relative, content):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, (dict, list)):
            content = json.dumps(content, indent=2)
        path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
        return path

    def package_054(self, slug="f", package="f-DP-1", status="accepted", audits=(), plan=PLAN, decided_by="Ada Lovelace"):
        base = f"spec/{slug}/deliveries/{package}"
        self.write(f"{base}/PLAN.md", plan)
        self.write(f"{base}/DELIVERY-RUN.json", legacy_record(status, package, audits, decided_by))
        self.write(f"{base}/HISTORY.md", "# History\n\nOriginal entry.\n")
        self.write(f"spec/{slug}/PRD.md", "---\nstatus: approved\n---\nprd\n")
        self.write("spec/ACTIVE.md", f"---\nslug: {slug}\ntitle: Feature\ncurrent_gate: 6\ncurrent_delivery: {package}\n---\n")
        return base

    def project_053(self, slug="f", status="accepted", audits=("epic-audit",), body="Remember: the vendor call is flaky.\n"):
        active = (f"---\nslug: {slug}\ntitle: Feature\ncurrent_gate: 6\ncurrent_delivery: n/a\nfeature_status: in-progress\n"
                  + (f"delivery_status: {status}\n" if status else "") + f"pending_audit: [{', '.join(audits)}]\n---\n{body}")
        self.write("spec/ACTIVE.md", active)
        self.write(f"spec/{slug}/PLAN.md", PLAN)
        self.write(f"spec/{slug}/DELIVERY-RUN.json", legacy_record(status or "accepted", delivery_id="<delivery-id>", version=2))
        self.write(f"spec/{slug}/HISTORY.md", "# History\n\nOld.\n")
        self.write(f"spec/{slug}/PRD.md", "---\nstatus: approved\n---\nprd\n")

    def run_tool(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = migrate.main(["--repo", str(self.repo), *args])
        return code, json.loads(out.getvalue())

    def record(self, relative):
        return json.loads((self.repo / relative).read_text(encoding="utf-8"))


class AcceptedAndOpenPackageTests(Project):
    def test_preview_changes_nothing(self):
        self.package_054()
        before = tree(self.repo)
        code, report = self.run_tool("preview")
        self.assertEqual(0, code, report)
        self.assertEqual("legacy", report["layout"])
        self.assertEqual(before, tree(self.repo))
        self.assertFalse((self.repo / ".sdp-backup").exists())

    def test_accepted_package_keeps_its_human_decision_and_original_record(self):
        base = self.package_054()
        original = (self.repo / base / "DELIVERY-RUN.json").read_bytes()
        code, report = self.run_tool("apply")
        self.assertEqual(0, code, report)
        record = self.record(f"{base}/DELIVERY-RUN.json")
        self.assertEqual(4, record["schema_version"])
        self.assertEqual("accepted", record["delivery_status"])
        self.assertEqual("Ada Lovelace", record["acceptance"]["decided_by"])
        self.assertEqual(3, record["migrated_from"]["schema_version"])
        self.assertEqual(hashlib.sha256(original).hexdigest(), record["migrated_from"]["original_sha256"])
        self.assertEqual(original, (self.repo / base / "DELIVERY-RUN.legacy.json").read_bytes())
        self.assertEqual([], core.validate_record(record))

    def test_open_package_restarts_as_planned_and_its_approval_is_voided(self):
        base = self.package_054(status="delivering", audits=("epic-1-audit",))
        code, report = self.run_tool("apply")
        self.assertEqual(0, code, report)
        record = self.record(f"{base}/DELIVERY-RUN.json")
        self.assertEqual("planned", record["delivery_status"])
        self.assertIsNone(record["plan"])
        self.assertEqual(["epic-1-audit"], record["pending_audit"])
        plan = (self.repo / base / "PLAN.md").read_text()
        self.assertIn("status: draft", plan)
        self.assertIn("approved_by: pending", plan)
        self.assertIn("Body text.", plan)
        history = (self.repo / base / "HISTORY.md").read_text()
        self.assertIn("Original entry.", history)
        self.assertIn("voided", history)
        self.assertIn("Ada Lovelace", history)

    def test_migrated_open_package_waits_for_a_fresh_human_approval(self):
        base = self.package_054(status="awaiting-acceptance")
        self.run_tool("apply")
        done = subprocess.run(
            [sys.executable, "-B", str(ROOT / ".apm/skills/sdp-core/scripts/sdp.py"), "--repo", str(self.repo),
             "--package", base, "--json", "next"], capture_output=True, text=True)
        payload = json.loads(done.stdout)
        self.assertEqual(("await-plan-approval", "human"), (payload["action"], payload["actor"]), payload)

    def test_every_open_status_restarts_as_planned(self):
        for status in ("planned", "delivering", "blocked", "awaiting-acceptance", "changes-requested"):
            with self.subTest(status=status):
                shutil.rmtree(self.repo / "spec", ignore_errors=True)
                base = self.package_054(status=status)
                code, report = self.run_tool("apply")
                self.assertEqual(0, code, report)
                self.assertEqual("planned", self.record(f"{base}/DELIVERY-RUN.json")["delivery_status"])

    def test_rejected_package_stays_rejected(self):
        base = self.package_054(status="rejected")
        code, report = self.run_tool("apply")
        self.assertEqual(0, code, report)
        self.assertEqual("rejected", self.record(f"{base}/DELIVERY-RUN.json")["delivery_status"])

    def test_second_run_is_a_no_op_and_current_layout_is_recognized(self):
        self.package_054()
        self.run_tool("apply")
        after_first = tree(self.repo)
        code, report = self.run_tool("apply")
        self.assertEqual(0, code, report)
        self.assertEqual("current", report["layout"])
        self.assertEqual([], report["operations"])
        self.assertEqual(after_first, tree(self.repo))

    def test_shared_specs_and_unrelated_files_are_untouched(self):
        self.package_054()
        self.write("src/app.py", "print('x')\n")
        self.write(".github/TECH.md", "# mine\n")
        before = tree(self.repo)
        self.run_tool("apply")
        after = tree(self.repo)
        for path in ("spec/f/PRD.md", "src/app.py", ".github/TECH.md"):
            self.assertEqual(before[path], after[path], path)


class FlatLayout053Tests(Project):
    def test_feature_level_package_moves_into_deliveries_and_active_becomes_a_pointer(self):
        self.project_053()
        code, report = self.run_tool("apply")
        self.assertEqual(0, code, report)
        self.assertFalse((self.repo / "spec/f/PLAN.md").exists())
        self.assertFalse((self.repo / "spec/f/DELIVERY-RUN.json").exists())
        target = "spec/f/deliveries/f-DP-1"
        record = self.record(f"{target}/DELIVERY-RUN.json")
        self.assertEqual(("accepted", 2), (record["delivery_status"], record["migrated_from"]["schema_version"]))
        self.assertEqual(["epic-audit"], record["pending_audit"])
        active = (self.repo / "spec/ACTIVE.md").read_text()
        self.assertNotIn("feature_status", active)
        self.assertNotIn("pending_audit", active)
        self.assertIn("current_delivery: f-DP-1", active)
        history = (self.repo / target / "HISTORY.md").read_text()
        self.assertIn("Old.", history)
        self.assertIn("vendor call is flaky", history)
        self.assertTrue((self.repo / target / "DELIVERY-RUN.legacy.json").is_file())

    def test_ambiguous_status_blocks_until_a_human_maps_it(self):
        self.project_053(status=None)
        before = tree(self.repo)
        code, report = self.run_tool("apply")
        self.assertEqual(1, code)
        self.assertTrue(report["ambiguities"])
        self.assertIn("--status-map", report["ambiguities"][0]["message"])
        self.assertEqual(before, tree(self.repo))
        code, report = self.run_tool("apply", "--status-map", "f=accepted")
        self.assertEqual(0, code, report)

    def test_status_map_rejects_unknown_values(self):
        self.project_053(status=None)
        code, report = self.run_tool("apply", "--status-map", "f=done")
        self.assertEqual(2, code)
        self.assertEqual("usage", report["error"])

    def test_not_planned_becomes_planned(self):
        self.project_053(status="not-planned")
        code, report = self.run_tool("apply")
        self.assertEqual(0, code, report)
        self.assertEqual("planned", self.record("spec/f/deliveries/f-DP-1/DELIVERY-RUN.json")["delivery_status"])


class RefusalTests(Project):
    def test_release_before_053_is_unsupported_with_an_upgrade_path(self):
        self.write("spec/ACTIVE.md", "---\nslug: f\ntitle: T\ncurrent_gate: 3\ncurrent_story: US-1\nstatus: in-progress\n---\n")
        before = tree(self.repo)
        code, report = self.run_tool("apply")
        self.assertEqual(1, code)
        self.assertEqual("unsupported_legacy_version", report["blockers"][0]["error"])
        self.assertIn("0.5.3", report["blockers"][0]["message"])
        self.assertEqual(before, tree(self.repo))

    def test_unknown_newer_schema_stops(self):
        base = self.package_054()
        record = legacy_record()
        record["schema_version"] = 9
        self.write(f"{base}/DELIVERY-RUN.json", record)
        before = tree(self.repo)
        code, report = self.run_tool("apply")
        self.assertEqual(1, code)
        self.assertEqual("unknown_newer_schema", report["blockers"][0]["error"])
        self.assertEqual(before, tree(self.repo))

    def test_accepted_without_a_recorded_human_is_never_carried_over(self):
        for who in (None, "TBD", "sdp.orchestrator"):
            with self.subTest(who=who):
                shutil.rmtree(self.repo / "spec", ignore_errors=True)
                base = self.package_054(decided_by=who)
                record = legacy_record(decided_by=who)
                self.write(f"{base}/DELIVERY-RUN.json", record)
                before = tree(self.repo)
                code, report = self.run_tool("apply")
                self.assertEqual(1, code, report)
                self.assertIn("without a recorded human decision", report["ambiguities"][0]["message"])
                self.assertEqual(before, tree(self.repo))

    def test_unreadable_record_blocks(self):
        base = self.package_054()
        self.write(f"{base}/DELIVERY-RUN.json", "{not json")
        code, report = self.run_tool("apply")
        self.assertEqual(1, code)
        self.assertEqual("record_unreadable", report["blockers"][0]["error"])

    def test_existing_legacy_evidence_is_never_overwritten(self):
        base = self.package_054()
        self.write(f"{base}/DELIVERY-RUN.legacy.json", "precious")
        before = tree(self.repo)
        code, report = self.run_tool("apply")
        self.assertEqual(1, code)
        self.assertEqual(before, tree(self.repo))
        self.assertEqual("precious", (self.repo / base / "DELIVERY-RUN.legacy.json").read_text())

    def test_linked_feature_folder_is_refused(self):
        outside = Path(self.tmp.name) / "outside"
        (outside / "deliveries/p").mkdir(parents=True)
        (outside / "deliveries/p/PLAN.md").write_text(PLAN)
        (self.repo / "spec").mkdir()
        try:
            os.symlink(outside, self.repo / "spec/f", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        code, report = self.run_tool("apply")
        self.assertEqual(1, code)
        self.assertEqual("path_escape", report["blockers"][0]["error"])
        self.assertEqual([(outside / "deliveries/p/PLAN.md").name], [p.name for p in (outside / "deliveries/p").iterdir()])

    def test_missing_repository_is_a_usage_error(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = migrate.main(["--repo", str(Path(self.tmp.name) / "nope"), "preview"])
        self.assertEqual(2, code)


class AtomicityAndRecoveryTests(Project):
    def test_failure_in_the_middle_restores_everything(self):
        self.package_054(status="delivering")
        self.write("spec/ACTIVE.md", "---\nslug: f\ntitle: T\ncurrent_gate: 6\ncurrent_delivery: f-DP-1\nfeature_status: in-progress\n---\nnotes\n")
        before = tree(self.repo)
        original = os.replace
        calls = {"count": 0}

        def failing(source, destination):
            calls["count"] += 1
            if calls["count"] == 3:
                raise OSError("simulated disk failure")
            return original(source, destination)

        with mock.patch.object(os, "replace", failing):
            code, report = self.run_tool("apply")
        self.assertEqual(3, code)
        self.assertIn("everything was restored", report["message"])
        self.assertEqual(before, tree(self.repo))

    def test_validation_failure_restores_everything(self):
        self.package_054()
        before = tree(self.repo)
        with mock.patch.object(migrate, "verify_records", return_value=["forced problem"]):
            code, report = self.run_tool("apply")
        self.assertEqual(1, code)
        self.assertEqual("validation_failed", report["error"])
        self.assertEqual(before, tree(self.repo))

    def test_restore_returns_the_exact_original_tree(self):
        self.package_054(status="delivering")
        before = tree(self.repo)
        code, report = self.run_tool("apply")
        self.assertNotEqual(before, tree(self.repo))
        code, restored = self.run_tool("restore", "--backup", report["backup"])
        self.assertEqual(0, code, restored)
        self.assertEqual(before, tree(self.repo))

    def test_restore_leaves_files_changed_after_migration_alone(self):
        base = self.package_054()
        code, report = self.run_tool("apply")
        edited = self.repo / base / "DELIVERY-RUN.json"
        edited.write_text(edited.read_text() + "\n")
        code, restored = self.run_tool("restore", "--backup", report["backup"])
        self.assertEqual(3, code)
        self.assertEqual("restore_conflict", restored["error"])
        self.assertIn("DELIVERY-RUN.json", restored["message"])

    def test_interrupted_migration_is_detected_and_blocks_a_new_apply(self):
        self.package_054()
        folder = self.repo / ".sdp-backup/20260101T000000000000Z"
        folder.mkdir(parents=True)
        (folder / "journal.json").write_text(json.dumps({"complete": False, "restored": False, "operations": [], "created_dirs": []}))
        code, status = self.run_tool("status")
        self.assertEqual(1, len(status["incomplete"]))
        code, report = self.run_tool("apply")
        self.assertEqual(3, code)
        self.assertEqual("incomplete_migration", report["error"])
        code, restored = self.run_tool("restore", "--backup", status["incomplete"][0])
        self.assertEqual(0, code, restored)
        code, report = self.run_tool("apply")
        self.assertEqual(0, code, report)

    def test_restore_rejects_paths_outside_the_backup_area(self):
        for bad in ("../outside", "spec", "."):
            code, report = self.run_tool("restore", "--backup", bad)
            self.assertNotEqual(0, code, bad)

    def test_keyboard_interrupt_during_apply_restores(self):
        self.package_054(status="delivering")
        before = tree(self.repo)
        original = os.replace

        def interrupted(source, destination):
            raise KeyboardInterrupt()

        with mock.patch.object(os, "replace", interrupted):
            with self.assertRaises(KeyboardInterrupt):
                self.run_tool("apply")
        self.assertEqual(before, tree(self.repo))


class MalformedAndAmbiguousInputTests(Project):
    def assert_refused(self, *args, error=None):
        before = tree(self.repo)
        code, report = self.run_tool(*args)
        self.assertEqual(1, code, report)
        self.assertEqual(before, tree(self.repo))
        if error:
            self.assertEqual(error, (report.get("blockers") or [{}])[0].get("error") or report.get("error"), report)
        return report

    def set_record(self, base, **changes):
        path = self.repo / base / "DELIVERY-RUN.json"
        record = json.loads(path.read_text())
        record.update(changes)
        path.write_text(json.dumps(record))

    def test_nested_package_is_identified_by_its_folder_not_by_a_record_field(self):
        base = self.package_054()
        self.set_record(base, delivery_id="other-DP-9")
        code, report = self.run_tool("apply")
        self.assertEqual(0, code, report)
        self.assertEqual("f-DP-1", self.record(f"{base}/DELIVERY-RUN.json")["delivery_id"])
        self.assertFalse((self.repo / "spec/f/deliveries/other-DP-9").exists())

    def test_packages_with_the_same_record_id_do_not_overwrite_each_other(self):
        first = self.package_054(package="f-DP-1")
        second = self.package_054(package="f-DP-2")
        self.set_record(first, delivery_id="f-DP-1", run_id="run-first")
        self.set_record(second, delivery_id="f-DP-1", run_id="run-second")
        code, report = self.run_tool("apply")
        self.assertEqual(0, code, report)
        self.assertEqual("run-first", json.loads((self.repo / first / "DELIVERY-RUN.legacy.json").read_text())["run_id"])
        self.assertEqual("run-second", json.loads((self.repo / second / "DELIVERY-RUN.legacy.json").read_text())["run_id"])

    def test_pending_audit_of_the_wrong_type_is_refused_without_a_traceback(self):
        for value in (5, True, "abc", {"a": 1}, [1, 2]):
            with self.subTest(value=value):
                shutil.rmtree(self.repo / "spec", ignore_errors=True)
                base = self.package_054()
                self.set_record(base, pending_audit=value)
                report = self.assert_refused("apply")
                self.assertIn("pending_audit", report["ambiguities"][0]["message"])

    def test_plan_status_of_the_wrong_type_is_refused_without_a_traceback(self):
        self.package_054(status="delivering", plan="---\nstatus: [a]\napproved_by: x\napproved_at: y\n---\nbody\n")
        self.assert_refused("apply")

    def test_rejected_without_a_recorded_decision_is_not_carried_over(self):
        base = self.package_054(status="rejected")
        self.set_record(base, acceptance={"decision": "pending", "decided_by": "Ada Lovelace", "decided_at": "2026-01-02T00:00:00Z"})
        report = self.assert_refused("apply")
        self.assertIn("rejected without a recorded human decision", report["ambiguities"][0]["message"])

    def test_status_map_cannot_invent_a_human_decision(self):
        self.package_054(status="delivering")
        report = self.assert_refused("apply", "--status-map", "f-DP-1=rejected")
        self.assertIn("without a recorded human decision", report["ambiguities"][0]["message"])

    def test_unknown_status_map_target_is_reported(self):
        self.package_054()
        report = self.assert_refused("apply", "--status-map", "typo-DP-9=accepted")
        self.assertEqual("unknown_status_map_target", report["blockers"][0]["error"])

    def test_active_notes_without_a_package_to_hold_them_stop_the_migration(self):
        self.package_054()
        self.write("spec/ACTIVE.md", "---\nslug: ghost\ntitle: T\ncurrent_gate: 6\ncurrent_delivery: n/a\nfeature_status: in-progress\n"
                                      "pending_audit: [a-1]\n---\nkeep this note\n")
        report = self.assert_refused("apply")
        self.assertIn("pending_audit or notes", report["ambiguities"][0]["message"])

    def test_text_that_is_not_utf8_is_never_rewritten_lossily(self):
        base = self.package_054()
        (self.repo / base / "HISTORY.md").write_bytes(b"# History\n\ncaf\xe9\n")
        self.assert_refused("apply", error="not_utf8")

    def test_restore_accepts_dotted_backup_paths(self):
        self.package_054(status="delivering")
        before = tree(self.repo)
        code, report = self.run_tool("apply")
        code, restored = self.run_tool("restore", "--backup", "./" + report["backup"] + "/")
        self.assertEqual(0, code, restored)
        self.assertEqual(before, tree(self.repo))

    def test_backup_area_that_leaves_the_repository_is_refused(self):
        self.package_054()
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        try:
            os.symlink(outside, self.repo / ".sdp-backup", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        before = tree(self.repo)
        code, report = self.run_tool("apply")
        self.assertEqual(3, code, report)
        self.assertEqual([], list(outside.iterdir()))
        self.assertEqual(before, tree(self.repo))


@unittest.skipUnless(have_tag("v0.5.4"), "release tag v0.5.4 is not available in this checkout")
class CopiedFileTests(Project):
    def install_054(self):
        names = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", "-z", "v0.5.4", "--", ".apm"],
                               capture_output=True).stdout.decode().split("\0")
        for name in filter(None, names):
            data = subprocess.run(["git", "-C", str(ROOT), "show", f"v0.5.4:{name}"], capture_output=True).stdout
            self.write(".github/" + name[len(".apm/"):], data)
        self.write(".github/sdp-version", "v0.5.4\n")
        self.write(".github/TECH.md", "# project policy\n")

    def test_manifest_covers_every_file_of_the_released_installation(self):
        self.install_054()
        manifest = json.loads(migrate.MANIFEST_PATH.read_text())
        owned = set(migrate.classify_legacy_files(self.repo, manifest)[0]["owned"])
        self.assertIn(".github/agents/sdp.developer.agent.md", owned)
        self.assertIn(".github/sdp-version", owned)
        self.assertNotIn(".github/TECH.md", owned)

    def test_preview_never_plans_removals_without_the_explicit_flags(self):
        self.install_054()
        code, report = self.run_tool("preview")
        self.assertEqual(0, code, report)
        self.assertFalse(any(op["op"] in ("remove", "rmdir_if_empty") for op in report["operations"]))

    def test_removal_needs_confirmation_that_the_package_is_installed(self):
        self.install_054()
        code, report = self.run_tool("apply", "--remove-legacy-files")
        self.assertEqual(1, code)
        self.assertEqual("confirmation_required", report["blockers"][0]["error"])
        self.assertTrue((self.repo / ".github/agents/sdp.developer.agent.md").exists())

    def test_verified_copies_move_to_the_backup_and_customized_ones_stay(self):
        self.install_054()
        custom = self.repo / ".github/agents/sdp.developer.agent.md"
        custom.write_text(custom.read_text() + "\n# my team's rule\n")
        pristine = self.repo / ".github/agents/sdp.reviewer.agent.md"
        before = pristine.read_bytes()
        code, report = self.run_tool("apply", "--remove-legacy-files", "--confirm-replacement-installed")
        self.assertEqual(0, code, report)
        self.assertTrue(custom.exists())
        self.assertFalse(pristine.exists())
        self.assertTrue((self.repo / ".github/TECH.md").exists())
        self.assertIn(".github/agents/sdp.developer.agent.md", report["legacy_files"]["customized"])
        backed_up = self.repo / report["backup"] / "files/.github/agents/sdp.reviewer.agent.md"
        self.assertEqual(before, backed_up.read_bytes())
        code, restored = self.run_tool("restore", "--backup", report["backup"])
        self.assertEqual(0, code, restored)
        self.assertEqual(before, pristine.read_bytes())

    def test_line_ending_conversion_does_not_make_a_file_look_customized(self):
        self.install_054()
        target = self.repo / ".github/agents/sdp.reviewer.agent.md"
        target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
        code, report = self.run_tool("preview", "--remove-legacy-files", "--confirm-replacement-installed")
        self.assertEqual(0, code, report)
        self.assertIn(".github/agents/sdp.reviewer.agent.md", report["legacy_files"]["owned"])

    def test_apm_managed_files_are_never_removed(self):
        self.install_054()
        self.write("apm.lock.yaml", "deployed_files:\n  - .github/agents/sdp.reviewer.agent.md\n")
        code, report = self.run_tool("apply", "--remove-legacy-files", "--confirm-replacement-installed")
        self.assertEqual(0, code, report)
        self.assertTrue((self.repo / ".github/agents/sdp.reviewer.agent.md").exists())
        self.assertIn(".github/agents/sdp.reviewer.agent.md", report["legacy_files"]["apm_managed"])

    def test_without_the_installer_marker_nothing_is_removed(self):
        self.install_054()
        (self.repo / ".github/sdp-version").unlink()
        code, report = self.run_tool("apply", "--remove-legacy-files", "--confirm-replacement-installed")
        self.assertEqual(1, code)
        self.assertEqual("no_installer_marker", report["blockers"][0]["error"])
        self.assertTrue((self.repo / ".github/agents/sdp.reviewer.agent.md").exists())

    def test_never_deletes_the_project_policy_file_or_unrelated_github_content(self):
        self.install_054()
        self.write(".github/workflows/ci.yml", "name: ci\n")
        self.run_tool("apply", "--remove-legacy-files", "--confirm-replacement-installed")
        self.assertEqual("# project policy\n", (self.repo / ".github/TECH.md").read_text())
        self.assertEqual("name: ci\n", (self.repo / ".github/workflows/ci.yml").read_text())

    def test_empty_directories_left_by_removal_are_cleaned_but_populated_ones_stay(self):
        self.install_054()
        self.write(".github/agents/my-own.agent.md", "mine")
        self.run_tool("apply", "--remove-legacy-files", "--confirm-replacement-installed")
        self.assertTrue((self.repo / ".github/agents/my-own.agent.md").exists())
        self.assertFalse((self.repo / ".github/prompts").exists())


if __name__ == "__main__":
    unittest.main()
