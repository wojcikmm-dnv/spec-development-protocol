---
status: draft
approved_by: pending
approved_at: pending
---

# SDP 2.0 Implementation Plan

## Purpose and Approval Boundary

Implement the direction in [REFACTOR_PORPOSAL.md](REFACTOR_PORPOSAL.md): portable
workflow and skill contracts, independent assurance, validated delivery state,
and package-manager/marketplace distribution with tag-triggered releases.

This root document is a program roadmap, not an active delivery package for
bare `/deliver`. The overall change is XL and must be split. Before executing
each step, create an appropriately sized package plan under
`spec/<feature>/deliveries/<delivery-id>/PLAN.md`, with its actual paths,
commands, acceptance criteria, dependencies, and human approval. Split any
step that remains XL. Do not populate approval metadata on the user's behalf.

Document authoring does not implement the proposal or authorize deletion,
publication, deployment, new infrastructure, or changes to client repositories.

## Outcome and Demonstration

A maintainer can publish a tagged, validated SDP package with release notes and
downloadable bundles. A user can install through APM or a qualified native
plugin channel, initialize a project without losing local work, and complete a
bug or feature delivery with independent review and explicit acceptance.

The demonstration must cover both Copilot in VS Code and Claude Code, including
an interrupted run, a rejected candidate and repair, a security-triggered
review, a stale-evidence rejection, and an existing-project migration.

## Non-Goals

- No hosted workflow engine, dashboard, model router, or new package manager.
- No automatic commit, merge, deployment, or human acceptance.
- No wholesale move to `.sdp/` or cosmetic artifact renaming.
- No self-review represented as independent assurance.
- No guarantee that packaging for a host proves runtime compatibility.
- No MSI/VSIX installer and no new custom client installation scripts.
- No claim that local validation is a sandbox or tamper-proof audit system.
- No live incident response or exhaustive skill catalog in the initial release.

## Delivery Shape and Policy

| Field | Value |
| --- | --- |
| Program size | XL; execute only as separate S/M/L packages |
| Program risk | High: assurance, migration, and executable distribution |
| Uncertainty | Bounded at roadmap level; resolve each design gate before affected implementation |
| Assurance | Independent reviewer for every package; security and QA according to triggers below |
| Mandatory profile | Never lower the project's required profile; select per package |

Security review is required for validator inputs, executable skills, path/file
ownership, migration, host permissions, dependencies, and release automation.
Independent QA is required for state/resume behavior, installation, migration,
host compatibility, and publication. Documentation-only packages can use Lean
with independent review and focused consistency checks.

## Change Boundary

| Surface | Intended work |
| --- | --- |
| `.apm/instructions/` | Minimal always-on invariants; move work-specific procedures to packages |
| `.apm/agents/`, `.apm/prompts/` | Thin host entry points and isolated worker roles |
| `.apm/skills/` | Extract expertise; add core/workflow resources, validator, and initialization capability |
| `.apm/templates/` | Versioned state and skill templates; preserve useful existing artifacts |
| `.apm/skills/sdp-templates/assets/` | Generated mirror only; never edit independently |
| `apm.yml`, plugin manifests, catalogs | Unified metadata, qualified packaging, pinned release references |
| `scripts/`, new `tests/` | Maintainer checks, packaging/release helpers, fixtures, evaluations |
| `.github/workflows/` | Validation and tag-release automation, not template source |
| `AGENTS.md` | Regenerate through the qualified APM compiler |
| `README.md`, `CHANGELOG.md`, new focused `docs/` | User guide, compatibility, migration, and release policy |
| `install.sh`, `install.ps1` | Retired in Step 13 on the owner's approval (2026-11-09) |

Existing `.agents/` and `.claude-plugin/` outputs must be classified before
touching them. Do not hand-edit generated files or historical `build/` outputs.
Use a clean temporary build directory for new artifacts. Do not alter unrelated
user files, credentials, repository settings, or installed global plugins.

## Ordered Steps

