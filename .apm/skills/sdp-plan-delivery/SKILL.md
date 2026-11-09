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
4. **Ground the plan in the real code.** Read the owning code and its neighbors
   before writing steps. Name the existing files and symbols to change or follow, the
   closest existing example to imitate, and the exact build, test, and lint commands
   from `TECH.md`. Do not list paths or commands you have not confirmed exist.
5. **Set the change boundary:** allowed paths, expected files, exclusions, and any
   dependency, data, or migration constraints.
6. **Order the work** in small increments that each leave the build green. Each step
   ends with a command or observable check. Put the check that proves each acceptance
   criterion in a verification table, naming the test (existing or to be added) and
   the failure it must detect, including error and boundary cases. Name which domain
   skills (`create-api-endpoint`, `create-ui-component`, `database-migration`,
   `error-handling`) apply.
7. **Record applicable risks only:** security boundaries, compatibility, rollback.
8. **Choose assurance.** Select a profile that is not below the project floor, and
   list stories' epic security policy. Do not lower mandatory controls.
9. **Check parallel safety** when another package is open: record `independent`,
   `additive-overlap`, or `sequenced after <id>` in the plan's Parallel Delivery
   section. Also set machine-readable frontmatter that the validator reads, for
   example `stories: [US-3, US-4]` and `sequenced_after: [auth-DP-1]` (inline lists
   only). Keep `status`, `approved_by`, and `approved_at` as they are.
   For a human-approved lightweight path add `gates: lightweight` and `basis:
   <existing contract and design it relies on>`; otherwise leave `gates` out (full).
   Every frontmatter field except the approval fields is covered by the approval, so
   changing any of them afterwards voids it.
10. **State autonomy:** the implementer owns local naming, idiom, and adjacent tests;
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
- Paths, symbols, and commands in the plan exist in the repository.
- The boundary is narrow enough to review in one sitting.
- No model routing, counters, hashes, or manifests in a normal plan.
- A reader can tell exactly when to stop and ask.
