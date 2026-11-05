#!/usr/bin/env python3
"""Migrate an SDP 0.5.3 or 0.5.4 project to the schema 4 layout (standard library only).

Previews by default. Applying makes a backup and a journal first, validates the result, and
restores everything if anything fails. It never fabricates an approval or acceptance: records
that cannot be verified are restarted as planned or stop the migration for a human decision.
"""

import argparse
import contextlib
import datetime
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

TOOL = "sdp-migrate 1"
SDP_PATH = Path(__file__).resolve().parent.parent.parent / "sdp-core" / "scripts" / "sdp.py"
MANIFEST_PATH = Path(__file__).resolve().parent.parent / "manifests" / "legacy-files.json"
BACKUP_ROOT = ".sdp-backup"
OPEN_STATUSES = ("planned", "delivering", "blocked", "awaiting-acceptance", "changes-requested")
TERMINAL_STATUSES = ("accepted", "rejected")
KNOWN_STATUSES = OPEN_STATUSES + TERMINAL_STATUSES
LEGACY_ACTIVE_KEYS = ("feature_status", "delivery_status", "pending_audit")
UNSUPPORTED_ACTIVE_KEYS = ("current_story", "final_status", "status")
POINTER_KEYS = ("slug", "title", "current_gate", "current_delivery")
MAX_BYTES = 5 * 1024 * 1024
EXIT_OK, EXIT_BLOCKED, EXIT_USAGE, EXIT_CONFLICT = 0, 1, 2, 3


class MigrationError(Exception):
    def __init__(self, code, error, message):
        super().__init__(message)
        self.code, self.error, self.message = code, error, message


