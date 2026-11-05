#!/usr/bin/env python3
"""Publish the release assets for a `v<semver>` tag to GitHub (standard library only).

    python scripts/publish-release.py --tag v1.2.3 --revision <commit> --assets-dir dist \
        --notes notes.md --repo owner/name

It only talks to the GitHub REST API (token from GITHUB_TOKEN) and is meant to run in the
publishing job after the build job produced and verified the assets. The flow is
create-or-resume a draft, upload only missing or differing assets, re-download and compare
every asset, confirm the tag still points at the built commit, then publish. A published
release is never modified: if its assets differ from the build, the run stops. Re-running
after any failure is safe.

Exit codes: 0 done (including "already published"), 10 the build output is not acceptable,
20 refused (a published release differs from the build, the tag no longer points at the built
commit, or a draft holds assets that are not part of the build), 30 upload or verification
failed (the draft is kept so the run can resume), 31 the final publish step failed.
"""

import argparse
import hashlib
import http.client
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from changelog import ChangelogError, is_prerelease, tag_version  # noqa: E402

EXIT_OK, EXIT_INPUT, EXIT_REFUSED, EXIT_UPLOAD, EXIT_PUBLISH = 0, 10, 20, 30, 31
DISCLAIMER = ("\n\nThe checksums in `SHA256SUMS` confirm that the files arrived intact. They do not "
              "authenticate who published them.\n")
API_VERSION = "2022-11-28"
STORE_ERRORS = (RuntimeError, ValueError, KeyError, TypeError)


class PublishError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def load_assets(directory, tag, revision):
    """Read and validate the build output; return {asset name: bytes}."""
    try:
        version = tag_version(tag)
    except ChangelogError as error:
        raise PublishError(EXIT_INPUT, str(error))
    directory = Path(directory)
    if not directory.is_dir():
        raise PublishError(EXIT_INPUT, f"{directory} is not a directory")
    present = sorted(path.name for path in directory.iterdir())
    metadata_path = directory / "release-metadata.json"
    if not metadata_path.is_file():
        raise PublishError(EXIT_INPUT, "release-metadata.json is missing from the build output")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except ValueError as error:
        raise PublishError(EXIT_INPUT, f"release-metadata.json is not valid JSON: {error}")
    if not isinstance(metadata, dict) or metadata.get("version") != version:
        found = metadata.get("version") if isinstance(metadata, dict) else None
        raise PublishError(EXIT_INPUT, f"release-metadata.json is for version {found!r}, not {version}")
    if metadata.get("revision") != revision:
        raise PublishError(EXIT_INPUT, f"the build recorded revision {metadata.get('revision')!r}, not {revision!r}")
    archive = f"{metadata.get('name')}-{version}.zip"
    expected = sorted([archive, "SHA256SUMS", "release-metadata.json"])
    if present != expected:
        raise PublishError(EXIT_INPUT, f"build output must contain exactly {expected}; found {present}")
    data = (directory / archive).read_bytes()
    digest = sha256(data)
    sums = (directory / "SHA256SUMS").read_text(encoding="utf-8").split()
    if sums != [digest, archive] and sums != [digest, "*" + archive]:
        raise PublishError(EXIT_INPUT, "SHA256SUMS does not match the archive")
    if metadata.get("sha256") != digest:
        raise PublishError(EXIT_INPUT, "release-metadata.json does not match the archive")
    return {name: (directory / name).read_bytes() for name in expected}


