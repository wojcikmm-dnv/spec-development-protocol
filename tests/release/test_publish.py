import contextlib
import hashlib
import importlib.util
import io
import json
import re
import tempfile
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("publish_release", ROOT / "scripts" / "publish-release.py")
publish_release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish_release)

SHA = "a" * 40
NOTES = "### Added\n\n- Something.\n"


def make_assets(base, tag="v1.2.3", revision=SHA, content=b"zip-bytes"):
    version = tag[1:]
    directory = Path(tempfile.mkdtemp(prefix="dist-", dir=base))
    name = f"demo-{version}.zip"
    digest = hashlib.sha256(content).hexdigest()
    (directory / name).write_bytes(content)
    (directory / "SHA256SUMS").write_text(f"{digest}  {name}\n")
    metadata = {"name": "demo", "version": version, "apm": "0.29.0", "sha256": digest, "files": 3}
    if revision is not None:
        metadata["revision"] = revision
    (directory / "release-metadata.json").write_text(json.dumps(metadata))
    return directory


class FakeStore:
    """An in-memory stand-in for the GitHub calls; `fail` names operations that should raise once."""

    def __init__(self):
        self.releases, self.blobs, self.calls, self.fail, self.next_id = {}, {}, [], set(), 100
        self.tag_commits, self.tag_queue = {}, []

    def tag_commit(self, tag):
        self.calls.append("tag")
        if self.tag_queue:
            return self.tag_queue.pop(0)
        return self.tag_commits.get(tag, SHA)

    def _id(self):
        self.next_id += 1
        return self.next_id

    def _maybe_fail(self, operation):
        if operation in self.fail:
            self.fail.discard(operation)
            raise RuntimeError(f"injected {operation} failure")

    def find(self, tag):
        self.calls.append("find")
        release = self.releases.get(tag)
        return None if release is None else {"id": release["id"], "draft": release["draft"], "prerelease": release["prerelease"],
                                             "assets": dict(release["assets"])}

    def create_draft(self, tag, notes, prerelease, revision):
        self.calls.append("create")
        self._maybe_fail("create")
        self.releases[tag] = {"id": self._id(), "draft": True, "prerelease": prerelease, "assets": {}, "notes": notes,
                              "revision": revision}
        return self.find(tag)

    def update_draft(self, release_id, tag, notes, prerelease):
        self.calls.append("update")
        release = self.release_for(release_id)
        release["notes"], release["prerelease"] = notes, prerelease

    def download(self, asset_id):
        self.calls.append("download")
        return self.blobs[asset_id]

    def release_for(self, release_id):
        return next(r for r in self.releases.values() if r["id"] == release_id)

    def upload(self, release_id, name, data):
        self.calls.append(f"upload:{name}")
        self._maybe_fail("upload")
        asset_id = self._id()
        self.blobs[asset_id] = data[:-1] if "corrupt" in self.fail else data
        self.release_for(release_id)["assets"][name] = asset_id

    def delete_asset(self, asset_id):
        self.calls.append("delete")
        for release in self.releases.values():
            release["assets"] = {n: i for n, i in release["assets"].items() if i != asset_id}
        del self.blobs[asset_id]

    def publish(self, release_id, prerelease):
        self.calls.append(f"publish:{prerelease}")
        self._maybe_fail("publish")
        release = self.release_for(release_id)
        release["draft"], release["prerelease"] = False, prerelease

    def mutations(self):
        return [c for c in self.calls if c.split(":")[0] in ("create", "update", "upload", "delete", "publish")]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = FakeStore()

    def assets(self, **kwargs):
        return make_assets(self.tmp.name, **kwargs)

    def run_publish(self, directory, tag="v1.2.3", revision=SHA):
        return publish_release.publish(self.store, tag, revision, directory, NOTES)

    def code_of(self, directory, tag="v1.2.3", revision=SHA):
        with self.assertRaises(publish_release.PublishError) as raised:
            self.run_publish(directory, tag, revision)
        return raised.exception.code


