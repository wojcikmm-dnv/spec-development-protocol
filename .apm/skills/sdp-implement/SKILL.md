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
2. **Work the steps in order** and run each step's check before moving on.
3. **Use the autonomy the plan grants** for naming, idiomatic local design, helper
   reuse, and adjacent tests. A simpler approach inside the boundary is fine when
   outcome, risk, and verification are unchanged; note why in one sentence.
4. **Write tests** with the `write-tests` skill. Test observable behavior; do not
   weaken or delete a failing test to get a pass.
5. **Touch shared hotspots additively:** add new files where the pattern allows,
   insert self-contained blocks, never reorder or reformat neighbors, do not
   regenerate lockfiles or run repository-wide formatting unless a dependency
   change is in the boundary. For migrations, use timestamp or package-unique
   identifiers when the toolchain supports them and never renumber existing ones.
6. **Keep comments durable.** No story, task, or criterion IDs, no step narration,
   no change history, no completed TODOs. Comment only a non-obvious invariant,
   compatibility constraint, security rationale, or deliberate trade-off.
7. **Run the plan's verification** and the project's build, lint, and tests.
8. **Report** changed paths, checks with results, deviations, unresolved risks, and
   triggers (`security:*`, `qa:*`) for areas you touched.

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
- The diff stays inside the allowed paths.
- Reported checks were actually run and their output was read.
