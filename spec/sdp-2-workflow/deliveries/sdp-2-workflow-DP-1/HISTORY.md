# Step 05 Delivery History

## 2026-11-05 - Accepted

Delivered `sdp-workflows` (coordinator skill and `workflows/bug.json`), workflow
validation and loading, and `sdp.py next` in the validator, with 29 new tests
(81 contract tests in total).

### Evidence

- WSL (Python 3.12): 81 contract tests and 28 skill tests pass.
- The workflow is exercised only through `next`: happy path to a human decision,
  failed review then one repair and recheck, interruption and resume (identical
  `next` output), blocked stage then rerun without a counted rejection, candidate
  changed after assurance, second rejection escalating with options, security
  trigger forwarded to an independent specialist (also under a waiver), missing
  independent capability blocking instead of self-review, plan edits mid-delivery,
  after a failed review, and while blocked all becoming a replan.
- Mutation checks: eight deliberate removals (escalation, capability check, repair
  routing, stale warning, binding check, trigger forwarding, blocked handling,
  review-optional workflow) were each caught.

### Independent review

Verdict fail with eight findings; triage:

- Fixed: the coordinator could not learn the approver's name from `approve-plan`;
  approval could bind to a plan body the human never saw (now `--expect-plan-fingerprint`
  from `next`, refused with `plan_changed`); `planned` did not check host capabilities
  before starting; Compliance reported only the first missing capability.
- Rejected: `SDP_WORKFLOW_DIR` as an attack (whoever controls the environment
  already controls `PATH` and the interpreter; definitions are still validated
  structurally, names are token-checked, and files are size-capped and symlink
  refused); a "stale candidate in the record" note (the fingerprint is recomputed
  from the tree on every read); and a claim that `changes-requested` skips the plan
  check (the binding check precedes every status branch; two tests now prove it).
- Clarified in the coordinator skill: how to relay the stale-evidence warning.

### Limits

Nothing wires these skills into a host or agent yet, so no agent has been observed
following `sdp-workflows`; that is Step 06. The existing orchestrator and prompts
still use schema 3; mixing them with schema 4 records on one package is unsupported
and documented. Only the `bug` workflow exists; the human who approves is an
asserted name, as documented in PROTOCOL.md.

The user's continue instruction is recorded as approval and acceptance.
