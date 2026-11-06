---
status: approved
approved_by: user (chat)
approved_at: 2026-11-06T14:02:53+01:00
---

# SDP 2.0 - Portable Delivery Protocol

> Specification, skills, and assurance for AI-assisted delivery.

## Status and Scope

This proposal consolidates the November 2026 review and distribution discussion
into a direction for 2027. It describes the target, not capabilities already
implemented. The owner reviewed and approved this document on 2026-11-06.

[PLAN.md](PLAN.md) is the ordered implementation roadmap. Neither document
authorizes an unrestricted rewrite, release, or deletion of client files.

## Executive Decision

Evolve SDP from a Copilot-oriented, six-gate instruction framework into a
portable delivery protocol with reusable skills, work-specific workflows,
isolated assurance, and executable validation of delivery records.

Keep the safeguards that already work. Replace the coupling between engineering
expertise, agent identities, platform paths, and one universal process.

"AI-Native Delivery Operating System" remains a long-term ambition, not the
initial product claim. Predictions about the winning 2027 architecture are
hypotheses to test through adoption and measured outcomes.

## Keep, Change, and Remove

| Keep | Change | Remove or demote |
| --- | --- | --- |
| Outcomes, acceptance criteria, boundaries, and non-goals | Six gates become the feature workflow | Six gates as mandatory process for every task |
| Independent assurance and explicit human acceptance | Engineering expertise moves into skills | One agent identity for every process stage |
| Lean, Balanced, and Compliance assurance | Personas become optional onboarding presets | Organization size as a safety boundary |
| Package-scoped state and bounded repairs | Validate state, evidence, and policy contracts | Duplicated hand-maintained process rules |
| Non-destructive setup and project ownership | APM, native marketplaces, and release bundles | Custom client installers in 2.0 |
| Scoped context and durable comments | Load detailed procedures on demand | Always-on instructions containing the entire process |

Do not delete a component until its replacement preserves its responsibilities
and has passed the relevant migration and compatibility checks.

## Non-Negotiable Invariants

- Approve the implementation outcome, change boundary, and verification before
  product changes. A workflow may reuse existing requirements and design.
- Keep implementation and assurance in separate execution contexts. A review
  skill invoked by the implementer is not independent review.
- Require technical review for every implementation delivery, including Lean.
  Optional specialists may be inapplicable only with a valid policy reason.
- Escalate new public behavior, dependencies, security/data boundaries,
  destructive operations, or weakened acceptance criteria for approval.
- Passing checks means awaiting acceptance. Only an explicit human decision
  accepts or rejects a candidate; acceptance never authorizes release or merge.
- Preserve unrelated changes, project policy, specs, and delivery history.
- Invalidate affected assurance when the candidate changes. Do not reuse stale
  evidence merely because the same filenames remain in the change list.
- Treat missing tools or unsupported capabilities as blocked, not passed.
- Allow one autonomous bounded repair after the first failed candidate;
  escalate a second autonomous rejection. Human-guided corrections are distinct.
- Keep delivery state package-scoped and enforce sequencing dependencies before
  execution. Separate worktrees do not prove behavioral independence.

## Architecture

Four responsibilities replace the original seven overlapping layers:

```text
Protocol contracts and project policy
                  |
        Workflows and skills
                  |
          Host adapters
                  |
Implementation -> Independent assurance -> Human acceptance
                  |
     Validation of state and evidence
```

### 1. Protocol

Define versioned contracts for work identity, workflow selection, approved
scope, required capabilities, assurance policy, evidence, transitions, and
acceptance. Keep specs readable; structure only fields software must validate.

Retain existing PRD, backlog, epic, design, plan, run, and history artifacts
where useful. Do not rename `DESIGN.md` to `ARCHITECTURE.md`, or add a separate
`ACCEPTANCE.md`, solely to make the framework look new. Use ADRs only for
significant durable decisions. Avoid storing the same approval or final status
in several documents.

### 2. Workflows and Skills

Workflows decide the path; skills package how to perform its activities.
Workflow definitions reference skill capabilities, not fixed agent names.

| Workflow | Required path | Delivery order |
| --- | --- | --- |
| Bug | Investigate/reproduce -> approve bounded plan -> fix/test -> independent review -> acceptance | First vertical slice |
| Feature | Intent -> refinement -> design -> approved plan -> implement/test -> assurance -> acceptance | Initial 2.0 scope |
| Migration | Current state -> gap/recovery analysis -> approved plan -> execute -> independent verification -> acceptance | After core qualification |
| Spike | Question -> bounded research -> reviewed findings -> human decision | After core qualification |
| Postmortem | Timeline -> impact -> root cause -> reviewed actions -> human decision | Later extension |

A bug workflow reuses established requirements; it does not bypass planning or
review. A spike must not silently become production implementation. The
original incident sequence is a postmortem, not live incident response.
Containment, emergency authorization, and service restoration are out of the
initial scope and require a separately designed incident workflow.

Each workflow declares inputs, outputs, entry/exit conditions, required and
conditional stages, failure routing, retry limits, and escalation rules.

