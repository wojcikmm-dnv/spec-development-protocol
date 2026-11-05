---
status: approved
approved_by: user (chat instruction to continue the roadmap in order)
approved_at: 2026-11-05T21:00:00+01:00
---

# Step 08a: Feature Workflow

## Outcome and Boundary

Express the gated feature process as the `feature` workflow in the schema 4 path:
upstream gates derived from artifact approvals, human-only artifact approval, story and
feature status derived from accepted packages, a lightweight shortcut that never drops
review or acceptance, and shared specs frozen during delivery.

Step 08 is split. This package is 08a only. 08b (slimming the always-on instructions and
replacing agent handoff chains) is deferred to Step 13 because the legacy agents still
read that file.

- Size: L; risk: High (a second approval path); uncertainty: Resolved. Profile: Balanced
  with independent review and security attention.

## Acceptance Criteria

1. The feature workflow's gates, story availability, and completion are derived from
   files and records, not stored.
2. Artifact approval needs a named human, can be bound to what the human saw, and is
   refused during delivery.
3. A plan cannot be approved while a gate is open unless it is lightweight with a stated
   basis; lightweight never skips independent review or acceptance.
4. Plan approval covers all machine-read frontmatter.
5. Existing bug workflow behavior is unchanged.

## Allowed Paths

`.apm/skills/sdp-core/scripts/sdp.py`, `.apm/skills/sdp-workflows/**`,
`.apm/skills/sdp-plan-delivery/SKILL.md`, `tests/contracts/**`, `docs/PROTOCOL.md`,
`PLAN.md`, `CHANGELOG.md`, this package's records.
