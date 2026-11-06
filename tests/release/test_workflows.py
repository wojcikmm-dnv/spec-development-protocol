import re
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # PyYAML is a maintainer-side dependency
    yaml = None

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
PINNED = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")


def load(name):
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def triggers(workflow):
    return workflow.get("on", workflow.get(True))  # YAML 1.1 reads a bare `on` key as True


def steps(workflow):
    for job_name, job in workflow["jobs"].items():
        for step in job.get("steps", []):
            yield job_name, step


@unittest.skipIf(yaml is None, "PyYAML is not installed")
class WorkflowSafetyTests(unittest.TestCase):
    names = ("ci.yml", "release.yml")

    def test_every_action_is_pinned_to_a_full_commit(self):
        for name in self.names:
            for job, step in steps(load(name)):
                if "uses" in step:
                    self.assertRegex(step["uses"], PINNED, f"{name}:{job}")

    def test_workflows_start_with_no_permissions_and_jobs_ask_for_what_they_need(self):
        for name in self.names:
            workflow = load(name)
            self.assertEqual({}, workflow["permissions"], name)
            for job_name, job in workflow["jobs"].items():
                self.assertIn("permissions", job, f"{name}:{job_name}")

    def test_only_the_publish_job_can_write(self):
        for name in self.names:
            for job_name, job in load(name)["jobs"].items():
                writes = [scope for scope, level in job["permissions"].items() if level != "read"]
                if (name, job_name) == ("release.yml", "publish"):
                    self.assertEqual(["contents"], writes)
                else:
                    self.assertEqual([], writes, f"{name}:{job_name}")

    def test_checkouts_do_not_persist_credentials(self):
        for name in self.names:
            for job, step in steps(load(name)):
                if step.get("uses", "").startswith("actions/checkout@"):
                    self.assertIs(False, step["with"]["persist-credentials"], f"{name}:{job}")

    def test_untrusted_context_is_never_interpolated_into_shell_commands(self):
        for name in self.names:
            for job, step in steps(load(name)):
                self.assertNotIn("${{", step.get("run", ""), f"{name}:{job}: pass values through env instead")

    def test_no_privileged_event_triggers(self):
        for name in self.names:
            events = triggers(load(name))
            for dangerous in ("pull_request_target", "workflow_run", "issue_comment", "workflow_dispatch"):
                self.assertNotIn(dangerous, events, name)

    def test_ci_runs_on_pull_requests_and_main(self):
        events = triggers(load("ci.yml"))
        self.assertIn("pull_request", events)
        self.assertEqual(["main"], events["push"]["branches"])

    def test_the_release_runs_only_for_version_tags_and_never_cancels_a_run_in_progress(self):
        workflow = load("release.yml")
        self.assertEqual({"push": {"tags": ["v*"]}}, triggers(workflow))
        self.assertIs(False, workflow["concurrency"]["cancel-in-progress"])
        self.assertIn("github.ref_name", workflow["concurrency"]["group"])

    def test_rerunning_all_jobs_can_replace_the_artifact_of_the_same_run(self):
        uploads = [step for _, step in steps(load("release.yml")) if step.get("uses", "").startswith("actions/upload-artifact@")]
        self.assertTrue(uploads)
        self.assertTrue(all(step["with"].get("overwrite") is True for step in uploads))

    def test_ci_only_cancels_superseded_pull_request_runs(self):
        value = load("ci.yml")["concurrency"]["cancel-in-progress"]
        self.assertIn("pull_request", str(value))
        self.assertIn("event_name", str(value))

    def test_publishing_waits_for_the_build_and_uses_its_artifact(self):
        jobs = load("release.yml")["jobs"]
        self.assertEqual("build", jobs["publish"]["needs"])
        self.assertNotIn("needs", jobs["build"])
        uses = [step["uses"].split("@")[0] for step in jobs["publish"]["steps"] if "uses" in step]
        self.assertIn("actions/download-artifact", uses)
        built = [step["uses"].split("@")[0] for step in jobs["build"]["steps"] if "uses" in step]
        self.assertIn("actions/upload-artifact", built)

    def test_the_build_validates_before_it_builds_and_refuses_untagged_main_history(self):
        text = "\n".join(step.get("run", "") for _, step in steps(load("release.yml")))
        order = [text.index(marker) for marker in ("merge-base --is-ancestor", "changelog.py --tag", "scripts/check-all.sh", "build-release.py")]
        self.assertEqual(sorted(order), order)
        self.assertIn('--tag "${TAG}" --revision "${GITHUB_SHA}"', text)

    def test_the_publish_job_receives_the_exact_commit_and_a_scoped_token(self):
        publish = load("release.yml")["jobs"]["publish"]
        run_step = next(step for step in publish["steps"] if "publish-release.py" in step.get("run", ""))
        self.assertIn('--revision "${GITHUB_SHA}"', run_step["run"])
        self.assertEqual("${{ secrets.GITHUB_TOKEN }}", run_step["env"]["GITHUB_TOKEN"])
        build = load("release.yml")["jobs"]["build"]
        self.assertFalse(any("GITHUB_TOKEN" in str(step.get("env", {})) for step in build["steps"]))

    def test_tool_pins_come_from_one_file(self):
        for name in self.names:
            text = (WORKFLOWS / name).read_text(encoding="utf-8")
            self.assertIn("scripts/release-tools.json", text, name)
            self.assertNotRegex(text, r"apm-cli==\d", name)


class CheckCoverageTests(unittest.TestCase):
    def suites(self):
        return sorted({p.parent.name for p in (ROOT / "tests").glob("*/test_*.py")})

    def test_the_shared_check_script_fails_if_the_checks_change_the_working_tree(self):
        text = (ROOT / "scripts" / "check-all.sh").read_text(encoding="utf-8")
        self.assertIn('if [ -n "$(git status --porcelain --untracked-files=all)" ]; then', text)
        self.assertRegex(text, r"changed the working tree[\s\S]*exit 1")

    def test_the_shared_check_script_runs_every_test_suite(self):
        text = (ROOT / "scripts" / "check-all.sh").read_text(encoding="utf-8")
        loop = re.search(r"run-suites\.py ([\w ]+)", text).group(1).split()
        self.assertEqual(self.suites(), sorted(loop))

    @unittest.skipIf(yaml is None, "PyYAML is not installed")
    def test_the_windows_job_runs_every_test_suite(self):
        runs = "\n".join(step.get("run", "") for job, step in steps(load("ci.yml")) if job == "windows")
        loop = re.search(r"run-suites\.py ([\w ]+)", runs).group(1).split()
        self.assertEqual(self.suites(), sorted(loop))

    def test_the_python39_job_runs_the_suites_for_shipped_scripts_without_third_party_packages(self):
        text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
        job = text[text.index("python39:"):]
        self.assertIn('python-version: "3.9"', job)
        self.assertNotIn("pip install", job)
        self.assertIn("run-suites.py contracts init migrate\n", job + "\n")

    def test_shell_scripts_keep_unix_line_endings_on_every_checkout(self):
        self.assertIn("*.sh text eol=lf", (ROOT / ".gitattributes").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