Progress: Steps 01-07, 08a, 09, 10 (local part), 11 (CI green on the fork; release not yet
exercised), 12, and 13 (installers retired) are accepted: packages `sdp-2-baseline-DP-1`,
`sdp-2-protocol-DP-1`, `sdp-2-core-DP-1`, `sdp-2-skills-DP-1`, `sdp-2-workflow-DP-1`,
`sdp-2-hosts-DP-1`, `sdp-2-init-DP-1`, `sdp-2-feature-DP-1`, `sdp-2-migrate-DP-1`,
`sdp-2-bundles-DP-1`, `sdp-2-release-DP-1`, `sdp-2-docs-DP-1`, `sdp-2-feature-DP-2`
(08b instructions), `sdp-2-feature-DP-3` (worker agents on the stage skills),
`sdp-2-docs-DP-2` (changelog CI status), `sdp-2-release-DP-2` (local rehearsal
preparation), `sdp-2-release-DP-3` (cross-OS archive verification), and
`sdp-2-release-DP-4` (legacy installer retirement).
The 08b instructions half is accepted as `sdp-2-feature-DP-2` (2026-11-06); the remaining
handoff chains and user-facing command mapping stay with the superseded-component scope of
Step 13. CI passed on all three matrices on runs 42222480747 (`bf43597f`, 2026-11-06),
42610731073 (`deee456`, 2026-11-09), and 42639411557 (`7ea3dbf`, 2026-11-09). The last
five packages were accepted on the owner's explicit chat exception (2026-11-09), which
waived the wait after delivery; external rehearsals, publication, and host qualification
stay open. Step 06's exit criterion is only partly met: GitHub Copilot CLI is
smoke-tested, but Claude Code was unavailable and is blocked, tracked as the open
obligation `step-06-claude-code-qualification`; no host has executed a full delivery.
Protocol design is in [docs/PROTOCOL.md](docs/PROTOCOL.md), the validator is in
`.apm/skills/sdp-core`, and the stage skills are under `.apm/skills`.
All later steps are pending. A step completes only when its checks and independent
assurance pass and a human accepts the package. Record actual evidence in that
package rather than duplicating reports here.

### Step 01 - Capture and Repair the Current Baseline

- [ ] Inventory canonical files, generated outputs, versions, known install
  layouts, and existing commands. Record a reproducible current-SDP baseline.
- [ ] Fix the missing `name` field in `.apm/templates/template.skill.md` and
  synchronize its generated mirror.
- [ ] Restrict orchestrator `not_applicable` handling to policy-optional stages;
  make mandatory review consistent with process and reviewer instructions.
- [ ] Regenerate root `AGENTS.md` so it agrees with package-scoped state and the
  pointer-only ACTIVE contract; do not manually patch generated process text.
- [ ] Reconcile root and `.github/plugin/` manifest versions with `apm.yml`;
  inspect other discovered manifests and establish how each is generated.

**Why:** Prevent known contradictions from becoming the 2.0 baseline.
**Depends on:** Approval of this documentation and the bounded baseline package.
**Verify:** `bash -n install.sh`, PowerShell installer syntax parsing,
`bash scripts/sync-templates.sh --check`, and `git diff --check`; add focused
metadata/contract checks that fail against the old inconsistent examples.
**Exit:** Reproducible generation and a documented baseline, without changing
client installation or introducing 2.0 behavior.

### Step 02 - Settle Protocol and Runtime Decisions

- [ ] Write a concise design defining work, workflow, skill capability,
  approval, candidate, evidence, stage result, acceptance, and ownership.
- [ ] Specify schema versions, supported transitions, security-policy
  precedence, trigger reevaluation, dependency sequencing, and repair counting.
- [ ] Define the source of truth for each field; retain approval on the plan
  and package run/history ownership without duplicate final-status fields.
- [ ] Choose a minimal cross-platform validator runtime and proven structured
  parsing/schema libraries. Record versions, distribution method, dependency
  justification, and missing-runtime behavior before writing validator code.
- [ ] Define plan/candidate change detection, including relevant untracked
  files, without making hashes routine user inputs.
- [ ] Define protected boundaries, stale-writer detection, and what local
  validation cannot enforce. Confirm the legacy migration support range.