Skills use the standard `SKILL.md` discovery surface with required `name` and
specific trigger descriptions. Use `references/`, `assets/`, and `scripts/`
only when needed. Put SDP-specific machine contracts in a companion descriptor
rather than assuming every host understands custom frontmatter fields.

Start with bounded investigation, delivery planning, implementation guidance,
write-tests, technical review, security review, and acceptance validation.
Extract useful existing material before writing replacements. Preserve API,
UI, migration, and error-handling guidance until equivalent coverage exists.

A product-quality skill needs clear inputs, observable outputs, failure and
escalation behavior, realistic examples, and evaluation cases. More checklists
alone are not differentiation. Stack-specific expertise should reuse suitable
existing skills instead of duplicating an entire ecosystem.

### 3. Host Adapters

Adapters map neutral capabilities into host-native agents, tools, prompts,
discovery locations, and context isolation. Retain agents when isolation or
different permissions justify them, not merely to name every workflow stage.

The first qualified hosts are GitHub Copilot in VS Code and Claude Code.
Existing APM targets for Codex, Gemini, and Cursor remain candidates for
qualification; packaging success alone must not imply runtime support. Copilot
CLI is a separate tested client, not automatically covered by VS Code results.

Publish a matrix of host/version, supported components, isolated dispatch,
tool restrictions, approval routing, initialization, and resume behavior. If a
host cannot dispatch an independent worker, provide an explicit manual review
path or block the affected mode. Never silently substitute self-review.

### 4. Validation

Build a small deterministic validator, not a general-purpose workflow engine
or hosted service. Validate schemas, approvals, required assurance, transitions,
candidate/evidence association, resume records, and package references.

Use structured parsers and a proven schema library. Select and document the
cross-platform runtime and dependency budget before implementing this layer.
Adapters invoke validation before advancing state; CI exercises invalid as
well as valid records. Use atomic writes and stale-writer detection for state.

Validation is not a sandbox or authenticated approval system. Local files can
be edited outside SDP, and terminal access can mutate files even without an
editor tool. Document these limits. Compliance integrations may use external
identity, protected CI, or retained evidence when project policy requires it.

## Assurance and State Contract

| Profile | Required assurance | Evidence |
| --- | --- | --- |
| Lean | Developer validation and independent technical review; specialists on trigger | Compact results and final summary |
| Balanced | Technical review; security and independent behavioral QA when triggered | Stage verdicts, evidence references, run checkpoint |
| Compliance | All project-mandated stages and integrity controls | Configured identity, manifests, environment, and retention |

Balanced remains the default. Plans may raise but not silently lower mandatory
policy. Solo Creator, Startup, Enterprise, and Regulated may be setup presets,
but none exempts a sensitive change from its assurance requirements.

Preserve explicit epic security policy and pending aggregate audits during
migration. An optional waiver cannot override mandatory project controls.
Reviewers report newly discovered security/QA triggers in a structured result;
the coordinator reevaluates required stages after implementation and review.

Workers return `pass`, `fail`, `blocked`, or, for permitted optional stages,
`not_applicable`, with findings, scope, checks, evidence, detected triggers, and
next action. Critical/High review or security findings and unmet required
acceptance criteria prevent acceptance readiness.

The run contract must specify and test:

- `planned -> delivering -> awaiting-acceptance -> accepted`;
- `awaiting-acceptance -> changes-requested -> delivering` or `rejected`;
- blocking and resume from the last valid checkpoint without implicit approval;
- approval binding to the selected plan and stale-approval detection;
- candidate identity including relevant untracked files and subsequent changes;
- one increment per rejected candidate, not per finding or failing stage;
- no rejection-count increment for environment failures or duplicate resumes;
- invalidation and rerunning of assurance after repairs or integration changes;
- single state ownership per run and handling of concurrent/stale writes;
- acceptance attribution and retained pending audit obligations.

Keep normal candidate bookkeeping automatic and compact. Do not expose hashes
as routine user inputs or reintroduce Compliance ceremony into every plan.

## Source, Installation, and Project Data

These are separate ownership boundaries:

| Boundary | Target policy |
| --- | --- |
| Maintainer source | `.apm/` remains canonical for distributable primitives |
| Package resources | Bundle protocol schemas, workflow definitions, and validator resources through supported skill assets/scripts |
| Host installation | APM or the native plugin manager owns installed framework files |
| Project data | Project policy, `spec/` artifacts, and package run/history remain project-owned |
| Build output | Generated packages and catalogs; never a second authoring source |

Do not move everything into `.sdp/`. Retain `spec/<slug>/deliveries/<id>/` and
the local `spec/ACTIVE.md` pointer initially. Keep existing project
`.github/TECH.md` compatible through a neutral resolver; a later policy-path
change requires its own justified migration.

Do not add unsupported top-level `.apm/` directories and assume APM packages
them. A concrete initial home is `sdp-core` and `sdp-workflows` skills containing
their respective resources. Keep `.apm/templates/` canonical and the existing
`sdp-templates` mirror until the pinned packager demonstrably supports a better
solution. Test package-relative resource discovery outside the author checkout.

