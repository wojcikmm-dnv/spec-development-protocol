---
status: approved
approved_by: user (chat: "11")
approved_at: 2026-11-05T23:59:30+01:00
---

# Step 11: CI and Tag-Release Automation

## Outcome and Boundary

Author pull-request CI and a tag-triggered release workflow, with the logic they depend on
(changelog extraction, release publishing, tree and tag verification) in tested scripts. The
owner authorized authoring the publishing configuration. Nothing is pushed, tagged, or
published, and no workflow has run on GitHub.

- Size: L; risk: High (publishes artifacts; handles a write token); uncertainty: Bounded
  (GitHub behavior is unverified until a rehearsal). Profile: Balanced with independent
  security and QA review.

## Acceptance Criteria

1. CI covers metadata, drift, contracts, fixtures, packaging, and versions, and the
   shipped scripts run on Python 3.9 with no third-party packages.
2. The release is triggered only by `v*` tags, builds from the tagged commit that is on
   `main`, and publishes in a separate job with the only write permission.
3. Release notes come from exactly the matching, nonempty changelog section.
4. Publishing is draft-first, verified, resumable, never alters a published release, and
   keeps prereleases off the latest release.
5. Failure classes are distinguishable and documented; checksums are not described as
   publisher authentication.

## Allowed Paths

`.github/workflows/**`, `.gitattributes`, `.gitignore`, `scripts/changelog.py`,
`scripts/publish-release.py`, `scripts/check-all.sh`, `scripts/build-release.py`,
`tests/release/**`, `tests/packaging/**`, `docs/RELEASING.md`, `README.md`, `CHANGELOG.md`,
`PLAN.md`, this package's records.
