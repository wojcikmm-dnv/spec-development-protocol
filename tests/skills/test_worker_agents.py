"""Worker agents route to their stage skills and keep their record duties."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / ".apm" / "agents"
SKILLS = ROOT / ".apm" / "skills"

STAGE_SKILLS = {
    "sdp.developer": "sdp-implement",
    "sdp.reviewer": "sdp-technical-review",
    "sdp.security": "sdp-security-review",
    "sdp.qa": "sdp-acceptance-validation",
}

# Sentences that belong to the stage skills only; their presence in an agent
# would mean the duplicated procedure text is creeping back.
PROCEDURE_IN_SKILL = {
    "sdp.developer": "Touch shared hotspots additively",
    "sdp.reviewer": "Inspect the actual changes",
    "sdp.security": "Map the changed attack surface",
    "sdp.qa": "closest representative environment",
}

TOOLS = {
    "sdp.developer": "tools: [read, search, edit, execute]",
    "sdp.reviewer": "tools: [read, search]",
    "sdp.security": "tools: [read, search, execute]",
    "sdp.qa": "tools: [read, search, execute]",
}

HANDOFFS = {
    "sdp.developer": [("sdp.reviewer", True)],
    "sdp.reviewer": [("sdp.security", False), ("sdp.qa", False), ("sdp.developer", False)],
    "sdp.security": [("sdp.qa", False), ("sdp.developer", False)],
    "sdp.qa": [("sdp.developer", False)],
}

# Choice strings kept on one file line each so newline reflow cannot hide them.
CONSTRAINTS = {
    "sdp.developer": ["Require an approved `PLAN.md`", "Never call yourself again or regenerate `PLAN.md`"],
    "sdp.reviewer": ["Never edit product code", "Critical/High findings fail"],
    "sdp.security": ["Respect an explicit `waived` policy", "Never edit product code", "Critical/High findings fail"],
    "sdp.qa": ["Unmet required ACs fail", "Never edit product code", "A QA pass is not human acceptance"],
}

MAX_WORKER_LINES = 60


def agent_text(name):
    return (AGENTS / f"{name}.agent.md").read_text(encoding="utf-8").replace("\r\n", "\n")


def frontmatter(text):
    start = text.index("---\n") + 4
    end = text.index("\n---", start)
    return text[start:end]


def handoff_sends(fm_text):
    sends = {}
    for entry in re.split(r"\n\s*-\s+label:", fm_text)[1:]:
        agent = re.search(r"agent:\s*(\S+)", entry).group(1)
        sends[agent] = re.search(r"send:\s*(true|false)", entry).group(1) == "true"
    return sends


class WorkerAgentTests(unittest.TestCase):
    def test_every_worker_agent_points_at_its_shipped_stage_skill(self):
        for agent_name, skill_name in STAGE_SKILLS.items():
            with self.subTest(agent=agent_name, skill=skill_name):
                skill_file = SKILLS / skill_name / "SKILL.md"
                self.assertTrue(skill_file.exists(), skill_name)
                self.assertIn(f"name: {skill_name}", skill_file.read_text(encoding="utf-8"))
                self.assertIn(f"`{skill_name}`", agent_text(agent_name), agent_name)

    def test_duplicated_procedure_text_lives_in_the_skills_not_the_agents(self):
        for agent_name, sentence in PROCEDURE_IN_SKILL.items():
            with self.subTest(agent=agent_name):
                skill_name = STAGE_SKILLS[agent_name]
                self.assertIn(sentence, (SKILLS / skill_name / "SKILL.md").read_text(encoding="utf-8"))
                self.assertNotIn(sentence, agent_text(agent_name), agent_name)

    def test_frontmatter_tools_and_handoffs_are_unchanged(self):
        for agent_name, sent in HANDOFFS.items():
            with self.subTest(agent=agent_name):
                fm = frontmatter(agent_text(agent_name))
                self.assertIn(TOOLS[agent_name], fm)
                self.assertEqual({agent: expected for agent, expected in sent}, handoff_sends(fm))

    def test_record_duties_and_hard_constraints_stay_inline(self):
        for agent_name, constraints in CONSTRAINTS.items():
            with self.subTest(agent=agent_name):
                text = agent_text(agent_name)
                for constraint in constraints:
                    self.assertIn(constraint, text, (agent_name, constraint))

    def test_worker_agents_stay_small(self):
        for agent_name in STAGE_SKILLS:
            with self.subTest(agent=agent_name):
                self.assertLessEqual(len(agent_text(agent_name).splitlines()), MAX_WORKER_LINES, agent_name)

    def test_record_duty_references_reach_the_run_record(self):
        self.assertIn("package run record", agent_text("sdp.developer"))
        self.assertIn("awaiting-acceptance", agent_text("sdp.qa"))


if __name__ == "__main__":
    unittest.main()
