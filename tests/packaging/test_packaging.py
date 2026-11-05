"""Packaging checks for the release ZIP (standard library only).

Pure checks run everywhere. Tests that build a real bundle need the APM version pinned in
scripts/release-tools.json and skip with a reason when it is not installed.
"""

import importlib.util
import contextlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("build_release", ROOT / "scripts" / "build-release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def copy_ignore(directory, names):
    """Skip repository-level folders that are not package sources, and bytecode caches anywhere."""
    skipped = {name for name in names if name == "__pycache__"}
    if Path(directory) == ROOT:
        skipped |= {name for name in names if name in (".git", "build", "dist", "spec", "tests", "node_modules", ".sdp-backup")}
    return skipped


def apm_available():
    try:
        release.check_apm_version(ROOT)
        return True
    except (release.BuildError, OSError):
        return False


NEEDS_APM = (lambda cls: cls) if os.environ.get("SDP_REQUIRE_APM") else unittest.skipUnless(
    apm_available(), "the apm version pinned in scripts/release-tools.json is not installed (set SDP_REQUIRE_APM=1 to fail instead)")


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def make_root(base, version="1.2.3"):
    """A minimal fake repository with every manifest the consistency check reads."""
    manifest = json.dumps({"name": "demo", "version": version})
    write(base / "apm.yml", f"name: demo\nversion: {version}\n")
    for relative in ("plugin.json", ".github/plugin/plugin.json", ".claude-plugin/plugin.json"):
        write(base / relative, manifest)
    write(base / ".claude-plugin/marketplace.json", json.dumps({"plugins": [{"name": "demo", "version": f"^{version}"}]}))
    write(base / "scripts/release-tools.json", json.dumps({"apm": "0.29.0"}))
    write(base / ".apm/agents/a.agent.md", "agent\n")
    write(base / ".apm/instructions/i.instructions.md", "instructions\n")
    write(base / ".apm/prompts/p.prompt.md", "prompt\n")
    write(base / ".apm/skills/s/SKILL.md", "skill\n")
    write(base / ".apm/skills/s/scripts/.hidden", "hidden\n")
    write(base / "LICENSE", "MIT\n")
    return base


def make_zip(path, root, mutate=None, version="1.2.3"):
    folder = f"demo-{version}"
    entries = {f"{folder}/{name}": (root / ".apm" / name).read_bytes() for name in
               ("agents/a.agent.md", "instructions/i.instructions.md", "skills/s/SKILL.md", "skills/s/scripts/.hidden")}
    entries[f"{folder}/commands/p.md"] = (root / ".apm/prompts/p.prompt.md").read_bytes()
    entries[f"{folder}/plugin.json"] = json.dumps({"name": "demo", "version": version}).encode()
    entries[f"{folder}/LICENSE"] = b"MIT\n"
    entries[f"{folder}/SETUP.md"] = b"setup\n"
    if mutate:
        mutate(entries)
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in entries.items():
            info = zipfile.ZipInfo("placeholder", (2026, 1, 1, 0, 0, 0))
            info.filename = name  # bypass the separator normalization of ZipInfo so hostile names survive
            archive.writestr(info, data)
    return path


class ConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = make_root(Path(self.tmp.name))

    def test_this_repository_is_consistent(self):
        self.assertEqual([], release.consistency_problems(ROOT))

    def test_a_consistent_tree_passes(self):
        self.assertEqual([], release.consistency_problems(self.root))

    def test_each_manifest_must_match_apm_yml(self):
        for relative in ("plugin.json", ".github/plugin/plugin.json", ".claude-plugin/plugin.json"):
            with self.subTest(relative=relative):
                root = make_root(Path(self.tmp.name) / ("case-" + relative.replace("/", "_")))
                write(root / relative, json.dumps({"name": "demo", "version": "9.9.9"}))
                self.assertTrue(any(relative in p for p in release.consistency_problems(root)))

    def test_marketplace_version_must_match(self):
        write(self.root / ".claude-plugin/marketplace.json", json.dumps({"plugins": [{"version": "^0.0.1"}]}))
        self.assertTrue(any("marketplace" in p for p in release.consistency_problems(self.root)))

    def test_a_missing_manifest_is_reported(self):
        (self.root / ".github/plugin/plugin.json").unlink()
        self.assertTrue(any("missing" in p for p in release.consistency_problems(self.root)))

    def test_versions_must_be_strict_semantic_versions(self):
        for bad in ("1.2", "v1.2.3", "01.2.3", "1.2.3.4", "latest"):
            with self.subTest(version=bad):
                root = make_root(Path(self.tmp.name) / ("v" + bad.replace(".", "_")), version=bad)
                self.assertTrue(any("semantic version" in p for p in release.consistency_problems(root)), bad)
        for good in ("1.2.3", "2.0.0-rc.1", "2.0.0+build.5"):
            with self.subTest(version=good):
                root = make_root(Path(self.tmp.name) / ("g" + good.replace(".", "_")), version=good)
                self.assertEqual([], release.consistency_problems(root))

    def test_the_apm_tool_must_be_pinned_exactly(self):
        for bad in ("latest", "0.29", ">=0.29.0", ""):
            with self.subTest(pin=bad):
                write(self.root / "scripts/release-tools.json", json.dumps({"apm": bad}))
                self.assertTrue(any("pin an exact apm" in p for p in release.consistency_problems(self.root)))


class VerifyBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = make_root(Path(self.tmp.name) / "src")
        self.zip = Path(self.tmp.name) / "bundle.zip"

    def problems(self, mutate=None):
        make_zip(self.zip, self.root, mutate)
        return release.verify_bundle(self.zip, self.root)

    def test_a_complete_bundle_is_accepted(self):
        self.assertEqual([], self.problems())

    def test_every_missing_resource_is_reported(self):
        for name in ("agents/a.agent.md", "instructions/i.instructions.md", "commands/p.md", "skills/s/SKILL.md",
                     "plugin.json", "LICENSE", "SETUP.md"):
            with self.subTest(name=name):
                problems = self.problems(lambda e, n=name: e.pop(f"demo-1.2.3/{n}"))
                self.assertTrue(any(name in p for p in problems), problems)

    def test_hidden_files_must_be_preserved(self):
        problems = self.problems(lambda e: e.pop("demo-1.2.3/skills/s/scripts/.hidden"))
        self.assertTrue(any(".hidden" in p for p in problems), problems)

    def test_bytecode_caches_are_rejected(self):
        for name in ("skills/s/scripts/__pycache__/x.cpython-311.pyc", "skills/s/scripts/__pycache__/note.txt", "skills/s/scripts/x.pyc"):
            with self.subTest(name=name):
                problems = self.problems(lambda e, n=name: e.update({f"demo-1.2.3/{n}": b"junk"}))
                self.assertTrue(any("excluded artifact" in p for p in problems), problems)

    def test_unsafe_entry_names_are_rejected(self):
        for name in ("../escape.txt", "demo-1.2.3/../escape.txt", "/abs.txt", "C:/abs.txt", "demo-1.2.3\\..\\escape.txt",
                     "demo-1.2.3/agents/a.agent.md/.", "demo-1.2.3/./agents/a.agent.md", "demo-1.2.3/agents/a.agent.md:evil",
                     "demo-1.2.3/agents/trailing."):
            with self.subTest(name=name):
                problems = self.problems(lambda e, n=name: e.update({n: b"x"}))
                self.assertTrue(any("unsafe entry" in p for p in problems), problems)

    def test_entries_outside_the_bundle_folder_are_rejected(self):
        problems = self.problems(lambda e: e.update({"other/file.txt": b"x"}))
        self.assertTrue(any("outside" in p for p in problems), problems)

    def test_symbolic_link_entries_are_rejected(self):
        make_zip(self.zip, self.root)
        with zipfile.ZipFile(self.zip, "a") as archive:
            info = zipfile.ZipInfo("demo-1.2.3/link")
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, "../../etc/passwd")
        self.assertTrue(any("symbolic link" in p for p in release.verify_bundle(self.zip, self.root)))

    def test_wrong_plugin_version_is_rejected(self):
        problems = self.problems(lambda e: e.update({"demo-1.2.3/plugin.json": json.dumps({"version": "9.9.9"}).encode()}))
        self.assertTrue(any("plugin.json has version" in p for p in problems), problems)

    def test_changed_content_is_detected(self):
        problems = self.problems(lambda e: e.update({"demo-1.2.3/agents/a.agent.md": b"tampered\n"}))
        self.assertTrue(any("content differs" in p for p in problems), problems)

    def test_duplicate_entries_are_detected(self):
        make_zip(self.zip, self.root)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with zipfile.ZipFile(self.zip, "a") as archive:
                archive.writestr("demo-1.2.3/agents/a.agent.md", "agent\n")
        self.assertTrue(any("duplicate" in p for p in release.verify_bundle(self.zip, self.root)))

    def test_case_colliding_entries_are_detected(self):
        problems = self.problems(lambda e: e.update({"demo-1.2.3/Agents/A.agent.md": b"x"}))
        self.assertTrue(any("case-colliding" in p for p in problems), problems)

    def test_files_that_do_not_come_from_the_source_are_rejected(self):
        for name in ("skills/s/.env", "agents/evil.sh", "extra.txt"):
            with self.subTest(name=name):
                problems = self.problems(lambda e, n=name: e.update({f"demo-1.2.3/{n}": b"x"}))
                self.assertTrue(any("unexpected file" in p for p in problems), problems)

    def test_line_endings_do_not_change_what_counts_as_identical(self):
        (self.root / ".apm/agents/a.agent.md").write_bytes(b"line one\r\nline two\r\n")
        self.assertEqual([], self.problems(lambda e: e.update({"demo-1.2.3/agents/a.agent.md": b"line one\nline two\n"})))
        problems = self.problems(lambda e: e.update({"demo-1.2.3/agents/a.agent.md": b"line one\r\nline two\r\n"}))
        self.assertTrue(any("content differs" in p for p in problems), problems)

    def test_binary_data_is_never_rewritten(self):
        self.assertEqual(b"a\nb", release.normalize(b"a\r\nb"))
        self.assertEqual(b"a\0\r\n", release.normalize(b"a\0\r\n"))


class BuilderBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def test_apm_version_pin_must_match_exactly(self):
        for output, accepted in (("Agent Package Manager (APM) CLI version 0.29.0\n", True), ("0.29.0", True),
                                 ("version 10.29.0", False), ("apm 0.29.0-evil", False), ("0.29.01", False), ("0.29.0.1", False),
                                 ("", False)):
            with self.subTest(output=output), mock.patch.object(release, "run_apm", return_value=output):
                if accepted:
                    self.assertEqual("0.29.0", release.check_apm_version(ROOT))
                else:
                    with self.assertRaises(release.BuildError):
                        release.check_apm_version(ROOT)

    def test_version_is_read_only_from_the_top_level_key(self):
        for text, expected in (("version: 1.2.3\n", "1.2.3"), ('version: "1.2.3"\n', "1.2.3"), ("version: '1.2.3' # note\n", "1.2.3"),
                               ("version: 1.2.3\r\n", "1.2.3"), ("name: x\nnested:\n  version: 9.9.9\nversion: 1.2.3\n", "1.2.3")):
            with self.subTest(text=text):
                (self.base / "apm.yml").write_bytes(text.encode())
                self.assertEqual(expected, release.manifest_version(self.base))
        for text in ("name: x\nnested:\n  version: 9.9.9\n", "# version: 1.2.3\n", "version:\nname: x\n"):
            with self.subTest(text=text):
                (self.base / "apm.yml").write_bytes(text.encode())
                try:
                    value = release.manifest_version(self.base)
                except release.BuildError:
                    continue
                self.assertFalse(release.SEMVER.match(value), value)

    def test_manifest_name_must_match_apm_yml(self):
        root = make_root(self.base / "named")
        write(root / "plugin.json", json.dumps({"name": "other", "version": "1.2.3"}))
        self.assertTrue(any("name" in p for p in release.consistency_problems(root)))

    def test_check_reports_a_broken_tree_without_a_traceback(self):
        for error in (ValueError("bad json"), KeyError("apm"), AttributeError("list"), OSError("missing")):
            with self.subTest(error=type(error).__name__):
                err = io.StringIO()
                with mock.patch.object(release, "consistency_problems", side_effect=error), contextlib.redirect_stderr(err):
                    self.assertEqual(1, release.main(["--check"]))
                self.assertIn("FAIL", err.getvalue())
                self.assertNotIn("Traceback", err.getvalue())

    def test_check_prints_nothing_on_stdout_when_it_fails(self):
        out = io.StringIO()
        with mock.patch.object(release, "consistency_problems", return_value=["x"]), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(1, release.main(["--check"]))
        self.assertEqual("", out.getvalue())

    def test_malformed_manifests_are_reported_not_raised_as_tracebacks_by_main(self):
        root = make_root(self.base / "broken")
        write(root / ".github/plugin/plugin.json", "[]")
        with self.assertRaises(release.BuildError):
            release.consistency_problems(root)


