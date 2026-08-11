---
status: draft
approved_by: pending
approved_at: pending
---

# EPIC-<N>: <Epic Title>

Traceability: `spec/<slug>/PRD.md` -> `spec/<slug>/BACKLOG.md` -> this epic.

## Security Review Policy

- **Policy**: `per-story | epic-level | waived`
- **Reason** (required if `epic-level` or `waived`): `<explicit justification, e.g. "internal tooling, no external input, no auth/data boundary changed">`

> If this policy is left unset and any story below touches auth, secrets, external input, or data boundaries, downstream agents (`sdp.reviewer`) must stop and require it to be set before hardening.

## Stories

### STORY-<N>: <Story Title>

**As a** `<user/persona>`
**I want** `<capability>`
**So that** `<benefit>`

**Acceptance Criteria**

1. Given `<context>`, when `<action>`, then `<expected result>`.
2. `<negative/edge case criterion>`

**Sizing**: `<S/M/L>` — must fit within one PLAN.md Scope Budget (see `sdlc-process.instructions.md`). If not, split into multiple stories.

**Dependencies**: `<other stories/epics, or "none">`

---

_Approval required before proceeding to Gate 3 (`/design-system`). Set `status: approved` above once confirmed._
