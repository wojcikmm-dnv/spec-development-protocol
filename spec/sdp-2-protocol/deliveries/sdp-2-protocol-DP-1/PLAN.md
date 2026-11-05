---
status: approved
approved_by: user (chat instruction to continue the roadmap in order)
approved_at: 2026-11-05T11:05:00+01:00
---

# Step 02: Settle Protocol and Runtime Decisions

## Outcome and Boundary

Produce `docs/PROTOCOL.md`: the versioned protocol contract (records, transitions,
ownership, policy precedence, candidate identity, repair counting, stale-writer
handling) and the validator runtime/dependency decision, with every proposal
invariant mapped to a planned test. Design only: no validator code, schemas,
or changes to agents, installers, or distributed content.

- Size: S; risk: Moderate; uncertainty: Resolved after the decisions recorded in
  the document. Profile: Lean with independent review.
- Security/QA: not applicable beyond review; the document introduces no
  executable behavior. Step 03 carries the security review of the validator.

## Acceptance Criteria

1. Every record, transition, and ownership rule in REFACTOR_PORPOSAL.md has a
   defined source of truth and no duplicated final-status field.
2. Runtime, versions, dependency budget, distribution, and missing-runtime
   behavior are decided with rationale and stated limits.
3. Candidate change detection covers untracked files without user-supplied hashes.
4. The supported legacy migration range is stated.
5. Each invariant maps to at least one named planned test for Steps 03-05.

## Allowed Paths

`docs/PROTOCOL.md`, `PLAN.md` step status, this package's records.

## Verification

Link and structure checks, a consistency read against the proposal, and an
independent read-only review. Open security or public-contract questions block
Step 03 instead of being guessed.
