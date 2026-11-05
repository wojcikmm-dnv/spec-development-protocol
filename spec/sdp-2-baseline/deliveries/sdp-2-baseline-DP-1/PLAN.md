---
status: approved
approved_by: user (explicit chat approval of Step 01)
approved_at: 2026-11-05T10:41:06+01:00
---

# Step 01: Repair the Current Baseline

## Outcome and Boundary

Make the current 0.5.4 metadata and instruction contracts consistent before
designing the 2.0 runtime. This is the bounded package explicitly approved in
chat, not approval to execute the XL root roadmap.

- Size: M; risk: Moderate; uncertainty: Resolved for the baseline repairs.
- Profile: Balanced, with independent read-only technical review.
- Security/QA: reassess from actual changes; no permissions, installer behavior,
  dependencies, runtime, migrations, or release automation may change here.
- Preserve unrelated files, both root planning documents, historical builds,
  and global tools. Do not create branches, commit, or publish.

## Acceptance Criteria

1. The canonical skill starter contains a name and folder-matching guidance;
   the generated template mirror remains byte-for-byte synchronized.
2. Developer validation and technical review are mandatory. Only optional
   specialists may return `not_applicable` with a valid policy reason.
3. Root and native plugin manifests agree with the canonical package version.
4. APM regenerates root context with package-scoped delivery state and a
   pointer-only ACTIVE contract; generation is checked in isolation.
5. A reusable baseline check detects historical metadata/instruction drift.
6. README and changelog document the check and repairs without claiming 2.0
   runtime enforcement or changing installation behavior.

## Allowed Paths

- `.apm/templates/template.skill.md` and its generated skill-asset mirror.
- `.apm/agents/sdp.orchestrator.agent.md`.
- `.github/plugin/plugin.json`, `.claude-plugin/plugin.json` when inconsistent.
- `AGENTS.md`, regenerated only through APM.
- One focused checker in `scripts/`, with its negative cases included.
- `README.md`, `CHANGELOG.md`, and this package's records.

`apm.yml` and root `plugin.json` are comparison inputs unless actual baseline
drift requires a minimal repair. Release versions/tag conventions are unchanged.

## Work and Verification

1. Inventory current tracked manifests, generated outputs, revision, tool
   versions, and generation procedure; record orientation in package history.
2. Fix canonical skill metadata, mirror it with the existing sync script, and
   immediately verify the name and byte equality.
3. Clarify mandatory-stage wording and immediately check process/reviewer
   consistency; this is a textual contract, not an execution engine.
4. Reconcile inconsistent manifests and validate parsed versions.
5. Generate APM context into a temporary output, confirm canonical content,
   then regenerate root `AGENTS.md` without changing other host outputs.
6. Add a structured-parser baseline check with failing historical examples;
   document any existing runtime prerequisites without installing dependencies.
7. Update documentation, run all checks, obtain independent review, and
   present an acceptance brief. Human acceptance is a separate decision.

Required checks: baseline checker including negative cases, Bash installer
syntax, PowerShell installer parser, template mirror check, APM validation and
isolated generation comparison, and `git diff --check`.

## Escalation

Stop for a required dependency installation, broad generation churn, changed
permissions, release/runtime contracts, or files outside this boundary. Local
naming and test organization are implementation choices inside the boundary.