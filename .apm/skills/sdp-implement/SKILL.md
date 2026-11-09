---
name: sdp-implement
description: Implements one approved delivery plan with focused tests inside its change boundary. Use when an approved PLAN.md exists and code must be changed to deliver it, including repairs after a failed review; escalates instead of expanding scope.
---

# Implement an Approved Plan

## Purpose

Deliver the approved outcome safely within its boundary, with tests that prove it,
and hand back an honest result for independent review.

## Prerequisites

- An approved plan whose body has not changed since approval. If it has, stop.
- Required capabilities available (build, test, and a way to hand off for review).

## Procedure

1. **Read only what you need:** the plan, scoped `AGENTS.md`, the settled decisions,
   the owning code, and neighboring tests.
2. **Learn the local conventions before writing.** Find the closest existing
   implementation of the same kind (a sibling endpoint, component, migration, or
   test) and match its structure, naming, error shape, and test style. Use the
   build, test, and lint commands from `TECH.md`; do not guess them. Establish a
   green baseline for the touched area first, so a later failure is yours.
3. **Load the matching domain skill** for each kind of change in the plan:
   `create-api-endpoint` (HTTP routes and contracts), `create-ui-component` (frontend),
   `database-migration` (schema and data changes), `error-handling` (failures,
   retries, user-facing errors). Apply it as a checklist, not as extra scope.
4. **Work the steps in order**, one small increment at a time. For each increment:
   write or extend the test that expresses the behavior and watch it fail for the
   right reason, make it pass with the simplest change, then run the step's check
   before moving on. When behavior cannot be driven by a test first, say so and
   verify it by running it.
5. **Use the autonomy the plan grants** for naming, idiomatic local design, helper
   reuse, and adjacent tests. A simpler approach inside the boundary is fine when
   outcome, risk, and verification are unchanged; note why in one sentence.
6. **Write tests** with the `write-tests` skill. Test observable behavior; do not
   weaken or delete a failing test to get a pass.
7. **When a check fails, find the cause before changing anything.** Read the actual
   error, form one hypothesis, change one thing, rerun. After two failed attempts
   on the same failure, stop and re-read the code and the plan instead of
   guessing again; if the cause is outside the boundary or the plan is wrong,
   escalate. Never silence, skip, or loosen a check to proceed.
8. **Touch shared hotspots additively:** add new files where the pattern allows,
   insert self-contained blocks, never reorder or reformat neighbors, do not
   regenerate lockfiles or run repository-wide formatting unless a dependency
   change is in the boundary. For migrations, use timestamp or package-unique
   identifiers when the toolchain supports them and never renumber existing ones.
9. **Keep comments durable.** No story, task, or criterion IDs, no step narration,
   no change history, no completed TODOs. Comment only a non-obvious invariant,
   compatibility constraint, security rationale, or deliberate trade-off.
10. **Run the plan's verification** and the project's build, lint, and tests, and
    read the output. Do not report a check you did not run.
11. **Review your own diff before handing off.** Read the full diff and confirm that
    every changed path is inside the boundary; every acceptance criterion maps to
    a test that exercises it; no debug output, dead code, commented-out code,
    stray files, or unrelated reformatting remain; inputs, errors, and empty or
    boundary values are handled; and no secret or personal data was added. Fix
    what you find. This is hygiene, not independent review, which still follows.
12. **Report** changed paths, checks with results, deviations, unresolved risks, the
    acceptance criteria with the test that covers each, anything you could not
    verify, and triggers (`security:*`, `qa:*`) for areas you touched.

## Escalation

Stop and return to planning for a new dependency or service, a changed public
contract, an expanded data or security boundary, a destructive operation, a weakened
acceptance criterion, or any path outside the boundary. Do not self-approve.

## Repairs

After a failed review, change the candidate to address the finding. A repair that
changes scope, outcome, or boundaries is a replan, not a repair. Do not re-submit an
unchanged candidate.

One autonomous repair is allowed after the first rejected candidate. If the repaired
candidate is rejected too, stop and hand the findings to a human; a further repair
needs human guidance. Environment failures are not rejections.

## Compliance Profile

Profile does not change how you implement. When Compliance is selected, report the
environment and evidence `TECH.md` asks for, as produced by project tooling.

## Quality Bar

- Every changed behavior has a test that fails without the change.
- The diff stays inside the allowed paths and follows the neighboring code's conventions.
- Reported checks were actually run and their output was read.
- Unverified behavior is named as unverified, never implied to work.
