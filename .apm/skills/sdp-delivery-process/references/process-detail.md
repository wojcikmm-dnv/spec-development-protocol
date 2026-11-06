# Delivery Process Detail

Full text of the stable (schema 3) delivery process: right-sizing, approvals, sizing, profiles,
assurance triggers, the plan contract, autonomy, supervised delivery, candidate identity, state,
parallel delivery, run state, worker verdicts, acceptance, traceability, and feedback routing.
It was moved here from the always-loaded instructions; nothing was removed.

## Right-Sizing Earlier Gates

The full artifact chain is recommended for new capabilities and material
behavior changes. For a small fix with an already clear product contract and an
established design, the user may explicitly approve a lightweight path that
references existing requirements and design instead of creating redundant
documents.

A lightweight path never removes:

- a clear outcome and non-goals;
- an implementation plan and change boundary;
- executable verification;
- independent review appropriate to risk;
- human acceptance.

## Artifact Approval

Gate artifacts use:

```yaml
status: draft | approved | rejected
approved_by: pending | <identity>
approved_at: pending | <ISO timestamp>
```

An agent that authors an artifact leaves it as `draft`. A downstream manual
gate requires approved metadata. Bare `/deliver` is the one convenience action
that may approve the active `PLAN.md` and immediately execute it.

Do not require content hashes for normal approval. Compliance profile may add a
plan digest and immutable archive when project policy requires them.

## Capability Sizing

Every delivery plan declares:

- **Size**: `S | M | L | XL`
- **Risk**: `Low | Moderate | High`
- **Uncertainty**: `Resolved | Bounded | Open`

`XL` packages must be split. `Open` uncertainty about public behavior, data
loss, security, or architecture returns to backlog/design before execution.
Size does not determine risk.

## Delivery Profiles

Profiles control assurance and evidence, not implementation quality.

### Lean

Use for small, low-risk, resolved changes with established contracts.

- Developer implements and runs focused validation.
- Reviewer independently checks correctness, maintainability, boundary, and
  tests.
- Security or QA runs only when a trigger below applies.
- Persist one final delivery summary and unresolved findings.

### Balanced (default)

Use for normal product work.

- Developer implements and validates.
- Reviewer always runs.
- Security runs when a security boundary is affected or policy requires it.
- QA runs when acceptance behavior can be exercised independently of code
  review or when risk/public behavior requires it.
- Persist compact stage verdicts and one final delivery summary.

### Compliance

Use when regulation, high risk, project policy, or the user explicitly requires
strong candidate identity and audit retention.

- Run developer, reviewer, required security, and QA stages.
- Record plan and upstream integrity, baseline and candidate manifests,
  environment identity, stage evidence, and immutable plan retention as
  configured by `TECH.md`.
- Revalidate candidate identity between stages.
- Never imply these records are a tamper-proof audit system.

`TECH.md` defines the project default and escalation rules. A plan may raise
the profile but must not silently lower a mandatory project profile.

## Assurance Triggers

Dispatch `sdp.security` when a change affects authentication, authorization,
secrets, untrusted input, sensitive data, cryptography, network trust
boundaries, dependency/infrastructure security, or a regulated control.

Dispatch `sdp.qa` when acceptance requires independently exercising observable
behavior, integration boundaries, accessibility, compatibility, migration,
performance, or a critical user journey. If QA can only repeat the same static
inspection and unit tests already reviewed, the reviewer may cover acceptance
in Lean/Balanced mode and record why QA is not applicable.

Every epic declares one security policy:

- `risk-based` (default) - use the triggers above;
- `per-story` - run security for every included story;
- `epic-level` - audit aggregate epic changes before its final acceptance;
- `waived` - skip specialist security review with an explicit reason.

Baseline secure-coding checks remain active in every profile.

## Delivery Contract

The default `PLAN.md` contains only information needed to decide, implement,
and verify the package:

1. outcome and demonstration;
2. included acceptance criteria and non-goals;
3. relevant context and settled decisions;
4. size, risk, uncertainty, and selected assurance profile;
5. change boundary;
6. ordered work steps;
7. verification;
8. applicable security, migration, recovery, or rollback notes;
9. implementation autonomy and escalation conditions.

Model routing, resource counters, manifests, and orchestration bookkeeping do
not belong in the default human plan.

## Implementation Autonomy

Plans lock outcomes, contracts, safety constraints, non-goals, and
verification. Within those boundaries, the developer owns local naming,
idiomatic implementation, helper reuse/extraction, and adjacent tests.

If the developer finds a simpler in-boundary approach, it may proceed after
briefly recording why outcome, risk, and verification remain unchanged. A
changed public contract, dependency, data/security boundary, destructive
operation, or acceptance criterion requires replanning or explicit approval.