**Why:** A protocol needs executable semantics before more agent instructions.
**Depends on:** Step 01.
**Verify:** Review valid/invalid example records for every transition and map
every invariant in the proposal to at least one planned test.
**Exit:** Approved design and runtime decisions; unresolved security or public
contract questions block Step 03 rather than being guessed during coding.

### Step 03 - Add Schemas and Deterministic Validation

- [ ] Add a standard `sdp-core` skill under `.apm/skills/`; package schemas,
  validator scripts, and references through supported resource directories.
- [ ] Implement read-only validation for approval, scope, stage results,
  mandatory assurance, security triggers, evidence, and schema compatibility.
- [ ] Implement validated state updates with atomic replacement and
  stale-writer protection. Keep inspection read-only and retries idempotent.
- [ ] Define explicit exit codes and machine-readable diagnostics. Never use
  an agent's prose assertion as a substitute for a required record/check.
- [ ] Add focused `tests/contracts/` and fixtures using the selected runtime's
  established test tooling; document exact local and CI commands.

**Why:** Detect invalid progression and recover safely from interruption.
**Depends on:** Step 02.
**Verify:** Reject unapproved/stale plans, unsupported schemas, missing review,
waivers overriding policy, stale evidence, untracked candidate changes, invalid
acceptance transitions, path escapes, and stale writers. Test valid resume,
partial writes, duplicate results, one-repair ceiling, and blocked environments
without rejection-count increments.
**Exit:** Deterministic positive/negative tests pass; security review confirms
trust-boundary handling and documents limits without claiming sandboxing.

### Step 04 - Extract Evaluated Skills

- [ ] Extract investigation, planning, implementation, technical review,
  security review, and acceptance-validation procedures from existing agents.
- [ ] Improve `write-tests` with task triggers, scoped evidence expectations,
  failure routing, and examples; distinguish isolated unit tests from intended
  integration I/O instead of universally banning network-backed tests.
- [ ] Define standard discovery metadata and a companion SDP descriptor for
  inputs, outputs, capabilities, applicability, and validation where needed.
- [ ] Reuse existing API/UI/migration/error-handling guidance. Keep compatible
  names until replacements and migration mappings are proven.
- [ ] Add evaluation fixtures for correct behavior, seeded defects, negative
  cases, and escalation. Do not require every skill to ship a script.

**Why:** Make expertise portable and demonstrably useful, not just reworded.
**Depends on:** Step 02; use Step 03 contracts for structured results.
**Verify:** Required `name`/folder matching, meaningful descriptions, resource
links, result validation, and bounded skill evaluations pass. Review does not
modify the candidate and reports independently inspected evidence.
**Exit:** Small evaluated skill set with explicit limitations and no lost
coverage from retired agent prose.

### Step 05 - Implement the Bug Workflow and Coordinator

- [ ] Add `sdp-workflows` under `.apm/skills/` with a versioned bug workflow
  resource referencing capabilities rather than fixed worker names.
- [ ] Implement reproduction, bounded plan approval, fix/test, independent
  technical review, triggered specialists, and human acceptance.
- [ ] Route coordinator transitions through Step 03 validation. Preserve
  single-writer run ownership and prohibit coordinator product-code edits.
- [ ] Enforce sequencing prerequisites, capability preflight, stale evidence
  invalidation, one autonomous repair, and explicit feedback classification.
- [ ] Ensure `inspect`, `resume`, rejection, and manual fallback have defined
  semantics and cannot approve a new or changed plan implicitly.

**Why:** Prove the smallest useful end-to-end workflow before expanding scope.
**Depends on:** Steps 03 and 04.
**Verify:** Run a fixture from reproduction to awaiting acceptance, inject a
review failure, repair once, interrupt/resume, change the candidate, and verify
required rechecks. A second autonomous rejection escalates.
**Exit:** Contract-level workflow tests pass without accepting or releasing
anything automatically.

### Step 06 - Qualify Copilot and Claude Adapters

- [ ] Map capabilities into thin host-native entry points and permissions.
  Keep isolated implementer and reviewer contexts; retain additional workers
  only where isolation or permissions justify them.
