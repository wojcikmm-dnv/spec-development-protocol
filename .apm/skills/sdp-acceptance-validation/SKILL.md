---
name: sdp-acceptance-validation
description: Independently exercises a delivery's observable acceptance criteria. Use when acceptance depends on user behavior, integrations, accessibility, compatibility, migration, performance, or a critical journey that tests and code review alone do not demonstrate; read-only and never replaces human acceptance.
---

# Acceptance Validation

## Purpose

Confirm that externally observable behavior satisfies the acceptance criteria in a
representative way, adding evidence that review and unit tests do not.

## Run Conditions

Run for a `qa:*` trigger, independent user-visible behavior, integration boundaries,
accessibility, compatibility, migration, performance, a critical journey, or when
Compliance or project policy requires it. Return `not_applicable` with a reason
only when review plus the focused tests already give the same evidence and no
trigger is undisposed. Run independently of the implementer; never edit product
code or tests.

## Procedure

1. **Derive scenarios** from every applicable acceptance criterion: the main path,
   negative cases, and material edge cases.
2. **Exercise them** in the closest representative environment: run the feature,
   call the endpoint, drive the UI, or run the migration against realistic data.
3. **Check what changed around it:** impacted integrations and regression risk in
   neighboring behavior.
4. **Confirm security disposition:** every trigger the plan or review reported has
   been handled by the security stage or a human decision.
5. **Record evidence:** exact commands, inputs, and observed output per scenario.
6. **Verdict** per `sdp-core/references/stage-result.md`. An unmet required
   criterion fails. A missing environment or tool is `blocked`, not a pass and not
   a rejection.

## Output

A `stage-result` with criterion-by-criterion coverage, evidence, and findings.
A passing result is not human acceptance; the human decision is separate.

## Compliance Profile

In Compliance this stage is required and may not be `not_applicable`. Return the
extra evidence `TECH.md` configures, as produced by project tooling; never invent it.

## Quality Bar

- Every required criterion appears with evidence or an explicit gap.
- Observed output is quoted, not inferred.
- Scenarios could fail; at least one negative case per criterion where meaningful.