@unittest.skipUnless(os.environ.get("SDP_REQUIRE_APM") or apm_available(), "apm is not installed")
class BuildFailureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "dist"

    def test_failed_verification_leaves_no_output(self):
        with mock.patch.object(release, "verify_bundle", return_value=["forced"]):
            with self.assertRaises(release.BuildError):
                release.build(self.out, ROOT)
        self.assertFalse(self.out.exists())

    def test_an_existing_output_folder_gets_no_partial_files_when_verification_fails(self):
        self.out.mkdir()
        with mock.patch.object(release, "verify_bundle", return_value=["forced"]):
            with self.assertRaises(release.BuildError):
                release.build(self.out, ROOT)
        self.assertEqual([], list(self.out.iterdir()))

    def test_a_stale_archive_from_another_version_blocks_the_build(self):
        self.out.mkdir()
        (self.out / "spec-development-protocol-0.0.1.zip").write_bytes(b"old")
        with self.assertRaises(release.BuildError) as raised:
            release.build(self.out, ROOT)
        self.assertIn("other archives", str(raised.exception))

    def test_a_hostile_archive_from_apm_is_refused_before_it_is_flattened(self):
        real = release.run_apm

        def hostile(arguments, cwd):
            output = real(arguments, cwd)
            if arguments[:1] == ["pack"]:
                scratch = Path(arguments[arguments.index("-o") + 1])
                archive_path = next(scratch.glob("*.zip"))
                with zipfile.ZipFile(archive_path, "a") as archive:
                    info = zipfile.ZipInfo("spec-development-protocol-0.5.4/skills/link")
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    archive.writestr(info, "../../../etc/passwd")
            return output

        with mock.patch.object(release, "run_apm", hostile):
            with self.assertRaises(release.BuildError) as raised:
                release.build(self.out, ROOT)
        self.assertIn("symbolic link", str(raised.exception))
        self.assertFalse(self.out.exists())


