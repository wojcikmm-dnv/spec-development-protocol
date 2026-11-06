#!/usr/bin/env python3
"""Build the verified-ownership manifest of files the old installers copied (maintainer tool).

For each supported release tag this records, per path the installer would have created under
.github/, the SHA-256 of the released content with line endings normalized to LF. The migration
tool treats a client file as SDP-owned only when its content matches one of these exactly.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / ".apm/skills/sdp-migrate/manifests/legacy-files.json"
RELEASES = {"0.5.3": "v0.5.3", "0.5.4": "v0.5.4"}


def git(*args):
    done = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)
    if done.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {done.stderr.decode(errors='replace').strip()}")
    return done.stdout


def digest(content):
    return hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()


def build():
    manifest = {"schema_version": 1, "normalization": "line endings converted to LF before hashing", "releases": {}}
    for version, tag in RELEASES.items():
        names = git("ls-tree", "-r", "--name-only", "-z", tag, "--", ".apm").decode().split("\0")
        files = {}
        for name in sorted(n for n in names if n):
            relative = name[len(".apm/"):]
            files[f".github/{relative}"] = digest(git("show", f"{tag}:{name}"))
        manifest["releases"][version] = {"tag": tag, "files": files}
    return manifest


def main():
    manifest = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    counts = ", ".join(f"{v}: {len(r['files'])} files" for v, r in manifest["releases"].items())
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({counts})")


if __name__ == "__main__":
    main()