- [ ] Pin tested Copilot/VS Code, Claude Code, and APM versions. Test actual
  supported manifest fields, command namespacing, and resource discovery.
- [ ] Define capability negotiation and an explicit manual-review fallback;
  block unsupported supervised modes rather than using self-review.
- [ ] Resolve installed resources from package locations, not the maintainer
  checkout. Support project-owned TECH through the neutral resolver.
- [ ] Publish a compatibility matrix distinguishing generated packages,
  smoke-tested installation, and qualified delivery execution.

**Why:** APM targets are useful but do not establish behavioral equivalence.
**Depends on:** Step 05.
**Verify:** Execute the same bug fixtures on both hosts, including failed
review, security-trigger forwarding, environment block, resume, and explicit
acceptance. Record host versions, evidence, and unavailable telemetry.
**Exit:** Both initial hosts pass. Unavailable host testing is blocked, not
assumed successful. Codex/Gemini/Cursor and Copilot CLI remain explicitly
unqualified until equivalent checks run.

### Step 07 - Add Non-Destructive Initialization

- [ ] Provide a dedicated initialization skill/entry point with deterministic
  filesystem checks using the chosen runtime, separate from installation.
- [ ] Preview missing configuration and directories; create only missing
  project-owned files after confirmation. Repeat runs must make no changes.
- [ ] Preserve existing TECH, AGENTS context maps, specs, run/history, and
  unrelated `.github/` content. Report conflicting or mixed installations.
- [ ] Support both APM-installed and native-plugin resource locations.
- [ ] Document the exact user-facing entry point after confirming host naming.

**Why:** Package managers do not replace the installers' project-setup role.
**Depends on:** Step 06.
**Verify:** Fresh, legacy, customized, read-only, and duplicate-install fixtures;
run initialization twice and compare contents. Reject unsafe paths/symlinks and
conflicts without partial overwrite. Security and independent QA both review.
**Exit:** Project setup works without either legacy installer.

### Step 08 - Add the Feature Workflow and Reduce Global Instructions

**Status:** split. 08a (feature workflow) is accepted. 08b was first deferred to Step 13
because the legacy agents and `/deliver` read the always-on process instructions. At the
owner's direction the instructions part is now done: the always-on process file is 133 lines,
and the detail moved verbatim into the on-demand `sdp-delivery-process` skill, which the
orchestrator and planner point to. The instructions half is accepted as package
`sdp-2-feature-DP-2` (2026-11-06). The worker agents were consolidated as package
`sdp-2-feature-DP-3` (2026-11-06): they point at the `sdp-implement`, `sdp-technical-review`,
`sdp-security-review`, and `sdp-acceptance-validation` skills for their stage procedures.
Handoff chains and user-facing command mapping still wait for Step 13. The new path does
not depend on that file; it is
self-contained in the `sdp-core` and `sdp-workflows` skills. Whether hosts load the skill when
needed is not yet observed.

- [x] 08a: express the six gates as the `feature` workflow with approved contracts,
  derived gate and story status, a lightweight path, and a frozen-spec rule.
- [x] 08b-instructions: reduce always-on process instructions to startup routing,
  ownership, safety invariants, and links; move the full delivery-process text verbatim
  into the on-demand `sdp-delivery-process` skill (package `sdp-2-feature-DP-2`,
  accepted 2026-11-06).
- [ ] 08b-agent-procedures: replace duplicated agent procedures and handoff chains with
  workflow references; preserve or explicitly migrate user-facing commands (mapping in
  `docs/PROTOCOL.md`). Started: the worker agents point at the stage skills
  (package `sdp-2-feature-DP-3`, 2026-11-06); the handoff chains and `/deliver` reference
  updates stay with Step 13.

- [ ] Express the existing six gates as the feature workflow using approved
  contracts, skills, and adapters; retain useful PRD/backlog/design templates.
- [ ] Support existing-contract shortcuts without removing bounded planning,
  independent review, or human acceptance.
- [ ] Reduce always-on process instructions to startup routing, ownership,
  safety invariants, and links to applicable workflows.
