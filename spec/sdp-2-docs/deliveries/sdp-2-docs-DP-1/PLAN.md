---
status: approved
approved_by: user (chat: "continue with next task")
approved_at: 2026-11-06T00:30:00+01:00
---

# Step 12: User Documentation

## Outcome and Boundary

Rewrite the user documentation around choosing a workflow, an installation channel,
initialization, scope approval, evidence, and acceptance. Move long inventories and policy
into focused reference documents. State only what was observed: no claim of untested host
support, no measured benefits, no 2.0 release that does not exist.

Step 13 (removing installers and superseded agents) was not started: its own preconditions
(a verified replacement channel and explicit approval of removals) are not met.

- Size: M; risk: Moderate (users follow these instructions); uncertainty: Resolved.
  Profile: Balanced with independent QA by following the documents.

## Acceptance Criteria

1. The README is concise and leads with the choice of workflow, channel, initialization, and
   acceptance; long material lives in `docs/`.
2. Every command, flag, variable, default, state, pinned tag, and path the documents name
   exists, and inventories equal the package contents.
3. Channel verification status and host observations are stated as observed.
4. Mixed-install detection, ownership, runtime requirements, validation limits, migration
   range, and rollback are documented.

## Allowed Paths

`README.md`, `docs/**`, `tests/release/test_docs.py`, `CHANGELOG.md`, `PLAN.md`, this
package's records.
