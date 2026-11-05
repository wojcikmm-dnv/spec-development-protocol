#!/usr/bin/env python3
"""Validate and update SDP delivery records (standard library only).

This checks records and enforces transitions. It is not a sandbox and cannot
prove who edited a file; see docs/PROTOCOL.md.
"""

import argparse
import contextlib
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA_VERSION = 4
STATUSES = (
    "planned",
    "delivering",
    "blocked",
    "awaiting-acceptance",
    "changes-requested",
    "accepted",
    "rejected",
)
TERMINAL = ("accepted", "rejected")
STAGES = ("developer", "reviewer", "security", "qa")
OPTIONAL_STAGES = ("security", "qa")
VERDICTS = ("pass", "fail", "blocked", "not_applicable")
PROFILES = ("Lean", "Balanced", "Compliance")
EPIC_POLICIES = ("risk-based", "per-story", "epic-level", "waived")
DISPOSITIONS = ("confirmed", "not_present", "accepted_risk")
AGENT_PREFIXES = ("sdp.",)

EXIT_OK, EXIT_INVALID, EXIT_USAGE, EXIT_CONFLICT = 0, 1, 2, 3

TRIGGER_RE = re.compile(r"^(security|qa):[A-Za-z0-9._-]+$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9._-]+$")
KEY_RE = re.compile(r"^([a-z][a-z0-9_]*):[ \t]*(.*)$")
FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")

RECORD_FIELDS = (
    "schema_version",
    "run_id",
    "delivery_id",
    "workflow",
    "profile",
    "branch",
    "delivery_status",
    "state_revision",
    "policy",
    "plan",
    "candidate",
    "stage_results",
    "trigger_dispositions",
    "rejected_candidates",
    "human_corrections",
    "pending_audit",
    "acceptance",
    "blocked_reason",
    "capability_source",
    "compliance",
)


class ProtocolError(Exception):
    def __init__(self, code, error, message):
        super().__init__(message)
        self.code = code
        self.error = error
        self.message = message


def invalid(error, message):
    return ProtocolError(EXIT_INVALID, error, message)


def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


# --- plan frontmatter -----------------------------------------------------

def split_plan(text):
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise invalid("plan_frontmatter", "PLAN.md must start with frontmatter")
    end = text.find("\n---\n", 3)
    if end == -1:
        raise invalid("plan_frontmatter", "PLAN.md frontmatter is not closed")
    return text[4:end], text[end + 5:]


def parse_frontmatter(front):
    """Read flat scalar and inline-list pairs; reject everything else."""
    values = {}
    for line in front.split("\n"):
        if not line.strip():
            continue
        match = KEY_RE.match(line)
        if not match:
            raise invalid("plan_frontmatter", f"Unsupported frontmatter line: {line!r}")
        key, raw = match.group(1), match.group(2).strip()
        if key in values:
            raise invalid("plan_frontmatter", f"Duplicate frontmatter key: {key}")
        if raw.startswith("["):
            if not raw.endswith("]"):
                raise invalid("plan_frontmatter", f"Unclosed list for {key}")
            items = [item.strip() for item in raw[1:-1].split(",") if item.strip()]
            if not all(TOKEN_RE.match(item) for item in items):
                raise invalid("plan_frontmatter", f"Unsupported list item for {key}")
            values[key] = items
        elif raw[:1] in "{|>&*!":
            raise invalid("plan_frontmatter", f"Unsupported value for {key}")
        else:
            if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
                raw = raw[1:-1]
            values[key] = raw
    return values


def parse_plan(text):
    front, body = split_plan(text)
    meta = parse_frontmatter(front)
    return {
        "status": meta.get("status", "draft"),
        "approved_by": meta.get("approved_by", "pending"),
        "approved_at": meta.get("approved_at", "pending"),
        "stories": meta.get("stories", []),
        "sequenced_after": meta.get("sequenced_after", []),
        "fingerprint": sha256_hex(body.encode("utf-8")),
    }


def set_frontmatter(text, updates):
    normalized = text.replace("\r\n", "\n")
    front, body = split_plan(normalized)
    lines = front.split("\n") if front else []
    for key, value in updates.items():
        entry = f"{key}: {value}"
        for index, line in enumerate(lines):
            match = KEY_RE.match(line)
            if match and match.group(1) == key:
                lines[index] = entry
                break
        else:
            lines.append(entry)
    return "---\n" + "\n".join(lines) + "\n---\n" + body


def plan_is_approved(plan):
    return (
        plan["status"] == "approved"
        and plan["approved_by"] not in ("", "pending")
        and plan["approved_at"] not in ("", "pending")
    )


# --- candidate identity ---------------------------------------------------

def git(repo, *args):
    try:
        done = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, check=False
        )
    except OSError as error:
        raise ProtocolError(EXIT_USAGE, "git_unavailable", f"Git is required: {error}")
    if done.returncode != 0:
        raise ProtocolError(
            EXIT_USAGE, "git_failed", done.stderr.decode("utf-8", "replace").strip()
        )
    return done.stdout


def head_revision(repo):
    return git(repo, "rev-parse", "--verify", "HEAD").decode().strip()


def _digest_path(path):
    if path.is_symlink():
        return sha256_hex(b"link:" + os.readlink(path).encode("utf-8", "surrogateescape"))
    if path.is_file():
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                digest.update(block)
        return digest.hexdigest()
    return "DELETED"


def compute_candidate(repo, base_revision, exclude_prefix):
    git(repo, "rev-parse", "--verify", f"{base_revision}^{{commit}}")
    repo = Path(repo)
    tokens = git(repo, "diff", "--name-status", "-z", "--no-renames", base_revision, "--").split(b"\0")
    paths = set()
    for index in range(0, len(tokens) - 1, 2):
        paths.add(tokens[index + 1].decode("utf-8", "surrogateescape"))
    untracked = git(repo, "ls-files", "-z", "--others", "--exclude-standard").split(b"\0")
    paths.update(item.decode("utf-8", "surrogateescape") for item in untracked if item)
    prefix = exclude_prefix.rstrip("/") + "/"
    paths = sorted(path for path in paths if not path.startswith(prefix))
    entries = [f"{path}\0{_digest_path(repo / path)}" for path in paths]
    return {
        "base_revision": base_revision,
        "changed_paths": paths,
        "fingerprint": sha256_hex("\n".join(entries).encode("utf-8", "surrogateescape")),
    }