- [ ] Replace duplicated agent-specific procedures and handoff chains with
  workflow references; preserve or explicitly migrate user-facing commands.
- [ ] Preserve package-scoped parallel work, audit obligations, and read-only
  shared specs. Require fresh verification after integration changes.

**Why:** Support normal feature work without imposing its ceremony on bugs.
**Depends on:** Steps 06 and 07.
**Verify:** Feature and bug fixtures select distinct paths; mandatory review,
profile floors, audit closure, and sequencing remain enforced. Compare generated
instructions with canonical source and verify no duplicate state ownership.
**Exit:** Initial 2.0 workflows pass on both qualified hosts.

### Step 09 - Implement and Test Legacy Migration

**Status:** accepted (package `sdp-2-migrate-DP-1`).

- [x] Build fixtures for the supported legacy range chosen in Step 02,
  including shared ACTIVE state, package-scoped state, and customizations.
- [x] Implement preview, backup, transformation on a copy, validation, and
  explicit application. Preserve scope, decisions, findings, and pending audits.
- [x] Detect already-migrated and unknown-newer schemas. Ask for human mapping
  of ambiguous statuses; never fabricate historical approval or evidence.
- [x] Detect duplicate copied/native installations and propose cleanup only
  for verified SDP-owned files, with explicit consent and restoration data.
- [x] Document coordinated rollback of package version and project-state
  backup, including how interrupted migrations are recovered.

**Why:** A major refactor must not discard client policy or delivery evidence.
**Depends on:** Steps 07 and 08.
**Verify:** Dry-run changes nothing; repeat application is idempotent; failure
leaves the original recoverable. Test custom files, collisions, path escapes,
unknown versions, unresolved audits, and backup restoration.
**Exit:** Supported migrations and rollback pass independent QA/security review.

### Step 10 - Produce Qualified Bundles and Catalogs

**Status:** local part accepted (package `sdp-2-bundles-DP-1`): version authority and
tag convention, pinned APM, deterministic verified ZIP, `tests/packaging/`, and the
catalog decision in [docs/RELEASING.md](docs/RELEASING.md). Not done: installing exact
bundles through hosted native channels and resolving immutable catalog revisions; Copilot
CLI loads a local marketplace live, so that needs a published repository and a tag
(tracked as `step-10-hosted-catalog-rehearsal`, to be done with Step 11/14 and the owner's
authorization).

- [ ] Standardize release tags on `v<semver>` and remove conflicting package
  tag overrides. Derive generated manifest versions from one authority.
- [ ] Pin APM and validate its actual archive/catalog behavior. Do not select
  a portable format that drops required agents, prompts, or instructions.
- [ ] Build installable ZIPs from `.apm/`; generate host variants only where
  native manifest/layout requirements differ. Include license/setup guidance.
- [ ] Choose a protected generated-catalog branch or separate catalog repo;
  document the decision and exact native revision-pinning behavior.
- [ ] Add `tests/packaging/` checks for missing resources, excluded artifacts,
  hidden-file preservation, safe extraction, versions, and clean installation.

**Why:** One authoring source should serve every supported distribution path.
**Depends on:** Steps 08 and 09.
**Verify:** Install exact generated bundles via APM and both native channels in
disposable locations, without relying on source-checkout paths. Validate all
expected components and run initialization plus a representative workflow.
**Exit:** Catalog entries resolve immutable qualified revisions; source ZIPs
are not presented as ready-to-install plugin bundles.

### Step 11 - Automate Validation and Tag Releases

**Status:** authored and tested locally (package `sdp-2-release-DP-1`), authorized by the
owner. Not done: a separately authorized prerelease rehearsal on GitHub and a native catalog
install (tracked as `step-11-github-rehearsal`). CI passes on all three matrices on the
owner's fork (latest verified: run 42610731073 on `deee456`, 2026-11-09). The earlier
failures were a real `migrate.py` Python-3.9 bug and a writer-lock bug under the runner's
short temp path; both are fixed and verified on GitHub. Earlier failures were a real
`migrate.py` Python-3.9 bug and a writer-lock bug under the runner's short temp path; both
were fixed and are now verified on GitHub (evidence in the `sdp-2-release-DP-1` records). The
release workflow and the publisher's REST usage have never run against GitHub. See
[docs/RELEASING.md](docs/RELEASING.md).