## Supervised Delivery

### Normal path

1. `/plan-task` resolves the active feature and asks for a package choice only
   when the selection is ambiguous.
2. The user reviews `PLAN.md`.
3. Bare `/deliver` resolves the active package and its plan, records
   approval, selects the required profile, and runs implementation plus
   assurance.
4. The orchestrator presents one concise acceptance brief.
5. The user replies with acceptance, rejection, or a natural-language
   correction.

### Advanced actions

- `/deliver --profile compliance` raises assurance for the active plan.
- `/deliver resume [delivery-id]` resumes an interrupted run. The ID is needed
  only when multiple runs are ambiguous.
- `/deliver inspect` reports current delivery state without changing it.
- `/deliver reject` records rejection of the awaiting candidate.

IDs, revisions, digests, and candidate hashes are internal details unless
ambiguity or Compliance profile makes them necessary.

### Correction routing

Interpret post-delivery feedback as:

- **bounded correction** - inside the approved outcome and boundary; summarize
  the interpretation, repair, and rerun assurance invalidated by changed files;
- **contract change** - changed requirement, public contract, risk, or boundary;
  stop and return to planning/design;
- **rejection** - record the decision and stop.

The autonomous repair ceiling is one repair after the first rejected candidate.
A second autonomous rejection escalates. Explicit human-guided corrections do
not consume this ceiling merely because the user requested them, but repeated
failure still requires a decision rather than an endless loop.

## Candidate Identity

Lean and Balanced profiles identify the candidate by the current working-tree
diff, changed paths, and whether relevant files changed after assurance. Record
the current Git revision only as orientation. Any product or test change
invalidates affected assurance.

Compliance profile may require content manifests and hashes. Missing compliance
identity tooling blocks Compliance delivery, not Lean/Balanced delivery.

Preserve unrelated user changes. Never revert them to construct a cleaner
candidate.

## Delivery State

Delivery state is package-scoped, so independent packages can run on separate
branches or git worktrees and merge without spec conflicts:

```text
spec/
  ACTIVE.md                      # local pointer only
  <slug>/
    PRD.md  BACKLOG.md  EPIC-*.md  DESIGN.md
    deliveries/
      <delivery-id>/
        PLAN.md
        DELIVERY-RUN.json
        HISTORY.md
```

`spec/ACTIVE.md` is a pointer, not delivery state:

```yaml
slug: <feature-slug>
title: <title>
current_gate: <1-6>
current_delivery: <delivery-id | n/a>
```

`ACTIVE.md` holds exactly these front-matter fields and no body. Update the
fields in place; never append progress notes, summaries, findings, decisions,
or history to it. Record that content where it belongs:

| Content | Location |
| --- | --- |
| Delivery outcome, blocks, escalations | package `HISTORY.md` |
| Stage, verdicts, findings, audit obligations | package `DELIVERY-RUN.json` |
| Product, backlog, or design decisions and open questions | `PRD.md`, `BACKLOG.md`/`EPIC-*.md`, `DESIGN.md` |
| Plan approval and deviations | package `PLAN.md` |

If an existing `ACTIVE.md` has body content, move it to the matching location
and reduce the file to the pointer fields.

Resolve the active package in this order and stop at the first unambiguous
match:

1. an explicit delivery ID argument;
2. the current branch named `<branch-prefix><delivery-id>` (default prefix
   `sdp/`);
3. `current_delivery` in `spec/ACTIVE.md`;
4. the only open package under `spec/*/deliveries/`;
5. otherwise ask once and record the choice in `spec/ACTIVE.md`.

A package is open unless its `delivery_status` is `accepted` or `rejected`.
`delivery_status` lives in the package `DELIVERY-RUN.json`; a package with a
`PLAN.md` and no run record is `planned`. Package transitions:

```text
planned -> delivering -> awaiting-acceptance -> accepted
               |                 |
               -> blocked        -> changes-requested -> delivering
                                 -> rejected
```

Feature and story status are derived, not stored: a story is done when an
accepted package includes it; a feature is done when every backlog story is
done and no package has `pending_audit`. Do not store another overlapping
status vocabulary.

During Gates 4-6, write only the package's own folder, `spec/ACTIVE.md`, and
product code/tests inside the plan boundary. `PRD.md`, `BACKLOG.md`, `EPIC-*.md`,
`DESIGN.md`, and `TECH.md` are read-only during delivery; a needed change
returns to Gate 2 or 3.

Delivery IDs use `<slug>-DP-<n>`. The planner picks the next `n` not used in
the tree, in sibling worktrees, or by existing `<branch-prefix>*` branches.