## Installation and Distribution

The 2.0 channels are:

1. APM for project dependencies, version pinning, and reproducible team setup.
2. GitHub Copilot agent-plugin marketplaces for native installation.
3. Claude Code plugin marketplaces for native installation.
4. GitHub Release ZIP bundles for local installation and manual setup.

Copilot agent plugins are not VS Code extensions; no VSIX or MSI is required.
Maintain an SDP catalog that users can add. Inclusion in an official curated
catalog requires a separate submission and is not a release success criterion.
Different hosts may require different manifests or layouts even when they share
skills. Generate those variants from the same canonical content.

Retire `install.sh` and `install.ps1` from the supported 2.0 distribution only
after replacement channels and migration tests pass. Historical tags retain
the old scripts. Document that old `main`-based installer URLs stop being the
supported setup path; do not silently repurpose them.

### Installation Is Not Initialization

Installing a package must not silently rewrite a project's specs or policy.
Provide an explicit, idempotent SDP initialization entry point that:

- checks host/runtime capabilities and resolves bundled resources;
- previews and creates only missing project configuration and directories;
- preserves existing TECH, scope maps, specs, history, and unrelated files;
- reports mixed versions and duplicate native/copied SDP installations;
- requests a decision for conflicts or migrations instead of using blanket force.

Plugin upgrades update package-owned files only. Manual ZIP users receive clear
destination and upgrade guidance, with no instruction to overwrite the whole
`.github/` directory.

### Tag-Triggered Release

Use one `v<semver>` convention, such as `v2.0.0`, across tags and generated
catalog references. Keep one authoritative package version and verify every
generated manifest against it.

On a release tag, GitHub Actions must:

1. Check out the exact tag and use pinned actions, APM, and build dependencies.
2. Validate versions and find the exact matching `CHANGELOG.md` section;
   reject missing/empty notes and never substitute `Unreleased` or another tag.
3. Run contract, metadata, mirror, packaging, and clean-install checks.
4. Build ready-to-use ZIP bundles from `.apm/`; use APM archive support where
   qualified rather than implementing a second packaging system.
5. Generate SHA-256 checksums and record source revision/tool versions.
6. Create or resume a draft release, attach and verify all assets, then publish.
7. Propose a catalog update referencing the exact qualified revision, not moving
   `main`; merge it through the catalog's protected publishing policy.

Use least-privilege job permissions; only the publishing job needs release
write access. Pre-releases must not replace the stable channel. Reruns must not
silently overwrite published assets with different bytes. A catalog update
failure is reported separately and can be retried without rebuilding a release.

GitHub's automatic source archives are not substitutes for installable bundles.
Separate platform ZIPs are justified only by required layout differences.
Checksums detect corruption; they are not proof of publisher identity.

## Migration and Compatibility

Inventory supported legacy layouts before implementing migration. Migrate a
copy first, with a preview and backup; validate before committing any change.
Preserve approved scope, acceptance decisions, unresolved findings, custom
policy, and audit obligations. Ambiguous legacy statuses require human mapping.

Unknown newer schemas, conflicting installs, and unrecognized file ownership
must stop automatic migration. Never remove files by name alone. Only clean up
verified SDP-owned legacy files with explicit consent after the replacement
loads correctly. Rollback restores the matching package and project-state
backup together; do not resume new-schema records with an old runtime.

## Qualification and Rollout

First prove one bug-fix package end to end on both initial hosts. Include failed
review, bounded repair, interrupted execution, stale evidence, security triggers,
and explicit human acceptance. Only then expand to the feature workflow and
broader skill catalog. Migration and spike workflows follow core qualification;
postmortem and live incident support are not initial 2.0 requirements.

Measure missed seeded defects, invalid transitions accepted, resume correctness,
human interventions, completion time, and cost when telemetry is available.
Record unavailable telemetry honestly. Compare against a fixed current-SDP
baseline on equivalent fixtures; do not claim universal productivity gains.

## Decisions Required Before Implementation

- Approve the versioned protocol and runtime/dependency choice before coding
  the validator; distinguish format validation from host enforcement.
- Pin APM and initial host versions after packaging/capability experiments.
- Select a protected catalog publication location and verify native revision
  selection before automating updates.
- Define the supported legacy migration range and evaluation thresholds from
  baseline evidence, not assumptions about historical formats.

These are bounded design gates in the implementation plan, not permission for
agents to improvise changes to security or distribution contracts.

## References

- [Implementation plan](PLAN.md)
- [Current framework documentation](README.md)
- [Current package metadata](apm.yml)
- [APM bundle documentation](https://microsoft.github.io/apm/producer/pack-a-bundle/)
- [Copilot agent plugins](https://code.visualstudio.com/docs/copilot/customization/agent-plugins)
- [Claude official plugin catalog](https://github.com/anthropics/claude-plugins-official)

The product promise is portable, reviewable delivery with evidence. Skills are
valuable when evaluated, orchestration is valuable when recoverable, and agents
remain replaceable only when adapters preserve the contract.