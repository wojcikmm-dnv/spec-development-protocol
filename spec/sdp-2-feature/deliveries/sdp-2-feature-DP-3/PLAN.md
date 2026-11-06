---
status: approved
approved_by: user (chat: start implementation)
approved_at: 2026-11-06
---

# Consolidate the Worker Agents onto Their Stage Skills

## Outcome and Boundary

The four worker agents duplicate their stage skills' procedures. They keep routing, record
duties, verdict scales, and hard constraints, and point at the shipped skills for the full
procedures: `sdp.developer` -> `sdp-implement`, `sdp.reviewer` -> `sdp-technical-review`,
`sdp.security` -> `sdp-security-review`, `sdp.qa` -> `sdp-acceptance-validation`.

- Size: S; risk: Low (templates, not product code); uncertainty: Resolved; profile:
  Balanced.
- Allowed paths: the four `.apm/agents/sdp.developer/reviewer/security/qa.agent.md`
  files, `tests/skills/test_worker_agents.py` (new), the `CHANGELOG.md` Changed bullet,
  the `PLAN.md` Step 08 note, and this package.
- Frontmatter (tools, handoffs and send flags), entry/run conditions, modes, verdict
  scales, and hard constraints are preserved, not moved.

## Acceptance Criteria

1. Each worker agent names its shipped stage skill, and each skill exists with matching
   frontmatter.
2. The hard constraints stay named inline: the developer never regenerates the plan;
   reviewer, security, and QA never edit product code; a QA pass is not human acceptance.
3. Frontmatter tools and handoff edges with send flags are unchanged.
4. A focused test module asserts the pointers, the preserved constraints, and that the
   referenced skills exist; the skills and release suites, baseline checks,
   install-script syntax, and whitespace checks pass; independent review passes; human
   acceptance stays explicit.

## Steps and Verification

1. Confirm equivalent sections exist in the four stage skills before editing.
2. Replace each agent's Responsibilities procedure block with a skill pointer plus its
   record duties.
3. Add `tests/skills/test_worker_agents.py`.
4. Update the changelog's Changed section and the Step 08 note in `PLAN.md`.
5. Run the skills and release suites, `python scripts/check-baseline.py`,
   `python scripts/check-skills.py`, `bash -n install.sh`, and `git diff --check`.
6. Independent read-only technical review, recorded with actual evidence.
7. Present the package for human acceptance.

Agent names and handoffs are unchanged, so `docs/PROTOCOL.md` command mappings, the
routing table, and the manifests need no update.
