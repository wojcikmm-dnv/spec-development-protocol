#!/usr/bin/env python3
"""Build the release ZIP for the SDP package (maintainer tool, standard library only).

The ZIP is APM's own bundle (`apm pack --archive`) cleaned and extended deterministically:
bytecode caches are dropped, text files are normalized to LF so the bytes do not depend on
the checkout's line endings, the license and setup guidance are added, entries are sorted
with fixed timestamps, and a SHA-256 checksum file is written. The version comes from
`apm.yml` only; every other manifest must agree or the build stops.

    python scripts/build-release.py [--output dist] [--check]

`--check` runs the consistency checks and does not build.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$")
EXCLUDED_PARTS = {"__pycache__", ".git", ".github", ".DS_Store", "node_modules"}
EXCLUDED_SUFFIXES = (".pyc", ".pyo")
ADDED_FILES = ("LICENSE", "SETUP.md")
FIXED_TIME = (2026, 1, 1, 0, 0, 0)
HOSTILE_NAME = re.compile(r"[\x00-\x1f:*?\"<>|]|[. ]$")


class BuildError(Exception):
    pass


def normalize(data):
    """LF line endings for text; binary data (anything with a NUL byte) is left alone."""
    return data if b"\0" in data else data.replace(b"\r\n", b"\n")


def manifest_field(field, root=ROOT):
    match = re.search(rf"^{field}:[ \t]*['\"]?([^\s'\"#]+)", (root / "apm.yml").read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise BuildError(f"apm.yml has no {field}")
    return match.group(1)


def manifest_version(root=ROOT):
    return manifest_field("version", root)


def read_json(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BuildError(f"{path.name} is not a JSON object")
    return value


def consistency_problems(root=ROOT):
    """Every generated or hand-written manifest must carry the name and version declared in apm.yml."""
    problems = []
    try:
        version, name = manifest_version(root), manifest_field("name", root)
    except (BuildError, OSError) as error:
        return [str(error)]
    if not SEMVER.match(version):
        problems.append(f"apm.yml version {version!r} is not a semantic version")
    for relative in ("plugin.json", ".github/plugin/plugin.json", ".claude-plugin/plugin.json"):
        path = root / relative
        if not path.is_file():
            problems.append(f"{relative} is missing")
            continue
        manifest = read_json(path)
        if manifest.get("version") != version:
            problems.append(f"{relative} has version {manifest.get('version')!r}; apm.yml declares {version!r}")
        if manifest.get("name") != name:
            problems.append(f"{relative} has name {manifest.get('name')!r}; apm.yml declares {name!r}")
    marketplace = root / ".claude-plugin" / "marketplace.json"
    if marketplace.is_file():
        for plugin in read_json(marketplace).get("plugins", []):
            listed = plugin.get("version") if isinstance(plugin, dict) else None
            if listed not in (version, f"^{version}"):
                problems.append(f".claude-plugin/marketplace.json lists {listed!r}; apm.yml declares {version!r}")
    tools = read_json(root / "scripts" / "release-tools.json")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(tools.get("apm", ""))):
        problems.append("scripts/release-tools.json must pin an exact apm version")
    return problems


def is_excluded(name):
    parts = name.split("/")
    return any(part in EXCLUDED_PARTS for part in parts) or name.endswith(EXCLUDED_SUFFIXES)


def unsafe_name(name):
    if not name or name.startswith("/") or "\\" in name or re.match(r"^[A-Za-z]:", name):
        return True
    parts = name.rstrip("/").split("/")
    if any(part in ("", ".", "..") for part in parts):
        return True
    return any(HOSTILE_NAME.search(part) for part in parts)


def entry_problems(infos):
    """Problems with the raw archive entries, before anything is merged or flattened."""
    problems, seen = [], set()
    for info in infos:
        name = info.filename
        if unsafe_name(name):
            problems.append(f"unsafe entry name: {name!r}")
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            problems.append(f"symbolic link entry: {name}")
        if is_excluded(name):
            problems.append(f"excluded artifact shipped: {name}")
        folded = name.casefold()
        if folded in seen:
            problems.append(f"duplicate or case-colliding entry: {name!r}")
        seen.add(folded)
    return problems


def expected_entries(root=ROOT):
    """Files the bundle must contain, relative to the bundle folder, derived from the source."""
    expected = set()
    for folder in ("agents", "instructions", "skills"):
        base = root / ".apm" / folder
        for path in base.rglob("*") if base.is_dir() else []:
            relative = path.relative_to(base).as_posix()
            if path.is_file() and not is_excluded(f"{folder}/{relative}"):
                expected.add(f"{folder}/{relative}")
    prompts = root / ".apm" / "prompts"
    for path in prompts.glob("*.prompt.md") if prompts.is_dir() else []:
        expected.add(f"commands/{path.name[:-len('.prompt.md')]}.md")
    expected.add("plugin.json")
    expected.update(ADDED_FILES)
    return expected


def source_for(relative, root=ROOT):
    if relative.startswith("commands/"):
        return root / ".apm" / "prompts" / (relative[len("commands/"):-3] + ".prompt.md")
    return root / ".apm" / relative


def verify_bundle(zip_path, root=ROOT):
    """Return a list of problems with a built release ZIP; empty means it is acceptable."""
    version = manifest_version(root)
    folder = f"{manifest_field('name', root)}-{version}"
    with zipfile.ZipFile(zip_path) as archive:
        infos = archive.infolist()
        problems = entry_problems(infos)
        names = [info.filename for info in infos]
        if any(not name.startswith(folder + "/") for name in names):
            problems.append(f"entries outside {folder}/")
        present = {name[len(folder) + 1:] for name in names if name.startswith(folder + "/") and not name.endswith("/")}
        expected = expected_entries(root)
        problems += [f"missing from bundle: {missing}" for missing in sorted(expected - present)]
        problems += [f"unexpected file in bundle: {extra}" for extra in sorted(present - expected)]
        manifest = f"{folder}/plugin.json"
        if manifest in names:
            declared = json.loads(archive.read(manifest)).get("version")
            if declared != version:
                problems.append(f"bundle plugin.json has version {declared!r}; expected {version!r}")
        for relative in sorted(expected & present):
            if relative in ADDED_FILES or relative == "plugin.json":
                continue
            source = source_for(relative, root)
            if source.is_file() and archive.read(f"{folder}/{relative}") != normalize(source.read_bytes()):
                problems.append(f"content differs from source: {relative}")
    return problems


def run_apm(arguments, cwd):
    done = subprocess.run(["apm", *arguments], cwd=cwd, capture_output=True, text=True)
    if done.returncode != 0:
        raise BuildError(f"apm {' '.join(arguments)} failed ({done.returncode}): {done.stderr.strip() or done.stdout.strip()}")
    return done.stdout


def check_apm_version(root=ROOT):
    pinned = read_json(root / "scripts" / "release-tools.json")["apm"]
    try:
        output = run_apm(["--version"], root)
    except (OSError, BuildError) as error:
        raise BuildError(f"apm {pinned} is required: {error}")
    if not re.search(r"(?<![\w.])" + re.escape(pinned) + r"(?![\w.-])", output):
        raise BuildError(f"apm {pinned} is pinned in scripts/release-tools.json; found: {output.strip()}")
    return pinned


def render_setup(version, root=ROOT):
    text = (root / "scripts" / "release-assets" / "SETUP.md").read_text(encoding="utf-8")
    return text.replace("{version}", version)


def collect_entries(root, folder, pinned):
    with tempfile.TemporaryDirectory() as scratch:
        run_apm(["pack", "--archive", "--marketplace", "none", "-o", scratch], root)
        produced = sorted(Path(scratch).glob("*.zip"))
        if len(produced) != 1:
            raise BuildError(f"apm pack produced {len(produced)} archives; expected one")
        entries = {}
        with zipfile.ZipFile(produced[0]) as archive:
            infos = [info for info in archive.infolist() if not info.is_dir()]
            hostile = [p for p in entry_problems(infos) if not p.startswith("excluded artifact")]
            if hostile:
                raise BuildError("apm produced an unacceptable archive: " + "; ".join(hostile[:3]))
            for info in infos:
                if not is_excluded(info.filename):
                    entries[info.filename] = normalize(archive.read(info))
    entries[f"{folder}/LICENSE"] = normalize((root / "LICENSE").read_bytes())
    entries[f"{folder}/SETUP.md"] = normalize(render_setup(manifest_version(root), root).encode("utf-8"))
    return entries


def write_atomic(path, data):
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_bytes(data)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def build(output, root=ROOT):
    problems = consistency_problems(root)
    if problems:
        raise BuildError("; ".join(problems))
    pinned = check_apm_version(root)
    version, name = manifest_version(root), manifest_field("name", root)
    folder = f"{name}-{version}"
    target_name = f"{folder}.zip"
    if output.is_dir():
        stale = sorted(p.name for p in output.glob("*.zip") if p.name != target_name)
        if stale:
            raise BuildError(f"{output} already contains other archives ({', '.join(stale)}); remove them so the checksum file covers every archive")
    entries = collect_entries(root, folder, pinned)
    with tempfile.TemporaryDirectory() as scratch:
        built = Path(scratch) / target_name
        with zipfile.ZipFile(built, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for entry_name in sorted(entries):
                info = zipfile.ZipInfo(entry_name, FIXED_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100644 << 16)
                info.create_system = 3
                archive.writestr(info, entries[entry_name])
        problems = verify_bundle(built, root)
        if problems:
            raise BuildError("built bundle failed verification: " + "; ".join(problems[:5]))
        data = built.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    metadata = {"name": name, "version": version, "apm": pinned, "sha256": digest, "files": len(entries)}
    output.mkdir(parents=True, exist_ok=True)
    target = output / target_name
    write_atomic(target, data)
    write_atomic(output / "SHA256SUMS", f"{digest}  {target_name}\n".encode("utf-8"))
    write_atomic(output / "release-metadata.json", (json.dumps(metadata, indent=2) + "\n").encode("utf-8"))
    return target, digest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", default="dist")
    parser.add_argument("--check", action="store_true", help="only run the consistency checks")
    arguments = parser.parse_args(argv)
    try:
        if arguments.check:
            problems = consistency_problems()
            for problem in problems:
                print(f"FAIL: {problem}", file=sys.stderr)
            if not problems:
                print("PASS: manifest versions agree")
            return 1 if problems else 0
        target, digest = build(Path(arguments.output))
    except (BuildError, OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"FAIL: {type(error).__name__ if not isinstance(error, BuildError) else 'build'}: {error}", file=sys.stderr)
        return 1
    print(f"Built {target} (sha256 {digest})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