# --- record structure -----------------------------------------------------

def _is_str(value):
    return isinstance(value, str) and value != ""


def _is_str_list(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_structure(record):
    errors = []
    if not isinstance(record, dict):
        return ["Record must be a JSON object"]
    for field in RECORD_FIELDS:
        if field not in record:
            errors.append(f"Missing field: {field}")
    for field in record:
        if field not in RECORD_FIELDS:
            errors.append(f"Unknown field: {field}")
    if errors:
        return errors
    version = record["schema_version"]
    if version != SCHEMA_VERSION:
        return [
            "Unsupported newer schema_version; upgrade SDP"
            if isinstance(version, int) and version > SCHEMA_VERSION
            else "Legacy or invalid schema_version; migrate the record"
        ]
    for field in ("run_id", "delivery_id", "workflow"):
        if not _is_str(record[field]):
            errors.append(f"{field} must be a non-empty string")
    if record["profile"] not in PROFILES:
        errors.append("profile must be Lean, Balanced, or Compliance")
    if record["branch"] is not None and not isinstance(record["branch"], str):
        errors.append("branch must be a string or null")
    if record["delivery_status"] not in STATUSES:
        errors.append("delivery_status is not a supported status")
    for field in ("state_revision", "rejected_candidates", "human_corrections"):
        if not _is_int(record[field]):
            errors.append(f"{field} must be a non-negative integer")
    policy = record["policy"]
    if not isinstance(policy, dict) or set(policy) != {"profile_floor", "epic_security_policy", "mandatory_stages"}:
        errors.append("policy must contain profile_floor, epic_security_policy, mandatory_stages")
    else:
        if policy["profile_floor"] not in PROFILES:
            errors.append("policy.profile_floor is invalid")
        if policy["epic_security_policy"] not in EPIC_POLICIES:
            errors.append("policy.epic_security_policy is invalid")
        if not (_is_str_list(policy["mandatory_stages"]) and set(policy["mandatory_stages"]) <= set(STAGES)):
            errors.append("policy.mandatory_stages must list known stages")
    plan = record["plan"]
    if plan is not None:
        if not isinstance(plan, dict) or set(plan) != {"fingerprint", "approval"}:
            errors.append("plan must be null or contain fingerprint and approval")
        elif not FINGERPRINT_RE.match(str(plan["fingerprint"])) or not (
            isinstance(plan["approval"], dict)
            and set(plan["approval"]) == {"approved_by", "approved_at"}
            and all(_is_str(v) for v in plan["approval"].values())
        ):
            errors.append("plan fingerprint or approval snapshot is invalid")
    candidate = record["candidate"]
    if candidate is not None:
        if not isinstance(candidate, dict) or set(candidate) != {"base_revision", "changed_paths", "fingerprint"}:
            errors.append("candidate must be null or contain base_revision, changed_paths, fingerprint")
        elif not (
            _is_str(candidate["base_revision"])
            and _is_str_list(candidate["changed_paths"])
            and FINGERPRINT_RE.match(str(candidate["fingerprint"]))
        ):
            errors.append("candidate values are invalid")
    if not isinstance(record["stage_results"], list):
        errors.append("stage_results must be a list")
    else:
        for index, result in enumerate(record["stage_results"]):
            errors.extend(f"stage_results[{index}]: {item}" for item in _result_errors(result))
    if not isinstance(record["trigger_dispositions"], list):
        errors.append("trigger_dispositions must be a list")
    else:
        for index, item in enumerate(record["trigger_dispositions"]):
            errors.extend(f"trigger_dispositions[{index}]: {e}" for e in _disposition_errors(item))
    if not _is_str_list(record["pending_audit"]):
        errors.append("pending_audit must be a list of strings")
    acceptance = record["acceptance"]
    if not (
        isinstance(acceptance, dict)
        and set(acceptance) == {"decision", "decided_by", "decided_at", "feedback"}
        and acceptance["decision"] in ("pending", "accepted", "rejected")
    ):
        errors.append("acceptance is invalid")
    if record["blocked_reason"] is not None and not isinstance(record["blocked_reason"], str):
        errors.append("blocked_reason must be a string or null")
    if record["capability_source"] is not None and not (
        isinstance(record["capability_source"], str)
        and re.match(r"^(explicit|host:[A-Za-z0-9._-]+)$", record["capability_source"])
    ):
        errors.append("capability_source must be null, explicit, or host:<name>")
    return errors


def _result_errors(result):
    if not isinstance(result, dict):
        return ["must be an object"]
    allowed = {
        "stage", "verdict", "candidate_fingerprint", "findings", "checks",
        "evidence", "detected_triggers", "next_action", "reason",
    }
    errors = [f"unknown field {key}" for key in result if key not in allowed]
    for key in ("stage", "verdict", "candidate_fingerprint"):
        if key not in result:
            errors.append(f"missing {key}")
    if errors:
        return errors
    if result["stage"] not in STAGES:
        errors.append("unknown stage")
    if result["verdict"] not in VERDICTS:
        errors.append("unknown verdict")
    if not FINGERPRINT_RE.match(str(result["candidate_fingerprint"])):
        errors.append("candidate_fingerprint is invalid")
    for key in ("findings", "checks", "evidence", "detected_triggers"):
        if key in result and not _is_str_list(result[key]):
            errors.append(f"{key} must be a list of strings")
    for trigger in result.get("detected_triggers", []) if _is_str_list(result.get("detected_triggers", [])) else []:
        if not TRIGGER_RE.match(trigger):
            errors.append(f"invalid trigger {trigger!r}")
    for key in ("next_action", "reason"):
        if key in result and result[key] is not None and not isinstance(result[key], str):
            errors.append(f"{key} must be a string or null")
    return errors


def _disposition_errors(item):
    if not isinstance(item, dict) or set(item) != {"trigger", "candidate_fingerprint", "disposition", "by", "reason"}:
        return ["must contain trigger, candidate_fingerprint, disposition, by, reason"]
    errors = []
    if not TRIGGER_RE.match(str(item["trigger"])):
        errors.append("invalid trigger")
    if not FINGERPRINT_RE.match(str(item["candidate_fingerprint"])):
        errors.append("invalid candidate_fingerprint")
    if item["disposition"] not in DISPOSITIONS:
        errors.append("invalid disposition")
    if not _is_str(item["by"]):
        errors.append("by is required")
    if item["reason"] is not None and not isinstance(item["reason"], str):
        errors.append("reason must be a string or null")
    return errors


# --- assurance rules ------------------------------------------------------

AGENT_WORDS = ("agent", "bot", "assistant", "copilot", "claude", "orchestrator", "automation")


def is_agent_identity(name):
    """Heuristic only: identities are asserted strings, not authenticated."""
    lowered = re.sub(r"[^a-z0-9.]+", " ", name.strip().lower())
    return (
        lowered.startswith(AGENT_PREFIXES)
        or lowered in STAGES
        or any(word in lowered.split() for word in AGENT_WORDS)
    )


def all_triggers(record):
    found = []
    for result in record["stage_results"]:
        for trigger in result.get("detected_triggers", []):
            if trigger not in found:
                found.append(trigger)
    return found


def risk_accepted(record, trigger, fingerprint):
    return any(
        item["trigger"] == trigger
        and item["candidate_fingerprint"] == fingerprint
        and item["disposition"] == "accepted_risk"
        and item["reason"]
        and not is_agent_identity(item["by"])
        for item in record["trigger_dispositions"]
    )


def required_stages(record, fingerprint):
    policy = record["policy"]
    required = {"developer", "reviewer"} | set(policy["mandatory_stages"])
    if "Compliance" in (record["profile"], policy["profile_floor"]):
        required |= set(OPTIONAL_STAGES)
    if policy["epic_security_policy"] == "per-story":
        required.add("security")
    for trigger in all_triggers(record):
        if not risk_accepted(record, trigger, fingerprint):
            required.add(trigger.split(":", 1)[0])
    return required


def latest_result(record, stage, fingerprint):
    matches = [
        result for result in record["stage_results"]
        if result["stage"] == stage and result["candidate_fingerprint"] == fingerprint
    ]
    return matches[-1] if matches else None


def unsatisfied_stages(record, fingerprint):
    reasons = []
    for stage in sorted(required_stages(record, fingerprint)):
        result = latest_result(record, stage, fingerprint)
        if result is None:
            reasons.append(f"{stage}: no result for the current candidate")
        elif result["verdict"] != "pass":
            reasons.append(f"{stage}: latest verdict is {result['verdict']}")
    return reasons


# --- semantic validation --------------------------------------------------

def validate_record(record, plan=None, current_fingerprint=None):
    errors = validate_structure(record)
    if errors:
        return errors
    status = record["delivery_status"]
    if PROFILES.index(record["profile"]) < PROFILES.index(record["policy"]["profile_floor"]):
        errors.append("profile is below the project profile floor")
    for index, result in enumerate(record["stage_results"]):
        if result["stage"] in ("developer", "reviewer") and result["verdict"] == "not_applicable":
            errors.append(f"stage_results[{index}]: {result['stage']} cannot be not_applicable")
        if result["verdict"] in ("fail", "blocked") and not result.get("findings"):
            errors.append(f"stage_results[{index}]: {result['verdict']} needs findings")
        if result["verdict"] == "not_applicable" and not result.get("reason"):
            errors.append(f"stage_results[{index}]: not_applicable needs a reason")
    for index, item in enumerate(record["trigger_dispositions"]):
        stage = item["trigger"].split(":", 1)[0]
        if item["disposition"] == "accepted_risk":
            if is_agent_identity(item["by"]) or not item["reason"]:
                errors.append(f"trigger_dispositions[{index}]: accepted_risk needs a human and a reason")
        elif item["by"] != stage:
            errors.append(f"trigger_dispositions[{index}]: only the {stage} stage can record {item['disposition']}")
    if status in ("delivering", "blocked", "changes-requested", "awaiting-acceptance"):
        if record["plan"] is None:
            errors.append("An approved plan binding is required")
        elif plan is not None:
            errors.extend(plan_binding_errors(record, plan))
    if status == "blocked" and not record["blocked_reason"]:
        errors.append("blocked status needs blocked_reason")
    if status in ("awaiting-acceptance", "accepted"):
        candidate = record["candidate"]
        if candidate is None:
            errors.append(f"{status} requires a candidate")
        else:
            errors.extend(unsatisfied_stages(record, candidate["fingerprint"]))
            if (
                status == "awaiting-acceptance"
                and current_fingerprint is not None
                and current_fingerprint != candidate["fingerprint"]
            ):
                errors.append("The working tree changed after assurance; results are stale")
    acceptance = record["acceptance"]
    if status == "accepted" and not (
        acceptance["decision"] == "accepted" and _is_str(acceptance["decided_by"]) and not is_agent_identity(acceptance["decided_by"])
    ):
        errors.append("accepted requires a recorded human decision")
    if status == "rejected" and acceptance["decision"] != "rejected":
        errors.append("rejected requires a recorded decision")
    if status not in TERMINAL and acceptance["decision"] != "pending":
        errors.append("acceptance decision recorded before a terminal status")
    return errors


def plan_binding_errors(record, plan):
    binding = record["plan"]
    errors = []
    if plan["fingerprint"] != binding["fingerprint"]:
        errors.append("PLAN.md changed after approval; approval is stale")
    if not plan_is_approved(plan):
        errors.append("PLAN.md is not approved")
    elif (
        plan["approved_by"] != binding["approval"]["approved_by"]
        or plan["approved_at"] != binding["approval"]["approved_at"]
    ):
        errors.append("PLAN.md approval metadata differs from the recorded approval")
    return errors


# --- transitions ----------------------------------------------------------

ALLOWED = {
    "planned": ("delivering",),
    "delivering": ("blocked", "awaiting-acceptance", "changes-requested", "planned", "rejected"),
    "blocked": ("delivering",),
    "changes-requested": ("delivering", "planned", "rejected"),
    "awaiting-acceptance": ("accepted", "changes-requested", "rejected"),
    "accepted": (),
    "rejected": (),
}


def new_record(delivery_id, workflow, profile, policy):
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": f"{delivery_id}-run-1",
        "delivery_id": delivery_id,
        "workflow": workflow,
        "profile": profile,
        "branch": None,
        "delivery_status": "planned",
        "state_revision": 0,
        "policy": policy,
        "plan": None,
        "candidate": None,
        "stage_results": [],
        "trigger_dispositions": [],
        "rejected_candidates": 0,
        "human_corrections": 0,
        "pending_audit": [],
        "acceptance": {"decision": "pending", "decided_by": None, "decided_at": None, "feedback": None},
        "blocked_reason": None,
        "capability_source": None,
        "compliance": None,
    }


