---
status: draft
approved_by: pending
approved_at: pending
---

# Plan: <Story Title> (STORY-<N>)

Traceability: `spec/<slug>/DESIGN.md` -> `spec/<slug>/EPIC-<N>-<slug>.md` (STORY-<N>).

## Scope Budget (mandatory)

| Field                   | Value                                                       | Limit                          |
| ----------------------- | ----------------------------------------------------------- | ------------------------------ |
| Files touched           | `<count>`                                                   | 8 max                          |
| Estimated changed lines | `<estimate>`                                                | 300 max (guideline)            |
| Complexity tier         | `<S/M/L>`                                                   | L requires justification below |
| Exploration budget      | `<e.g., "only files listed below and DESIGN.md section 3">` | stated up front                |

**If this story cannot fit the budget above, STOP.** Do not produce an oversized plan — recommend splitting the story and return it to Gate 2 (`sdp.analyst`).

**Justification for tier L (if applicable):** `<why this cannot be split further>`

## Files to Change

- `<path/to/file>` — `<what changes and why>`

## Implementation Steps

1. `<step>`
2. `<step>`

## Test Plan

- `<test case derived from acceptance criteria>`

## Risks & Rollback

- Risk: `<risk>` — Mitigation: `<mitigation>`
- Rollback: `<how to revert this change safely>`

---

_Approval required before implementation. Set `status: approved` above, then run `/implement`. `sdp.developer` will refuse to run otherwise._
