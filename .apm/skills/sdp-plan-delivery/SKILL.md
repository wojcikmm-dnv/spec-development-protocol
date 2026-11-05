---
name: sdp-plan-delivery
description: Writes an implementation-grade delivery plan for one coherent package. Use when turning approved requirements or a diagnosed bug into a PLAN.md with outcome, change boundary, ordered verifiable work, size, risk, and escalation conditions before implementation starts.
---

# Plan a Delivery Package

## Purpose

Produce a plan a separate implementer can execute safely: what will work, what may
change, how it is verified, and what requires coming back for approval.

## Prerequisites

- Approved requirements and design, or a diagnosed bug with a bounded fix proposal.
  A user-approved lightweight path may reference an existing contract and design
  instead of new documents. It never removes the outcome and non-goals, this plan
  and its boundary, executable verification, independent review, or human
  acceptance. If later packages changed the area, say so and confirm the design
  still holds.
- `TECH.md` for stack, commands, and policy. Use the PLAN template found under
  `.github/templates`, `.agents/skills/sdp-templates/assets`, or
  `.github/skills/sdp-templates/assets`.

## Procedure

1. **Choose one coherent package.** Bundle only stories that share one demonstrable
   outcome. Exclude any story that already belongs to an open package.
2. **State the outcome**, a short way to observe it, the included acceptance
   criteria, and explicit non-goals.
3. **Declare size, risk, and uncertainty.** Size XL or Open uncertainty about
   behavior, data loss, security, or architecture stops here: recommend splitting or
   more design instead of planning.
4. **Set the change boundary:** allowed paths, expected files, exclusions, and any
   dependency, data, or migration constraints.
5. **Order the work.** Each step ends with a command or observable check. Put the
   check that proves each acceptance criterion in a verification table.
6. **Record applicable risks only:** security boundaries, compatibility, rollback.
7. **Choose assurance.** Select a profile that is not below the project floor, and
   list stories' epic security policy. Do not lower mandatory controls.
8. **Check parallel safety** when another package is open: record `independent`,
   `additive-overlap`, or `sequenced after <id>` in the plan's Parallel Delivery
   section. Also set machine-readable frontmatter that the validator reads, for
   example `stories: [US-3, US-4]` and `sequenced_after: [auth-DP-1]` (inline lists
   only). Keep `status`, `approved_by`, and `approved_at` as they are.
9. **State autonomy:** the implementer owns local naming, idiom, and adjacent tests;
   replanning is required for new dependencies, public contract changes, expanded
   data or security boundaries, destructive operations, weakened criteria, or paths
   outside the boundary.

## Output

`spec/<slug>/deliveries/<id>/PLAN.md` as `draft`, with approval fields `pending`.
Do not approve it and do not write product code. Approval is recorded later, when
the user approves (for example with the validator's `approve --by <human>`), and
any edit to the plan afterwards voids that approval.

## Quality Bar

- Every acceptance criterion has a check that can fail.
- The boundary is narrow enough to review in one sitting.
- No model routing, counters, hashes, or manifests in a normal plan.
- A reader can tell exactly when to stop and ask.
