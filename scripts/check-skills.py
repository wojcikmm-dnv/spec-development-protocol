#!/usr/bin/env python3
"""Check skill structure, descriptors, and evaluation cases (maintainer tool)."""

import importlib.util
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".apm/skills"
CORE_SCRIPTS = SKILLS / "sdp-core/scripts"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KINDS = ("correct", "seeded-defect", "negative", "escalation")
VERDICTS = ("pass", "fail", "blocked", "not_applicable")
MAX_SKILL_LINES = 500


def load_grader():
    spec = importlib.util.spec_from_file_location("grade_eval", CORE_SCRIPTS / "grade_eval.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_skill(folder):
    text = (folder / "SKILL.md").read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    parts = text.split("---\n", 2)
    if len(parts) != 3 or parts[0]:
        raise ValueError("missing frontmatter")
    meta = yaml.safe_load(parts[1])
    if not isinstance(meta, dict):
        raise ValueError("frontmatter is not a mapping")
    return meta, parts[2], text.count("\n")


def descriptor_errors(descriptor, schema):
    try:
        import jsonschema
    except ImportError:
        required = schema["required"]
        return [f"missing {key}" for key in required if key not in descriptor]
    validator = jsonschema.Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(descriptor)]


def case_errors(skill, document, grader):
    errors = []
    cases = document.get("cases", [])
    if len(cases) < 3:
        errors.append("needs at least three evaluation cases")
    if not any(case.get("kind") != "correct" for case in cases):
        errors.append("needs at least one seeded-defect, negative, or escalation case")
    if not any(case.get("kind") == "correct" for case in cases):
        errors.append("needs a correct case")
    seen = set()
    for case in cases:
        label = f"case {case.get('id')!r}"
        if case.get("id") in seen:
            errors.append(f"{label}: duplicate id")
        seen.add(case.get("id"))
        if case.get("kind") not in KINDS:
            errors.append(f"{label}: unknown kind")
        expect = case.get("expect", {})
        if expect.get("verdict") not in VERDICTS:
            errors.append(f"{label}: expect.verdict is invalid")
            continue
        reference = case.get("reference_result")
        if not isinstance(reference, dict):
            errors.append(f"{label}: missing reference_result")
            continue
        for failure in grader.grade(case, reference):
            errors.append(f"{label}: reference result does not satisfy its own case: {failure}")
        if expect["verdict"] in ("fail", "blocked") and not expect.get("finding_patterns"):
            errors.append(f"{label}: a {expect['verdict']} case must name the finding it expects")
    return errors


def check_skill(folder, schema, grader):
    errors = []
    try:
        meta, body, lines = read_skill(folder)
    except (OSError, ValueError, yaml.YAMLError) as error:
        return [f"SKILL.md: {error}"]
    name = meta.get("name")
    if name != folder.name:
        errors.append(f"name {name!r} must match folder {folder.name!r}")
    if not (isinstance(name, str) and NAME_RE.match(name) and len(name) <= 64):
        errors.append("name must be lowercase kebab-case, at most 64 characters")
    description = meta.get("description")
    if not (isinstance(description, str) and description.strip()):
        errors.append("description is required")
    elif len(description) > 1024:
        errors.append("description exceeds 1024 characters")
    if lines > MAX_SKILL_LINES:
        errors.append(f"SKILL.md has {lines} lines; keep it under {MAX_SKILL_LINES}")
    for target in re.findall(r"\]\((?!https?://|#)([^)]+)\)", body):
        if not (folder / target.split("#")[0]).exists():
            errors.append(f"broken link: {target}")
    descriptor_path = folder / "sdp.skill.json"
    if not descriptor_path.exists():
        return errors
    if not re.search(r"\buse when\b", description or "", re.IGNORECASE):
        errors.append('description should say when to use the skill ("Use when ...")')
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    errors.extend(f"sdp.skill.json: {m}" for m in descriptor_errors(descriptor, schema))
    evaluation = folder / descriptor.get("evaluation", "evals/cases.json")
    if not evaluation.exists():
        errors.append(f"evaluation file missing: {descriptor.get('evaluation')}")
    else:
        document = json.loads(evaluation.read_text(encoding="utf-8"))
        if document.get("skill") != folder.name:
            errors.append("evals skill name must match the folder")
        errors.extend(case_errors(folder.name, document, grader))
    return errors


def main():
    schema = json.loads((SKILLS / "sdp-core/schemas/skill-descriptor.schema.json").read_text(encoding="utf-8"))
    grader = load_grader()
    failed = False
    legacy = []
    for folder in sorted(p for p in SKILLS.iterdir() if (p / "SKILL.md").exists()):
        errors = check_skill(folder, schema, grader)
        if not (folder / "sdp.skill.json").exists():
            legacy.append(folder.name)
        for error in errors:
            print(f"FAIL: {folder.name}: {error}", file=sys.stderr)
        failed = failed or bool(errors)
    if legacy:
        print("NOTE: skills without a descriptor or evaluations: " + ", ".join(legacy))
    if not failed:
        print("PASS: skill structure, descriptors, and evaluation cases.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
