---
status: approved
approved_by: user (chat instruction to continue the roadmap in order)
approved_at: 2026-11-05T23:30:00+01:00
---

# Step 10 (local part): Qualified Bundles

## Outcome and Boundary

Produce one verified, reproducible release ZIP from the single authoring source, with one
version authority, a pinned APM, and tests for the packaging rules. Publishing, hosted
catalog resolution, and tag creation are out of this package; they need the owner's
authorization and are tracked as `step-10-hosted-catalog-rehearsal`.

- Size: M; risk: Moderate (release artifact integrity); uncertainty: Bounded.
  Profile: Balanced with independent security and QA review.

## Acceptance Criteria

1. Manifests agree on name and strict semantic version; the APM version is pinned exactly.
2. The ZIP contains every source resource byte-identical (LF-normalized) and nothing
   unexpected; unsafe, hostile, colliding, symbolic-link, and cache entries are refused.
3. The same commit yields the same bytes regardless of checkout line endings; failures
   leave no partial output.
4. A clean extraction runs init, migration, and validator scripts without the source tree.
5. The catalog decision and the unverified items are documented.

## Allowed Paths

`scripts/build-release.py`, `scripts/release-tools.json`, `scripts/release-assets/**`,
`tests/packaging/**`, `docs/RELEASING.md`, `README.md`, `CHANGELOG.md`, `PLAN.md`,
`.gitignore`, this package's records.