def bind_plan(record, plan):
    if record["delivery_status"] != "planned":
        raise invalid("invalid_transition", "A plan can only be approved while the package is planned")
    updated = json.loads(json.dumps(record))
    updated["plan"] = {
        "fingerprint": plan["fingerprint"],
        "approval": {"approved_by": plan["approved_by"], "approved_at": plan["approved_at"]},
    }
    return updated


def transition(record, to, context):
    """Return a new record or raise. `context` supplies facts read from disk."""
    current = record["delivery_status"]
    if current in TERMINAL:
        raise invalid("terminal_state", f"{current} is final")
    if to not in ALLOWED[current]:
        raise invalid("invalid_transition", f"{current} -> {to} is not allowed")
    updated = json.loads(json.dumps(record))
    plan = context["plan"]
    human = context.get("decided_by")
    reason = context.get("reason")

    def need_human():
        if not human or is_agent_identity(human):
            raise invalid("human_required", "This decision needs a named human, not an agent identity")

    if to == "delivering":
        if updated["plan"] is None:
            raise invalid("plan_unapproved", "Approve the plan before delivery")
        errors = plan_binding_errors(updated, plan)
        if errors:
            raise invalid("plan_stale", "; ".join(errors))
        if current == "planned":
            capabilities = set(context.get("capabilities", ()))
            missing = set(context.get("required_capabilities", ("implement", "technical-review"))) - capabilities
            if missing:
                raise invalid("capability_missing", f"Required capabilities unavailable: {', '.join(sorted(missing))}")
            for prerequisite in plan["sequenced_after"]:
                if context["prerequisites"].get(prerequisite) != "accepted":
                    raise invalid("prerequisite_open", f"{prerequisite} must be accepted first")
            for story in plan["stories"]:
                other = context["open_story_owners"].get(story)
                if other:
                    raise invalid("story_conflict", f"{story} already belongs to open package {other}")
            updated["candidate"] = {
                "base_revision": context["head"], "changed_paths": [], "fingerprint": context["fingerprint"],
            }
            updated["capability_source"] = context.get("capability_source", "explicit")
        if current == "changes-requested":
            if updated["rejected_candidates"] >= 2 and not context.get("human_guided"):
                raise invalid("escalation_required", "Two candidates were rejected; a human must guide the next repair")
            if context.get("human_guided"):
                need_human()
                updated["human_corrections"] += 1
        updated["blocked_reason"] = None
    elif to == "blocked":
        if not reason:
            raise invalid("reason_required", "blocked needs a reason")
        updated["blocked_reason"] = reason
    elif to == "awaiting-acceptance":
        errors = plan_binding_errors(updated, plan)
        if errors:
            raise invalid("plan_stale", "; ".join(errors))
        candidate = {**updated["candidate"], **context["candidate"]}
        updated["candidate"] = candidate
        remaining = unsatisfied_stages(updated, candidate["fingerprint"])
        if remaining:
            raise invalid("assurance_incomplete", "; ".join(remaining))
    elif to == "changes-requested":
        if current == "awaiting-acceptance":
            need_human()
            if not reason:
                raise invalid("reason_required", "Describe the requested change")
            updated["human_corrections"] += 1
        else:
            raise invalid("invalid_transition", "A failing stage result moves delivery to changes-requested")
    elif to == "planned":
        if not reason:
            raise invalid("reason_required", "State why the plan must change")
        updated["plan"] = None
        updated["candidate"] = None
    elif to == "accepted":
        need_human()
        candidate = updated["candidate"]
        if context["fingerprint"] != candidate["fingerprint"]:
            raise invalid("evidence_stale", "The working tree changed after assurance; rerun the affected stages")
        errors = validate_record({**updated, "delivery_status": "awaiting-acceptance"}, plan, context["fingerprint"])
        if errors:
            raise invalid("assurance_incomplete", "; ".join(errors))
        updated["acceptance"] = {"decision": "accepted", "decided_by": human, "decided_at": now(), "feedback": reason}
    elif to == "rejected":
        need_human()
        updated["acceptance"] = {"decision": "rejected", "decided_by": human, "decided_at": now(), "feedback": reason}
    updated["delivery_status"] = to
    return updated


