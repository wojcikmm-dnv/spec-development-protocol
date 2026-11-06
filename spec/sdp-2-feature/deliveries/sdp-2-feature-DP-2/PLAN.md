---
status: approved
approved_by: user (chat answer: the slim always-on instructions option)
approved_at: 2026-11-06
---

# Step 08b: Reduce Always-On Process Instructions

## Outcome and Boundary

Move the full schema-3 delivery process text verbatim out of the always-on
instructions into the on-demand `sdp-delivery-process` skill; keep startup
routing, ownership, safety invariants, and links always-on; regenerate root
`AGENTS.md`; keep prompts as thin entry points.

This package covers the instructions half of the split Step 08b only.
Replacing duplicated agent procedures and handoff chains remains with Step 13
because the legacy agents and `/deliver` read those files. The new workflow
path does not depend on the instructions file; it is self-contained in the
`sdp-core` and `sdp-workflows` skills.

- Size: M; risk: Moderate (this text is loaded into every conversation);
  uncertainty: Resolved. Profile: Balanced with independent review. Security
  is not triggered: no executable, authentication, or trust-boundary change.
  Whether a host reliably loads the skill on demand is unobserved and stays a
  recorded limit, not a claim in acceptance documents.

## Acceptance Criteria

1. The always-on file keeps only startup context resolution, agent routing,
   the six gates, approvals, state ownership, the repair ceiling, and
   acceptance rules, and stays under 140 lines.
2. The full process text is preserved verbatim in the skill's reference;
   nothing is lost or silently weakened.
3. The skill has required discovery frontmatter (`name`, a specific trigger
   description) and the relative link resolves from the skill folder.
4. The orchestrator and planner agents reference the skill consistently with
   its `name`; nothing still points at removed instruction text.
5. The generated root `AGENTS.md` agrees with the canonical `.apm` source.
6. Tests enforce the contract: always-on line cap, always-on invariants,
   frontmatter, moved-section headings and content, and no stale pointers.

## Verification

`python scripts/run-suites.py skills contracts`, `python scripts/check-baseline.py`,
`python scripts/check-skills.py`, the template mirror sync check, and
`python scripts/build-release.py --check`. A git diff of the moved file closes
the verbatim-transfer question against the pre-change state.

## Allowed Paths

`.apm/instructions/**`, `.apm/agents/**`, `.apm/skills/sdp-delivery-process/**`,
`AGENTS.md`, `CHANGELOG.md`, `PLAN.md`, `docs/REFERENCE.md`, `tests/skills/**`,
this package's records.
