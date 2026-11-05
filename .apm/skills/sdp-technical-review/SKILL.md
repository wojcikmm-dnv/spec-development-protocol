---
name: sdp-technical-review
description: Independently reviews a code change for correctness, scope, tests, and maintainability. Use when a delivery candidate is ready for review, before security or acceptance validation; must run in a separate context from the implementer and never edits code.
---

# Technical Review

## Purpose

Give independent confidence that the change is correct, tested, maintainable, and
inside the approved contract. This stage is mandatory for every implementation.

## Independence

Run in a different context from the implementer, with read-only access to the code.
If the host cannot provide that, report `blocked`; do not review your own work and
call it independent.

## Procedure

1. **Inspect the actual changes**, not the description of them, plus the neighboring
   code they touch.
2. **Check scope:** every changed path is inside the plan's boundary and serves the
   outcome. Flag unplanned dependencies, contract changes, and drive-by edits.
3. **Check correctness:** logic, edge cases, error handling, concurrency, resource
   handling, compatibility, and regressions in callers.
4. **Check tests:** each changed behavior has a test that would fail without it;
   tests assert behavior, not implementation; none were skipped or weakened.
5. **Check comments and traceability:** flag story or criterion IDs, step narration,
   completed TODOs, and comments that restate code.
6. **Report triggers** for any security or QA area touched, even if you cannot judge
   it. Do not dismiss a trigger; the specialist stage or a human disposes of it.
7. **Decide the verdict** using `sdp-core/references/stage-result.md`.

## Output

A `stage-result`: verdict, findings with severity, path and line, and a concrete
fix each, checks performed, evidence, triggers, and next action. Never edit code.

## Compliance Profile

Review is mandatory in every profile. In Compliance, also return the extra evidence
`TECH.md` configures, as produced by project tooling; never invent it.

## Quality Bar

- Each finding is reproducible from the cited location.
- A Critical or High finding is never softened to pass.
- "Looks fine" is never a finding; state what you checked.
- Praise and style preferences are omitted unless they hide a defect.