def load_core():
    if not SDP_PATH.is_file():
        raise MigrationError(EXIT_USAGE, "core_missing", "The sdp-core skill must be installed next to sdp-migrate")
    spec = importlib.util.spec_from_file_location("sdp_core", SDP_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = None
MAPPED_USED = set()


def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def lf_sha(data):
    return sha(data.replace(b"\r\n", b"\n"))


def is_link(path):
    if path.is_symlink():
        return True
    junction = getattr(os.path, "isjunction", None)
    return bool(junction and junction(path))


def checked(repo, relative):
    """Return repo/relative after refusing links, junctions, and escapes along the whole path."""
    path = repo.joinpath(*relative.split("/"))
    if any(part in ("", ".", "..") for part in relative.split("/")):
        raise MigrationError(EXIT_CONFLICT, "path_escape", f"Unsafe path: {relative}")
    for parent in [path, *path.parents]:
        if parent == repo:
            break
        if is_link(parent):
            raise MigrationError(EXIT_CONFLICT, "path_escape", f"{relative} passes through a link or junction")
    existing = path
    while existing != repo and not (existing.exists() or existing.is_symlink()):
        existing = existing.parent
    resolved = Path(os.path.realpath(existing))
    if resolved != repo and repo not in resolved.parents:
        raise MigrationError(EXIT_CONFLICT, "path_escape", f"{relative} resolves outside the repository")
    return path


def read_bytes(path):
    if path.stat().st_size > MAX_BYTES:
        raise MigrationError(EXIT_BLOCKED, "file_too_large", f"{path.name} is larger than {MAX_BYTES} bytes")
    return path.read_bytes()


def read_text(path):
    """Strict UTF-8: text that would be rewritten must not be silently altered."""
    try:
        return read_bytes(path).decode("utf-8")
    except UnicodeDecodeError:
        raise MigrationError(EXIT_BLOCKED, "not_utf8", f"{path.name} is not valid UTF-8; convert it before migrating")


# --- analysis --------------------------------------------------------------

def parse_active(repo):
    path = checked(repo, "spec/ACTIVE.md")
    if not path.is_file():
        return None
    text = read_text(path).replace("\r\n", "\n")
    try:
        front, body = core.split_plan(text)
        meta = core.parse_frontmatter(front)
    except core.ProtocolError as error:
        return {"error": error.message, "meta": {}, "body": "", "text": text}
    return {"meta": meta, "body": body.strip(), "text": text}


def package_id_for(slug, record):
    """Id for a feature-level (flat) package; nested packages are identified by their folder name."""
    candidate = record.get("delivery_id") if isinstance(record, dict) else None
    if isinstance(candidate, str) and core.TOKEN_RE.match(candidate) and not core.is_placeholder(candidate):
        return candidate
    return f"{slug}-DP-1"


def analyze(repo, status_map):
    spec_dir = checked(repo, "spec")
    active = parse_active(repo)
    blockers, ambiguities, warnings, packages = [], [], [], []
    if active and "error" in active:
        blockers.append({"error": "active_unreadable", "message": f"spec/ACTIVE.md: {active['error']}"})
        active = None
    if active and any(key in active["meta"] for key in UNSUPPORTED_ACTIVE_KEYS):
        blockers.append({"error": "unsupported_legacy_version",
                         "message": "spec/ACTIVE.md uses fields from SDP 0.5.2 or earlier (" +
                                    ", ".join(k for k in UNSUPPORTED_ACTIVE_KEYS if k in active["meta"]) +
                                    "). Upgrade stepwise to 0.5.3 first; this tool supports 0.5.3 and 0.5.4."})
    if not spec_dir.is_dir():
        return {"layout": "none", "packages": [], "blockers": blockers, "ambiguities": ambiguities,
                "warnings": warnings, "active": active}
    for slug_dir in sorted(p for p in spec_dir.iterdir() if p.is_dir() and core.TOKEN_RE.match(p.name)):
        slug = slug_dir.name
        if is_link(slug_dir):
            blockers.append({"error": "path_escape", "message": f"spec/{slug} is a link"})
            continue
        flat = [name for name in ("PLAN.md", "DELIVERY-RUN.json", "HISTORY.md") if (slug_dir / name).is_file()]
        if any(name in flat for name in ("PLAN.md", "DELIVERY-RUN.json")):
            packages.append(analyze_package(repo, slug, slug_dir, True, active, status_map, blockers, ambiguities))
        deliveries = slug_dir / "deliveries"
        if deliveries.is_dir():
            for folder in sorted(p for p in deliveries.iterdir() if p.is_dir()):
                if not core.TOKEN_RE.match(folder.name):
                    continue
                if (folder / "PLAN.md").is_file() or (folder / "DELIVERY-RUN.json").is_file():
                    packages.append(analyze_package(repo, slug, folder, False, active, status_map, blockers, ambiguities))
    packages = [p for p in packages if p]
    layout = "none"
    schemas = {p["source_schema"] for p in packages}
    if any(s > 4 for s in schemas if isinstance(s, int)):
        blockers.append({"error": "unknown_newer_schema",
                         "message": "A run record uses a newer schema than this tool understands; upgrade SDP instead"})
    if packages:
        layout = "current" if schemas == {4} else "legacy"
    legacy_active = bool(active and any(k in active["meta"] for k in LEGACY_ACTIVE_KEYS))
    if layout == "none" and legacy_active:
        layout = "legacy"
    return {"layout": layout, "packages": packages, "blockers": blockers, "ambiguities": ambiguities,
            "warnings": warnings, "active": active, "legacy_active": legacy_active}


def analyze_package(repo, slug, folder, flat, active, status_map, blockers, ambiguities):
    relative = folder.relative_to(repo).as_posix()
    plan_path, record_path = folder / "PLAN.md", folder / "DELIVERY-RUN.json"
    for path in (plan_path, record_path, folder / "HISTORY.md"):
        if path.exists() and is_link(path):
            blockers.append({"error": "path_escape", "message": f"{relative}/{path.name} is a link"})
            return None
    record, original = None, None
    if record_path.is_file():
        original = read_bytes(record_path)
        try:
            record = json.loads(original.decode("utf-8"))
        except (ValueError, UnicodeDecodeError, RecursionError):
            blockers.append({"error": "record_unreadable", "message": f"{relative}/DELIVERY-RUN.json is not valid JSON"})
            return None
        if not isinstance(record, dict):
            blockers.append({"error": "record_unreadable", "message": f"{relative}/DELIVERY-RUN.json is not an object"})
            return None
    version = record.get("schema_version") if record else None
    package_id = package_id_for(slug, record) if flat else folder.name
    if version is not None and not isinstance(version, int):
        blockers.append({"error": "unsupported_legacy_version", "message": f"{relative}: schema_version is not a number"})
        return None
    if version == 4:
        return {"id": folder.name, "slug": slug, "source_schema": 4, "folder": relative, "flat": flat, "status": record.get("delivery_status")}
    if version is not None and version > 4:
        return {"id": folder.name, "slug": slug, "source_schema": version, "folder": relative, "flat": flat, "status": None}
    if version is not None and version not in (2, 3):
        blockers.append({"error": "unsupported_legacy_version",
                         "message": f"{relative}: run record schema {version} is older than 0.5.3 and is not supported"})
        return None
    if flat and version == 3:
        ambiguities.append({"id": package_id, "message": f"{relative} has a schema 3 record at the feature root; move it manually"})
        return None
    if not flat and version == 2:
        ambiguities.append({"id": package_id, "message": f"{relative} has a schema 2 record inside deliveries/; unexpected layout"})
        return None
    status = None
    if record and version == 3:
        status = record.get("delivery_status")
    elif record and version == 2:
        legacy_active = active["meta"] if active else {}
        status = legacy_active.get("delivery_status") if legacy_active.get("slug") == slug else None
    elif not record:
        status = "planned"
    override = status_map.get(package_id) or status_map.get(slug if flat else package_id)
    for key in (package_id, slug if flat else package_id):
        if key in status_map:
            MAPPED_USED.add(key)
    if override:
        status = override
    if status == "not-planned":
        status = "planned"
    if status not in KNOWN_STATUSES:
        ambiguities.append({"id": package_id, "message": f"{relative}: status {status!r} cannot be determined; "
                                                        f"map it with --status-map {package_id}=<one of {', '.join(KNOWN_STATUSES)}>"})
        return None
    return {"id": package_id, "slug": slug, "source_schema": version if version else 0, "folder": relative, "flat": flat,
            "status": status, "record": record, "original": original, "has_plan": plan_path.is_file(),
            "has_history": (folder / "HISTORY.md").is_file()}


# --- planning --------------------------------------------------------------

def legacy_to_record(package, active_meta):
    record = package.get("record") or {}
    notes = []
    legacy_profile = record.get("profile")
    profile = legacy_profile if legacy_profile in core.PROFILES else "Balanced"
    if legacy_profile not in core.PROFILES:
        notes.append("profile was not a valid SDP profile; set to Balanced")
    policy = {"profile_floor": "Lean", "epic_security_policy": "risk-based", "mandatory_stages": []}
    new = core.new_record(package["id"], "feature", profile, policy)
    run_id = record.get("run_id")
    if isinstance(run_id, str) and run_id and not core.is_placeholder(run_id) and "<" not in run_id:
        new["run_id"] = run_id
    new["state_revision"] = 1
    if isinstance(record.get("branch"), str):
        new["branch"] = record["branch"]
    legacy_audits = record.get("pending_audit")
    if legacy_audits is not None and not (isinstance(legacy_audits, list) and all(isinstance(a, str) for a in legacy_audits)):
        return None, ["pending_audit is not a list of strings"]
    audits = list(legacy_audits or [])
    if active_meta and active_meta.get("slug") == package["slug"] and isinstance(active_meta.get("pending_audit"), list):
        audits += [a for a in active_meta["pending_audit"] if isinstance(a, str) and a not in audits]
    new["pending_audit"] = audits
    status = package["status"]
    if status in OPEN_STATUSES:
        new["delivery_status"] = "planned"
        if status != "planned":
            notes.append(f"was {status}; restarted as planned because candidate and plan binding cannot be verified")
    else:
        acceptance = record.get("acceptance") if isinstance(record.get("acceptance"), dict) else {}
        decided_by, decided_at = acceptance.get("decided_by"), acceptance.get("decided_at")
        if acceptance.get("decision") != status or core.not_a_human(decided_by if isinstance(decided_by, str) else ""):
            return None, [f"{status} without a recorded human decision"]
        new["delivery_status"] = status
        new["acceptance"] = {
            "decision": status,
            "decided_by": decided_by if isinstance(decided_by, str) else None,
            "decided_at": decided_at if isinstance(decided_at, str) else None,
            "feedback": acceptance.get("feedback") if isinstance(acceptance.get("feedback"), str) else None,
        }
    legacy_version = package["source_schema"] if package["source_schema"] in (2, 3) else 3
    new["migrated_from"] = {"schema_version": legacy_version, "tool": TOOL, "at": now(),
                            "original_sha256": sha(package["original"]) if package.get("original") else sha(b""),
                            "notes": notes}
    return new, notes


def history_note(package, notes, voided, active_body=""):
    lines = ["", "## Migrated to schema 4", "",
             f"- Source: run record schema {package['source_schema'] or 'none'} (status {package['status']}).",
             "- The original record is preserved next to this file as `DELIVERY-RUN.legacy.json`."]
    lines += [f"- {note}." for note in notes]
    if voided:
        lines.append(f"- {voided}")
    if active_body:
        lines += ["", "Notes that were in the body of the earlier `spec/ACTIVE.md`:", "",
                  *[f"> {line}" if line else ">" for line in active_body.split("\n")]]
    lines.append("")
    return "\n".join(lines)


def plan_operations(repo, analysis, options):
    ops, summaries, ambiguities = [], [], list(analysis["ambiguities"])
    active = analysis["active"]
    active_meta = active["meta"] if active else None
    migrated_ids = {}
    for package in analysis["packages"]:
        if package["source_schema"] in (4,) or (isinstance(package["source_schema"], int) and package["source_schema"] > 4):
            continue
        new, notes = legacy_to_record(package, active_meta)
        if new is None:
            ambiguities.append({"id": package["id"], "message": f"{package['folder']}: {notes[0]}; fix the legacy record or restart the package, then rerun"})
            continue
        problems = core.validate_record(new)
        if problems:
            raise MigrationError(EXIT_BLOCKED, "internal_invalid", f"{package['id']}: migrated record failed validation: " + "; ".join(problems[:3]))
        target = f"spec/{package['slug']}/deliveries/{package['id']}"
        source = package["folder"]
        migrated_ids[package["slug"]] = package["id"]
        plan_text = None
        voided = None
        if package["has_plan"]:
            plan_text = read_text(checked(repo, f"{source}/PLAN.md"))
            try:
                parsed = core.parse_plan(plan_text)
            except core.ProtocolError as error:
                ambiguities.append({"id": package["id"], "message": f"{source}/PLAN.md: {error.message}"})
                continue
            if not isinstance(parsed.get("status"), str):
                ambiguities.append({"id": package["id"], "message": f"{source}/PLAN.md: status is not a string"})
                continue
            if package["status"] in OPEN_STATUSES and parsed["status"].strip() == "approved":
                voided = (f"The plan approval by {parsed['approved_by']} at {parsed['approved_at']} was voided because the "
                          "approved plan cannot be verified; a named human must approve it again.")
                plan_text = core.set_frontmatter(plan_text, {"status": "draft", "approved_by": "pending", "approved_at": "pending"})
        legacy_json = f"{target}/DELIVERY-RUN.legacy.json"
        history_path = f"{source}/HISTORY.md"
        history_text = read_text(checked(repo, history_path)) if package["has_history"] else "# History\n"
        history_text = history_text.rstrip("\n") + "\n" + history_note(
            package, notes, voided,
            active["body"] if active and active_meta and active_meta.get("slug") == package["slug"] else "")
        if package["flat"]:
            if (repo / "spec" / package["slug"] / "deliveries" / package["id"]).exists():
                ambiguities.append({"id": package["id"], "message": f"{target} already exists; cannot move the feature-level package into it"})
                continue
            if package["has_plan"]:
                ops.append({"op": "write", "path": f"{target}/PLAN.md", "text": plan_text, "mode": "create"})
                ops.append({"op": "remove", "path": f"{source}/PLAN.md"})
            if package.get("original") is not None:
                ops.append({"op": "write", "path": legacy_json, "bytes_b64": package["original"].hex(), "mode": "create"})
                ops.append({"op": "remove", "path": f"{source}/DELIVERY-RUN.json"})
            ops.append({"op": "write", "path": f"{target}/DELIVERY-RUN.json", "text": json.dumps(new, indent=2) + "\n", "mode": "create"})
            ops.append({"op": "write", "path": f"{target}/HISTORY.md", "text": history_text, "mode": "create"})
            if package["has_history"]:
                ops.append({"op": "remove", "path": history_path})
        else:
            if (repo / legacy_json).exists():
                ambiguities.append({"id": package["id"], "message": f"{legacy_json} already exists; refusing to overwrite preserved evidence"})
                continue
            if package.get("original") is not None:
                ops.append({"op": "write", "path": legacy_json, "bytes_b64": package["original"].hex(), "mode": "create"})
            ops.append({"op": "write", "path": f"{target}/DELIVERY-RUN.json", "text": json.dumps(new, indent=2) + "\n", "mode": "replace"})
            if voided:
                ops.append({"op": "write", "path": f"{target}/PLAN.md", "text": plan_text, "mode": "replace"})
            ops.append({"op": "write", "path": f"{target}/HISTORY.md", "text": history_text,
                        "mode": "replace" if package["has_history"] else "create"})
        summaries.append({"id": package["id"], "from": source, "to": target, "source_schema": package["source_schema"],
                          "status": package["status"], "becomes": new["delivery_status"], "approval_voided": bool(voided)})
    if analysis.get("legacy_active") and active_meta is not None:
        pointer = {key: active_meta[key] for key in POINTER_KEYS if key in active_meta}
        slug = pointer.get("slug")
        audits = active_meta.get("pending_audit")
        has_content = bool(active["body"]) or bool(audits)
        if has_content and (slug not in migrated_ids or (audits is not None and not isinstance(audits, list))):
            ambiguities.append({"id": str(slug), "message": "spec/ACTIVE.md carries pending_audit or notes that no migrated package can hold; "
                                                          "move them into the right package or feature document, then rerun"})
            return ops, summaries, ambiguities
        if slug in migrated_ids and pointer.get("current_delivery") in (None, "n/a", ""):
            pointer["current_delivery"] = migrated_ids[slug]
        for key in POINTER_KEYS:
            pointer.setdefault(key, "n/a")
        text = "---\n" + "\n".join(f"{key}: {pointer[key]}" for key in POINTER_KEYS) + "\n---\n"
        ops.append({"op": "write", "path": "spec/ACTIVE.md", "text": text, "mode": "replace"})
    return ops, summaries, ambiguities


def classify_legacy_files(repo, manifest):
    """Which copied files are provably SDP-owned, customized, or managed by APM."""
    lock = repo / "apm.lock.yaml"
    lock_text = read_bytes(lock).decode("utf-8", errors="replace") if lock.is_file() else ""
    marker = repo / ".github" / "sdp-version"
    marker_present = marker.is_file()
    known = {}
    for release in manifest["releases"].values():
        for path, digest in release["files"].items():
            known.setdefault(path, set()).add(digest)
    result = {"owned": [], "customized": [], "apm_managed": []}
    if not marker_present:
        return result, marker_present
    for path in sorted(known):
        target = repo.joinpath(*path.split("/"))
        if not target.is_file() or is_link(target):
            continue
        if path in lock_text:
            result["apm_managed"].append(path)
        elif lf_sha(read_bytes(target)) in known[path]:
            result["owned"].append(path)
        else:
            result["customized"].append(path)
    text = marker.read_text(encoding="utf-8", errors="replace")
    if re.fullmatch(r"[\w.@-]{1,80}\s*", text) and ".github/sdp-version" not in lock_text:
        result["owned"].append(".github/sdp-version")
    return result, marker_present


def removal_operations(repo, classification):
    ops = [{"op": "remove", "path": path} for path in classification["owned"]]
    candidates = set()
    for path in classification["owned"]:
        parts = path.split("/")[:-1]
        for depth in range(len(parts), 1, -1):
            candidates.add("/".join(parts[:depth]))
    for candidate in sorted(candidates, key=lambda p: (-p.count("/"), p)):
        if candidate.startswith(".github/"):
            ops.append({"op": "rmdir_if_empty", "path": candidate})
    return ops


def make_plan(repo, options):
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    analysis = analyze(repo, options["status_map"])
    ops, summaries, ambiguities = plan_operations(repo, analysis, options)
    classification, marker = classify_legacy_files(repo, manifest)
    warnings = list(analysis["warnings"])
    removal = []
    if options["remove_legacy_files"]:
        if not options["confirm_replacement"]:
            analysis["blockers"].append({"error": "confirmation_required",
                                         "message": "--remove-legacy-files needs --confirm-replacement-installed: confirm the SDP package is installed and loads before removing copied files"})
        elif not marker:
            analysis["blockers"].append({"error": "no_installer_marker",
                                         "message": "No .github/sdp-version marker was found, so copied files cannot be told apart from APM-managed ones; nothing will be removed"})
        else:
            removal = removal_operations(repo, classification)
    if classification["customized"]:
        warnings.append("Customized copies are kept: " + ", ".join(classification["customized"]))
    if classification["apm_managed"]:
        warnings.append("APM-managed files are kept: " + ", ".join(classification["apm_managed"][:5]) + (" ..." if len(classification["apm_managed"]) > 5 else ""))
    all_ops = ops + removal
    for op in all_ops:
        checked(repo, op["path"])
    report = {"layout": analysis["layout"], "packages": summaries, "ambiguities": ambiguities,
              "blockers": analysis["blockers"], "warnings": warnings,
              "legacy_files": {k: v for k, v in classification.items()},
              "operations": [{"op": o["op"], "path": o["path"]} for o in all_ops]}
    return report, all_ops


# --- applying, journaling, restoring --------------------------------------

def backup_dir_for(repo):
    checked(repo, BACKUP_ROOT)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return repo / BACKUP_ROOT / stamp


def replace_with_retry(source, destination):
    # Windows can briefly deny a rename while an indexer or scanner holds the new file.
    for attempt in range(8):
        try:
            os.replace(source, destination)
            return
        except PermissionError:
            if attempt == 7:
                raise
            time.sleep(0.05 * (attempt + 1))


def write_json_atomic(path, data):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=1), encoding="utf-8", newline="\n")
    with open(temporary, "r+b") as handle:
        os.fsync(handle.fileno())
    replace_with_retry(temporary, path)


