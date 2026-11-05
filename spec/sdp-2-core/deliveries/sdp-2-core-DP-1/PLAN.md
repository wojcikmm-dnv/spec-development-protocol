---
status: approved
approved_by: user (chat instruction to continue the roadmap in order)
approved_at: 2026-11-05T11:40:00+01:00
---

# Step 03: Schemas and Deterministic Validation

## Outcome and Boundary

Ship the `sdp-core` skill: a standard-library Python validator and JSON Schema for
schema-4 run records implementing docs/PROTOCOL.md, with contract tests mapped to
its invariants. The validator is not yet called by any agent or workflow
(Steps 05-06).

- Size: L; risk: High (trust boundaries, file writes, subprocess); uncertainty:
  Resolved by Step 02. Profile: Balanced with independent review and specialist
  security review. Independent QA: covered by contract tests under two operating
  systems; no user-facing install or host behavior changed.

## Acceptance Criteria

1. The validator enforces approval binding, mandatory review, trigger-driven
   specialists, candidate fingerprints, repair counting, transitions, sequencing,
   stale writers, and atomic locked updates, with distinct exit codes.
2. Contract tests cover each invariant in the PROTOCOL.md map and run locally.
3. The published schema and validator agree on valid and invalid records.
4. Security review findings are fixed or documented as limits.
5. No third-party runtime dependency; the skill packages with scripts and schema.

## Allowed Paths

`.apm/skills/sdp-core/**`, `tests/contracts/**`, `docs/PROTOCOL.md`, `.gitignore`,
`README.md`, `CHANGELOG.md`, this package's records.

## Verification

`python -m unittest discover -s tests/contracts` on Windows and WSL; mutation
checks of the key rules; `apm pack --dry-run --verbose` for packaging contents;
existing baseline checks.
