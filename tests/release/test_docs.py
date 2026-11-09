import importlib.util
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
CODE_SPAN = re.compile(r"`([^`\n]+)`")
FENCE = re.compile(r"^```", re.MULTILINE)
# Options of tools outside this repository that the documents show.
EXTERNAL_FLAGS = {"--dry-run", "--local-only", "--single-agents", "--target", "--output", "--plugin-dir", "--deny-tool",
                  "--max-ai-credits", "--archive", "--marketplace", "--check-versions", "--check-clean", "--version"}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prose(text):
    """The document without fenced code blocks."""
    parts = FENCE.split(text)
    return "".join(parts[::2])


def slug(heading):
    text = re.sub(r"`", "", heading.strip().lower())
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path):
    found, fenced = set(), False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#{1,6} ", line):
            found.add(slug(line.lstrip("#")))
    return found


class LinkTests(unittest.TestCase):
    def test_every_relative_link_and_anchor_resolves(self):
        for document in DOCS:
            for target in LINK.findall(prose(document.read_text(encoding="utf-8"))):
                if re.match(r"[a-z]+:", target):
                    continue
                path, _, anchor = target.partition("#")
                resolved = (document.parent / path).resolve() if path else document
                with self.subTest(document=document.name, target=target):
                    self.assertTrue(resolved.exists(), f"{document.name} links to missing {target}")
                    if anchor and resolved.suffix == ".md":
                        self.assertIn(anchor, anchors(resolved), f"{document.name}: no heading for #{anchor} in {resolved.name}")

    def test_repository_paths_named_in_docs_exist(self):
        for document in DOCS:
            for span in CODE_SPAN.findall(document.read_text(encoding="utf-8")):
                match = re.fullmatch(r"((?:scripts|docs|tests|\.apm)/[\w./-]+?)/?", span)
                if not match or any(char in span for char in "<*"):
                    continue
                with self.subTest(document=document.name, path=span):
                    self.assertTrue((ROOT / match.group(1)).exists(), f"{document.name} names missing {span}")

    def test_script_paths_under_installed_skills_exist(self):
        for document in DOCS:
            for skill, script in re.findall(r"<installed skills>/([\w-]+)/scripts/([\w.-]+)", document.read_text(encoding="utf-8")):
                with self.subTest(document=document.name, script=f"{skill}/{script}"):
                    self.assertTrue((ROOT / ".apm" / "skills" / skill / "scripts" / script).is_file())

    def test_slash_commands_named_in_docs_are_real_prompts(self):
        prompts = {p.name[:-len(".prompt.md")] for p in (ROOT / ".apm" / "prompts").glob("*.prompt.md")}
        for document in DOCS:
            for command in re.findall(r"`/([a-z][a-z-]+)(?: [^`]*)?`", prose(document.read_text(encoding="utf-8"))):
                with self.subTest(document=document.name, command=command):
                    self.assertIn(command, prompts)


class InventoryTests(unittest.TestCase):
    reference = (ROOT / "docs" / "REFERENCE.md").read_text(encoding="utf-8")

    def section(self, name):
        return self.reference.split(f"## {name}")[1].split("\n## ")[0]

    def listed(self, name):
        return set(re.findall(r"^\| `([^`]+)`", self.section(name), re.MULTILINE))

    def test_the_agent_prompt_and_skill_tables_list_exactly_what_exists(self):
        agents = {a.name[:-len(".agent.md")] for a in (ROOT / ".apm" / "agents").glob("*.agent.md")}
        prompts = {"/" + p.name[:-len(".prompt.md")] for p in (ROOT / ".apm" / "prompts").glob("*.prompt.md")}
        skills = {s.name for s in (ROOT / ".apm" / "skills").iterdir()}
        self.assertEqual(agents, self.listed("Agents"))
        self.assertEqual(prompts, self.listed("Prompts"))
        self.assertEqual(skills, self.listed("Skills"))

    def test_the_template_table_lists_exactly_the_templates(self):
        rows = set()
        for cell in re.findall(r"^\| ([^|]+) \|", self.section("Templates"), re.MULTILINE):
            rows.update(re.findall(r"`([^`]+)`", cell))
        existing = {t.name for t in (ROOT / ".apm" / "templates").iterdir()}
        self.assertEqual(existing, rows)

    def test_the_customization_table_points_at_real_conventions(self):
        text = self.section("Customization")
        for path in (".github/instructions/coding-standards.instructions.md", ".github/TECH.md"):
            self.assertIn(path, text)
        self.assertTrue((ROOT / ".apm" / "instructions" / "coding-standards.instructions.md").is_file())


