import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SLIM = ROOT / ".apm" / "instructions" / "sdlc-process.instructions.md"
SKILL = ROOT / ".apm" / "skills" / "sdp-delivery-process"
DETAIL = SKILL / "references" / "process-detail.md"
MAX_ALWAYS_ON_LINES = 140

# Headings of the former single instructions file that moved, in full, into the reference.
MOVED = [
    "Right-Sizing Earlier Gates", "Artifact Approval", "Capability Sizing", "Delivery Profiles", "Assurance Triggers",
    "Delivery Contract", "Implementation Autonomy", "Supervised Delivery", "Candidate Identity", "Delivery State",
    "Parallel Delivery", "Run State and Evidence", "Worker Verdicts", "Human Acceptance", "Source-Code Traceability",
    "Feedback Routing",
]

# One distinctive sentence per moved section: if one disappears, that section was silently changed.
MOVED_CONTENT = {
    "Right-Sizing Earlier Gates": "instead of creating redundant",
    "Artifact Approval": "Bare `/deliver` is the one convenience action",
    "Capability Sizing": "Size does not determine risk.",
    "Delivery Profiles": "Profiles control assurance and evidence, not implementation quality.",
    "Assurance Triggers": "epic-level` - audit aggregate epic changes before its final acceptance;",
    "Delivery Contract": "orchestration bookkeeping do",
    "Implementation Autonomy": "briefly recording why outcome, risk, and verification remain unchanged",
    "Supervised Delivery": "`/deliver --profile compliance` raises assurance for the active plan.",
    "Candidate Identity": "changed paths, and whether relevant files changed after assurance",
    "Delivery State": "`ACTIVE.md` holds exactly these front-matter fields and no body.",
    "Parallel Delivery": "Parallel delivery is opt-in and adds no step to single-package work.",
    "Run State and Evidence": "Use the package `DELIVERY-RUN.json` as a small resume checkpoint:",
    "Worker Verdicts": "are recorded debt unless project policy says otherwise.",
    "Human Acceptance": "sets `delivery_status: awaiting-acceptance`",
    "Source-Code Traceability": "commits/PRs, and delivery history.",
    "Feedback Routing": "Non-additive overlap with another open package | Gate 4 (sequence or re-split)",
}

# Rules that must stay loaded in every conversation.
ALWAYS_ON = [
    "Do not write product code before a delivery plan is approved",
    "only a named\nhuman approves",
    "Developer validation and independent technical review are mandatory in every profile",
    "Only optional security or QA stages may be `not_applicable`",
    "Critical or High review or security findings fail assurance",
    "one repair after the first rejected candidate",
    "never revert them",
    "Never invent evidence",
    "no body",
    "read-only",
    "Only an explicit human decision accepts or rejects",
    "Do not add them as\nproduction-code comments",
    "is in the `sdp-delivery-process` skill; load it",
]


def headings(path):
    return set(re.findall(r"^## (.+)$", path.read_text(encoding="utf-8"), re.MULTILINE))


class AlwaysOnSizeTests(unittest.TestCase):
    def test_the_always_loaded_file_stays_small(self):
        lines = len(SLIM.read_text(encoding="utf-8").splitlines())
        self.assertLessEqual(lines, MAX_ALWAYS_ON_LINES, f"{lines} lines are loaded into every conversation")

    def test_the_rules_that_must_never_be_forgotten_are_still_always_on(self):
        text = SLIM.read_text(encoding="utf-8").replace("\r\n", "\n")
        for rule in ALWAYS_ON:
            with self.subTest(rule=rule):
                self.assertIn(rule, text)

    def test_the_six_gates_and_agent_routing_are_still_always_on(self):
        text = SLIM.read_text(encoding="utf-8")
        for gate in ("Discovery", "Refinement", "Architecture", "Planning", "Implementation", "Assurance and acceptance"):
            self.assertIn(f"**{gate}**", text)
        for agent in (ROOT / ".apm" / "agents").glob("sdp.*.agent.md"):
            name = agent.name[:-len(".agent.md")]
            if name != "sdp.coordinator":
                self.assertIn(f"`{name}`", text, name)


class ReferenceTests(unittest.TestCase):
    def test_every_moved_section_exists_in_the_reference(self):
        present = headings(DETAIL)
        text = DETAIL.read_text(encoding="utf-8")
        for heading in MOVED:
            with self.subTest(heading=heading):
                self.assertIn(heading, present)
        for heading, sentence in MOVED_CONTENT.items():
            with self.subTest(heading=heading):
                self.assertIn(sentence, text, f"the '{heading}' section was silently altered")

    def test_the_skill_has_discovery_frontmatter(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: sdp-delivery-process", text)
        self.assertIn("Use when planning, delivering, reviewing, resuming, or auditing", text)

    def test_the_skill_names_every_section_it_points_to(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for heading in ("Right-Sizing Earlier Gates", "Assurance Triggers", "Delivery Contract", "Supervised Delivery",
                        "Candidate Identity", "Delivery State", "Parallel Delivery", "Human Acceptance", "Feedback Routing"):
            self.assertIn(heading, text)
            self.assertIn(heading, headings(DETAIL))

    def test_the_agents_that_need_the_detail_are_told_where_it_is(self):
        for name in ("sdp.orchestrator", "sdp.planner"):
            text = (ROOT / ".apm" / "agents" / f"{name}.agent.md").read_text(encoding="utf-8")
            self.assertIn("sdp-delivery-process", text, name)

    def test_nothing_still_points_at_text_that_no_longer_exists(self):
        for path in list((ROOT / ".apm").rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("from the process instructions", text, path.name)

    def test_the_generated_root_context_carries_the_slim_file_not_the_old_one(self):
        generated = (ROOT / "AGENTS.md").read_text(encoding="utf-8").replace("\r\n", "\n")
        self.assertNotIn("## Parallel Delivery", generated)
        self.assertIn("`sdp-delivery-process`", generated)


if __name__ == "__main__":
    unittest.main()
