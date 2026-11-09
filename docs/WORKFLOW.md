# Workflow Guide

How an SDP delivery runs, what each gate produces, and who decides what. This guide
describes the stable `/deliver` workflow. The schema 4 preview (`/run-workflow`) keeps the
same gates and human decisions; its contract is in [PROTOCOL.md](PROTOCOL.md).

## The six gates

```text
Gate 1: Discovery     -> PRD.md
Gate 2: Refinement    -> BACKLOG.md + EPIC-*.md
Gate 3: Architecture  -> DESIGN.md
Gate 4: Planning      -> PLAN.md
Gate 5: Implementation
Gate 6: Assurance -> human acceptance
```

Gate artifacts start as draft and carry:

```yaml
status: draft | approved | rejected
approved_by: pending | <identity>
approved_at: pending | <ISO timestamp>
```

Manual downstream gates require approval metadata. Bare `/deliver` is the convenience action
that records approval of the current plan before execution. Approval always names a human;
an agent never approves its own work.

### Right-sized earlier gates

Use the full chain for new capabilities and material behavior. For a small fix with an
established product contract and design, the user may explicitly approve a lightweight path
that references existing artifacts.

The lightweight path still requires a clear outcome and non-goals, a plan and change
boundary, executable verification, proportionate independent review, and human acceptance.

### Capability sizing

Every delivery declares size (`S`, `M`, `L`, `XL`), risk (`Low`, `Moderate`, `High`), and
uncertainty (`Resolved`, `Bounded`, `Open`). XL work is split. Open uncertainty about
behavior, data, security, or architecture returns to refinement or design.

### Implementation autonomy

The plan locks outcome, contracts, safety constraints, non-goals, and verification. The
developer owns naming, idiomatic local design, helper reuse or extraction, and adjacent tests
inside the boundary. A simpler in-boundary solution may proceed when outcome, risk, and
verification are unchanged. Public-contract, dependency, security or data-boundary, or
destructive changes require replanning.

### Durable comments

Production comments must not contain story, task, epic, delivery, ticket, or acceptance
criterion identifiers, implementation-step narration, change history, obvious restatements,
or completed planning notes. Keep comments for durable non-obvious invariants, compatibility
constraints, security rationale, protocol quirks, or deliberate trade-offs. Traceability
belongs in specs, meaningful tests, commit or pull request descriptions, and delivery history.

## Delivery profiles

| Profile | Use | Assurance | Evidence |
| --- | --- | --- | --- |
| Lean | Small, low-risk, resolved work | Developer validation and reviewer; specialists only on trigger | Final summary |
| Balanced | Normal product work | Reviewer always; security and QA when they add evidence | Compact run checkpoint and final summary |
| Compliance | Regulated or high-risk work, or when requested | Full policy-required sequence | Configured hashes, manifests, environment, retained evidence |

Balanced is the default. A plan may raise but not silently lower a mandatory project profile.
Developer validation and independent technical review are mandatory in every profile. Only
optional security or QA stages may be `not_applicable`, with a policy reason that cannot
override mandatory project controls. Compliance does not claim to be a tamper-proof audit
system.

## Security and QA routing

Each epic selects `risk-based` (default), `per-story`, `epic-level`, or `waived` with a
reason. Risk-based security runs when a change affects authentication or authorization,
secrets, untrusted input, sensitive data, cryptography, network trust, dependency or
infrastructure security, or regulated controls. Secure coding applies in every profile.

QA runs when independently exercising behavior adds confidence: user journeys, integrations,
accessibility, compatibility, migrations, performance, or critical workflows. If QA could
only repeat the review and focused tests, Lean and Balanced may record it as not applicable.

The reviewer answers "is the code technically correct and maintainable?" QA answers "does
independently observable behavior satisfy acceptance?"

## Supervised and manual delivery

Supervised:

```text
/deliver
/deliver --profile compliance
/deliver resume
/deliver inspect
/deliver reject
```

IDs are requested only when several active or resumable runs are ambiguous. The orchestrator
dispatches one worker at a time and never writes product code. One autonomous repair is
allowed after the first rejected candidate; a second autonomous rejection escalates. A
human-guided correction does not consume that ceiling merely because feedback was given.