def op_bytes(op):
    if "bytes_b64" in op:
        return bytes.fromhex(op["bytes_b64"])
    return op["text"].encode("utf-8")


def incomplete_journals(repo):
    root = repo / BACKUP_ROOT
    found = []
    if root.is_dir() and not is_link(root):
        for journal in sorted(root.glob("*/journal.json")):
            try:
                data = json.loads(journal.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                found.append(journal.parent)
                continue
            if not data.get("complete") and not data.get("restored"):
                found.append(journal.parent)
    return found


def apply_plan(repo, ops, records_to_check):
    pending = incomplete_journals(repo)
    if pending:
        raise MigrationError(EXIT_CONFLICT, "incomplete_migration",
                             "An earlier migration did not finish: run `restore --backup " + pending[0].relative_to(repo).as_posix() + "`")
    for op in ops:
        checked(repo, op["path"])
        if op["op"] == "write" and op["mode"] == "create" and repo.joinpath(*op["path"].split("/")).exists():
            raise MigrationError(EXIT_CONFLICT, "exists", f"{op['path']} already exists; nothing was changed")
    backup = backup_dir_for(repo)
    files = backup / "files"
    files.mkdir(parents=True)
    journal_path = backup / "journal.json"
    entries = []
    for op in ops:
        target = repo.joinpath(*op["path"].split("/"))
        entry = {"op": op["op"], "path": op["path"], "existed": target.is_file(), "done": False}
        if op["op"] == "remove" and not target.is_file():
            continue
        if target.is_file():
            data = read_bytes(target)
            destination = files.joinpath(*op["path"].split("/"))
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            entry["backup_sha256"] = sha(data)
        if op["op"] == "write":
            entry["written_sha256"] = sha(op_bytes(op))
        entries.append(entry)
    journal = {"version": 1, "tool": TOOL, "started": now(), "complete": False, "restored": False,
               "operations": entries, "created_dirs": []}
    write_json_atomic(journal_path, journal)
    todo = [op for op in ops if not (op["op"] == "remove" and not repo.joinpath(*op["path"].split("/")).is_file())]
    try:
        for op, entry in zip(todo, entries):
            target = repo.joinpath(*op["path"].split("/"))
            entry["started"] = True
            write_json_atomic(journal_path, journal)
            if op["op"] == "write":
                missing = []
                for parent in target.parents:
                    if parent == repo or parent.exists():
                        break
                    missing.append(parent)
                for parent in reversed(missing):
                    journal["created_dirs"].append(parent.relative_to(repo).as_posix())
                    write_json_atomic(journal_path, journal)
                    parent.mkdir()
                temporary = target.with_name(target.name + ".sdp-tmp")
                try:
                    temporary.write_bytes(op_bytes(op))
                    with open(temporary, "r+b") as handle:
                        os.fsync(handle.fileno())
                    replace_with_retry(temporary, target)
                except BaseException:
                    with contextlib.suppress(OSError):
                        temporary.unlink()
                    raise
            elif op["op"] == "remove":
                target.unlink()
            elif op["op"] == "rmdir_if_empty":
                try:
                    target.rmdir()
                    entry["removed_dir"] = True
                except OSError:
                    pass
            entry["done"] = True
            write_json_atomic(journal_path, journal)
        problems = verify_records(repo, records_to_check)
        if problems:
            raise MigrationError(EXIT_BLOCKED, "validation_failed", "; ".join(problems[:3]))
    except BaseException as error:
        restored = restore_backup(repo, backup)
        if isinstance(error, MigrationError):
            raise MigrationError(error.code, error.error, f"{error.message}; everything was restored ({restored} items)")
        raise MigrationError(EXIT_CONFLICT, "apply_failed", f"{error}; everything was restored ({restored} items)")
    journal["complete"] = True
    write_json_atomic(journal_path, journal)
    return backup


def verify_records(repo, records):
    problems = []
    for relative in records:
        path = repo.joinpath(*relative.split("/"))
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            problems.append(f"{relative}: {error}")
            continue
        problems += [f"{relative}: {item}" for item in core.validate_record(record)]
    return problems


def restore_backup(repo, backup):
    journal_path = backup / "journal.json"
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    for entry in journal["operations"]:
        checked(repo, entry["path"])
    for directory in journal.get("created_dirs", []):
        checked(repo, directory)
    restored = 0
    conflicts = []
    for entry in reversed(journal["operations"]):
        if not entry.get("started"):
            continue
        target = repo.joinpath(*entry["path"].split("/"))
        stray = target.with_name(target.name + ".sdp-tmp")
        if stray.is_file():
            stray.unlink()
        current = sha(target.read_bytes()) if target.is_file() else None
        if entry["op"] == "write" and not entry["existed"]:
            if current is None:
                continue
            if current == entry.get("written_sha256"):
                target.unlink()
                restored += 1
            else:
                conflicts.append(entry["path"])
        elif entry["op"] in ("write", "remove") and entry["existed"]:
            source = backup / "files" / Path(*entry["path"].split("/"))
            if not source.is_file() or sha(source.read_bytes()) != entry.get("backup_sha256"):
                conflicts.append(entry["path"] + " (backup missing or altered)")
                continue
            if current == entry.get("backup_sha256"):
                continue
            if current is not None and current != entry.get("written_sha256"):
                conflicts.append(entry["path"])
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            restored += 1
        elif entry["op"] == "rmdir_if_empty" and entry.get("removed_dir"):
            target.mkdir(parents=True, exist_ok=True)
    for directory in reversed(journal.get("created_dirs", [])):
        try:
            repo.joinpath(*directory.split("/")).rmdir()
        except OSError:
            pass
    if conflicts:
        raise MigrationError(EXIT_CONFLICT, "restore_conflict",
                             "Some files changed since the migration and were left alone: " + ", ".join(conflicts) +
                             ". Move or revert those files, then run restore again; every other file was already restored")
    journal["restored"] = True
    write_json_atomic(journal_path, journal)
    return restored


# --- command line -----------------------------------------------------------

def parse_status_map(values):
    mapping = {}
    for item in values:
        key, _, status = item.partition("=")
        if not (core.TOKEN_RE.match(key) and status in KNOWN_STATUSES):
            raise MigrationError(EXIT_USAGE, "usage", f"--status-map expects <id>=<{'|'.join(KNOWN_STATUSES)}>, got {item!r}")
        mapping[key] = status
    return mapping


def main(argv=None):
    global core
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preview", "apply"):
        sub = commands.add_parser(name)
        sub.add_argument("--status-map", action="append", default=[], help="<package id or slug>=<status> for an ambiguous status")
        sub.add_argument("--remove-legacy-files", action="store_true", help="move verified copied SDP files into the backup")
        sub.add_argument("--confirm-replacement-installed", action="store_true")
    commands.add_parser("status")
    restore = commands.add_parser("restore")
    restore.add_argument("--backup", required=True, help="backup folder under .sdp-backup")
    arguments = parser.parse_args(argv)
    try:
        core = load_core()
        repo = Path(os.path.realpath(arguments.repo))
        if not repo.is_dir():
            raise MigrationError(EXIT_USAGE, "repo_missing", f"Not a directory: {repo}")
        if arguments.command == "status":
            pending = incomplete_journals(repo)
            print(json.dumps({"ok": True, "incomplete": [p.relative_to(repo).as_posix() for p in pending]}, indent=2))
            return EXIT_OK
        if arguments.command == "restore":
            requested = arguments.backup
            if os.path.isabs(requested):
                requested = os.path.relpath(os.path.realpath(requested), repo)
            requested = os.path.normpath(requested).replace("\\", "/")
            backup = checked(repo, requested)
            if not (backup / "journal.json").is_file() or BACKUP_ROOT not in backup.relative_to(repo).parts[:1]:
                raise MigrationError(EXIT_USAGE, "backup_missing", f"No journal in {arguments.backup}")
            restored = restore_backup(repo, backup)
            print(json.dumps({"ok": True, "restored": restored}, indent=2))
            return EXIT_OK
        options = {"status_map": parse_status_map(arguments.status_map),
                   "remove_legacy_files": arguments.remove_legacy_files,
                   "confirm_replacement": arguments.confirm_replacement_installed}
        if arguments.command == "apply":
            pending = incomplete_journals(repo)
            if pending:
                raise MigrationError(EXIT_CONFLICT, "incomplete_migration",
                                     "An earlier migration did not finish: run `restore --backup " + pending[0].relative_to(repo).as_posix() + "`")
        MAPPED_USED.clear()
        report, ops = make_plan(repo, options)
        for key in options["status_map"]:
            if key not in MAPPED_USED:
                report["blockers"].append({"error": "unknown_status_map_target", "message": f"--status-map {key} does not match any package"})
        report["mode"] = arguments.command
        blocked = bool(report["blockers"] or report["ambiguities"])
        if report["layout"] == "current" and not ops:
            report["message"] = "Already on the current layout; nothing to do"
        if blocked:
            report["ok"] = False
            print(json.dumps(report, indent=2))
            return EXIT_BLOCKED
        if arguments.command == "apply" and ops:
            records = [op["path"] for op in ops if op["op"] == "write" and op["path"].endswith("/DELIVERY-RUN.json")]
            backup = apply_plan(repo, ops, records)
            report["backup"] = backup.relative_to(repo).as_posix()
        report["ok"] = True
        print(json.dumps(report, indent=2))
        return EXIT_OK
    except MigrationError as error:
        print(json.dumps({"ok": False, "error": error.error, "message": error.message}))
        return error.code


if __name__ == "__main__":
    sys.exit(main())
