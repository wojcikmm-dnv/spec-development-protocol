# SDP Protocol Contract (draft 1)

Status: Steps 02-04 are implemented: the record validator and schema live in
`.apm/skills/sdp-core`, and stage expertise lives in the skills below. Workflows,
host adapters, and agent wiring (Steps 05-08) are not implemented yet, so nothing
here describes behavior an installed agent already follows.

The protocol makes delivery records checkable by software. It validates records;
it is not a sandbox, an authentication system, or tamper-proof audit. Local files
can be edited outside SDP.

## Concepts and Ownership

| Concept | Source of truth | Writer |
| --- | --- | --- |
| Project policy (profile floor, mandatory controls) | project `TECH.md` | humans only |
| Intent, backlog, design | `PRD.md`, `BACKLOG.md`, `EPIC-*.md`, `DESIGN.md` | gate agents; read-only during delivery |
| Plan and its approval | package `PLAN.md` frontmatter and body | planner drafts; approval written by the coordinator on explicit user action |
| Run state | package `DELIVERY-RUN.json` | the coordinator only, through the validator |
| Outcome narrative | package `HISTORY.md` | the coordinator |
| Active package pointer | local `spec/ACTIVE.md` | planner or coordinator; pointer fields only |
| Product code and tests | the repository | the implementer only |

Status is stored once. `delivery_status` lives only in the run record. Feature
and story status are derived from accepted packages. Approval lives only in
`PLAN.md`; the run record stores a fingerprint of the approved plan, not a copy
of the approval.

A workflow definition is a versioned resource naming ordered stages, required
and conditional capabilities, failure routing, and retry limits. It references
capabilities (`implement`, `technical-review`, `security-review`,
`acceptance-validation`), never agent names. Adapters map capabilities to hosts.

## Run Record (schema_version 4)

Extends schema 3. Fields:

- `schema_version`, `run_id`, `delivery_id`, `workflow`, `profile`, `branch`.
- `delivery_status`: `planned | delivering | blocked | awaiting-acceptance |
  changes-requested | accepted | rejected`.
- `state_revision`: integer incremented by every write.
- `plan`: `{ fingerprint, approval: { approved_by, approved_at } }`, the digest of
  the approved plan body and a snapshot of its approval metadata.
- `candidate`: `{ base_revision, changed_paths, fingerprint }`.
- `stage_results[]`: `{ stage, verdict, candidate_fingerprint, findings,
  checks, evidence, detected_triggers, next_action }`.
- `trigger_dispositions[]`: `{ trigger, candidate_fingerprint, disposition,
  by, reason }` with disposition `confirmed | not_present | accepted_risk`.
- `rejected_candidates`: integer (replaces `autonomous_rejection_count`).
- `pending_audit[]`, `acceptance`, optional `compliance`.

A reader supports schema 4 and refuses an unknown newer schema. Schema 3 records
are migrated by the Step 09 tooling, never silently reinterpreted.

## Transitions

| From | To | Condition |
| --- | --- | --- |
| (none) | planned | plan exists |
| planned | delivering | plan approved; fingerprint recorded; prerequisites accepted; capabilities available |
| delivering | blocked | environment, capability, or tool failure; no rejection counted |
| blocked | delivering | cause cleared; resume from last valid checkpoint |
| delivering | awaiting-acceptance | every required stage passed for the current candidate fingerprint |
| delivering | changes-requested | a required stage failed; candidate rejected once |
| changes-requested | delivering | bounded repair (autonomous or human-guided) |
| delivering, changes-requested | planned | the repair would change outcome, scope, acceptance criteria, dependencies, a security/data boundary, public contract, or paths outside the plan boundary; the approval is void |
| awaiting-acceptance | accepted | explicit human decision |
| awaiting-acceptance | changes-requested | human requests changes |
| awaiting-acceptance, changes-requested, delivering | rejected | explicit human decision |

Every other transition is invalid. `accepted` and `rejected` are terminal.
Resuming never approves a new or changed plan; a changed plan body fails the
fingerprint check and returns the package to `planned`.

## Approval and Stale Plans

The coordinator computes the plan fingerprint (SHA-256 of the body after
frontmatter, normalized to LF) when the user approves, and snapshots
`approved_by` and `approved_at` into the run record as `plan.approval`. The
validator recomputes the fingerprint and compares the snapshot with the
`PLAN.md` frontmatter before every transition into or within `delivering`. A
mismatch in either means the approval is stale or altered. The snapshot is a
consistency check, not a second source of truth. Users never supply or read
hashes in the normal flow.

