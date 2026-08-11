---
description: Defines the 6-stage SDLC gate process, agent routing, and orchestration rules for structured delivery.
applyTo: "**/*"
---

# SDLC Process Instructions

You are operating under the **Spec Development Protocol (SDP)** — a spec-first, gate-driven engineering framework for both greenfield and legacy projects. This file is the **single source of truth** for process, gate ordering, agent routing, and orchestration. Coding standards live separately in `coding-standards.instructions.md`.

All work must follow these gates sequentially unless an explicit exception below applies.

## Mandatory Startup Context

1. Read `@/.github/TECH.md` first — it defines the stack, cloud environment, and project-specific standards. All agents and decisions must be consistent with it. If it does not exist, invoke `sdp.discover` before Gate 1 to draft it from repository evidence.
2. Follow the 6-gate SDLC below — never skip or reorder gates without explicit user approval.
3. Route specialized work through the agents in `@/.github/agents/` using the routing table below.
4. Check `@/spec/ACTIVE.md` — if it exists, it names the currently active feature and its progress (slug, title, current gate, current story, status). Use it as the default working context for all gate operations when no explicit feature is specified in the user's input, and as the resume point after an interrupted session.
5. Resolve the `AGENTS.md` context chain before broad repo exploration: read root-level `AGENTS.md` plus the nearest `AGENTS.md` files in the target module path and follow their scope constraints.

## AGENTS.md Context Strategy (Required)

- Use `AGENTS.md` files as scoped context maps to avoid loading unrelated repository areas.
- Resolution order:
  1. Repository root `AGENTS.md` (global rules and boundaries)
  2. Nearest domain-level `AGENTS.md` (for example solution/app folder)
  3. Nearest module-level `AGENTS.md` in the exact implementation path
- If instructions conflict, the most specific (closest) `AGENTS.md` wins for that module.
- Before searching for files, identify the target module and read only its relevant `AGENTS.md` chain.
- Suggested placement in client repositories:
  - One `AGENTS.md` in each meaningful `.NET` library/service folder (typically next to each `.csproj` or library root).
  - One `AGENTS.md` in each frontend app/package root (for example `apps/web`, `src/frontend`, `packages/ui`).

## Agent Routing

| Task                                    | Agent           | Entry-point prompt |
| --------------------------------------- | --------------- | ------------------ |
| Legacy stack discovery                  | `sdp.discover`  | `/discover-tech`   |
| Discovery / PRD creation                | `sdp.prd`       | `/create-prd`      |
| Backlog refinement (epics, stories, AC) | `sdp.analyst`   | `/refine-backlog`  |
| Architecture / technical design         | `sdp.architect` | `/design-system`   |
| Task planning (no code)                 | `sdp.planner`   | `/plan-task`       |
| Implementation                          | `sdp.developer` | `/implement`       |
| Code and design review                  | `sdp.reviewer`  | `/run-review`      |
| Security assessment                     | `sdp.security`  | `/audit-security`  |
| Acceptance criteria validation          | `sdp.qa`        | `/qa-validate`     |

**Prefer prompt commands over manually selecting an agent.** Each gate has exactly one entry-point prompt; use it instead of invoking the agent directly, so the correct mode and inputs are always applied.

## SDLC Discipline

- Never write code before an approved implementation plan exists.
- Implement exactly one story or task at a time — no bundling.
- Keep every artifact traceable: PRD → backlog → design → plan → code → validation.
- Block on incomplete or ambiguous artifacts.
- Flag and block progression if gate exit criteria are not met.

---

## Feature Folder Convention

All artifacts for a feature are stored in `spec/<feature-slug>/`.

```
spec/
  ACTIVE.md              # Active feature slug, title, and progress state
  <feature-slug>/
    PRD.md               # Gate 1: Product Requirements
    BACKLOG.md           # Gate 2: Epics and stories
    EPIC-<N>-<slug>.md   # Gate 2: Epic details
    DESIGN.md            # Gate 3: Technical design
    PLAN.md              # Gate 4: Implementation plan
    HISTORY.md           # Log of completed tasks and hardening outcomes
```

