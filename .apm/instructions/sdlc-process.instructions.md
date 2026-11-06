---
description: Defines the six-gate SDP workflow, proportional assurance, and supervised delivery.
applyTo: "**/*"
---

# SDLC Process Instructions

The Spec Development Protocol (SDP) is a spec-first, gate-driven framework for
greenfield and legacy projects. This file holds only the rules that must never be
forgotten. The full process (profiles, assurance triggers, delivery state, parallel
delivery, acceptance, feedback routing) is in the `sdp-delivery-process` skill; load it
when you plan, deliver, resume, or audit a package.

Use the smallest process that gives independent confidence in the change.
Traceability supports delivery; it must not become the delivery.

## Startup Context

1. Read `@/.github/TECH.md`. If it is missing in a legacy project, use
   `sdp.discover` to draft it.
2. Resolve the active feature and package. `spec/ACTIVE.md`, when present, is a local
   pointer to the active feature, gate, and delivery package; the resolution order is
   in the `sdp-delivery-process` skill.
3. Resolve the applicable `AGENTS.md` chain from repository root to the target
   module before broad exploration.
4. Resolve `SDP_TEMPLATE_ROOT` to the first existing directory:
   `.github/templates`, `.agents/skills/sdp-templates/assets`, then
   `.github/skills/sdp-templates/assets`.
5. Follow the gates in order unless the user explicitly approves a lightweight
   path or a return to an earlier gate.

## Agent Routing

| Work | Agent | Prompt |
| --- | --- | --- |
| Legacy stack discovery | `sdp.discover` | `/discover-tech` |
| Product requirements | `sdp.prd` | `/create-prd` |
| Backlog and acceptance criteria | `sdp.analyst` | `/refine-backlog` |
| Technical design | `sdp.architect` | `/design-system` |
| Delivery planning | `sdp.planner` | `/plan-task` |
| Manual implementation | `sdp.developer` | `/implement` |
| Manual code review | `sdp.reviewer` | `/run-review` |
| Manual security audit | `sdp.security` | `/audit-security` |
| Manual acceptance validation | `sdp.qa` | `/qa-validate` |
| Supervised implementation and assurance | `sdp.orchestrator` | `/deliver` |

## The Six Gates

1. **Discovery** - define the problem, users, outcome, and scope in `PRD.md`.
2. **Refinement** - define epics, stories, acceptance criteria, dependencies,
   and security policy in `BACKLOG.md` and `EPIC-*.md`.
3. **Architecture** - record contracts, boundaries, decisions, and material
   non-functional requirements in `DESIGN.md`.
4. **Planning** - create one implementation-grade `PLAN.md` per coherent
   delivery package in `spec/<slug>/deliveries/<delivery-id>/`.
5. **Implementation** - change product code and tests within the approved
   boundary.
6. **Assurance and acceptance** - run proportionate independent checks, present
   an acceptance brief, and wait for a human decision.

Do not write product code before a delivery plan is approved. A user who has
reviewed the active plan and invokes bare `/deliver` explicitly approves that
exact current plan; the orchestrator records `status`, approver, and time before
implementation. Manual `/implement` still requires approval metadata to be
present.

## Approvals

Gate artifacts carry `status: draft | approved | rejected`, `approved_by`, and
`approved_at`. An agent that authors an artifact leaves it as `draft`; only a named
human approves. A downstream manual gate requires approved metadata.

For a small fix with an established product contract and design, the user may
explicitly approve a lightweight path that references existing artifacts. It never
removes a clear outcome and non-goals, a plan and change boundary, executable
verification, independent review appropriate to risk, or human acceptance.

## Assurance

- Every delivery plan declares size (`S | M | L | XL`), risk (`Low | Moderate | High`),
  and uncertainty (`Resolved | Bounded | Open`). `XL` is split; `Open` uncertainty about
  behavior, data loss, security, or architecture returns to backlog or design.
- Profiles are `Lean`, `Balanced` (default), and `Compliance`. A plan may raise but not
  silently lower a mandatory project profile.
- Developer validation and independent technical review are mandatory in every profile.
  Only optional security or QA stages may be `not_applicable`, with a policy reason that
  does not override mandatory project controls.
- Security runs when a change affects authentication, authorization, secrets,
  untrusted input, sensitive data, cryptography, network trust, dependency or
  infrastructure security, or a regulated control. QA runs when independently exercising
  observable behavior adds evidence. Secure-coding checks apply in every profile.
- Critical or High review or security findings fail assurance. Tool or environment
  failure is `blocked`, not a quality rejection.
- The autonomous repair ceiling is one repair after the first rejected candidate; a
  second autonomous rejection escalates to the human.
- Any product or test change invalidates the assurance it affects. Preserve unrelated
  user changes; never revert them to construct a cleaner candidate.
- Never invent evidence, verdicts, checks, model names, or telemetry.

## Implementation Autonomy

Plans lock outcomes, contracts, safety constraints, non-goals, and verification.
Inside those, the developer owns naming, idiomatic local design, helper reuse, and
adjacent tests. A changed public contract, dependency, data or security boundary,
destructive operation, or acceptance criterion requires replanning or explicit approval.

## State

`spec/ACTIVE.md` holds only the pointer fields `slug`, `title`, `current_gate`, and
`current_delivery`, and no body; notes go to the package `HISTORY.md` or
`DELIVERY-RUN.json`. `delivery_status` lives in the package `DELIVERY-RUN.json`. During
Gates 4-6, write only the package's own folder, `spec/ACTIVE.md`, and product code or
tests inside the plan boundary; `PRD.md`, `BACKLOG.md`, `EPIC-*.md`, `DESIGN.md`, and
`TECH.md` are read-only and a needed change returns to Gate 2 or 3.

## Human Acceptance

A passing assurance sequence produces one acceptance brief (outcome and demonstration,
criteria coverage, review/security/QA disposition, deviations and risks, checks and
evidence references). Only an explicit human decision accepts or rejects. Acceptance does
not authorize commit, merge, deployment, or selection of the next package.

## Source-Code Traceability

Story, epic, task, delivery, and acceptance-criterion identifiers belong in specs, tests
when useful, commits or pull requests, and delivery history. Do not add them as
production-code comments.

## Feedback

Return a finding to the gate that owns it (implementation defects and unmet criteria to
Gate 5, changed requirements to Gate 4 or earlier, architecture defects to Gate 3). Do not
silently fix a changed contract and continue.