class PublishFlowTests(Base):
    def test_a_new_release_is_drafted_uploaded_verified_and_published(self):
        report = self.run_publish(self.assets())
        release = self.store.releases["v1.2.3"]
        self.assertEqual("published", report["state"])
        self.assertFalse(release["draft"])
        self.assertEqual(3, len(release["assets"]))
        self.assertIn("do not authenticate who published", release["notes"])
        self.assertIn("- Something.", release["notes"])
        self.assertLess(self.store.calls.index("create"), self.store.calls.index("publish:False"))

    def test_a_prerelease_tag_is_never_published_as_stable(self):
        directory = self.assets(tag="v2.0.0-rc.1")
        report = self.run_publish(directory, tag="v2.0.0-rc.1")
        self.assertTrue(report["prerelease"])
        self.assertIn("publish:True", self.store.calls)
        self.assertTrue(self.store.releases["v2.0.0-rc.1"]["prerelease"])

    def test_rerunning_after_publication_changes_nothing(self):
        directory = self.assets()
        self.run_publish(directory)
        self.store.calls.clear()
        report = self.run_publish(directory)
        self.assertEqual("already-published", report["state"])
        self.assertEqual([], self.store.mutations())

    def test_a_published_release_with_different_bytes_is_refused_untouched(self):
        self.run_publish(self.assets(content=b"first"))
        before = {k: dict(v) for k, v in self.store.releases.items()}
        blobs = dict(self.store.blobs)
        self.store.calls.clear()
        self.assertEqual(publish_release.EXIT_REFUSED, self.code_of(self.assets(content=b"second")))
        self.assertEqual([], self.store.mutations())
        self.assertEqual(before, self.store.releases)
        self.assertEqual(blobs, self.store.blobs)

    def test_a_published_release_missing_an_asset_is_refused(self):
        directory = self.assets()
        self.run_publish(directory)
        release = self.store.releases["v1.2.3"]
        release["assets"].pop("SHA256SUMS")
        self.store.calls.clear()
        self.assertEqual(publish_release.EXIT_REFUSED, self.code_of(directory))
        self.assertEqual([], self.store.mutations())

    def test_an_interrupted_upload_resumes_without_repeating_finished_work(self):
        directory = self.assets()
        calls_before = []
        self.store.fail.add("upload")
        self.assertEqual(publish_release.EXIT_UPLOAD, self.code_of(directory))
        self.assertTrue(self.store.releases["v1.2.3"]["draft"])
        uploaded_first = len(self.store.releases["v1.2.3"]["assets"])
        self.store.calls.clear()
        report = self.run_publish(directory)
        self.assertEqual("published", report["state"])
        self.assertNotIn("create", self.store.calls)
        self.assertEqual(3 - uploaded_first, len([c for c in self.store.calls if c.startswith("upload:")]))
        self.assertEqual(3, len(self.store.releases["v1.2.3"]["assets"]))
        self.assertEqual(calls_before, [])

    def test_a_draft_with_a_stale_asset_gets_it_replaced(self):
        old = self.assets(content=b"old build")
        self.store.fail.add("publish")
        self.assertEqual(publish_release.EXIT_PUBLISH, self.code_of(old))
        self.store.calls.clear()
        report = self.run_publish(self.assets(content=b"new build"))
        self.assertEqual("published", report["state"])
        self.assertIn("delete", self.store.calls)
        names = self.store.releases["v1.2.3"]["assets"]
        archive = self.store.blobs[names["demo-1.2.3.zip"]]
        self.assertEqual(b"new build", archive)

    def test_a_failed_publish_step_keeps_verified_assets_and_a_rerun_only_publishes(self):
        directory = self.assets()
        self.store.fail.add("publish")
        self.assertEqual(publish_release.EXIT_PUBLISH, self.code_of(directory))
        self.assertTrue(self.store.releases["v1.2.3"]["draft"])
        self.store.calls.clear()
        report = self.run_publish(directory)
        self.assertEqual("published", report["state"])
        self.assertEqual(["update", "publish:False"], self.store.mutations())

    def test_assets_that_do_not_verify_are_never_published(self):
        self.store.fail.add("corrupt")
        self.assertEqual(publish_release.EXIT_UPLOAD, self.code_of(self.assets()))
        self.assertTrue(self.store.releases["v1.2.3"]["draft"])
        self.assertNotIn("publish:False", self.store.calls)

    def test_a_publish_call_that_leaves_the_release_a_draft_is_not_reported_as_success(self):
        class Silent(FakeStore):
            def publish(self, release_id, prerelease):
                self.calls.append("publish:ignored")

        self.store = Silent()
        self.assertEqual(publish_release.EXIT_PUBLISH, self.code_of(self.assets()))

    def test_a_failure_creating_the_draft_changes_nothing(self):
        self.store.fail.add("create")
        self.assertEqual(publish_release.EXIT_UPLOAD, self.code_of(self.assets()))
        self.assertEqual({}, self.store.releases)

    def test_a_lookup_failure_is_reported_not_raised(self):
        class Broken(FakeStore):
            def find(self, tag):
                raise RuntimeError("HTTP 500")
        self.store = Broken()
        self.assertEqual(publish_release.EXIT_UPLOAD, self.code_of(self.assets()))

    def test_two_runs_that_race_converge_on_one_release(self):
        directory = self.assets()
        first = self.store
        self.run_publish(directory)
        report = self.run_publish(directory)
        self.assertEqual("already-published", report["state"])
        self.assertEqual(1, len(first.releases))