This detects accidental or inconsistent edits. It cannot prove who approved:
someone who edits both files consistently is not detected locally.

## Candidate Identity

The candidate is every tracked file that differs from `base_revision` (the
commit checked out when delivery started), including tracked files that match
`.gitignore`, plus untracked files that Git does not ignore. Paths are read with
NUL-delimited Git output (`git diff --name-status -z`, `git ls-files -z --others
--exclude-standard`) so unusual filenames are handled. Untracked ignored files
are invisible to Git and therefore outside the candidate; this is a documented
limit.

The whole `spec/<slug>/deliveries/<id>/` folder is excluded, including its
additions, changes, and deletions. Outside it, deleted files record a deletion
marker. The fingerprint is the SHA-256 of the sorted list of `path` and
file-content digest pairs.

A stage result is valid only for the candidate fingerprint it records. When the
fingerprint changes, results with a different fingerprint are stale and must be
rerun; the validator refuses `awaiting-acceptance` while any required result is
stale. Compliance may add environment identity and retained manifests on top.

Without Git, the validator blocks supervised delivery rather than guessing.

## Assurance Policy and Precedence

Order of authority, highest first:

1. Project mandatory controls and the project profile floor (`TECH.md`).
2. Compliance requirements, when the profile is Compliance.
3. Epic security policy: `risk-based | per-story | epic-level | waived`.
4. Plan-declared profile (may raise, never lower).
5. Detected triggers.

A `waived` epic policy skips optional specialist review only; it cannot override
levels 1 and 2. Developer validation and technical review are always required
and can never be `not_applicable`. Security and QA may be `not_applicable` only
with a reason when no higher level or trigger requires them.

A waiver also cannot silently suppress a detected trigger. While a trigger is
undisposed, the specialist stage stays required even under `waived`.

Trigger reevaluation: after the implementer and again after the reviewer, the
coordinator recomputes required stages from policy, changed paths, and every
`detected_triggers` value reported so far. A newly detected trigger adds the
stage; it is never dropped because an earlier evaluation did not need it.

Trigger disposition: a trigger is undisposed until either (a) the matching
specialist stage ran for the current candidate and recorded `confirmed` or
`not_present`, or (b) a human recorded `accepted_risk` with a reason. A
reviewer's own dismissal does not dispose of a trigger. Dispositions stay in the
record and apply only to the candidate fingerprint they were recorded for.

## Repair Counting

`rejected_candidates` increments once when a candidate first receives a failing
stage verdict (Critical or High finding, or an unmet required acceptance
criterion). Additional failing results for the same candidate fingerprint, a
resumed duplicate result, and `blocked` verdicts do not increment it.

A repair is bounded when it changes product code, tests, or comments inside the
approved change boundary to resolve a failed verdict. A change that would alter
outcome, scope, acceptance criteria, dependencies, a security/data boundary,
the public contract, or paths outside the boundary is not a repair: it returns
the package to `planned` for replanning and voids the approval.

- 1 rejected candidate: one autonomous bounded repair is allowed.
- 2 rejected candidates without human involvement: escalate; no third attempt.
- A human-guided correction does not consume the ceiling but is recorded.

## Sequencing and Parallel Packages

A plan may declare `sequenced_after: [delivery-id]`. The validator refuses
`planned -> delivering` until each prerequisite is `accepted`. A story belongs
to at most one open package; the validator rejects a second open package that
claims the same story.

## Stale Writers and Atomicity

Writers pass the `state_revision` they read. A write succeeds only if the stored
revision still matches, then increments it. Writes use a temporary file in the
same directory and an atomic replace, under an exclusive OS-level advisory lock
on a persistent sibling lock file (`fcntl` on POSIX, `msvcrt` on Windows). The
lock file is never deleted, and the OS releases the lock when the holder exits,
so a crashed writer leaves nothing to clean up and no timeout is needed. A
stale or lock-held write fails with a distinct code and changes nothing.
Retrying an identical result is idempotent. Inspection is read-only and takes
no lock.

An interrupted write leaves the previous record intact because replacement is
atomic. Network file systems may not honor advisory locks; the revision check
still detects the resulting stale write on the next attempt.

This guards accidental concurrency. It cannot stop a person or tool that edits
the files directly; the validator detects the resulting invalid states on the
next read.

## Validator Runtime Decision

Decision: Python 3.9 or newer, standard library only, for the shipped validator.

