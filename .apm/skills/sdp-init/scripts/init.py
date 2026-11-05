#!/usr/bin/env python3
"""Initialize a repository for SDP without overwriting anything (standard library only).

Creates only what is missing: the project policy file and the spec folder. It previews
by default; nothing is written without --apply. Existing files are never changed.
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

EXIT_OK, EXIT_CONFLICT, EXIT_USAGE = 0, 1, 2
TECH_RELATIVE = ".github/TECH.md"
SPEC_RELATIVE = "spec"
PACKAGE_TEMPLATE_ROOT = Path(__file__).resolve().parent.parent.parent / "sdp-templates" / "assets"
LEGACY_MARKERS = (
    (".github/sdp-version", "file"),
    (".github/agents/sdp.orchestrator.agent.md", "file"),
    (".github/agents/sdp.developer.agent.md", "file"),
    (".github/instructions/sdlc-process.instructions.md", "file"),
    (".github/prompts/deliver.prompt.md", "file"),
)
MAX_TEMPLATE_BYTES = 1024 * 1024


class InitError(Exception):
    def __init__(self, code, error, message):
        super().__init__(message)
        self.code, self.error, self.message = code, error, message


def inside(repo, path):
    """True when path resolves to repo or a location below it."""
    resolved = Path(os.path.realpath(path))
    return resolved == repo or repo in resolved.parents


def find_template(repo, name, explicit_root):
    """Templates come from the installed package or an explicit directory, never from the
    repository being initialized: a cloned repo is untrusted and the result is later read
    by agents as project instructions."""
    candidates = []
    if explicit_root:
        candidates.append(("--template-root", Path(explicit_root)))
    candidates.append(("package", PACKAGE_TEMPLATE_ROOT))
    for source, root in candidates:
        path = root / name
        if path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_TEMPLATE_BYTES:
            return source, path
    raise InitError(EXIT_CONFLICT, "template_missing", f"Template {name} was not found; install the SDP package first")


def is_link(path):
    """Symbolic links, and on Windows also junctions, which is_symlink() does not report."""
    if path.is_symlink():
        return True
    junction = getattr(os.path, "isjunction", None)
    return bool(junction and junction(path))


def inspect_target(repo, relative, kind):
    """Classify a destination as missing, present, or conflicting without touching it."""
    path = repo / relative
    for parent in [path, *path.parents]:
        if parent == repo:
            break
        if is_link(parent):
            return "conflict", f"{parent.relative_to(repo).as_posix()} is a symbolic link or junction"
    existing = path
    while existing != repo and not (existing.exists() or existing.is_symlink()):
        existing = existing.parent
    if not inside(repo, existing):
        return "conflict", f"{existing.relative_to(repo).as_posix() if existing != repo else relative} resolves outside the repository"
    if not path.exists() and not path.is_symlink():
        for parent in path.parents:
            if parent == repo:
                break
            if parent.exists() and not parent.is_dir():
                return "conflict", f"{parent.relative_to(repo).as_posix()} exists but is not a directory"
        return "missing", None
    if kind == "file" and not path.is_file():
        return "conflict", f"{relative} exists but is not a file"
    if kind == "dir" and not path.is_dir():
        return "conflict", f"{relative} exists but is not a directory"
    return "present", None


def legacy_findings(repo):
    """Return (installer_marker, sdp_files, legacy_state).

    Only `.github/sdp-version` is unique to the old install scripts. The same agent and
    instruction files are also what APM deploys, so they alone prove nothing."""
    marker = (repo / ".github/sdp-version").is_file()
    sdp_files = [relative for relative, _ in LEGACY_MARKERS
                 if relative != ".github/sdp-version" and (repo / relative).is_file()]
    state = []
    active = repo / SPEC_RELATIVE / "ACTIVE.md"
    if active.is_file() and not is_link(active):
        text = active.read_text(encoding="utf-8", errors="replace")
        if "feature_status:" in text or "final_status:" in text or "current_story:" in text:
            state.append("spec/ACTIVE.md uses the legacy shared-state fields")
    return marker, sdp_files, state


def plan(repo, explicit_root):
    repo = Path(os.path.realpath(repo))
    if not repo.is_dir():
        raise InitError(EXIT_USAGE, "repo_missing", f"Not a directory: {repo}")
    actions, preserved, conflicts, warnings = [], [], [], []
    if not (repo / ".git").exists():
        warnings.append("This is not a Git repository root; the validator needs Git to fingerprint candidates")
    source, template = find_template(repo, "TECH.md", explicit_root)
    for relative, kind in ((TECH_RELATIVE, "file"), (SPEC_RELATIVE, "dir")):
        state, detail = inspect_target(repo, relative, kind)
        if state == "conflict":
            conflicts.append({"path": relative, "reason": detail})
        elif state == "present":
            preserved.append(relative)
        elif kind == "file":
            actions.append({"action": "create-file", "path": relative, "from": source,
                            "reason": "project policy file; fill in your stack and commands"})
        else:
            actions.append({"action": "create-dir", "path": relative,
                            "reason": "holds feature folders and delivery packages"})
    marker, sdp_files, state = legacy_findings(repo)
    legacy = []
    if marker:
        legacy = [".github/sdp-version", *sdp_files]
        warnings.append("Files copied by the earlier install script were found (.github/sdp-version). They may "
                        "duplicate or conflict with the installed package. Do not run both; review them "
                        "with the sdp-migrate skill. Nothing was changed.")
    elif sdp_files and not (repo / "apm.lock.yaml").is_file():
        legacy = list(sdp_files)
        warnings.append("SDP agent or instruction files exist under .github but there is no APM lockfile or "
                        "installer marker. If they are plain copies they may duplicate the installed package: "
                        + ", ".join(sdp_files))
    if state:
        legacy.extend(state)
        warnings.append("Delivery state uses an earlier layout: " + "; ".join(state))
    return repo, template, {"actions": actions, "preserved": preserved, "conflicts": conflicts,
                            "warnings": warnings, "legacy_files": legacy, "template_source": source}


def make_parents(repo, destination, created):
    missing = []
    for parent in destination.parents:
        if parent == repo or parent.exists():
            break
        missing.append(parent)
    for parent in reversed(missing):
        parent.mkdir(exist_ok=False)
        created.append(parent)


def write_new(destination, content):
    """Create destination without ever replacing an existing file."""
    handle, temporary = tempfile.mkstemp(dir=destination.parent, prefix=".sdp-init-", suffix=".tmp")
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError:
            raise
        except OSError:
            descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(content)
            except BaseException:
                os.unlink(destination)
                raise
    finally:
        os.unlink(temporary)


def apply(repo, template, report):
    """Create the missing items; undo everything created if any step fails."""
    created = []
    try:
        for action in report["actions"]:
            state, detail = inspect_target(repo, action["path"], "dir" if action["action"] == "create-dir" else "file")
            if state != "missing":
                raise InitError(EXIT_CONFLICT, "changed_since_preview",
                                f"{action['path']} is no longer missing ({detail or state}); nothing was written")
            destination = repo / action["path"]
            make_parents(repo, destination, created)
            if action["action"] == "create-dir":
                destination.mkdir(exist_ok=False)
                created.append(destination)
                continue
            write_new(destination, template.read_bytes())
            created.append(destination)
    except BaseException:
        leftovers = []
        for path in reversed(created):
            try:
                path.unlink() if path.is_file() else path.rmdir()
            except OSError:
                leftovers.append(str(path))
        if leftovers:
            report["rollback_leftovers"] = leftovers
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--apply", action="store_true", help="create the missing items (default: preview only)")
    parser.add_argument("--template-root", default=None, help="directory containing TECH.md (advanced)")
    arguments = parser.parse_args(argv)
    report = {}
    try:
        repo, template, report = plan(arguments.repo, arguments.template_root)
        report["mode"] = "apply" if arguments.apply else "preview"
        if report["conflicts"]:
            report["ok"] = False
            print(json.dumps(report, indent=2))
            return EXIT_CONFLICT
        if arguments.apply:
            apply(repo, template, report)
        report["ok"] = True
        print(json.dumps(report, indent=2))
        return EXIT_OK
    except InitError as error:
        print(json.dumps({"ok": False, "error": error.error, "message": error.message}))
        return error.code
    except OSError as error:
        leftovers = report.get("rollback_leftovers")
        note = "any items created were removed" if not leftovers else f"could not remove: {', '.join(leftovers)}"
        print(json.dumps({"ok": False, "error": "write_failed", "message": f"{error}; {note}"}))
        return EXIT_CONFLICT


if __name__ == "__main__":
    sys.exit(main())