class TagAndDraftSafetyTests(Base):
    def test_a_tag_that_points_elsewhere_stops_everything_before_any_change(self):
        self.store.tag_commits["v1.2.3"] = "b" * 40
        self.assertEqual(publish_release.EXIT_REFUSED, self.code_of(self.assets()))
        self.assertEqual([], self.store.mutations())

    def test_a_missing_tag_is_refused(self):
        self.store.tag_commits["v1.2.3"] = None
        self.assertEqual(publish_release.EXIT_REFUSED, self.code_of(self.assets()))
        self.assertEqual([], self.store.mutations())

    def test_a_tag_that_moves_after_the_upload_is_never_published(self):
        self.store.tag_queue = [SHA, "c" * 40]
        self.assertEqual(publish_release.EXIT_REFUSED, self.code_of(self.assets()))
        self.assertTrue(self.store.releases["v1.2.3"]["draft"])
        self.assertNotIn("publish:False", self.store.calls)

    def test_an_already_published_release_whose_tag_moved_is_not_reported_as_current(self):
        directory = self.assets()
        self.run_publish(directory)
        self.store.tag_commits["v1.2.3"] = "d" * 40
        self.assertEqual(publish_release.EXIT_REFUSED, self.code_of(directory))

    def test_the_draft_is_created_for_the_built_commit(self):
        self.run_publish(self.assets())
        self.assertEqual(SHA, self.store.releases["v1.2.3"]["revision"])

    def test_a_resumed_draft_gets_the_changelog_notes_back(self):
        directory = self.assets()
        self.store.fail.add("publish")
        self.code_of(directory)
        self.store.releases["v1.2.3"]["notes"] = "UNRELEASED SCRATCH NOTES"
        self.run_publish(directory)
        self.assertIn("- Something.", self.store.releases["v1.2.3"]["notes"])
        self.assertNotIn("SCRATCH", self.store.releases["v1.2.3"]["notes"])

    def test_a_draft_holding_foreign_assets_is_refused_not_published(self):
        directory = self.assets()
        self.store.fail.add("publish")
        self.code_of(directory)
        self.store.releases["v1.2.3"]["assets"]["stale-extra.zip"] = 999
        self.store.blobs[999] = b"stale"
        self.store.calls.clear()
        self.assertEqual(publish_release.EXIT_REFUSED, self.code_of(directory))
        self.assertEqual([], self.store.mutations())
        self.assertTrue(self.store.releases["v1.2.3"]["draft"])

    def test_an_unreadable_asset_in_a_draft_is_replaced_instead_of_wedging_every_rerun(self):
        directory = self.assets()
        self.store.fail.add("publish")
        self.code_of(directory)
        broken = self.store.releases["v1.2.3"]["assets"]["demo-1.2.3.zip"]
        original = self.store.download

        def download(asset_id):
            if asset_id == broken:
                raise RuntimeError("GET failed with HTTP 404")
            return original(asset_id)

        self.store.download = download
        report = self.run_publish(directory)
        self.assertEqual("published", report["state"])
        self.assertIn("demo-1.2.3.zip", report["uploaded"])

    def test_errors_reading_published_assets_use_the_documented_exit_code(self):
        directory = self.assets()
        self.run_publish(directory)

        def download(asset_id):
            raise RuntimeError("GET failed with HTTP 503")

        self.store.download = download
        self.assertEqual(publish_release.EXIT_UPLOAD, self.code_of(directory))

    def test_a_tag_lookup_failure_uses_the_documented_exit_code(self):
        def tag_commit(tag):
            raise RuntimeError("GET failed with HTTP 500")

        self.store.tag_commit = tag_commit
        self.assertEqual(publish_release.EXIT_UPLOAD, self.code_of(self.assets()))


