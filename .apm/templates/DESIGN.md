---
status: draft
approved_by: pending
approved_at: pending
---

# Design: <Feature Title>

Traceability: `spec/<slug>/BACKLOG.md` / `EPIC-*.md`.

## 1) Architecture Overview

`<summary and rationale, right-sized to the problem>`

## 2) Module Boundaries & Ownership

- `<module/service>` — owns `<responsibility>`

## 3) Contracts

- API: `<endpoint, method, request/response schema>`
- Data schema: `<entities, fields, relations>`

## 4) Patterns Applied

- `<e.g., Ports & Adapters at the DB boundary — only where complexity justifies it>`

## 5) Non-Functional Requirements

- Security: `<authn/authz, data handling>`
- Performance: `<latency/throughput targets>`
- Reliability: `<failure modes, retries>`

## 6) Story Complexity/Effort Rating

| Story ID | Complexity (S/M/L) | Notes                                                           |
| -------- | ------------------ | --------------------------------------------------------------- |
| STORY-1  | `<S/M/L>`          | `<why; flag if likely to exceed a single PLAN.md Scope Budget>` |

> Any story rated **L** or flagged as likely to exceed the Gate 4 Scope Budget should be sent back to `sdp.analyst` for splitting before planning.

## 7) Trade-offs & Decisions

- `<decision>` — chosen over `<alternative>` because `<rationale>`.

## 8) Open Questions / Assumptions

- `<question or assumption>`

---

_Approval required before proceeding to Gate 4 (`/plan-task`). Set `status: approved` above once confirmed._