Every gate artifact (`PRD.md`, `BACKLOG.md`, `EPIC-*.md`, `DESIGN.md`, `PLAN.md`) MUST follow its template in `.github/templates/` and MUST start with a status header:

```
status: draft | approved | rejected
approved_by: <name or "pending">
approved_at: <ISO date or "pending">
```

Agents MUST treat an artifact as usable input for the next gate **only** when `status: approved`. Do not infer approval from conversational tone alone — check the field. An agent that produces an artifact sets `status: draft` and stops; only the user (or an explicit user instruction such as "approved") flips it to `approved`.

`ACTIVE.md` format:

```
slug: <feature-slug>
title: <Human Readable Feature Title>
current_gate: <1-6>
current_story: <story id or "n/a">
status: <in-progress | blocked | done>
```

Agents read and update `spec/ACTIVE.md` at the start and end of every gate so work can resume correctly after an interrupted session.

---

## The 6 Gates

1.  **Discovery (PRD)**: Define the "what" and "why".
    - **Owner**: `sdp.prd`
    - **Output**: `spec/<feature-slug>/PRD.md`

2.  **Refinement (Backlog)**: Break PRD into epics and right-sized stories (INVEST: Independent, Negotiable, Valuable, Estimable, Small, Testable — target ~1 day/1 PR of effort per story; split anything larger).
    - **Owner**: `sdp.analyst`
    - **Output**: `spec/<feature-slug>/BACKLOG.md`, `EPIC-*.md`
    - Each epic declares a `security_review` policy (see Security Review Policy below).

3.  **Architecture (Design)**: Create the technical design, including a rough complexity/effort rating per story so oversized stories are caught before planning.
    - **Owner**: `sdp.architect`
    - **Output**: `spec/<feature-slug>/DESIGN.md`

4.  **Planning (Task Plan)**: Create an implementation plan for exactly one story. **Does not write code.**
    - **Owner**: `sdp.planner`
    - **Output**: `spec/<feature-slug>/PLAN.md`, including a mandatory Scope Budget (see below).

5.  **Implementation (Code)**: Execute the approved plan exactly.
    - **Owner**: `sdp.developer`
    - **Output**: Code, tests, and docs. Appends to `HISTORY.md`.
    - **Terminal step**: once implementation is complete, the only valid next action is handing off to `sdp.reviewer`. `sdp.developer` never re-invokes itself and never regenerates `PLAN.md` on its own initiative.

6.  **Hardening (Validate)**: Review, secure, and test.
    - **Sequence**: `sdp.reviewer` → `sdp.security` (unless waived/deferred, see policy below) → `sdp.qa`
    - **Output**: Review, audit, and QA reports appended to `HISTORY.md`.

---

## Plan Scope Budget (Gate 4, mandatory)

To keep implementation time and token usage predictable, every `PLAN.md` MUST declare a Scope Budget before it can be approved:

| Field                   | Limit                                                                   |
| ----------------------- | ----------------------------------------------------------------------- |
| Files touched           | 8 max                                                                   |
| Estimated changed lines | 300 max (guideline, not a hard line-counter)                            |
| Complexity tier         | S / M / L — L requires an explicit justification note                   |
| Exploration budget      | Stated up front (e.g., "read only files listed in DESIGN.md section X") |

**Rule**: If a plan would exceed these limits, `sdp.planner` MUST stop and recommend splitting the story, returning it to Gate 2 (`sdp.analyst`) for re-slicing instead of producing an oversized plan. Do not silently plan past the budget.

## Gate 4 → Gate 5 Handoff (Loop Prevention)

`sdp.planner` (plan-task) and `sdp.developer` (implement) are **separate agents** with **no self-referencing handoff**. This prevents the plan → implement → implement → implement loop seen when a single agent's mode is ambiguous:

