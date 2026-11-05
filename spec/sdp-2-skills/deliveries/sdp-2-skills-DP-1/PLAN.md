---
status: approved
approved_by: user (chat instruction to continue the roadmap in order)
approved_at: 2026-11-05T13:00:00+01:00
---

# Step 04: Extract Evaluated Skills

## Outcome and Boundary

Extract stage expertise into portable skills with a shared result contract,
companion descriptors, and evaluation cases, and improve `write-tests`. Agents and
prompts are unchanged; wiring is Step 08.

- Size: L; risk: Moderate; uncertainty: Resolved. Profile: Balanced with independent
  review. Security: not triggered (guidance, fixtures, and read-only checkers; no
  dependency, permission, or network change). QA: structural tests cover the
  observable checker behavior.

## Acceptance Criteria

1. Skills exist for investigation, planning, implementation, technical review,
   security review, and acceptance validation, each with a descriptor and cases.
2. `write-tests` is improved and the unit-versus-integration rule is accurate.
3. No coverage from the current agents is lost; a coverage map exists.
4. Evaluation cases include seeded defects, negatives, and escalations, and every
   reference answer satisfies its case.
5. Name, description, link, descriptor, and case structure are checked by tooling
   with tests that prove it rejects broken skills.

## Allowed Paths

`.apm/skills/**` (new and `write-tests`, plus description lines of four legacy
skills), `scripts/check-skills.py`, `tests/skills/**`, `docs/PROTOCOL.md`,
`README.md`, `CHANGELOG.md`, this package's records.

## Verification

`python scripts/check-skills.py`, `python -m unittest discover -s tests/skills`,
existing contract tests and baseline checks, and independent review.