class _StripAuthOnRedirect(urllib.request.HTTPRedirectHandler):
    """Asset downloads redirect to another host; the token must not follow."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None and urllib.parse.urlsplit(newurl).netloc != urllib.parse.urlsplit(req.full_url).netloc:
            redirected.headers = {k: v for k, v in redirected.headers.items() if k.lower() != "authorization"}
            redirected.unredirected_hdrs = {k: v for k, v in redirected.unredirected_hdrs.items() if k.lower() != "authorization"}
        return redirected


class GitHubStore:
    """The few REST calls the publisher needs."""

    def __init__(self, repo, token, api_url="https://api.github.com", upload_url="https://uploads.github.com"):
        self.repo, self.token = repo, token
        self.api_url, self.upload_url = api_url.rstrip("/"), upload_url.rstrip("/")
        self.opener = urllib.request.build_opener(_StripAuthOnRedirect())

    def _request(self, method, url, *, body=None, content_type="application/json", accept="application/vnd.github+json",
                 allow_missing=False):
        request = urllib.request.Request(url, data=body, method=method)
        request.add_header("Authorization", f"Bearer {self.token}")
        request.add_header("Accept", accept)
        request.add_header("X-GitHub-Api-Version", API_VERSION)
        if body is not None:
            request.add_header("Content-Type", content_type)
        path = urllib.parse.urlsplit(url).path
        try:
            with self.opener.open(request, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            error.close()
            if error.code == 404 and allow_missing:
                return None
            raise RuntimeError(f"{method} {path} failed with HTTP {error.code}")
        except (OSError, http.client.HTTPException) as error:
            raise RuntimeError(f"{method} {path} failed: {getattr(error, 'reason', None) or type(error).__name__}")

    def _json(self, path, **options):
        raw = self._request("GET", f"{self.api_url}/repos/{self.repo}/{path}", **options)
        return None if raw is None else json.loads(raw)

    def find(self, tag):
        found, page = [], 1
        while True:
            releases = self._json(f"releases?per_page=100&page={page}")
            found += [release for release in releases if release.get("tag_name") == tag]
            if len(releases) < 100:
                break
            page += 1
        if len(found) > 1:
            raise RuntimeError(f"{len(found)} releases exist for {tag}; delete the extra drafts and rerun")
        return self._shape(found[0]) if found else None

    @staticmethod
    def _shape(release):
        return {"id": release["id"], "draft": bool(release.get("draft")), "prerelease": bool(release.get("prerelease")),
                "assets": {asset["name"]: asset["id"] for asset in release.get("assets", [])}}

    def create_draft(self, tag, notes, prerelease, revision):
        body = json.dumps({"tag_name": tag, "target_commitish": revision, "name": tag, "body": notes, "draft": True,
                           "prerelease": prerelease}).encode()
        return self._shape(json.loads(self._request("POST", f"{self.api_url}/repos/{self.repo}/releases", body=body)))

    def update_draft(self, release_id, tag, notes, prerelease):
        body = json.dumps({"name": tag, "body": notes, "prerelease": prerelease}).encode()
        self._request("PATCH", f"{self.api_url}/repos/{self.repo}/releases/{release_id}", body=body)

    def tag_commit(self, tag):
        """The commit a tag points at (annotated tags are peeled), or None if the tag does not exist."""
        reference = self._json(f"git/ref/tags/{urllib.parse.quote(tag)}", allow_missing=True)
        for _ in range(5):
            if reference is None:
                return None
            target = reference["object"]
            if target["type"] == "commit":
                return target["sha"]
            if target["type"] != "tag":
                return None
            reference = self._json(f"git/tags/{target['sha']}", allow_missing=True)
        return None

    def download(self, asset_id):
        return self._request("GET", f"{self.api_url}/repos/{self.repo}/releases/assets/{asset_id}", accept="application/octet-stream")

    def upload(self, release_id, name, data):
        url = f"{self.upload_url}/repos/{self.repo}/releases/{release_id}/assets?name={urllib.parse.quote(name)}"
        self._request("POST", url, body=data, content_type="application/octet-stream")

    def delete_asset(self, asset_id):
        self._request("DELETE", f"{self.api_url}/repos/{self.repo}/releases/assets/{asset_id}")

    def publish(self, release_id, prerelease):
        body = json.dumps({"draft": False, "prerelease": prerelease, "make_latest": "false" if prerelease else "legacy"}).encode()
        self._request("PATCH", f"{self.api_url}/repos/{self.repo}/releases/{release_id}", body=body)


def remote_matches(store, release, name, data, tolerant=False):
    """Whether the stored asset equals `data`. A draft's unreadable asset counts as different so it is replaced."""
    asset_id = release["assets"].get(name)
    if asset_id is None:
        return False
    try:
        return store.download(asset_id) == data
    except STORE_ERRORS:
        if tolerant:
            return False
        raise


def require_tag_at(store, tag, revision):
    try:
        actual = store.tag_commit(tag)
    except STORE_ERRORS as error:
        raise PublishError(EXIT_UPLOAD, f"could not read the tag {tag}: {error}")
    if actual != revision:
        raise PublishError(EXIT_REFUSED, f"tag {tag} points at {actual or 'nothing'}, not at the built commit {revision}; nothing was published")