Manual: `/implement`, `/run-review`, `/audit-security`, `/qa-validate`. Manual mode suits
expert control, troubleshooting, or runtimes without specialist dispatch.

The schema 4 preview expresses the same stages by capability instead of fixed agent
names and runs them with `/run-workflow`; the mapping from each command above to its
schema 4 equivalent is in [PROTOCOL.md](PROTOCOL.md#command-mapping).

Both modes stop at an acceptance brief. Acceptance never commits, merges, deploys, or selects
the next package.

## Evidence and acceptance

The acceptance brief states the delivered outcome and demonstration, acceptance-criteria
coverage, the review, security, and QA disposition, deviations and remaining risks, the checks
run and where their output is, and merge readiness when other packages are open. A passing
assurance sequence never accepts anything: only a named human accepts, rejects, or describes
a correction. A correction inside the approved outcome and boundary is repaired and rechecked;
a changed requirement returns to planning.

## Parallel delivery with Git worktrees

Independent packages can be delivered at the same time on separate branches, typically in
separate worktrees. Single-package work is unchanged. SDP stays merge-friendly by
construction:

- every package writes only its own `spec/<slug>/deliveries/<delivery-id>/` folder;
- shared specs (`PRD.md`, `BACKLOG.md`, `EPIC-*.md`, `DESIGN.md`, `TECH.md`) are read-only
  during delivery, and feature and story status are derived from accepted packages;
- a story belongs to at most one open package;
- when other packages are open, `/plan-task` marks the plan `independent`,
  `additive-overlap` (shared hotspots with a named merge-friendly technique), or `sequenced`;
- the developer edits shared hotspots additively: new files where possible, self-contained
  blocks, unique migration IDs, no lockfile churn or mass reformatting;
- the acceptance brief reports merge readiness; it is informational and never blocks.

```text
# primary worktree
/plan-task US-3          -> spec/<slug>/deliveries/<slug>-DP-1/PLAN.md
/plan-task US-5 US-6     -> spec/<slug>/deliveries/<slug>-DP-2/PLAN.md (independent)
git add spec && git commit -m "Plan DP-1 and DP-2"
git worktree add ../app-<slug>-DP-1 -b sdp/<slug>-DP-1
git worktree add ../app-<slug>-DP-2 -b sdp/<slug>-DP-2

# each worktree, in its own VS Code window or agent session
/deliver                 -> the sdp/<delivery-id> branch selects the package
```

Merge accepted packages in any order; the later package updates from the integration branch
and reruns the affected verification. Agents propose Git commands but create worktrees,
commit, or merge only on explicit request. The active package resolves from an explicit ID,
the `sdp/<delivery-id>` branch, `spec/ACTIVE.md`, or the only open package. Teams using
parallel delivery should add `spec/ACTIVE.md` to `.gitignore`; it is only a local pointer.

## Artifacts and state

```text
spec/
  ACTIVE.md                  # local pointer
  <feature-slug>/
    PRD.md
    BACKLOG.md
    EPIC-*.md
    DESIGN.md
    deliveries/
      <delivery-id>/
        PLAN.md
        DELIVERY-RUN.json
        HISTORY.md
```

`ACTIVE.md` is a marker with front-matter pointer fields only (`slug`, `title`,
`current_gate`, `current_delivery`) and no body. Progress notes, summaries, and findings go to
the package `HISTORY.md` or `DELIVERY-RUN.json`; product and design notes go to their gate
artifacts. `delivery_status` lives in the package `DELIVERY-RUN.json`; a package with a plan
and no run record is `planned`. Feature and story status are derived from accepted packages.

```text
planned -> delivering -> awaiting-acceptance -> accepted
               |                 |
               -> blocked        -> changes-requested -> delivering
                                 -> rejected
```

`DELIVERY-RUN.json` is a compact resume checkpoint: status, branch, profile, current stage,
completed stages, changed paths, compact verdicts, material findings, audit obligations, and
the acceptance decision. `HISTORY.md` holds one concise final entry per delivery plus
unresolved blocking or escalation entries; detailed logs stay in test or CI output and are
referenced.