def record_result(record, result, fingerprint):
    """Add a stage result for the current candidate; may block or reject it."""
    result = {**result, "candidate_fingerprint": fingerprint}
    if any(existing == result for existing in record["stage_results"]):
        return record
    if record["delivery_status"] != "delivering":
        raise invalid("invalid_transition", "Results are recorded only while delivering")
    errors = _result_errors(result)
    if errors:
        raise invalid("invalid_result", "; ".join(errors))
    stage, verdict = result["stage"], result["verdict"]
    if stage in ("developer", "reviewer") and verdict == "not_applicable":
        raise invalid("mandatory_stage", f"{stage} is mandatory and cannot be not_applicable")
    if verdict in ("fail", "blocked") and not result.get("findings"):
        raise invalid("invalid_result", f"{verdict} needs findings")
    if verdict == "not_applicable" and not result.get("reason"):
        raise invalid("invalid_result", "not_applicable needs a reason")
    if stage != "developer" and (
        latest_result(record, "developer", fingerprint) is None
        or latest_result(record, "developer", fingerprint)["verdict"] != "pass"
    ):
        raise invalid("developer_first", "Record a passing developer result for this candidate first")
    if verdict == "not_applicable" and stage in required_stages(record, fingerprint):
        raise invalid("stage_required", f"{stage} is required and cannot be not_applicable")
    prior = latest_result(record, stage, fingerprint)
    if prior is not None and prior["verdict"] == "fail" and verdict != "fail":
        raise invalid("candidate_unchanged", f"The candidate is unchanged since it failed {stage}; change it before rerunning")
    updated = json.loads(json.dumps(record))
    if verdict == "fail" and not any(
        existing["verdict"] == "fail" and existing["candidate_fingerprint"] == fingerprint
        for existing in updated["stage_results"]
    ):
        updated["rejected_candidates"] += 1
    updated["stage_results"].append(result)
    if verdict == "fail":
        updated["delivery_status"] = "changes-requested"
    elif verdict == "blocked":
        updated["delivery_status"] = "blocked"
        updated["blocked_reason"] = "; ".join(result["findings"])
    return updated


