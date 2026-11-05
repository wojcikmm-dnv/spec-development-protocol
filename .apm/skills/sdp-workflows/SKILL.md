---
name: sdp-workflows
description: Runs an SDP delivery workflow for one package by following the validator's next-action output. Use when coordinating a bug fix from approved plan through implementation, independent review, specialist stages, and human acceptance, including resuming an interrupted run, handling a failed review, or reporting status.
---

# Run a Delivery Workflow

## Purpose

Coordinate one delivery package without carrying state in your head. The validator
decides what happens next; you dispatch the work and record what came back.

## Prerequisites

- `sdp-core` is installed beside this skill (the validator finds workflow
  definitions in the sibling `sdp-workflows/workflows` folder; set
  `SDP_WORKFLOW_DIR` to override). Python 3.9+ and Git are available.
- A package folder `spec/<slug>/deliveries/<id>/` with a `PLAN.md`.
- A host that can run workers in separate contexts for review and specialists. If it
  cannot, stop at the block the validator reports; do not review your own work.

## Workflows

| Workflow | Definition | Use for |
| --- | --- | --- |
| `bug` | `workflows/bug.json` | fixing a reported defect |

The feature workflow arrives in a later release; do not improvise one.

## Procedure

Set `V` to `python <sdp-core>/scripts/sdp.py --repo <repo> --package <package> --json`,
where `<sdp-core>` is the sibling folder `../sdp-core` next to this skill's folder (do
not search the disk for it).

Capabilities: run `V next --host <name>` when a profile exists in this skill's `hosts/`
folder (`copilot-cli`, `claude-code`). Only capabilities a profile has verified with
evidence count; an unverified host blocks the workflow. Use `--capabilities` only with a
list the human told you the host can really provide, and never to get past a block
yourself.

1. Run `V next`. It returns one action and who owns it. Do exactly that action.
2. Act on the result:
   - `await-plan-approval` or `await-human-decision`: stop and ask the human. Name
     the options. Never decide for them. For plan approval, show the human the exact
     plan; when they approve, run `V approve --by <their name>
     --expect-plan-fingerprint <plan_fingerprint from next>` so the approval binds to
     what they saw. If it reports `plan_changed`, show the new plan and ask again.
   - `approve-plan`: PLAN.md is already marked approved by a human but no run record
     exists. Record it with `V approve --by <approved_by from next>
     --expect-plan-fingerprint <plan_fingerprint from next>`. Do not substitute your
     own name or ask the human to repeat themselves.
   - `start-delivery` or `resume-delivery`: run `V transition --to delivering
     --expected-revision <n> --host <name>` (or the same human-supplied
     `--capabilities` list you used with `next`). The run record stores where the
     capabilities came from (`host:<name>` or `explicit`).
   - `run-stage`: dispatch the named skill in a worker context with the stated
     isolation, give it only the plan outcome, criteria, boundary, changed paths,
     prior findings, and checks, then record its verdict with the `record_with`
     command. A developer repair must change the candidate first.
   - `request-acceptance`: run `V transition --to awaiting-acceptance` and present
     one acceptance brief: outcome and demonstration, criteria coverage, stage
     verdicts, deviations, remaining risks, evidence references, and the capability
     source from `V inspect` (say plainly when it was `explicit`, because that means a
     human asserted isolation rather than a host profile verifying it).
   - `replan`, `resolve-block`, `escalate-to-human`, `blocked-capability`: stop and
     report the reason and options. For `blocked-capability`, list every missing
     capability the action names.
   - `await-human-decision` may carry a `warning` that the working tree changed after
     assurance. Tell the human in plain words that earlier review no longer covers the
     current code, so accepting is refused until changes are requested and review
     reruns.
   - `done`: report the outcome.
3. After every command, run `V next` again. Never assume the result of a command.

## Rules

- Dispatch one worker at a time. You never edit product code or tests.
- Record only what workers returned. Never invent a verdict, evidence, or a check.
- Use the revision you last read. On exit code 3, re-read with `V inspect` and retry
  once; do not force.
- Interrupted or resumed runs start from `V next`, which reads the stored record and
  the working tree; resuming never approves a changed plan.
- Acceptance needs a named human and never commits, merges, deploys, or picks the
  next package. Human corrections go through `transition --to changes-requested`
  with a reason, then `--human-guided` for the repair.
- Human feedback that changes scope, contract, or risk is a replan, not a repair.

## Status

`V inspect` reports the status, required and unsatisfied stages, and the number of
rejected candidates. Use it for "where are we" questions; it never changes state.
To reject a delivery on a human's instruction, run `V transition --to rejected
--decided-by <human> --reason <why> --expected-revision <n>`.

## Quality Bar

- Every state change in the run went through the validator.
- Each dispatched stage matches the `next` output at that moment.
- The acceptance brief cites recorded results, not recollection.
