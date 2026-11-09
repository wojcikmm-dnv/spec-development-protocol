# Spec Development Protocol (SDP)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

SDP is an open-source, spec-driven delivery framework for AI coding agents, built for GitHub
Copilot Agent Mode. It keeps product intent, implementation, independent assurance, and human
acceptance connected without forcing compliance-grade ceremony onto every change.

```text
/plan-task
review PLAN.md
/deliver
accept, reject, or describe a correction
```

AI coding assistants can implement quickly before intent, constraints, and verification are
clear. SDP puts the specification first, right-sizes the artifacts to the work, keeps
independent review proportional to risk, and ends every delivery with a human decision.

## Contents

- [Choose a workflow](#choose-a-workflow)
- [Install](#install)
- [Initialize a project](#initialize-a-project)
- [Quick start](#quick-start)
- [Scope, evidence, and acceptance](#scope-evidence-and-acceptance)
- [The schema 4 preview](#the-schema-4-preview)
- [Requirements and limits](#requirements-and-limits)
- [Documentation](#documentation)
- [Contributing](#contributing)

## Choose a workflow

| You want to | Use | Notes |
| --- | --- | --- |
| Fix a reported defect | the `bug` workflow (preview) or `/plan-task` then `/deliver` | Diagnose first, then a small plan. |
| Build a capability or change behavior materially | the six gates: `/create-prd`, `/refine-backlog`, `/design-system`, `/plan-task`, `/deliver` | Each gate is a draft until a named human approves it. |
| Make a small change with an existing contract and design | a lightweight plan (`/plan-task`, `/deliver`) | Still needs a plan, executable verification, independent review, and human acceptance. |
| Adopt SDP in an existing codebase | `/discover-tech` first, then any of the above | Drafts `TECH.md` from repository evidence. |

The process is the same six gates every time (discovery, refinement, architecture, planning,
implementation, assurance); the cost of each gate is proportional to the work. See the
[workflow guide](docs/WORKFLOW.md) for profiles (Lean, Balanced, Compliance), security and QA
routing, and parallel delivery.

## Install

| Channel | Command | Status |
| --- | --- | --- |
| APM | `apm install WojcikMM/spec-development-protocol` | Bundle built and tested here; hosted install not re-run for the current candidate |
| GitHub Copilot CLI marketplace | `copilot plugin marketplace add WojcikMM/spec-development-protocol` | Verified with a local directory only |
| Claude Code marketplace | generated `.claude-plugin/` files | Not tested (Claude Code was unavailable) |
| Release ZIP | from a GitHub release | None published for 2.0 yet |

Which version has what: the released 0.5.x tags contain the stable agents, prompts,
instructions, and six skills (API, UI, migration, errors, tests, and the template assets). The `sdp-init`, `sdp-migrate`,
validator, and workflow skills described below exist on the current `main` branch and will ship
in the first 2.0 release, which has not been published. Pin a released tag rather than a moving
branch, for example `apm install WojcikMM/spec-development-protocol#v0.5.4`; that gives you the
stable workflow only. Details, the APM versus native plugin difference, stable versus
prerelease tags, updating, and the manual fallback are in
[docs/INSTALLATION.md](docs/INSTALLATION.md).

## Initialize a project

Installing gives you skills and agents; initializing creates your project's own files. Run the
init script from the installed package's `skills` folder (`<installed skills>` below; use
`python3` where `python` is not available). It previews first and never overwrites:

```bash
python <installed skills>/sdp-init/scripts/init.py --repo .          # preview
python <installed skills>/sdp-init/scripts/init.py --repo . --apply  # create what is missing
```

It creates `.github/TECH.md` and an empty `spec/` folder; Git does not track an empty folder,
so commit your first spec file before relying on `spec/` being in the repository. Fill in
`TECH.md`: stack and commands, conventions, the default delivery profile (Balanced is
recommended; missing model telemetry never blocks Lean or Balanced), security and
independent-QA triggers, and optional model routing. Add scoped `AGENTS.md` files where they
reduce scanning, starting from the `AGENTS.md` template in the `sdp-templates` skill's
`assets/` folder. Then enable Agent Mode in VS Code and confirm the custom agents and prompts
appear.

## Quick start

Example: add user registration.

| Step | Action | Prompt | Output |
| --- | --- | --- | --- |
| 1 | Define outcome and scope | `/create-prd` | `PRD.md`, `ACTIVE.md` |
| 2 | Approve the PRD and refine behavior | `/refine-backlog` | `BACKLOG.md`, `EPIC-*.md` |
| 3 | Approve the backlog and design contracts | `/design-system` | `DESIGN.md` |
| 4 | Approve the design and plan the package | `/plan-task` | `PLAN.md` |
| 5 | Read the plan and deliver it | `/deliver` | code, tests, proportional assurance |
| 6 | Review the acceptance brief | plain language | accept, reject, or describe a correction |

Bare `/deliver` resolves the active package, approves the plan you just read, implements it,
runs the required assurance, and stops for your decision. A correction such as "the empty
state is wrong: keep the action visible but disabled" is repaired and rechecked when it stays
inside the approved outcome; a changed requirement returns to planning.

## Scope, evidence, and acceptance

- **Scope is approved before code.** A plan names the outcome, change boundary, non-goals,
  and verification. Developers choose local design inside it; a changed public contract,
  dependency, data or security boundary, or destructive operation needs replanning.
- **Assurance is independent and proportional.** Developer validation and independent
  technical review always run. Security and QA run when a trigger or policy says they add
  evidence. A passing check is recorded as evidence, never as acceptance.
- **A named human accepts.** The acceptance brief lists the outcome, criteria coverage, stage
  verdicts, deviations, risks, and checks with where to find their output. Acceptance never
  commits, merges, or deploys.

## The schema 4 preview

A validator-backed path is being built alongside the stable commands. It stores each package
as a schema 4 run record, derives the next action from files instead of conversation, enforces
legal transitions, binds approval to the exact plan a human saw, and refuses to substitute
self-review when a host cannot run an independent reviewer. Entry points are the
`sdp.coordinator` agent and `/run-workflow`; the `bug` and `feature` workflows exist.

Status, stated plainly: the validator and its tests are in place, and GitHub Copilot CLI
loaded the skills and followed two read-only steps in bounded trials. No host has executed a
full delivery, so no host is qualified, and Claude Code is untested. See
[docs/COMPATIBILITY.md](docs/COMPATIBILITY.md). Projects on 0.5.3 or 0.5.4 move with
`sdp-migrate` ([docs/UPGRADING.md](docs/UPGRADING.md)); keep using `/deliver` for real work
until a host is qualified.

## Requirements and limits

- Visual Studio Code with the GitHub Copilot extension and Agent Mode, and a Copilot
  subscription, for the stable prompts. Note that no host observation covers a full delivery
  on either path; the only host with any recorded observation is GitHub Copilot CLI (see
  [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md)), and VS Code is untested.
- Python 3.9 or newer and Git for the shipped scripts, which use only the standard library.
  Without Python the schema 4 workflow stops with an explicit message and the stable prompts
  keep working. APM itself needs its own runtime (see [docs/INSTALLATION.md](docs/INSTALLATION.md)).
- The validator checks records and enforces transitions. It is not a sandbox: approver names
  are asserted strings, and it cannot prove who reviewed what. Compliance profile adds
  retained evidence but is not a tamper-proof audit system.
- Nothing here claims that a model follows the skills, or any productivity gain.

## Documentation

| Document | Contents |
| --- | --- |
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Channels, pinning, updating, requirements, mixed installs |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | Gates, profiles, routing, supervised and manual delivery, parallel work, state |
| [docs/REFERENCE.md](docs/REFERENCE.md) | Agents, prompts, skills, templates, customization, structure |
| [docs/UPGRADING.md](docs/UPGRADING.md) | `sdp-migrate`, rollback, older layouts |
| [docs/PROTOCOL.md](docs/PROTOCOL.md) | The record, transition, and approval contract |
| [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md) | What was observed on each host |
| [docs/RELEASING.md](docs/RELEASING.md) | Building, verifying, and publishing a release |
| [CHANGELOG.md](CHANGELOG.md) | History |

## Contributing

1. Edit distributable content in `.apm/`, never the repository's own `.github/` (maintainer
   automation only). `.apm/templates/` is canonical; run `bash scripts/sync-templates.sh`
   after changing it.
2. Keep instructions, agents, prompts, templates, documentation, and tool output aligned.
3. Run the Linux checks CI runs: `bash scripts/check-all.sh`, in a Linux checkout (CI also runs
   the suites on Windows and the shipped scripts on Python 3.9). It needs Python 3.10 or newer
   (APM requires it), Git, PyYAML 6.0.3, `jsonschema`, and the APM version pinned
   in `scripts/release-tools.json`. The individual commands are listed in that script. The
   shipped scripts themselves need only Python 3.9.
4. After changing canonical instructions, regenerate the root context with the installed APM
   (verified with 0.29.0) and preview first with `--dry-run`:

   ```bash
   apm compile --local-only --single-agents --target copilot --output AGENTS.md
   ```

Release packaging and publishing are described in [docs/RELEASING.md](docs/RELEASING.md). The
baseline checks are textual consistency checks, not proof that an agent enforced delivery
gates.

## License

[MIT](LICENSE)