- [ ] Add pull-request CI for metadata, template/generated-content drift,
  contracts, fixtures, packaging, and version consistency.
- [ ] Add a release workflow triggered by `v*` tags with strict semantic-version
  validation; build only from the tagged commit using pinned tooling/actions.
- [ ] Extract only the matching nonempty changelog section with a structured
  Markdown parser. Test optional dates, prereleases, duplicate/missing sections,
  and unrelated newer entries; never fall back to `Unreleased`.
- [ ] Use separate validation/build and publishing jobs with minimal
  permissions. Gate publication on all required evidence.
- [ ] Assemble a draft release, upload ZIPs, SHA-256 checksums, and revision/tool
  metadata, verify assets, then publish. Keep prereleases off stable.
- [ ] Add concurrency/idempotency handling: resume incomplete drafts; do not
  overwrite differing published bytes. Propose protected catalog updates only
  after publication, with exact revision references.

**Why:** Tags should reproducibly produce complete releases, not partial uploads.
**Depends on:** Step 10 and explicit authorization of publishing configuration.
**Verify:** Fixture tests for changelog extraction, mismatched versions, failed
build/upload, reruns, concurrent runs, and prerelease behavior. Perform a
separately authorized prerelease rehearsal and native catalog install.
**Exit:** Release and catalog failures are distinguishable and recoverable;
checksums are not described as publisher authentication.

### Step 12 - Rewrite User Documentation and Migration Guidance

**Status:** accepted for the current state (package `sdp-2-docs-DP-1`). Installation examples
were followed from a scratch repository by an independent reviewer; hosted-channel installs
and the 2.0 changelog entry (kept under `Unreleased`, labeled as planned) stay open until a
release exists. Docs were refreshed with Step 13's installer retirement (package
`sdp-2-release-DP-4`, accepted 2026-11-09); a final refresh remains after Step 14.

- [ ] Rewrite README around choosing a workflow, installation channel,
  initialization, scope approval, evidence, and acceptance.
- [ ] Move long inventories and detailed compatibility/migration/release policy
  into focused reference docs; keep the quick start runnable and concise.
- [ ] Explain APM versus native plugins, Copilot plugins versus VSIX, curated
  catalog submissions, ZIP usage, stable/prerelease selection, and updates.
- [ ] Document manual fallback, runtime requirements, validation limits,
  ownership, migration range, rollback, and mixed-install detection.
- [ ] Add the 2.0 changelog entry with breaking changes and migration steps.
  Avoid claims of untested host support or measured productivity gains.

**Why:** Users need a reliable setup and delivery path, not an architecture pitch.
**Depends on:** Steps 09-11; draft docs alongside implementation and finalize here.
**Verify:** Follow every installation and quick-start example from a clean
environment; validate links, package names, commands, and compatibility claims.
**Exit:** Documentation agrees with generated bundles and release behavior.

### Step 13 - Retire Legacy Installers and Superseded Components

**Status:** accepted (package `sdp-2-release-DP-4`, delivered and accepted on the owner's
chat approval, 2026-11-09). The gate deviation is recorded honestly: no 2.0
release is published and the hosted-channel rehearsal is pending, and the owner approved the
removal with that gap known. Superseded agents/prompts and the remaining Step 08 handoff
chains stay with the later packages.

- [x] The owner explicitly approved deleting `install.sh` and `install.ps1` for 2.0 with the
  replacement-channel gates not fully met (no published release; hosted catalog and Claude
  Code qualification outstanding). Deviation recorded in `sdp-2-release-DP-4`.
- [x] Removed install-script commands from README, `docs/INSTALLATION.md`, `docs/UPGRADING.md`,
  `docs/RELEASING.md`, `scripts/check-all.sh`, and the maintainer validation instructions;
  historical changelog statements preserved.
- [x] Explained historical tag availability (released 0.5.x tags keep the scripts) and
  retired the moving-`main` installer URLs without adding wrappers.