## Parallel Delivery

Parallel delivery is opt-in and adds no step to single-package work. Several
packages may be open at once when they are independent; each runs the normal
`/deliver` flow on its own branch, typically in its own git worktree.

### Parallel safety at planning

When another package is open in this tree or a sibling worktree
(`git worktree list`), the planner compares change boundaries and records one
verdict in the plan:

- `independent` - no shared files and no dependency on unmerged behavior;
- `additive-overlap` - only shared integration hotspots such as registrations,
  routes, DI wiring, exports, configuration, migrations, or lockfiles; the plan
  names the merge-friendly technique for each;
- `sequenced` - needs another package's unmerged contract or changes the same
  behavior; deliver after that package merges, or re-split.

A story belongs to at most one open package. Do not split one story's
acceptance criteria across concurrent packages. When no other package is open,
the planner skips this check.

### Merge-friendly implementation

Inside an overlapping hotspot, the developer:

- prefers adding a new file where the established pattern allows it;
- inserts entries as a self-contained block without reordering or reformatting
  neighbors;
- uses timestamp or package-unique migration identifiers when the toolchain
  supports them and never renumbers existing migrations;
- does not regenerate lockfiles or run repository-wide formatting unless a
  dependency change is inside the boundary.

### Worktree flow

1. Plan the packages in the primary worktree and commit the spec changes so
   every branch starts with all plans.
2. Per package: `git worktree add ../<repo>-<delivery-id> -b sdp/<delivery-id>`,
   then open it in its own editor window or agent session.
3. Run bare `/deliver` in each worktree; the branch name resolves the package.
4. Merge accepted packages in any order. The later package updates from the
   integration branch and reruns verification affected by the integration.

Agents may propose these commands but create branches or worktrees, commit,
or merge only on explicit user request.

### Merge readiness

Before the acceptance brief, the orchestrator runs a read-only, best-effort
check: intersect the candidate's changed paths with files changed on the
integration branch since the merge base and with changed paths of other open
packages in sibling worktrees. Report `clean` or the overlapping paths with a
recommendation. The check never blocks acceptance and is skipped silently when
Git or an integration branch is unavailable.

## Run State and Evidence

Use the package `DELIVERY-RUN.json` as a small resume checkpoint:

- delivery, `delivery_status`, branch, and selected profile;
- current stage and completed stages;
- changed paths;
- compact stage verdicts and material findings;
- autonomous rejection count;
- pending audit obligations;
- acceptance decision.

Reference existing test/CI logs instead of copying them into Markdown. Successful
stages need a verdict and evidence reference, not a narrative report in several
files. The package `HISTORY.md` receives one final delivery summary plus
unresolved blocking/escalation entries.

Compliance extensions may add manifests, hashes, environment fingerprints,
detailed command evidence, model identity when exposed, and retention data.

## Worker Verdicts

Workers return:

```text
pass | fail | blocked | not_applicable
```

Each result includes the stage, material findings, checks performed, evidence
references, changed/scope paths, and recommended next action. Never invent
evidence, model names, telemetry, or successful checks.

Critical/High review or security findings fail assurance. Medium/Low findings
are recorded debt unless project policy says otherwise. Unmet required
acceptance criteria fail QA. Tool/environment failure is `blocked`, not a
quality rejection.

## Human Acceptance

A passing assurance sequence sets `delivery_status: awaiting-acceptance` and
produces a brief containing:

- delivered outcome and demonstration;
- acceptance-criteria coverage;
- review/security/QA disposition;
- deviations and remaining risks;
- checks and evidence references;
- merge readiness when other packages are open or the integration branch has
  moved.

Only an explicit human decision sets `accepted` or `rejected`. Acceptance does
not authorize commit, merge, deployment, or selection of the next package.

## Source-Code Traceability

Story, epic, task, delivery, and acceptance-criterion identifiers belong in
specs, tests when useful, commits/PRs, and delivery history. Do not add them as
production-code comments.

## Feedback Routing

| Finding | Return |
| --- | --- |
| Implementation defect or Critical/High review finding | Gate 5 |
| Security implementation defect | Gate 5 |
| Security architecture defect | Gate 3 |
| Unmet acceptance criterion | Gate 5 |
| Changed requirement or boundary | Gate 4, or Gate 2/3 when necessary |
| XL package or Open uncertainty | Gate 2/3 |
| Non-additive overlap with another open package | Gate 4 (sequence or re-split) |
| Repeated autonomous rejection | Human decision |

Feedback loops are explicit, bounded, and proportional. Do not silently fix a
changed contract and continue.