def add_disposition(record, item):
    errors = _disposition_errors(item)
    if errors:
        raise invalid("invalid_disposition", "; ".join(errors))
    stage = item["trigger"].split(":", 1)[0]
    if item["disposition"] != "accepted_risk" and latest_result(record, stage, item["candidate_fingerprint"]) is None:
        raise invalid("invalid_disposition", f"The {stage} stage has not run for this candidate")
    updated = json.loads(json.dumps(record))
    updated["trigger_dispositions"].append(item)
    problems = [e for e in validate_record(updated) if e.startswith("trigger_dispositions")]
    if problems:
        raise invalid("invalid_disposition", "; ".join(problems))
    return updated


# --- storage --------------------------------------------------------------

def resolve_package(repo, package):
    repo = Path(repo).resolve()
    spec_root = (repo / "spec").resolve()
    target = Path(package)
    target = (target if target.is_absolute() else repo / target).resolve()
    if spec_root != target and spec_root not in target.parents:
        raise ProtocolError(EXIT_USAGE, "path_escape", "Package must be inside the repository spec/ folder")
    if not target.is_dir():
        raise ProtocolError(EXIT_USAGE, "package_missing", f"No such package folder: {package}")
    for name in ("PLAN.md", "DELIVERY-RUN.json"):
        path = target / name
        if path.is_symlink() or (path.exists() and spec_root not in path.resolve().parents):
            raise ProtocolError(EXIT_USAGE, "path_escape", f"{name} must be a regular file inside spec/")
    return repo, target


def lock_path(record_path):
    folder = Path(tempfile.gettempdir()) / "sdp-locks"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / (sha256_hex(str(record_path).encode()) + ".lock")


exclusive_lock_held = False


