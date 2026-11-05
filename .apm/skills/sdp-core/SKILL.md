---
name: sdp-core
description: Validates and updates SDP delivery run records. Use when approving a delivery plan, recording a stage result, changing delivery status, checking whether assurance is stale, or inspecting a package under spec/.
---

# SDP Core

## Purpose

Make delivery records checkable. The bundled validator enforces plan approval,
required assurance, candidate identity, repair counting, and legal status
transitions for a package folder under `spec/<slug>/deliveries/<id>/`. It
validates records. It is not a sandbox and cannot prove who edited a file.

## Prerequisites

- Python 3.9 or newer (standard library only) and Git on `PATH`.
- If either is missing, do not advance delivery state: report that validation is
  unavailable and say so in the acceptance brief. Compliance projects must stop.

## Usage

Run the script from the installed skill folder, never from a checkout:

`python scripts/sdp.py --repo <repo> --package spec/<slug>/deliveries/<id> [--json] <command>`

| Command | Purpose |
| --- | --- |
| `validate` | Check the record against the plan and working tree; read-only |
| `inspect` | `validate` plus required and unsatisfied stages; read-only |
| `approve --by <human>` | Record plan approval; the human is named by the user, never an agent |
| `transition --to <status> --expected-revision <n>` | Move status when the rules allow |
| `result --stage <stage> --verdict <verdict> --expected-revision <n>` | Record a stage result for the current candidate |
| `disposition --trigger <t> --disposition <d> --by <who> --expected-revision <n>` | Record a trigger disposition |

Pass the `state_revision` you last read. Exit codes: 0 success, 1 invalid
records or refused transition, 2 usage or environment error, 3 stale writer or
lock held. Add `--json` for machine-readable output.

## Rules the validator enforces

1. Delivery starts only from an approved plan whose body and approval metadata
   are unchanged since approval.
2. Developer validation and technical review are always required and cannot be
   `not_applicable`. Security and QA are required by Compliance, policy,
   `per-story`, or any undisposed trigger; a waiver does not hide a trigger.
3. Results count only for the current candidate. A changed working tree makes
   earlier results stale.
4. A candidate is rejected once, when it first fails. Two autonomous rejections
   require human-guided repair. Blocked results are not rejections.
5. A repair that changes scope, outcome, or boundaries returns the package to
   `planned` and voids approval.
6. Acceptance and rejection need a named human, never an agent identity.

## Quality Bar

- Every state change goes through the validator, with the revision you read.
- Never edit `DELIVERY-RUN.json` by hand to move state.
- Quote the validator's output as evidence; do not assert a pass it did not give.
