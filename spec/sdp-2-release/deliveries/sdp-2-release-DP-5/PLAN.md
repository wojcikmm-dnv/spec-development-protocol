---
status: approved
approved_by: user (chat: "go ahead" — authorizes the prerelease-tag push the roadmap listed as
  needing separate owner authorization, under the standing 2026-11-09 exception that records
  acceptance immediately after delivery)
approved_at: 2026-11-09
---

# GitHub Prerelease Rehearsal (Step 11)

## Outcome and Boundary

Execute the separately authorized 2.0.0-rc.1 prerelease rehearsal on the owner's fork
(`wojcikmm-dnv/spec-development-protocol`): prepare the version, run every local check,
push, push the `v2.0.0-rc.1` tag so the release workflow runs against GitHub for the
first time, and verify the published prerelease, its assets, its checksums against a
local build, and a hosted install with initialization run twice. This is the
`step-11-github-rehearsal` obligation and the hosted-catalog part of Step 10
(`step-10-hosted-catalog-rehearsal`).

`2.0.0-rc.1` was the rehearsal version documented in `docs/RELEASING.md` before this
package existed. The owner authorized the version, the target repository, and the tag
push in the same chat that started this package. Publication still goes through the
workflow's own gates: the build job refuses a tag off `main`, a missing changelog
section, or a dirty tree, and the publish job never marks a prerelease as latest.

- Size: M; risk: High (publication automation runs for the first time); uncertainty:
  Resolved for the local steps, Open for real GitHub API behavior until each run verifies
  it; profile: Lean with independent review and QA on the published result.
- Allowed changes: `apm.yml`, `plugin.json`, `.github/plugin/plugin.json`,
  `.claude-plugin/plugin.json`, the two generated marketplace files, `CHANGELOG.md`,
  `PLAN.md`, `docs/RELEASING.md`, `docs/INSTALLATION.md` channel-verification wording,
  `docs/COMPATIBILITY.md` if a host is observed, `tests/release/test_docs.py`, the
  release ZIP and generated notes kept outside tracked source, and this package.
- Excluded: the stable version bump (follows host qualification and human acceptance,
  Step 14), paid AI host trials (need a separately agreed spending limit), Claude Code
  qualification (host unavailable), tag protection and release-environment settings,
  any change to workflow YAML or release scripts, the template mirror, and the
  historical build archives.

## Acceptance Criteria

1. The tag `v2.0.0-rc.1` points at a `main` commit where every manifest agrees on
   `2.0.0-rc.1`, the marketplace files match `apm pack`'s regeneration at that tag, the
   changelog has exactly one nonempty section for `2.0.0-rc.1`, and the full check
   battery passes in a clean Linux checkout.
2. The release workflow's build and publish jobs both succeed on GitHub; the release is
   published, flagged as a prerelease, not marked latest, and carries the ZIP,
   `SHA256SUMS`, and release metadata for that tag.
3. The published ZIP's SHA-256 matches `SHA256SUMS` and a local build of the same commit
   with the pinned tool version. The hosted APM channel resolves the prerelease and
   initializes a disposable project with no changes on the second run.
4. Documentation and test expectations move from "the release workflow has never run" to
   the recorded evidence; the verdict is independently reviewed, and acceptance is a
   human decision recorded in this package.

## Verification

Local: `scripts/run-suites.py` on all six suites, `scripts/changelog.py --tag
v2.0.0-rc.1`, `scripts/build-release.py --check`, `apm pack --check-versions
--check-clean --dry-run`, `bash scripts/check-all.sh` in a clean Linux checkout of the
prepared commit (the rehearsal venv for APM). Remote: the workflow run summary, the
GitHub release fields via the REST API, `SHA256SUMS` against the downloaded ZIP and
against a local build of the same commit. Hosted channel: `apm install
wojcikmm-dnv/spec-development-protocol#v2.0.0-rc.1` into a disposable location,
record what the channel resolves, and run `sdp-init` preview, apply, and apply again.
An independent read-only review of the whole diff follows delivery.