@contextlib.contextmanager
def exclusive_lock(record_path):
    global exclusive_lock_held
    descriptor = os.open(lock_path(record_path), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise ProtocolError(EXIT_CONFLICT, "lock_held", "Another writer holds this record")
        exclusive_lock_held = True
        yield
    finally:
        exclusive_lock_held = False
        os.close(descriptor)


MAX_RECORD_BYTES = 5 * 1024 * 1024
MAX_PLAN_BYTES = 2 * 1024 * 1024


def read_limited(path, limit):
    path = Path(path)
    if path.is_symlink():
        raise ProtocolError(EXIT_USAGE, "path_escape", f"{path.name} must not be a symbolic link")
    if path.stat().st_size > limit:
        raise invalid("file_too_large", f"{path.name} exceeds {limit} bytes")
    return path.read_text(encoding="utf-8")


def read_record(path):
    try:
        return json.loads(read_limited(path, MAX_RECORD_BYTES))
    except FileNotFoundError:
        return None
    except (OSError, ValueError, RecursionError) as error:
        raise invalid("record_unreadable", f"Cannot read run record: {error}")


def write_atomic(path, record):
    path = Path(path)
    if path.is_symlink():
        raise ProtocolError(EXIT_USAGE, "path_escape", f"{path.name} must not be a symbolic link")
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".run-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(record, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temporary)
        raise


def stored_record(record_path, expected_revision):
    """Read the stored record under the lock and enforce the revision check."""
    stored = read_record(record_path)
    if stored is not None:
        problems = validate_structure(stored)
        if problems:
            raise invalid("record_invalid", "; ".join(problems))
        if expected_revision != stored["state_revision"]:
            raise ProtocolError(
                EXIT_CONFLICT, "stale_revision",
                f"Record is at revision {stored['state_revision']}, not {expected_revision}",
            )
    elif expected_revision not in (None, 0):
        raise ProtocolError(EXIT_CONFLICT, "stale_revision", "Record does not exist yet")
    return stored


def update_record(record_path, mutate, expected_revision, plan_path=None):
    """Under one lock: read record and plan, mutate, validate, replace atomically."""
    record_path = Path(record_path)
    with exclusive_lock(record_path):
        stored = stored_record(record_path, expected_revision)
        plan = parse_plan(read_limited(plan_path, MAX_PLAN_BYTES)) if plan_path else None
        updated = mutate(stored, plan)
        if updated is stored:
            return stored
        updated["state_revision"] = (stored["state_revision"] + 1) if stored else 1
        errors = validate_record(updated, plan)
        if errors:
            raise invalid("record_invalid", "; ".join(errors))
        write_atomic(record_path, updated)
        return updated


def approve_plan(record_path, plan_path, expected_revision, make_record, by, expected_fingerprint=None):
    """Record approval in PLAN.md and the run record as one locked operation."""
    with exclusive_lock(record_path):
        stored = stored_record(record_path, expected_revision)
        if stored is not None and stored["delivery_status"] != "planned":
            raise invalid("invalid_transition", "A plan can only be approved while the package is planned")
        current = read_limited(plan_path, MAX_PLAN_BYTES)
        if expected_fingerprint and parse_plan(current)["fingerprint"] != expected_fingerprint:
            raise invalid("plan_changed", "PLAN.md changed since the human reviewed it; show the current plan and ask again")
        edited = set_frontmatter(
            current,
            {"status": "approved", "approved_by": by, "approved_at": now()},
        )
        updated = bind_plan(stored or make_record(), parse_plan(edited))
        updated["state_revision"] = (stored["state_revision"] + 1) if stored else 1
        errors = validate_record(updated)
        if errors:
            raise invalid("record_invalid", "; ".join(errors))
        write_atomic_text(plan_path, edited)
        write_atomic(record_path, updated)
        return updated


def open_story_owners(repo, current_dir):
    owners = {}
    for plan_path in sorted(Path(repo, "spec").glob("*/deliveries/*/PLAN.md")):
        folder = plan_path.parent
        if folder.resolve() == current_dir.resolve():
            continue
        record = read_record(folder / "DELIVERY-RUN.json")
        if record is not None and record.get("delivery_status") in TERMINAL:
            continue
        for story in parse_plan(read_limited(plan_path, MAX_PLAN_BYTES)).get("stories", []):
            owners.setdefault(story, folder.name)
    return owners


def prerequisite_statuses(repo, plan):
    statuses = {}
    for prerequisite in plan["sequenced_after"]:
        found = list(Path(repo, "spec").glob(f"*/deliveries/{prerequisite}/DELIVERY-RUN.json"))
        record = read_record(found[0]) if found else None
        statuses[prerequisite] = record["delivery_status"] if record else "planned"
    return statuses


# --- workflows and next action ---------------------------------------------

DEFAULT_WORKFLOW_DIR = Path(__file__).resolve().parent.parent.parent / "sdp-workflows" / "workflows"


def workflow_dir():
    override = os.environ.get("SDP_WORKFLOW_DIR")
    return Path(override) if override else DEFAULT_WORKFLOW_DIR
STAGE_ORDER = ("developer", "reviewer", "security", "qa")
REQUIRED_KINDS = ("always", "on-trigger-or-policy")
ISOLATION_BY_STAGE = {"developer": "none", "reviewer": "independent", "security": "independent", "qa": "independent"}


def validate_workflow(document):
    errors = []
    if not isinstance(document, dict):
        return ["Workflow must be a JSON object"]
    if document.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not (isinstance(document.get("workflow"), str) and TOKEN_RE.match(document["workflow"])):
        errors.append("workflow must be a simple name")
    stages = document.get("stages")
    if not isinstance(stages, list) or [s.get("stage") if isinstance(s, dict) else None for s in stages] != list(STAGE_ORDER):
        errors.append("stages must be developer, reviewer, security, qa in that order")
    else:
        for item in stages:
            name = item["stage"]
            for key in ("capability", "skill"):
                if not (isinstance(item.get(key), str) and item[key]):
                    errors.append(f"{name}: {key} is required")
            if item.get("isolation") != ISOLATION_BY_STAGE[name]:
                errors.append(f"{name}: isolation must be {ISOLATION_BY_STAGE[name]}")
            if item.get("required") not in REQUIRED_KINDS:
                errors.append(f"{name}: required must be one of {', '.join(REQUIRED_KINDS)}")
            if name in ("developer", "reviewer") and item.get("required") != "always":
                errors.append(f"{name}: must be required always")
    limits = document.get("limits")
    if not (isinstance(limits, dict) and limits.get("rejected_candidates_before_escalation") == 2):
        errors.append("limits.rejected_candidates_before_escalation must be 2")
    capabilities = document.get("capabilities_required")
    if not (_is_str_list(capabilities) and {"implement", "technical-review", "independent-context"} <= set(capabilities)):
        errors.append("capabilities_required must include implement, technical-review, and independent-context")
    if not isinstance(document.get("pre_delivery", []), list):
        errors.append("pre_delivery must be a list")
    return errors


def load_workflow(name):
    if not (isinstance(name, str) and TOKEN_RE.match(name)):
        raise invalid("workflow_unknown", "Invalid workflow name")
    path = workflow_dir() / f"{name}.json"
    try:
        document = json.loads(read_limited(path, MAX_PLAN_BYTES))
    except FileNotFoundError:
        raise invalid("workflow_unknown", f"No workflow definition named {name!r}")
    except (OSError, ValueError, RecursionError) as error:
        raise invalid("workflow_invalid", f"Cannot read workflow {name!r}: {error}")
    problems = validate_workflow(document)
    if problems:
        raise invalid("workflow_invalid", "; ".join(problems))
    return document


def _stage_action(workflow, stage, record, **extra):
    entry = next(item for item in workflow["stages"] if item["stage"] == stage)
    return {
        "action": "run-stage", "actor": "worker", "stage": stage,
        "capability": entry["capability"], "skill": entry["skill"], "isolation": entry["isolation"],
        "record_with": f"result --stage {stage} --verdict <verdict> --expected-revision {record['state_revision']}",
        **extra,
    }


def next_action(workflow, record, plan, fingerprint, capabilities=None):
    """Derive the single next step from stored facts; read-only and deterministic."""
    if record is None:
        if plan_is_approved(plan):
            return {"action": "approve-plan", "actor": "coordinator", "approved_by": plan["approved_by"],
                    "plan_fingerprint": plan["fingerprint"],
                    "reason": "PLAN.md is marked approved but no run record exists; record it with the approved_by name and --expect-plan-fingerprint"}
        return {"action": "await-plan-approval", "actor": "human", "plan_fingerprint": plan["fingerprint"],
                "reason": "Show the human this exact plan; a named human must approve it before any product change"}
    status = record["delivery_status"]
    revision = record["state_revision"]
    base = {"state_revision": revision, "status": status}
    if status in TERMINAL:
        return {**base, "action": "done", "actor": "none", "reason": f"The package is {status}"}
    if status == "awaiting-acceptance":
        stale = record["candidate"] and fingerprint != record["candidate"]["fingerprint"]
        return {**base, "action": "await-human-decision", "actor": "human",
                "options": ["accepted", "changes-requested", "rejected"],
                "warning": "The working tree changed after assurance; accepting is refused until changes are requested and assurance reruns" if stale else None}
    if record["plan"] is None:
        return {**base, "action": "await-plan-approval", "actor": "human", "plan_fingerprint": plan["fingerprint"],
                "reason": "The approval was voided; replan, then a named human must approve again"}
    binding = plan_binding_errors(record, plan)
    if binding:
        return {**base, "action": "replan", "actor": "human", "reason": "; ".join(binding),
                "then": "transition --to planned with a reason, edit the plan, and approve it again"}
    if status == "planned":
        granted = workflow["capabilities_required"] if capabilities is None else capabilities
        missing = sorted(set(workflow["capabilities_required"]) - set(granted))
        if missing:
            return {**base, "action": "blocked-capability", "actor": "human", "missing": missing,
                    "reason": f"The host cannot provide {', '.join(missing)}; delivery cannot start and self-review is not a substitute"}
        return {**base, "action": "start-delivery", "actor": "coordinator", "transition_to": "delivering",
                "capabilities_required": workflow["capabilities_required"]}
    if status == "blocked":
        return {**base, "action": "resolve-block", "actor": "human", "reason": record["blocked_reason"],
                "then": "transition --to delivering once the cause is cleared"}
    if status == "changes-requested":
        if record["rejected_candidates"] >= workflow["limits"]["rejected_candidates_before_escalation"]:
            return {**base, "action": "escalate-to-human", "actor": "human",
                    "reason": "Two candidates were rejected; a human must guide the next repair or decide",
                    "options": ["transition --to delivering --human-guided --decided-by <human>",
                                "transition --to planned --reason <why>", "transition --to rejected --decided-by <human>"]}
        return {**base, "action": "resume-delivery", "actor": "coordinator", "transition_to": "delivering"}
    results = [r for r in record["stage_results"] if r["candidate_fingerprint"] == fingerprint]
    failing = [r for r in results if r["verdict"] == "fail"]
    stages_needed = required_stages(record, fingerprint)
    present = {s: latest_result(record, s, fingerprint) for s in STAGE_ORDER}
    if failing:
        return {**base, **_stage_action(workflow, "developer", record, repair=True,
                                        findings=[f for r in failing for f in r.get("findings", [])]),
                "reason": "The candidate failed review and is unchanged; the developer must change it, then record a developer result"}
    for stage in STAGE_ORDER:
        if stage != "developer" and stage not in stages_needed:
            continue
        result = present[stage]
        if result is None or result["verdict"] != "pass":
            if capabilities is not None:
                gaps = {}
                for later in STAGE_ORDER[STAGE_ORDER.index(stage):]:
                    if later in stages_needed and (present[later] is None or present[later]["verdict"] != "pass"):
                        entry = next(item for item in workflow["stages"] if item["stage"] == later)
                        needed = {entry["capability"]}
                        if entry["isolation"] == "independent":
                            needed.add("independent-context")
                        absent = sorted(needed - set(capabilities))
                        if absent:
                            gaps[later] = absent
                if stage in gaps:
                    every = sorted({cap for caps in gaps.values() for cap in caps})
                    return {**base, "action": "blocked-capability", "actor": "human", "stage": stage,
                            "missing": every, "missing_by_stage": gaps,
                            "reason": f"The host cannot provide {', '.join(every)}; self-review is not a substitute"}
            stale_note = None
            if any(r["stage"] == stage for r in record["stage_results"]) and result is None:
                stale_note = "Earlier results for this stage belong to a previous candidate and are stale"
            return {**base, **_stage_action(workflow, stage, record, notes=stale_note)}
    return {**base, "action": "request-acceptance", "actor": "coordinator", "transition_to": "awaiting-acceptance",
            "required_stages": sorted(stages_needed)}


# --- host capability profiles ----------------------------------------------

DEFAULT_HOSTS_DIR = Path(__file__).resolve().parent.parent.parent / "sdp-workflows" / "hosts"
CAPABILITY_NAMES = (
    "implement", "technical-review", "security-review", "acceptance-validation", "independent-context",
)


def validate_host_profile(document):
    errors = []
    if not isinstance(document, dict):
        return ["Host profile must be a JSON object"]
    if document.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not (isinstance(document.get("host"), str) and TOKEN_RE.match(document["host"])):
        errors.append("host must be a simple name")
    capabilities = document.get("capabilities")
    if not (isinstance(capabilities, dict) and set(capabilities) == set(CAPABILITY_NAMES)):
        errors.append("capabilities must list exactly: " + ", ".join(CAPABILITY_NAMES))
    else:
        for name, entry in capabilities.items():
            if not (isinstance(entry, dict) and entry.get("provided") in (True, False, "unverified")):
                errors.append(f"{name}: provided must be true, false, or \"unverified\"")
            elif entry["provided"] is True and not (isinstance(entry.get("evidence"), list) and entry["evidence"]):
                errors.append(f"{name}: a verified capability must cite evidence")
    return errors


def load_host_capabilities(name):
    """Capabilities a host profile has verified; unverified means not provided."""
    if not (isinstance(name, str) and TOKEN_RE.match(name)):
        raise invalid("host_unknown", "Invalid host name")
    folder = Path(os.environ.get("SDP_HOSTS_DIR") or DEFAULT_HOSTS_DIR)
    try:
        document = json.loads(read_limited(folder / f"{name}.json", MAX_PLAN_BYTES))
    except FileNotFoundError:
        raise invalid("host_unknown", f"No host profile named {name!r}; pass --capabilities explicitly")
    except (OSError, ValueError, RecursionError) as error:
        raise invalid("host_invalid", f"Cannot read host profile {name!r}: {error}")
    problems = validate_host_profile(document)
    if problems:
        raise invalid("host_invalid", "; ".join(problems))
    return [cap for cap, entry in document["capabilities"].items() if entry["provided"] is True]


# --- command line ---------------------------------------------------------

def parser():
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--repo", default=".")
    root.add_argument("--package", required=True, help="package folder under spec/")
    root.add_argument("--json", action="store_true")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("validate")
    commands.add_parser("inspect")
    following = commands.add_parser("next", help="print the next required action (read-only)")
    following.add_argument("--workflow", default="bug", help="used only before a run record exists")
    following.add_argument("--capabilities", default=None, help="comma-separated host capabilities; omit to skip the check")
    following.add_argument("--host", default=None, help="derive capabilities from a host profile's verified entries")
    approve = commands.add_parser("approve")
    approve.add_argument("--by", required=True)
    approve.add_argument("--workflow", default="bug")
    approve.add_argument("--expect-plan-fingerprint", help="refuse unless PLAN.md still has this fingerprint (from `next`)")
    approve.add_argument("--profile", choices=PROFILES, default="Balanced")
    approve.add_argument("--profile-floor", choices=PROFILES, default="Lean")
    approve.add_argument("--epic-security-policy", choices=EPIC_POLICIES, default="risk-based")
    approve.add_argument("--mandatory-stage", action="append", default=[], choices=STAGES)
    approve.add_argument("--expected-revision", type=int)
    move = commands.add_parser("transition")
    move.add_argument("--to", required=True, choices=STATUSES)
    move.add_argument("--expected-revision", type=int, required=True)
    move.add_argument("--capabilities", default="")
    move.add_argument("--host", default=None, help="derive capabilities from a host profile's verified entries")
    move.add_argument("--decided-by")
    move.add_argument("--reason")
    move.add_argument("--human-guided", action="store_true")
    result = commands.add_parser("result")
    result.add_argument("--stage", required=True, choices=STAGES)
    result.add_argument("--verdict", required=True, choices=VERDICTS)
    result.add_argument("--expected-revision", type=int, required=True)
    for name in ("finding", "check", "evidence", "trigger"):
        result.add_argument(f"--{name}", action="append", default=[])
    result.add_argument("--reason")
    disposition = commands.add_parser("disposition")
    disposition.add_argument("--trigger", required=True)
    disposition.add_argument("--disposition", required=True, choices=DISPOSITIONS)
    disposition.add_argument("--by", required=True)
    disposition.add_argument("--reason")
    disposition.add_argument("--expected-revision", type=int, required=True)
    return root


def facts(repo, package_dir, record):
    prefix = package_dir.relative_to(repo).as_posix()
    base = record["candidate"]["base_revision"] if record and record["candidate"] else head_revision(repo)
    return compute_candidate(repo, base, prefix)


def run(arguments):
    repo, package_dir = resolve_package(arguments.repo, arguments.package)
    plan_path, record_path = package_dir / "PLAN.md", package_dir / "DELIVERY-RUN.json"
    if not plan_path.is_file():
        raise ProtocolError(EXIT_USAGE, "plan_missing", "PLAN.md is missing")
    plan = parse_plan(read_limited(plan_path, MAX_PLAN_BYTES))
    record = read_record(record_path)
    command = arguments.command

    if command in ("validate", "inspect"):
        if record is None:
            return {"status": "planned", "valid": True, "errors": []}
        fingerprint = None
        if record["delivery_status"] == "awaiting-acceptance":
            fingerprint = facts(repo, package_dir, record)["fingerprint"]
        errors = validate_record(record, plan, fingerprint)
        summary = {
            "status": record["delivery_status"], "valid": not errors, "errors": errors,
            "state_revision": record["state_revision"],
            "rejected_candidates": record["rejected_candidates"],
            "capability_source": record["capability_source"],
        }
        if command == "inspect" and record["candidate"]:
            fp = record["candidate"]["fingerprint"]
            summary["required_stages"] = sorted(required_stages(record, fp))
            summary["unsatisfied"] = unsatisfied_stages(record, fp)
        if errors:
            raise ProtocolError(EXIT_INVALID, "invalid_record", "; ".join(errors))
        return summary

    if command == "next":
        workflow = load_workflow(record["workflow"] if record else arguments.workflow)
        capabilities = None
        source = "unchecked"
        if arguments.capabilities is not None and arguments.host is not None:
            raise ProtocolError(EXIT_USAGE, "usage", "Use either --capabilities or --host, not both")
        if arguments.capabilities is not None:
            capabilities = [item for item in arguments.capabilities.split(",") if item]
            source = "explicit"
        elif arguments.host is not None:
            capabilities = load_host_capabilities(arguments.host)
            source = f"host:{arguments.host}"
        problems = validate_structure(record) if record else []
        if problems:
            raise invalid("record_invalid", "; ".join(problems))
        fingerprint = facts(repo, package_dir, record)["fingerprint"] if record and record["candidate"] else None
        return {**next_action(workflow, record, plan, fingerprint, capabilities), "capability_source": source}

    if command == "approve":
        load_workflow(arguments.workflow)
        if not arguments.by or is_agent_identity(arguments.by):
            raise invalid("human_required", "Approval needs a named human")
        policy = {
            "profile_floor": arguments.profile_floor,
            "epic_security_policy": arguments.epic_security_policy,
            "mandatory_stages": sorted(set(arguments.mandatory_stage)),
        }

        def make_record():
            return new_record(package_dir.name, arguments.workflow, arguments.profile, policy)

        approve_plan(
            record_path, plan_path, arguments.expected_revision if record else None,
            make_record, arguments.by, arguments.expect_plan_fingerprint,
        )
        return {"status": "planned", "approved": True}

    if record is None:
        raise invalid("plan_unapproved", "No run record; approve the plan first")

    def locked_facts(stored):
        return facts(repo, package_dir, stored)

    if command == "transition":
        if arguments.host is not None and arguments.capabilities:
            raise ProtocolError(EXIT_USAGE, "usage", "Use either --capabilities or --host, not both")
        if arguments.host is not None:
            asserted, source = load_host_capabilities(arguments.host), f"host:{arguments.host}"
        else:
            asserted, source = [item for item in arguments.capabilities.split(",") if item], "explicit"

        def move(stored, current_plan):
            candidate = locked_facts(stored)
            context = {
                "plan": current_plan,
                "required_capabilities": load_workflow(stored["workflow"])["capabilities_required"],
                "fingerprint": candidate["fingerprint"],
                "candidate": candidate,
                "head": head_revision(repo),
                "capabilities": asserted,
                "capability_source": source,
                "decided_by": arguments.decided_by,
                "reason": arguments.reason,
                "human_guided": arguments.human_guided,
                "prerequisites": prerequisite_statuses(repo, current_plan),
                "open_story_owners": open_story_owners(repo, package_dir),
            }
            return transition(stored, arguments.to, context)

        updated = update_record(record_path, move, arguments.expected_revision, plan_path)
        return {"status": updated["delivery_status"], "state_revision": updated["state_revision"]}

    if command == "result":
        item = {
            "stage": arguments.stage, "verdict": arguments.verdict,
            "findings": arguments.finding, "checks": arguments.check,
            "evidence": arguments.evidence, "detected_triggers": arguments.trigger,
        }
        if arguments.reason:
            item["reason"] = arguments.reason
        updated = update_record(
            record_path,
            lambda stored, _plan: record_result(stored, item, locked_facts(stored)["fingerprint"]),
            arguments.expected_revision, plan_path,
        )
        return {"status": updated["delivery_status"], "rejected_candidates": updated["rejected_candidates"],
                "state_revision": updated["state_revision"]}

    if command == "disposition":
        def dispose(stored, _plan):
            item = {
                "trigger": arguments.trigger,
                "candidate_fingerprint": locked_facts(stored)["fingerprint"],
                "disposition": arguments.disposition, "by": arguments.by, "reason": arguments.reason,
            }
            return add_disposition(stored, item)

        updated = update_record(record_path, dispose, arguments.expected_revision, plan_path)
        return {"status": updated["delivery_status"], "state_revision": updated["state_revision"]}
    raise ProtocolError(EXIT_USAGE, "usage", f"Unknown command {command}")


def write_atomic_text(path, text):
    if Path(path).is_symlink():
        raise ProtocolError(EXIT_USAGE, "path_escape", f"{Path(path).name} must not be a symbolic link")
    handle, temporary = tempfile.mkstemp(dir=Path(path).parent, prefix=".plan-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temporary)
        raise


def main(argv=None):
    arguments = parser().parse_args(argv)
    try:
        outcome = run(arguments)
        payload = {"ok": True, **outcome}
        code = EXIT_OK
    except ProtocolError as error:
        payload = {"ok": False, "error": error.error, "message": error.message}
        code = error.code
    if arguments.json:
        print(json.dumps(payload))
    elif payload["ok"]:
        print("OK " + json.dumps({k: v for k, v in payload.items() if k != "ok"}))
    else:
        print(f"FAIL [{payload['error']}] {payload['message']}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