| Option | Assessment |
| --- | --- |
| Python 3.9+, stdlib | Chosen. No install step, JSON/hash/atomic-replace in stdlib, widely present on developer machines and CI, already used for maintainer checks. |
| Node.js | Comparable availability, but would add a package ecosystem and a lockfile for no benefit here. |
| PowerShell 7 | Not installed by default on Linux or macOS. |
| Compiled binary | Needs per-platform build and signing; disproportionate for this scope. |

Dependency budget: zero third-party runtime dependencies. Consequences:

- Run records are JSON. Plan approval frontmatter is a flat set of scalar
  `key: value` pairs read by a restricted parser that rejects anything else
  rather than guessing. Maintainer tooling may keep using PyYAML.
- The schemas ship as JSON Schema files, documented as the contract. The
  shipped validator implements the same rules directly; CI checks parity with
  the `jsonschema` library, a development-only dependency that is never
  distributed.
- Distribution: scripts ship inside the `sdp-core` skill under `scripts/` and are
  resolved relative to the installed skill, never the author checkout.
- Missing runtime: supervised delivery and state-changing commands are blocked
  with an explicit message. Manual prose workflows may continue, and the
  acceptance brief must say validation was unavailable. Compliance requires it.

All validator entry points use explicit exit codes: 0 success, 1 invalid
records, 2 usage or environment error, 3 stale writer or lock conflict. Output
is machine-readable JSON on request.

## Legacy Migration Range

Supported source layouts: SDP 0.5.3 (schema 2, shared `ACTIVE.md` state) and
0.5.4 (schema 3, package-scoped state). Earlier layouts are unsupported:
the tooling stops and names the upgrade path. Ambiguous statuses require a
human mapping; approvals and evidence are never fabricated.

`sdp-migrate` (`scripts/migrate.py`) implements the move. It previews by default;
`apply` writes `.sdp-backup/<timestamp>/` (originals plus a write-ahead journal), applies
the changes with atomic replaces, validates every migrated record, and restores
everything if anything fails. Rules:

- Nested packages are identified by their folder name; a feature-level (0.5.3) package
  moves to `spec/<slug>/deliveries/<id>/` with the record's `delivery_id` when it is a
  safe token, otherwise `<slug>-DP-1`.
- `accepted` and `rejected` packages keep their recorded decision only when it names a
  human; otherwise the migration stops for a human decision. Every open status restarts as
  `planned` with `plan: null`; an approved plan's approval is voided in `PLAN.md` (body
  untouched) and recorded in `HISTORY.md`.
- The original record is preserved as `DELIVERY-RUN.legacy.json` and its hash recorded in
  `migrated_from`. Pending audit obligations are preserved; notes and audits in the old
  `ACTIVE.md` that no migrated package can hold stop the migration.
- Copied legacy files are removed only with `--remove-legacy-files
  --confirm-replacement-installed`, only when the old installer marker exists, the file is
  not APM-managed, and its content matches a released file; they move into the backup.
- An interrupted migration is detected by `status`; `apply` refuses until `restore` runs.
  `restore` never overwrites a file edited after the migration; it reports it instead.
- Exit codes: 0 success, 1 blocked or ambiguous (nothing changed), 2 usage, 3 conflict
  or restored failure.

## Assurance Limits

The validator enforces that required stages have a passing result recorded for
the current candidate. It cannot prove the reviewer was a different person,
session, or permission set. Isolation comes from the host adapter and project
policy; the coordinator must refuse to substitute self-review when a host cannot
dispatch an independent worker. Compliance projects needing proof of
independence must use external identity or protected CI evidence.

## Protected Boundaries

The validator only reads and writes inside the active package folder and
`spec/ACTIVE.md`, and refuses absolute paths, parent traversal, and symlinks that
leave the repository. `PLAN.md` and `DELIVERY-RUN.json` must be regular files,
and reads are size-capped (2 MiB plan, 5 MiB record). The plan, the candidate
fingerprint, and the stored record are all evaluated under the write lock, and
approval updates `PLAN.md` and the record as one locked operation. It never
edits product code, shared specs, or `TECH.md`.

Identities (`--by`, `--decided-by`) are asserted strings, not authenticated. A
heuristic refuses obvious agent identities such as `sdp.*`, stage names, `bot`,
`copilot`, or `claude` for human-only decisions. Any caller can still assert a
human name; stopping that needs host-level approval prompts or external identity.

A candidate that failed a stage cannot be re-passed for that stage until it
changes, so a repair has to alter the candidate and a rerun cannot silently
replace a failing verdict.

## Workflow Definitions and the Next Action

