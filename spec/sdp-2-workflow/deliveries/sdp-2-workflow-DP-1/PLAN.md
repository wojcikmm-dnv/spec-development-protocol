---
status: approved
approved_by: user (chat instruction to continue the roadmap in order)
approved_at: 2026-11-05T15:00:00+01:00
---

# Step 05: Bug Workflow and Coordinator

## Outcome and Boundary

Add a validated `bug` workflow definition and a read-only `next` command that derives
the next action from stored facts, plus the `sdp-workflows` coordinator skill that
follows it. The existing `sdp.orchestrator` agent and prompts are unchanged; host
wiring is Step 06 and feature-workflow wiring is Step 08.

- Size: L; risk: High (approval, assurance routing, escalation); uncertainty: Resolved
  by PROTOCOL.md. Profile: Balanced with independent review. Security: the
  environment override and approval binding were reviewed by the independent
  reviewer. QA: scenario tests drive the workflow only through `next`.

## Acceptance Criteria

1. The bug workflow references capabilities and skills, never agent names, and the
   validator refuses definitions that weaken review, isolation, order, or the limit.
2. `next` handles every delivery status, including resume, human-requested changes,
   stale evidence, stale approval, escalation, blocks, triggers, and missing host
   capabilities, and never writes.
3. Approval can bind to the plan the human reviewed.
4. A coordinator skill tells an agent exactly how to follow `next`, never edit
   product code, and never accept or commit.
5. Scenarios from the roadmap pass: failed review, one repair, interruption and
   resume, candidate change after assurance, second-rejection escalation.

## Allowed Paths

`.apm/skills/sdp-workflows/**`, `.apm/skills/sdp-core/scripts/sdp.py`,
`tests/contracts/test_workflow.py`, `docs/PROTOCOL.md`, `CHANGELOG.md`, this
package's records.
