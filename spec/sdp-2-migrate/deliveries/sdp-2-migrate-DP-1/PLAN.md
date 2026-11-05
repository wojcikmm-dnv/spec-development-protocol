---
status: approved
approved_by: user (chat instruction to continue the roadmap in order)
approved_at: 2026-11-05T22:30:00+01:00
---

# Step 09: Legacy Migration

## Outcome and Boundary

Provide `sdp-migrate`, a tool that moves an SDP 0.5.3 or 0.5.4 project to the schema 4
layout without fabricating approvals, losing history, or leaving a half-migrated tree.

- Size: L; risk: High (rewrites user state and can delete copied files); uncertainty:
  Resolved. Profile: Balanced with independent security and QA review.

## Acceptance Criteria

1. Preview changes nothing; apply writes a backup and journal first, validates every
   migrated record, and restores everything on any failure, including interruption.
2. Open packages restart as `planned` with their approval voided and recorded; accepted
   and rejected packages carry over only with a recorded named human decision.
3. Original records are preserved; pending audit obligations survive or the migration
   stops; nothing is silently reinterpreted.
4. Copied legacy files are removed only on explicit request, only by released-content
   hash, with the installer marker, never APM-managed ones, and into the backup.
5. Links, junctions, and path escapes are refused; malformed input gives clean errors.
6. Rollback (`restore`, `status`) never overwrites later edits.

## Allowed Paths

`.apm/skills/sdp-migrate/**`, `.apm/skills/sdp-core/scripts/sdp.py` and its run-record
schema (the `migrated_from` field), `.apm/skills/sdp-init/scripts/init.py` (warning text),
`scripts/build-legacy-manifests.py`, `tests/migrate/**`, `docs/PROTOCOL.md`, `README.md`,
`CHANGELOG.md`, `PLAN.md`, this package's records.