class InputValidationTests(Base):
    def test_good_assets_load(self):
        loaded = publish_release.load_assets(self.assets(), "v1.2.3", SHA)
        self.assertEqual(["SHA256SUMS", "demo-1.2.3.zip", "release-metadata.json"], sorted(loaded))

    def test_bad_inputs_stop_before_anything_is_contacted(self):
        good = self.assets()
        cases = {}
        extra = self.assets(content=b"extra")
        (extra / "notes.txt").write_text("surprise")
        cases["extra file"] = (extra, "v1.2.3", SHA)
        wrong_sum = self.assets(content=b"sum")
        (wrong_sum / "SHA256SUMS").write_text("0" * 64 + "  demo-1.2.3.zip\n")
        cases["checksum mismatch"] = (wrong_sum, "v1.2.3", SHA)
        wrong_meta = self.assets(content=b"meta")
        data = json.loads((wrong_meta / "release-metadata.json").read_text())
        data["sha256"] = "0" * 64
        (wrong_meta / "release-metadata.json").write_text(json.dumps(data))
        cases["metadata mismatch"] = (wrong_meta, "v1.2.3", SHA)
        missing = self.assets(content=b"missing")
        (missing / "release-metadata.json").unlink()
        cases["missing metadata"] = (missing, "v1.2.3", SHA)
        no_revision = self.assets(content=b"norev", revision=None)
        cases["no recorded revision"] = (no_revision, "v1.2.3", SHA)
        cases["other revision"] = (good, "v1.2.3", "b" * 40)
        cases["other version"] = (good, "v1.2.4", SHA)
        cases["bad tag"] = (good, "1.2.3", SHA)
        cases["not a directory"] = (Path(self.tmp.name) / "nope", "v1.2.3", SHA)
        for label, (directory, tag, revision) in cases.items():
            with self.subTest(label), self.assertRaises(publish_release.PublishError) as raised:
                publish_release.publish(self.store, tag, revision, directory, NOTES)
            self.assertEqual(publish_release.EXIT_INPUT, raised.exception.code, label)
        self.assertEqual([], self.store.calls)

    def test_invalid_json_metadata_is_an_input_error(self):
        directory = self.assets()
        (directory / "release-metadata.json").write_text("{not json")
        self.assertEqual(publish_release.EXIT_INPUT, self.code_of(directory))