- `sdp.planner` only ever produces `PLAN.md` with `status: draft` and stops. It never calls itself and never calls `sdp.developer` automatically.
- Moving from Gate 4 to Gate 5 requires an explicit user action: approving the plan (`status: approved`) and running `/implement`.
- `sdp.developer` only ever hands off forward to `sdp.reviewer` after implementation. It never re-enters implementation or planning on its own.
- If an approved plan needs to change mid-implementation, `sdp.developer` MUST stop, explain why, and request the user route back to `/plan-task` for an amended, re-approved plan — it must not silently keep "implementing" in a loop.

---

## Hardening Gate Rules (Gate 6)

### Unified Severity Taxonomy

`sdp.reviewer`, `sdp.security`, and `sdp.qa` all use the same four-level severity scale so findings can be aggregated and gated consistently:

| Severity     | Meaning                                          | Gate outcome                           |
| ------------ | ------------------------------------------------ | -------------------------------------- |
| **Critical** | Breaks correctness, security, or data integrity  | Always blocks; must return to Gate 5   |
| **High**     | Significant risk or defect, must fix before ship | Blocks; must return to Gate 5          |
| **Medium**   | Should fix, does not block this story            | Logged in `HISTORY.md` as tracked debt |
| **Low**      | Cosmetic/suggestion                              | Logged only, no action required        |

### Security Review Policy (per-epic, configurable)

Security audits are not always required per-story. `BACKLOG.md`/`EPIC-*.md` declares one of:

- **`per-story` (default)** — `sdp.security` runs on every story before QA.
- **`epic-level`** — `sdp.security` is deferred until all stories in the epic are implemented, then runs once against the full epic diff. `sdp.reviewer` hands off directly to `sdp.qa` for individual stories and notes the deferral in `HISTORY.md`; the epic cannot be marked done until the deferred audit completes.
- **`waived`** — Security audit is intentionally skipped, with a documented reason recorded in the epic's `security_review` field (e.g., "internal tooling, no external input, no auth/data boundary changed"). `sdp.reviewer` hands off directly to `sdp.qa` and logs the waiver and reason in `HISTORY.md`. Agents must not complain or block when a waiver is explicitly declared — but must complain and stop if `security_review` is unset/ambiguous on a story that touches auth, secrets, external input, or data boundaries.

### Loop Breaker / Escalation

Hardening feedback loops (reviewer/security/qa → developer → hardening again) are capped:

- **After 2 failed hardening cycles on the same story** (i.e., the same story fails review, security, or QA twice), the responsible agent MUST stop auto-retrying and escalate to the user for a decision (e.g., descope, split the story, accept documented risk) instead of routing back to Gate 5 a third time.
- Escalations are logged in `HISTORY.md` with the cycle count and reason.

---

## Feedback Loops

Failures route back to the appropriate gate, not to the start.

| Finding Source                          | Returns To        | Action                                        |
| --------------------------------------- | ----------------- | --------------------------------------------- |
| `sdp.reviewer` (Critical/High)          | Gate 5            | Developer fixes findings.                     |
| `sdp.security` (Critical/High)          | Gate 5 or 3       | Developer or Architect fixes issues.          |
| `sdp.qa` (fail)                         | Gate 5            | Developer fixes defects.                      |
| Blocked Story                           | Gate 2            | Analyst updates backlog.                      |
| PRD Gaps                                | Gate 1            | PRD agent updates PRD.                        |
| 2x failed hardening cycle on same story | User (escalation) | User decides: descope, split, or accept risk. |

**Rule**: Never silently fix and continue. Feedback loops must be explicit. See Loop Breaker above for the retry cap.

---

## Cross-Gate Rules

- Reference `@/.github/TECH.md` for stack and standards.
- Resolve `AGENTS.md` before broad file searches.
- Maintain traceability: PRD -> Backlog -> Design -> Plan -> Code -> Validation.
- Block on incomplete, ambiguous, or unapproved (`status: draft`/`rejected`) artifacts.
- Implement one story at a time through Gates 4-6.
- Prefer the prompt commands (`/create-prd`, `/refine-backlog`, `/design-system`, `/plan-task`, `/implement`, `/run-review`, `/audit-security`, `/qa-validate`, `/discover-tech`) over manually invoking an agent.