@NEEDS_APM
class RealBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.work = Path(cls.tmp.name)
        cls.zip, cls.digest = release.build(cls.work / "dist")

    def test_the_bundle_passes_every_check(self):
        self.assertEqual([], release.verify_bundle(self.zip, ROOT))

    def test_checksum_file_matches_the_archive(self):
        import hashlib
        line = (self.work / "dist" / "SHA256SUMS").read_text().strip()
        self.assertEqual(f"{hashlib.sha256(self.zip.read_bytes()).hexdigest()}  {self.zip.name}", line)

    def test_two_builds_are_byte_identical(self):
        second, digest = release.build(self.work / "dist2")
        self.assertEqual(self.digest, digest)
        self.assertEqual(self.zip.read_bytes(), second.read_bytes())

    def test_a_clean_install_runs_without_the_source_checkout(self):
        extracted = self.work / "extracted"
        with zipfile.ZipFile(self.zip) as archive:
            archive.extractall(extracted)
        bundle = next(extracted.iterdir())
        project = self.work / "project"
        (project / ".git").mkdir(parents=True)
        environment = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
        for script, arguments in (
            ("sdp-init/scripts/init.py", ["--repo", str(project)]),
            ("sdp-migrate/scripts/migrate.py", ["--repo", str(project), "preview"]),
            ("sdp-core/scripts/sdp.py", ["--help"]),
        ):
            with self.subTest(script=script):
                done = subprocess.run([sys.executable, "-B", str(bundle / "skills" / script), *arguments], cwd=str(project),
                                      capture_output=True, text=True, env=environment)
                self.assertIn(done.returncode, (0, 1), done.stderr + done.stdout)
                self.assertNotIn("Traceback", done.stderr)
        self.assertFalse((project / ".github").exists(), "preview must not write")
        self.assertTrue((bundle / "skills/sdp-migrate/manifests/legacy-files.json").is_file())
        self.assertTrue((bundle / "skills/sdp-templates/assets/TECH.md").is_file())

    def test_source_artifacts_are_excluded_and_hidden_files_are_kept_in_a_scratch_copy(self):
        scratch = self.work / "scratch"
        shutil.copytree(ROOT, scratch, ignore=copy_ignore)
        write(scratch / ".apm/skills/sdp-core/scripts/__pycache__/leftover.cpython-311.pyc", "junk")
        write(scratch / ".apm/skills/sdp-core/scripts/__pycache__/note.txt", "junk")
        write(scratch / ".apm/skills/sdp-core/scripts/.probe", "kept")
        built, _ = release.build(scratch / "dist", scratch)
        with zipfile.ZipFile(built) as archive:
            names = archive.namelist()
        self.assertFalse([n for n in names if "__pycache__" in n or n.endswith(".pyc")])
        self.assertIn(f"spec-development-protocol-{release.manifest_version(ROOT)}/skills/sdp-core/scripts/.probe", names)

    def test_apm_release_gates_agree_with_the_committed_marketplace_files(self):
        done = subprocess.run(["apm", "pack", "--check-versions", "--check-clean", "--dry-run"], cwd=str(ROOT),
                              capture_output=True, text=True)
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)

    def test_bundle_bytes_do_not_depend_on_the_checkouts_line_endings(self):
        digests = {}
        for style in ("lf", "crlf"):
            scratch = self.work / f"eol-{style}"
            shutil.copytree(ROOT, scratch, ignore=copy_ignore)
            for path in scratch.rglob("*"):
                if path.is_file() and (".apm" in path.parts or path.parent == scratch or "release-assets" in path.parts):
                    data = path.read_bytes()
                    if b"\0" not in data:
                        data = data.replace(b"\r\n", b"\n")
                        path.write_bytes(data.replace(b"\n", b"\r\n") if style == "crlf" else data)
            _, digests[style] = release.build(scratch / "dist", scratch)
        self.assertEqual(digests["lf"], digests["crlf"])

    def test_a_version_mismatch_stops_the_build(self):
        scratch = self.work / "mismatch"
        shutil.copytree(ROOT, scratch, ignore=copy_ignore)
        manifest = scratch / "plugin.json"
        manifest.write_text(manifest.read_text().replace(release.manifest_version(ROOT), "9.9.9"))
        with self.assertRaises(release.BuildError):
            release.build(scratch / "dist", scratch)
        self.assertFalse((scratch / "dist").exists())


if __name__ == "__main__":
    unittest.main()