class ClaimTests(unittest.TestCase):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    installation = (ROOT / "docs" / "INSTALLATION.md").read_text(encoding="utf-8")

    def test_the_repository_and_package_names_match_the_manifest(self):
        manifest = (ROOT / "apm.yml").read_text(encoding="utf-8")
        name = re.search(r"^name:\s*(\S+)", manifest, re.MULTILINE).group(1)
        owner = re.search(r"owner:\s*\n\s*name:\s*(\S+)", manifest).group(1)
        for text in (self.readme, self.installation):
            self.assertIn(f"{owner}/{name}", text)
            self.assertNotRegex(text, rf"(?i)(?<!{owner}/){name}@(?!{name})")

    def test_install_commands_agree_between_the_readme_and_the_installation_guide(self):
        for command in ("apm install WojcikMM/spec-development-protocol",
                        "copilot plugin marketplace add WojcikMM/spec-development-protocol"):
            self.assertIn(command, self.readme)
            self.assertIn(command, self.installation)

    def test_no_host_is_called_qualified_and_untested_hosts_are_not_claimed(self):
        for text in (self.readme, self.installation):
            self.assertNotRegex(text, r"(?i)\bqualified (on|for|with)\b")
        self.assertIn("Not tested", self.readme)
        self.assertIn("Claude Code was not available", self.installation)

    def test_the_documents_do_not_promise_measured_benefits(self):
        pattern = (r"(?i)(\b\d+(\.\d+)?\s*(%|x|\u00d7|times)\s*(faster|quicker|more productive|productivity|fewer|better|cheaper))"
                   r"|\b(twice|double|triple)\b[^.\n]{0,20}\b(fast|quick|productiv)|\b(faster|quicker) delivery\b")
        for document in DOCS:
            self.assertNotRegex(document.read_text(encoding="utf-8"), pattern, document.name)

    def test_every_option_the_documents_show_exists_in_this_repository_or_a_named_tool(self):
        known = set(EXTERNAL_FLAGS)
        for source in [*(ROOT / ".apm" / "skills").glob("*/scripts/*.py"), *(ROOT / "scripts").glob("*.py")]:
            known.update(re.findall(r"add_argument\(\s*\"(--[a-z][a-z-]*)\"", source.read_text(encoding="utf-8")))
        for document in DOCS:
            if document.name in ("PROTOCOL.md", "COMPATIBILITY.md", "RELEASING.md"):
                continue
            for flag in set(re.findall(r"(?<![\w-])(--[a-z][a-z-]+)", document.read_text(encoding="utf-8"))):
                with self.subTest(document=document.name, flag=flag):
                    self.assertIn(flag, known)

    def test_the_docs_do_not_present_the_retired_install_scripts(self):
        for text in (self.readme, self.installation):
            self.assertNotIn("install.sh", text)
            self.assertNotIn("install.ps1", text)
            self.assertNotIn("SDP_BRANCH", text)

    def test_the_documented_states_are_the_validators_states(self):
        core = load_module("sdp_core_for_docs", ROOT / ".apm" / "skills" / "sdp-core" / "scripts" / "sdp.py")
        workflow = (ROOT / "docs" / "WORKFLOW.md").read_text(encoding="utf-8")
        diagram = workflow.split("planned -> delivering")[1].split("```")[0]
        shown = set(re.findall(r"[a-z]+(?:-[a-z]+)*", "planned -> delivering" + diagram)) - {"delivering"} | {"delivering"}
        self.assertEqual(set(core.STATUSES), shown)
        for profile in core.PROFILES:
            self.assertIn(profile, workflow)

    def test_the_recommended_default_profile_is_the_templates_default(self):
        template = (ROOT / ".apm" / "templates" / "TECH.md").read_text(encoding="utf-8")
        self.assertIn("Balanced", template)
        self.assertIn("Balanced is the default", (ROOT / "docs" / "WORKFLOW.md").read_text(encoding="utf-8"))
        self.assertIn("Balanced is\nrecommended", self.readme)

    def test_host_claims_never_exceed_the_compatibility_matrix(self):
        matrix = (ROOT / "docs" / "COMPATIBILITY.md").read_text(encoding="utf-8").split("## Matrix")[1].split("\n## ")[0]
        rows = [[cell.strip() for cell in line.strip("|").split("|")] for line in matrix.splitlines() if line.startswith("| ") and "---" not in line][1:]
        self.assertTrue(rows)
        executed = any(row[5].lower().startswith("yes") for row in rows)
        qualified = any(row[6].lower().startswith("yes") for row in rows)
        readme = " ".join(self.readme.split())
        self.assertEqual(executed, "No host has executed a full delivery" not in readme)
        self.assertEqual(qualified, "no host is qualified" not in readme)

    def test_versions_named_as_pins_are_real_tags_when_tags_are_available(self):
        tags = subprocess.run(["git", "-C", str(ROOT), "tag"], capture_output=True, text=True).stdout.split()
        if not tags:
            self.skipTest("no tags in this checkout")
        for document in DOCS:
            for tag in set(re.findall(r"(?:SDP_BRANCH=|#)(v\d+\.\d+\.\d+)\b", document.read_text(encoding="utf-8"))):
                self.assertIn(tag, tags, f"{document.name} pins {tag}")

    def test_the_documented_python_floor_matches_the_ci_job(self):
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn('python-version: "3.9"', ci)
        self.assertIn("Python 3.9 or newer", self.readme)

    def test_the_documented_apm_version_matches_the_pin(self):
        import json
        pinned = json.loads((ROOT / "scripts" / "release-tools.json").read_text(encoding="utf-8"))["apm"]
        self.assertIn(f"APM {pinned}", self.installation)

    def test_release_evidence_distinguishes_ci_from_publication_and_host_execution(self):
        text = (ROOT / "docs" / "RELEASING.md").read_text(encoding="utf-8")
        verified = text.split("## Verified CI evidence")[1].split("\n## ")[0]
        for evidence in ("42222480747", "bf43597f66e1f2a8a108a61c2e90cf5cb94b0a91",
                         "Linux, Python 3.12", "Windows, Python 3.12", "Python 3.9"):
            self.assertIn(evidence, verified)
        self.assertIn("It does not prove", verified)
        pending = text.split("## What is not verified")[1]
        self.assertIn("release workflow has never run", pending)
        self.assertIn("Python 3.9 host execution", pending)
        self.assertNotIn("Neither fix has been confirmed", text)
        self.assertNotIn("scripts parse as 3.9 but were run", text)

    def test_local_rehearsal_preparation_preserves_authorization_boundaries(self):
        text = (ROOT / "docs" / "RELEASING.md").read_text(encoding="utf-8")
        preparation = text.split("### Preparing a prerelease rehearsal locally")[1].split("\n## ")[0]
        for boundary in ("not the current package version or an approved release",
                         "Stop for separate owner authorization", "it is not a dry run",
                         "separately agreed spending limit", "explicit removal approval"):
            self.assertIn(boundary, preparation)

    def test_archive_reproducibility_evidence_is_bound_to_a_candidate_and_environment(self):
        text = (ROOT / "docs" / "RELEASING.md").read_text(encoding="utf-8")
        evidence = text.split("## Verified archive reproducibility")[1].split("\n## ")[0]
        for detail in ("Windows and WSL Linux", "e7908dee783ea8a18275c826d6c413f6e25f6e29",
                       "0.29.0", "88757e6cfbc291fb6179e8764939ec4878f505721ffe804fc435181b305eb215",
                       "not a", "guarantee for later candidates"):
            self.assertIn(detail, evidence)
        self.assertIn("actual GitHub release runner's archive bytes", text)
        self.assertNotIn("across operating systems was observed on Windows only", text)


if __name__ == "__main__":
    unittest.main()