- [ ] Remove superseded agents/prompts only after compatibility mappings and
  coverage checks pass; document any breaking command names.
- [x] Kept the template mirror, historical build archives, and client customization
  reports (`.github/sdp-version` marker detection) untouched.

**Why:** Remove maintenance burden only after the replacement is usable.
**Depends on:** Accepted Steps 09-12 and explicit approval of removals.
**Verify:** No active documentation/CI depends on removed files; archived
instructions remain historical. All supported channels still install,
initialize, migrate, and execute their smoke workflows.
**Exit:** No custom client installers are required or advertised for 2.0.

### Step 14 - Evaluate and Accept the Initial 2.0 Candidate

- [ ] Run the fixed baseline comparison for bugs and features on both initial
  hosts, with seeded defects and equivalent tasks.
- [ ] Report defect detection, invalid transitions, resume correctness, human
  intervention, elapsed time, and cost only when observable.
- [ ] Require zero accepted invalid transitions in the deterministic suite,
  preservation of fixture data, and correct handling of critical seeded cases.
  Apply additional approved thresholds from the baseline design.
- [ ] Complete independent review, security audit, and QA; record remaining
  debt and capability limitations in one acceptance brief.
- [ ] Obtain explicit human acceptance. Request separate authorization to
  create/push the stable release tag or merge catalog publication changes.

**Why:** Validate the product claim before expanding workflows or marketing.
**Depends on:** Steps 01-13.
**Verify:** Link actual test logs, host evidence, release rehearsal, migration
results, and stage verdicts; do not mark unavailable checks as passed.
**Exit:** Accepted initial 2.0 candidate with a separately controlled release.

### Step 15 - Expand Only After Core Qualification

- [ ] Plan migration and spike workflow packages using the proven contracts;
  keep research output distinct from permission to modify production code.
- [ ] Add architecture/performance/accessibility/observability/release-readiness
  skills only with demonstrated demand and evaluation fixtures.
- [ ] Qualify additional hosts independently before extending support claims.
- [ ] Treat postmortem as a separate extension; design live incident response
  only with explicit emergency authorization and recovery requirements.

**Why:** Avoid a broad, untested catalog and universal-process complexity.
**Depends on:** Step 14; not a blocker for initial 2.0 acceptance or release.
**Verify:** Each extension passes the same contract, security, packaging,
compatibility, and human-acceptance requirements relevant to its behavior.
**Exit:** Individually accepted extensions, not an implied unlimited roadmap.

## Dependency and Execution Rules

Execute in numbered order unless an approved package establishes independence.
Documentation and fixture preparation can accompany their owning steps, but
must not skip downstream gates. Steps 03 and 04 may run independently after
Step 02 if their schema/result contracts are fixed. Do not parallelize changes
to shared contracts, generated mirrors, or version metadata without coordination.

Do not add runtime dependencies, change schema ownership, weaken assurance,
move project data, or publish artifacts as an unrecorded implementation detail.
If qualification disproves an assumption, return to the relevant design step.

## Completion Checklist

- [ ] Proposal invariants map to executable checks and documented limits.
- [ ] Bug and feature workflows pass on both initially qualified hosts.
- [ ] Required review cannot be replaced by self-review or `not_applicable`.
- [ ] Approval, rejection, repair, resume, and stale-evidence cases are verified.
- [ ] Installation and initialization preserve project-owned files.
- [ ] Supported legacy migration and coordinated rollback are demonstrated.
- [ ] APM, native catalogs, and release ZIPs deliver complete qualified content.
- [ ] Tag, manifests, changelog notes, checksums, and catalog revision agree.
- [ ] Initializers and docs no longer require the retired client installers.
- [ ] Independent assurance and human acceptance are recorded before release.

## Verification of These Planning Documents

For this documentation-only change, check draft approval metadata, reciprocal
links, ordered steps, dependency references, consistent scope, and removal of
the original assurance/profile contradictions. Run `git diff --check`, the
existing template mirror check.
These checks do not prove that any proposed 2.0 capability is implemented.