def publish(store, tag, revision, assets_dir, notes):
    local = load_assets(assets_dir, tag, revision)
    prerelease = is_prerelease(tag_version(tag))
    full_notes = notes.rstrip("\n") + DISCLAIMER
    report = {"tag": tag, "revision": revision, "prerelease": prerelease, "uploaded": [], "kept": []}
    require_tag_at(store, tag, revision)
    try:
        release = store.find(tag)
    except STORE_ERRORS as error:
        raise PublishError(EXIT_UPLOAD, f"could not look up the release: {error}")
    if release is not None and not release["draft"]:
        try:
            differing = [name for name, data in local.items() if not remote_matches(store, release, name, data)]
        except STORE_ERRORS as error:
            raise PublishError(EXIT_UPLOAD, f"could not read the published assets: {error}")
        if differing:
            raise PublishError(EXIT_REFUSED, f"{tag} is already published and its assets differ from this build "
                                             f"({', '.join(differing)}); nothing was changed")
        report.update(state="already-published", kept=sorted(local))
        return report
    try:
        if release is None:
            release = store.create_draft(tag, full_notes, prerelease, revision)
            report["created_draft"] = True
        else:
            extra = sorted(set(release["assets"]) - set(local))
            if extra:
                raise PublishError(EXIT_REFUSED, f"the draft for {tag} holds assets that are not part of this build "
                                                 f"({', '.join(extra)}); remove them and rerun")
            store.update_draft(release["id"], tag, full_notes, prerelease)
        for name, data in local.items():
            if remote_matches(store, release, name, data, tolerant=True):
                report["kept"].append(name)
                continue
            if name in release["assets"]:
                store.delete_asset(release["assets"][name])
            store.upload(release["id"], name, data)
            report["uploaded"].append(name)
        release = store.find(tag)
        mismatched = [name for name, data in local.items() if release is None or not remote_matches(store, release, name, data)]
        if mismatched:
            raise PublishError(EXIT_UPLOAD, f"uploaded assets did not verify ({', '.join(mismatched)}); the draft was kept, rerun to resume")
    except PublishError:
        raise
    except STORE_ERRORS as error:
        raise PublishError(EXIT_UPLOAD, f"upload failed: {error}; the draft was kept, rerun to resume")
    require_tag_at(store, tag, revision)
    try:
        store.publish(release["id"], prerelease)
        final = store.find(tag)
        if final is None or final["draft"]:
            raise RuntimeError("the release is still a draft")
    except STORE_ERRORS as error:
        raise PublishError(EXIT_PUBLISH, f"assets are uploaded and verified but publishing failed: {error}; rerun to retry")
    report["state"] = "published"
    return report


def summary(report):
    lines = [f"Release {report['tag']}: {report['state']}",
             f"Commit: {report['revision']}", f"Prerelease: {str(report['prerelease']).lower()}",
             f"Uploaded: {', '.join(report['uploaded']) or 'none'}", f"Already present: {', '.join(report['kept']) or 'none'}"]
    if report["state"] == "published":
        lines.append(f"A catalog entry for this release should reference tag {report['tag']} at commit {report['revision']}.")
    return "\n".join(lines) + "\n"


def main(argv=None, store=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--assets-dir", required=True)
    parser.add_argument("--notes", required=True)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--api-url", default=os.environ.get("GITHUB_API_URL", "https://api.github.com"))
    parser.add_argument("--upload-url", default="https://uploads.github.com")
    parser.add_argument("--summary-file", default=os.environ.get("GITHUB_STEP_SUMMARY", ""))
    arguments = parser.parse_args(argv)
    try:
        if store is None:
            token = os.environ.get("GITHUB_TOKEN", "")
            if not token or "/" not in arguments.repo:
                raise PublishError(EXIT_INPUT, "GITHUB_TOKEN and --repo owner/name are required")
            store = GitHubStore(arguments.repo, token, arguments.api_url, arguments.upload_url)
        try:
            notes = Path(arguments.notes).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise PublishError(EXIT_INPUT, f"cannot read the release notes: {error}")
        if not notes.strip():
            raise PublishError(EXIT_INPUT, "the release notes are empty")
        report = publish(store, arguments.tag, arguments.revision, arguments.assets_dir, notes)
    except PublishError as error:
        print(f"FAIL ({error.code}): {error}", file=sys.stderr)
        return error.code
    text = summary(report)
    print(text, end="")
    if arguments.summary_file:
        with open(arguments.summary_file, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