class CommandLineTests(Base):
    def run_main(self, *arguments, environ=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = publish_release.main(list(arguments), store=self.store)
        return code, out.getvalue(), err.getvalue()

    def arguments(self, directory, notes_text=NOTES, summary=None):
        notes = Path(self.tmp.name) / "notes.md"
        notes.write_text(notes_text)
        found = ["--tag", "v1.2.3", "--revision", SHA, "--assets-dir", str(directory), "--notes", str(notes), "--repo", "o/r"]
        return found + (["--summary-file", str(summary)] if summary else [])

    def test_success_prints_and_appends_a_summary_with_the_exact_revision(self):
        summary = Path(self.tmp.name) / "summary.md"
        summary.write_text("earlier\n")
        code, out, _ = self.run_main(*self.arguments(self.assets(), summary=summary))
        self.assertEqual(0, code)
        text = summary.read_text()
        self.assertTrue(text.startswith("earlier\n"))
        self.assertIn(f"tag v1.2.3 at commit {SHA}", text)
        self.assertIn("published", out)

    def test_empty_notes_stop_the_run(self):
        code, _, err = self.run_main(*self.arguments(self.assets(), notes_text="  \n"))
        self.assertEqual(publish_release.EXIT_INPUT, code)
        self.assertEqual([], self.store.calls)

    def test_failures_use_distinct_exit_codes(self):
        self.store.fail.add("publish")
        code, _, err = self.run_main(*self.arguments(self.assets()))
        self.assertEqual(publish_release.EXIT_PUBLISH, code)
        self.assertIn("rerun", err)
        codes = {publish_release.EXIT_INPUT, publish_release.EXIT_REFUSED, publish_release.EXIT_UPLOAD, publish_release.EXIT_PUBLISH}
        self.assertEqual(4, len(codes))

    def test_without_a_token_nothing_is_attempted(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                unittest.mock.patch.dict("os.environ", {"GITHUB_TOKEN": ""}):
            code = publish_release.main(self.arguments(self.assets()))
        self.assertEqual(publish_release.EXIT_INPUT, code)
        self.assertIn("GITHUB_TOKEN", err.getvalue())


class FakeGitHub(BaseHTTPRequestHandler):
    """A small GitHub REST fake. Asset downloads redirect to a different host name."""

    server_version = "FakeGitHub"

    def log_message(self, *args):
        pass

    def _send(self, code, body=b"", content_type="application/json", headers=None):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _record(self):
        self.server.requests.append((self.command, self.path, self.headers.get("Authorization")))

    def _body(self):
        return self.rfile.read(int(self.headers.get("Content-Length") or 0))

    def do_GET(self):
        self._record()
        state, parsed = self.server.state, urllib.parse.urlsplit(self.path)
        if state.get("fail_get"):
            return self._send(500)
        if parsed.path.startswith("/blob/"):
            return self._send(200, state["blobs"][int(parsed.path.rsplit("/", 1)[1])], "application/octet-stream")
        if re.fullmatch(r"/repos/o/r/releases/assets/\d+", parsed.path):
            asset_id = int(parsed.path.rsplit("/", 1)[1])
            return self._send(302, b"", headers={"Location": f"http://127.0.0.1:{self.server.blob_port}/blob/{asset_id}"})
        if parsed.path == "/repos/o/r/releases":
            query = urllib.parse.parse_qs(parsed.query)
            page, per_page = int(query["page"][0]), int(query["per_page"][0])
            ordered = state["releases"]
            return self._send(200, json.dumps(ordered[(page - 1) * per_page: page * per_page]).encode())
        match = re.fullmatch(r"/repos/o/r/git/ref/tags/(.+)", parsed.path)
        if match:
            entry = state["tags"].get(urllib.parse.unquote(match.group(1)))
            if entry is None:
                return self._send(404)
            return self._send(200, json.dumps({"object": {"type": entry[0], "sha": entry[1]}}).encode())
        match = re.fullmatch(r"/repos/o/r/git/tags/([0-9a-f]+)", parsed.path)
        if match:
            return self._send(200, json.dumps({"object": {"type": "commit", "sha": state["peeled"][match.group(1)]}}).encode())
        self._send(404)

    def do_POST(self):
        self._record()
        state, parsed = self.server.state, urllib.parse.urlsplit(self.path)
        if parsed.path == "/repos/o/r/releases":
            payload = json.loads(self._body())
            release = {"id": 1000 + len(state["releases"]), "tag_name": payload["tag_name"], "draft": payload["draft"],
                       "prerelease": payload["prerelease"], "body": payload["body"], "assets": [],
                       "target_commitish": payload.get("target_commitish")}
            state["releases"].insert(0, release)
            return self._send(201, json.dumps(release).encode())
        match = re.fullmatch(r"/upload/repos/o/r/releases/(\d+)/assets", parsed.path)
        if match:
            release = next(r for r in state["releases"] if r["id"] == int(match.group(1)))
            name = urllib.parse.parse_qs(parsed.query)["name"][0]
            asset_id = 5000 + len(state["blobs"])
            state["blobs"][asset_id] = self._body()
            release["assets"].append({"id": asset_id, "name": name})
            return self._send(201, json.dumps({"id": asset_id}).encode())
        self._send(404)

    def do_PATCH(self):
        self._record()
        match = re.fullmatch(r"/repos/o/r/releases/(\d+)", self.path)
        release = next(r for r in self.server.state["releases"] if r["id"] == int(match.group(1)))
        payload = json.loads(self._body())
        self.server.state["patches"].append(payload)
        release.update(payload)
        self._send(200, json.dumps(release).encode())

    def do_DELETE(self):
        self._record()
        asset_id = int(self.path.rsplit("/", 1)[1])
        for release in self.server.state["releases"]:
            release["assets"] = [a for a in release["assets"] if a["id"] != asset_id]
        self.server.state["blobs"].pop(asset_id, None)
        self._send(204)


class HttpAdapterTests(Base):
    def setUp(self):
        super().setUp()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeGitHub)
        self.blob_server = ThreadingHTTPServer(("127.0.0.1", 0), FakeGitHub)
        self.server.state = self.blob_server.state = {"releases": [], "blobs": {}, "patches": [], "tags": {"v1.2.3": ("commit", SHA)},
                                                      "peeled": {}}
        self.server.requests = []
        self.blob_server.requests = self.server.requests
        self.server.blob_port = self.blob_server.server_port
        for server in (self.server, self.blob_server):
            threading.Thread(target=server.serve_forever, daemon=True).start()
            self.addCleanup(lambda s=server: (s.shutdown(), s.server_close()))
        base = f"http://127.0.0.1:{self.server.server_port}"
        self.store = publish_release.GitHubStore("o/r", "secret-token", base, base + "/upload")

    def test_full_publish_through_the_http_layer(self):
        report = self.run_publish(self.assets())
        self.assertEqual("published", report["state"])
        release = self.server.state["releases"][0]
        self.assertFalse(release["draft"])
        self.assertEqual({"SHA256SUMS", "demo-1.2.3.zip", "release-metadata.json"}, {a["name"] for a in release["assets"]})
        self.assertIn("do not authenticate who published", release["body"])
        patch = [r for r in self.server.requests if r[0] == "PATCH"]
        self.assertEqual(1, len(patch))

    def test_the_token_is_sent_to_the_api_but_never_to_the_redirect_target(self):
        self.run_publish(self.assets())
        blob_requests = [r for r in self.server.requests if r[1].startswith("/blob/")]
        api_requests = [r for r in self.server.requests if not r[1].startswith("/blob/")]
        self.assertTrue(blob_requests)
        self.assertTrue(all(r[2] is None for r in blob_requests), blob_requests)
        self.assertTrue(all(r[2] == "Bearer secret-token" for r in api_requests))

    def test_rerun_over_http_is_a_no_op(self):
        directory = self.assets()
        self.run_publish(directory)
        self.server.requests.clear()
        report = self.run_publish(directory)
        self.assertEqual("already-published", report["state"])
        self.assertEqual([], [r for r in self.server.requests if r[0] in ("POST", "PATCH", "DELETE")])

    def test_release_lookup_pages_through_more_than_one_hundred_releases(self):
        self.server.state["releases"] = [{"id": i, "tag_name": f"v0.0.{i}", "draft": False, "prerelease": False, "assets": []}
                                         for i in range(1, 151)]
        found = self.store.find("v0.0.150")
        self.assertEqual(150, found["id"])
        self.assertIsNone(self.store.find("v9.9.9"))

    def test_http_errors_become_publish_errors_not_tracebacks(self):
        self.server.state["fail_get"] = True
        self.assertEqual(publish_release.EXIT_UPLOAD, self.code_of(self.assets()))

    def mutating_requests(self):
        return [r for r in self.server.requests if r[0] in ("POST", "PATCH", "DELETE")]

    def test_the_draft_targets_the_built_commit_and_stable_releases_use_the_legacy_latest_rule(self):
        self.run_publish(self.assets())
        self.assertEqual(SHA, self.server.state["releases"][0]["target_commitish"])
        self.assertEqual("legacy", self.server.state["patches"][-1]["make_latest"])

    def test_a_prerelease_is_never_made_latest_over_http(self):
        self.server.state["tags"]["v2.0.0-rc.1"] = ("commit", SHA)
        self.run_publish(self.assets(tag="v2.0.0-rc.1"), tag="v2.0.0-rc.1")
        patch = self.server.state["patches"][-1]
        self.assertEqual(("false", True), (patch["make_latest"], patch["prerelease"]))

    def test_an_annotated_tag_is_peeled_to_its_commit(self):
        self.server.state["tags"]["v1.2.3"] = ("tag", "e" * 40)
        self.server.state["peeled"]["e" * 40] = SHA
        self.assertEqual(SHA, self.store.tag_commit("v1.2.3"))
        self.assertEqual("published", self.run_publish(self.assets())["state"])

    def test_a_tag_pointing_elsewhere_or_missing_changes_nothing_over_http(self):
        for entry in (("commit", "b" * 40), None):
            with self.subTest(entry=entry):
                if entry is None:
                    self.server.state["tags"].pop("v1.2.3")
                else:
                    self.server.state["tags"]["v1.2.3"] = entry
                self.assertEqual(publish_release.EXIT_REFUSED, self.code_of(self.assets()))
                self.assertEqual([], self.mutating_requests())

    def test_two_releases_for_one_tag_stop_the_run(self):
        directory = self.assets()
        self.run_publish(directory)
        self.server.state["releases"].append(dict(self.server.state["releases"][0], id=4242, draft=True))
        self.assertEqual(publish_release.EXIT_UPLOAD, self.code_of(directory))

    def test_an_unreachable_server_is_a_reported_failure_not_a_traceback(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), FakeGitHub)
        port = server.server_port
        server.server_close()
        self.store.api_url = f"http://127.0.0.1:{port}"
        self.assertEqual(publish_release.EXIT_UPLOAD, self.code_of(self.assets()))


import unittest.mock  # noqa: E402  (used above through the unittest package)

if __name__ == "__main__":
    unittest.main()
