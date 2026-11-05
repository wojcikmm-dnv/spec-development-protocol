#!/usr/bin/env python3
"""Check source metadata and textual contracts, not delivery execution."""

import argparse
import copy
import json
from pathlib import Path
import sys
import unittest

try:
    import yaml
except ImportError:
    sys.exit("Baseline check requires Python 3 and PyYAML; no dependencies were installed.")


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATHS = (
    "plugin.json",
    ".github/plugin/plugin.json",
    ".claude-plugin/plugin.json",
)


def read_text(path):
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def frontmatter(text):
    sections = text.split("---\n", 2)
    if len(sections) != 3 or sections[0]:
        raise ValueError("Missing YAML frontmatter")
    metadata = yaml.safe_load(sections[1])
    if not isinstance(metadata, dict):
        raise ValueError("Frontmatter must be a mapping")
    return metadata, sections[2].strip()


def snapshot(root):
    template = read_text(root / ".apm/templates/template.skill.md")
    instructions = [
        frontmatter(read_text(path))[1]
        for path in sorted((root / ".apm/instructions").glob("*.instructions.md"))
    ]
    return {
        "package": yaml.safe_load(read_text(root / "apm.yml")),
        "manifests": {
            path: json.loads(read_text(root / path)) for path in MANIFEST_PATHS
        },
        "template": frontmatter(template)[0],
        "orchestrator": read_text(root / ".apm/agents/sdp.orchestrator.agent.md"),
        "generated": read_text(root / "AGENTS.md"),
        "instructions": instructions,
    }


def validate(data):
    errors = []
    package = data["package"]
    for path, manifest in data["manifests"].items():
        for field in ("name", "version"):
            if manifest.get(field) != package.get(field):
                errors.append(f"{path}: {field} differs from apm.yml")
    if data["template"].get("name") != "<skill-name>":
        errors.append("Skill starter must declare name: <skill-name>")
    normalized = " ".join(data["orchestrator"].split())
    required = (
        "Developer validation and independent technical review are mandatory in every profile",
        "neither stage may return `not_applicable`",
        "only optional security or QA stages may return `not_applicable`",
        "does not override mandatory project controls",
    )
    for statement in required:
        if statement not in normalized:
            errors.append(f"Orchestrator missing mandatory-stage contract: {statement}")
    if "Lean/Balanced stages may return `not_applicable`" in normalized:
        errors.append("Orchestrator still permits generic stage skipping")
    generated = data["generated"]
    for body in data["instructions"]:
        if body not in generated:
            errors.append("AGENTS.md is out of sync with canonical instructions; regenerate with APM")
    if "feature_status: <in-progress" in generated:
        errors.append("AGENTS.md still describes legacy shared delivery state")
    return errors


def mirror_errors(root):
    source = root / ".apm/templates"
    mirror = root / ".apm/skills/sdp-templates/assets"
    source_files = {path.relative_to(source): path for path in source.rglob("*") if path.is_file()}
    mirror_files = {path.relative_to(mirror): path for path in mirror.rglob("*") if path.is_file()}
    if source_files.keys() != mirror_files.keys():
        return ["Template mirror file set differs from canonical templates"]
    return [
        f"Template mirror differs: {relative}"
        for relative, path in source_files.items()
        if path.read_bytes() != mirror_files[relative].read_bytes()
    ]


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(snapshot(ROOT))

    def test_current_baseline(self):
        self.assertEqual([], validate(self.data))
        self.assertEqual([], mirror_errors(ROOT))

    def test_stale_manifest_versions(self):
        for path in MANIFEST_PATHS:
            with self.subTest(path=path):
                data = copy.deepcopy(self.data)
                data["manifests"][path]["version"] = "0.5.2"
                self.assertTrue(any("version differs" in error for error in validate(data)))

    def test_missing_skill_name(self):
        self.data["template"].pop("name", None)
        self.assertTrue(any("Skill starter" in error for error in validate(self.data)))

    def test_generic_review_skip_permission(self):
        self.data["orchestrator"] = "Lean/Balanced stages may return `not_applicable` with a policy reason."
        self.assertTrue(any("generic stage skipping" in error for error in validate(self.data)))

    def test_missing_mandatory_review_contract(self):
        self.data["orchestrator"] = "Dispatch developer and reviewer when applicable."
        self.assertTrue(any("mandatory-stage contract" in error for error in validate(self.data)))

    def test_legacy_shared_state(self):
        self.data["generated"] += "\nfeature_status: <in-progress | blocked | done>\n"
        self.assertTrue(any("legacy shared" in error for error in validate(self.data)))

    def test_stale_generated_context(self):
        self.data["generated"] = "# AGENTS.md\n"
        self.assertTrue(any("out of sync" in error for error in validate(self.data)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="also exercise historical drift cases in memory")
    arguments = parser.parse_args()
    try:
        errors = validate(snapshot(ROOT)) + mirror_errors(ROOT)
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: package metadata, skill starter, mandatory-stage wording, generated context, and template mirror.")
    if arguments.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(RegressionTests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())