# Reference

Inventories of what the package contains. Everything here lives under `.apm/` in the source
repository and is checked against it by `tests/release/test_docs.py`.

## Agents

| Agent | Responsibility |
| --- | --- |
| `sdp.discover` | Discover legacy technology context |
| `sdp.prd` | Define product outcome and scope |
| `sdp.analyst` | Create coherent stories and acceptance criteria |
| `sdp.architect` | Record right-sized technical decisions |
| `sdp.planner` | Create an implementation-grade plan |
| `sdp.developer` | Implement product code and tests |
| `sdp.reviewer` | Review technical correctness and maintainability |
| `sdp.security` | Audit security-sensitive changes |
| `sdp.qa` | Validate independently observable acceptance |
| `sdp.orchestrator` | Coordinate stable delivery and human acceptance |
| `sdp.coordinator` | Preview: coordinate a schema 4 workflow by following the validator's next action |

## Prompts

| Prompt | Purpose |
| --- | --- |
| `/discover-tech` | Draft TECH from repository evidence |
| `/create-prd` | Draft product requirements |
| `/refine-backlog` | Draft stories and acceptance criteria |
| `/design-system` | Draft technical design |
| `/plan-task` | Plan the active delivery |
| `/deliver` | Approve and deliver the active plan (stable) |
| `/implement` | Manual implementation |
| `/run-review` | Manual review |
| `/audit-security` | Manual security audit |
| `/qa-validate` | Manual acceptance validation |
| `/run-workflow` | Preview: run the schema 4 bug workflow for the active package |

## Skills

| Skill | Purpose |
| --- | --- |
| `create-api-endpoint` | Secure REST endpoint guidance |
| `create-ui-component` | Accessible UI component guidance |
| `database-migration` | Safe migration and recovery guidance |
| `error-handling` | Consistent observable failure handling |
| `write-tests` | Meaningful behavior-focused tests |
| `sdp-core` | The validator for delivery run records, schemas, and the stage-result grader |
| `sdp-workflows` | The `bug` and `feature` workflow definitions, host profiles, and the coordinator procedure |
| `sdp-init` | Create the project's `TECH.md` and `spec/` without overwriting anything |
| `sdp-migrate` | Move an SDP 0.5.3 or 0.5.4 project to the schema 4 layout, with backup and restore |
| `sdp-investigate` | Diagnose a reported defect before a plan |
| `sdp-plan-delivery` | Produce an implementation-grade plan |
| `sdp-implement` | Implement inside an approved boundary |
| `sdp-technical-review` | Independent technical review |
| `sdp-security-review` | Independent security review |
| `sdp-acceptance-validation` | Independent acceptance validation |
| `sdp-templates` | Generated copies of the templates (APM cannot package `.apm/templates/` directly) |
| `sdp-delivery-process` | The full text of the stable delivery process (profiles, assurance triggers, state, parallel delivery, acceptance, feedback routing), loaded on demand instead of with every conversation |

## Templates

| Template | Purpose |
| --- | --- |
| `TECH.md` | Stack, commands, conventions, delivery policy |
| `AGENTS.md` | Scoped context map |
| `ACTIVE.md` | Local pointer to the active feature and package |
| `PRD.md` | Product outcome |
| `BACKLOG.md`, `EPIC.md` | Stories, acceptance criteria, security policy |
| `DESIGN.md` | Contracts, boundaries, decisions |
| `PLAN.md` | Outcome, work, boundary, verification, autonomy |
| `DELIVERY-RUN.json` | Compact resume state |
| `HISTORY.md` | Final outcomes and unresolved blocks |
| `template.agent.md`, `template.prompt.md`, `template.skill.md` | Starters for custom agents, prompts, and skills |

## Customization

| Need | Location |
| --- | --- |
| Project coding standards | `.github/instructions/coding-standards.instructions.md` |
| Delivery, security, and QA policy | `.github/TECH.md` |
| Custom agents | `.github/agents/*.agent.md` |
| Custom prompts | `.github/prompts/*.prompt.md` |
| Custom skills | `.github/skills/<name>/SKILL.md` |
| Module context | repository or module `AGENTS.md` files |

The paths assume files installed into `.github/`. With APM or a native plugin the host places
the package's files itself; keep project-owned files (`TECH.md`, `AGENTS.md`, `spec/`) in the
repository and never edit installed package files in place.

## Repository structure

```text
.apm/
  agents/ instructions/ prompts/
  skills/
    sdp-templates/assets/   # generated mirror of .apm/templates
  templates/                # canonical authoring source
docs/                       # this documentation
scripts/                    # maintainer tooling (not shipped)
spec/                       # delivery records of this repository itself
tests/                      # contracts, skills, init, migrate, packaging, release
```

Edit distributable content only in `.apm/`; the repository's own `.github/` is for maintainer
automation. After changing `.apm/templates/` run `bash scripts/sync-templates.sh` (or
`apm run sync-templates`) and check with `--check` (`apm run check-templates`).