A workflow is a JSON file in the `sdp-workflows` skill (`workflows/<name>.json`,
schema 1). It lists pre-delivery steps, the four delivery stages in fixed order with
their capability, skill, isolation, and whether the stage is `always` or
`on-trigger-or-policy`, the capabilities a host must offer, the repair limit, and the
acceptance rule. It names capabilities and skills, never agents. The validator
refuses a definition that makes developer or reviewer optional, drops isolation from
assurance, reorders stages, or changes the escalation limit from two.

`sdp.py next` derives the single next action from the stored record, the plan, and
the working tree, and never writes. A coordinator repeats: run `next`, do that one
action, record the result through the validator, run `next` again. Because the
action is derived from stored facts, an interrupted run resumes by running `next`.
Actions: `approve-plan`, `await-plan-approval`, `start-delivery`, `run-stage`
(with stage, skill, isolation, and the exact `result` command; `repair` when an
unchanged candidate failed), `resume-delivery`, `resolve-block`, `escalate-to-human`,
`blocked-capability`, `replan`, `request-acceptance`, `await-human-decision`, and
`done`. If the host lacks a capability the next stage needs, the action is
`blocked-capability`; self-review is never offered as a substitute.

Only the `bug` and `feature` workflows exist.

### Feature gates

The `feature` workflow lists upstream gates: PRD (gate 1), BACKLOG and every EPIC
(gate 2), DESIGN (gate 3). A gate is approved when its artifact's own frontmatter has
`status: approved` with a named `approved_by` and an `approved_at`; nothing else is
stored. `feature-next --slug <slug>` reports the first open gate, then story
availability derived from the backlog's story table and accepted packages: a story is
done when an accepted package includes it, held while an open package includes it,
and offered only when its listed dependencies are done. The feature is complete when
every backlog story is done and no package has a pending audit. `approve-artifact`
records a named human's approval (optionally bound to the artifact fingerprint the
human saw) and refuses while any package of that feature is delivering, blocked,
awaiting acceptance, or in changes-requested, because shared specs are read-only
during delivery.

Plan approval for a feature package is refused while a gate is open, unless the plan
declares `gates: lightweight` with a non-empty `basis`. A lightweight plan skips only
the upstream documents: it still needs this plan and its boundary, executable
verification, independent review, and human acceptance.

### What the plan approval covers

The plan fingerprint covers the body and every frontmatter field other than
`status`, `approved_by`, and `approved_at` (for example `stories`, `sequenced_after`,
`gates`, `basis`), so none of them can change after approval without voiding it.
Upstream gate artifacts are not hashed into the plan: editing an approved PRD or
design later does not void an approved plan, which is why shared specs are frozen
during delivery. Gate authoring stays with the existing gate agents for now.

## Host Capabilities

A workflow lists the capabilities a host must provide: `implement`,
`technical-review`, and `independent-context`; security and QA stages add
`security-review` and `acceptance-validation`. Every stage whose isolation is
`independent` also needs `independent-context`, meaning a separate session or subagent
with different permissions from the implementer. A host profile
(`sdp-workflows/hosts/<host>.json`) records each capability as `true` with cited
evidence, `false`, or `"unverified"`; the validator refuses `true` without evidence.
`next --host <name>` counts only verified capabilities, and an explicit
`--capabilities` list overrides it only when a human supplies it. The result reports
`capability_source` (`host:<name>`, `explicit`, or `unchecked`). A missing capability
produces `blocked-capability`, never a self-review. See `docs/COMPATIBILITY.md` for
what has actually been observed per host.

`transition --to delivering` accepts the same `--host` or `--capabilities` and records
the source in the run record's `capability_source` (`host:<name>` or `explicit`),
which `inspect` reports and the acceptance brief must state. A limit remains: an
explicit list is a caller's assertion, and nothing local can prove the host really has
those capabilities or that a human supplied the list. The record makes that choice
visible; stopping it needs host-level approval prompts or protected CI.

### Command mapping

Existing commands keep working until Step 13. The schema 4 path maps to them as follows:

| Existing command | Schema 4 equivalent |
| --- | --- |
| `/discover-tech` | unchanged (gate authoring stays with agents) |
| `/create-prd`, `/refine-backlog`, `/design-system` | unchanged entry points; approval moves to `approve-artifact` |
| `/plan-task` | the `sdp-plan-delivery` skill, then `approve --by <human>` |
| `/deliver`, `/deliver inspect`, `/deliver resume`, `/deliver reject` | `/run-workflow` (preview): `next`, `inspect`, `transition --to rejected` |
| `/implement` | the `sdp-implement` and `write-tests` skills |
| `/run-review` | the `sdp-technical-review` skill |
| `/audit-security` | the `sdp-security-review` skill |
| `/qa-validate` | the `sdp-acceptance-validation` skill |

## Skill Coverage Map

Stage expertise is extracted into skills. Agents keep their current files until
Step 08 replaces their procedures with workflow references, so no coverage is
removed yet.

| Current agent responsibility | Skill | Notes |
| --- | --- | --- |
| `sdp.developer` implement within boundary, autonomy, durable comments | `sdp-implement`, `write-tests` | merge-friendly hotspots included |
| `sdp.planner` plan, sizing, parallel safety | `sdp-plan-delivery` | uses the PLAN template |
| `sdp.reviewer` correctness, scope, tests, comment hygiene, trigger reports | `sdp-technical-review` | independence is a host requirement |
| `sdp.security` threat model, aggregate epic audit | `sdp-security-review` | waiver cannot hide a trigger |
| `sdp.qa` scenario derivation and execution | `sdp-acceptance-validation` | human acceptance stays separate |
| bug diagnosis (new) | `sdp-investigate` | feeds the bug workflow |
| `sdp.discover`, `sdp.prd`, `sdp.analyst`, `sdp.architect` | not extracted | gate authoring stays with agents for now |
| `sdp.orchestrator` | not a skill | coordination uses `sdp-core` and, later, workflows |

Each extracted skill carries `sdp.skill.json` and `evals/cases.json`. Evaluation
cases are deterministic graders for a result a host produced; they do not run a
model and do not prove a given model follows the skill. The grader checks that
required evidence is present (verdict, expected findings, triggers, severity floor),
not that the reasoning is good: a keyword-stuffed answer can pass, so review real
output with human judgment. Case kinds: `correct` input should pass; `seeded-defect`
contains a defect that must be found; `negative` is a tempting wrong action or false
alarm that must be declined; `escalation` is a boundary that must be handed back.
Grade real output with
`python scripts/grade_eval.py --cases <cases.json> --case <id> --result <file>`.

## Invariant-to-Test Map

| Invariant | Planned test (Steps 03-05) |
| --- | --- |
| Approval before product changes | `test_unapproved_plan_blocks_delivering` |
| Stale approval detected | `test_edited_plan_body_invalidates_approval`, `test_edited_approval_metadata_detected` |
| Unbounded repair replans | `test_unbounded_repair_returns_to_planned` |
| Waiver cannot hide a trigger | `test_waiver_does_not_suppress_undisposed_trigger` |
| Triggers need real disposition | `test_reviewer_cannot_dispose_trigger`, `test_accepted_risk_requires_human_reason` |
| Candidate edge cases | `test_tracked_gitignored_file_in_candidate`, `test_deleted_file_marker`, `test_package_folder_excluded_from_candidate` |
| Crashed writer leaves no stale lock | `test_released_lock_after_holder_exit` |
| Self-review not substitutable | `test_missing_independent_capability_blocks` |
| Review always required | `test_missing_review_prevents_awaiting_acceptance`, `test_review_not_applicable_rejected` |
| Waiver cannot override mandatory controls | `test_waiver_cannot_lower_project_floor` |
| Triggers force specialists | `test_reviewer_detected_trigger_adds_security` |
| Stale evidence invalidated | `test_candidate_change_invalidates_results` |
| Untracked files identify candidate | `test_untracked_file_changes_fingerprint` |
| Blocked is not passed or rejected | `test_blocked_does_not_count_rejection` |
| One repair, then escalate | `test_second_rejection_escalates` |
| No double count | `test_duplicate_failure_counts_once` |
| Human acceptance only | `test_acceptance_requires_human_decision` |
| Invalid transitions refused | `test_all_invalid_transitions_rejected` |
| Terminal states | `test_terminal_states_are_final` |
| Resume without implicit approval | `test_resume_keeps_approval_binding` |
| Prerequisites enforced | `test_sequenced_package_waits_for_prerequisite` |
| One open package per story | `test_story_in_two_open_packages_rejected` |
| Single writer, stale write refused | `test_stale_revision_write_refused`, `test_lock_conflict_reports_distinct_code` |
| Partial write safe | `test_interrupted_write_leaves_previous_record` |
| Unknown newer schema refused | `test_unknown_schema_version_refused` |
| Path escape refused | `test_path_traversal_and_symlink_escape_refused` |
| Unpreserved pending audits | `test_pending_audit_survives_transitions` |
| Shared specs read-only in delivery | `test_validator_never_writes_shared_specs` |
