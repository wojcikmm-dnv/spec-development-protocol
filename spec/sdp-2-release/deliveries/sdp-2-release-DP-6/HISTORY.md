# Delivery History - 0.6.0 Release Preparation

## 2026-11-10 - Delivered and accepted

Owner authorization: "Prepare the release of new version - but that should not be version
2.0.0-rc.1 but 0.6.0. Please keep check the CHANGELOG.md and all stuff if we cover all
latest changes." (2026-11-10 chat), under the standing exception that records acceptance
immediately after delivery. Preparation only: the `v0.6.0` tag and publication stay gated
on separate authorization per `docs/RELEASING.md`.

Prepared:

- Version `0.6.0` set in `apm.yml` (manifest and the active `packages:` range `^0.6.0`,
  which is what `apm pack` derives the marketplace version from), and in the root,
  `.github/plugin/`, and `.claude-plugin/` `plugin.json` manifests.
- `CHANGELOG.md` gained the `0.6.0` section (the stable release of the rehearsed
  `2.0.0-rc.1` content, the rehearsal evidence, the guard tests, and the version bump) and
  the `Unreleased` notes keep the host and distribution qualification limits plus the
  prepared-release pointer. The published `2.0.0-rc.1` section is frozen — the GitHub
  release body contains it verbatim.
- `docs/RELEASING.md`, `docs/INSTALLATION.md`, `README.md`, and `PLAN.md` name `0.6.0` as
  the release version in their forward-looking phrasing (Step 14 status records the
  owner's instruction and the still-open tag gate); rehearsal evidence stays historical.
- `tests/release/test_changelog.py` binds the real-changelog extractable-history check to
  `v0.6.0` as well.

Coverage check requested by the owner: everything landed since the published `0.5.4` is in
the changelog — schema 4 records/`sdp-migrate`, `sdp-init` and the installer removal, the
tightened skills, the docs redistribution, the CI and tag-release workflows, and the
`2.0.0-rc.1` rehearsal (its own frozen section) — and the only lands after the `2.0.0-rc.1`
tag (the recorded rehearsal-evidence docs, test guards, and delivery records) are covered
by the new `0.6.0` section. Nothing found uncovered.

Checks: all six suites, `check-baseline.py`, `check-skills.py`, and
`sync-templates.sh --check` green; `scripts/changelog.py --tag v0.6.0` extracts the
section; `scripts/build-release.py --check` and `apm pack --check-versions --check-clean
--dry-run` green after the commit; Windows `git diff --check` clean.

Pending: the owner-authorized `v0.6.0` tag and publication (STOP gate), then the
post-release verification per `docs/RELEASING.md`. Host qualification (Step 14), the
Copilot CLI marketplace and Claude-hosted channel installs, and Step 15 stay open.

## 2026-11-10 - Bounded correction (owners' natural-language feedback)

The owner described the problem: with both sections present, the changelog listed
`[2.0.0-rc.1]` (a higher semver) after `[0.6.0]`, breaking version order, and asked that
all rc.1 mentions be removed and the rc.1 content wrapped into the `0.6.0` release.
Repaired and rechecked:

- The separate `[2.0.0-rc.1]` section is gone. Its full content (Removed, Documentation,
  Changed, Fixed, Added, Maintenance) now lives inside `[0.6.0] - 2026-11-10` as the
  stable release of the rehearsed content; the two `Fixed` lists were merged into one
  block; the version ordering is `[Unreleased]`, `[0.6.0]`, `[v0.5.4]`, ... descending.
- "This prerelease ..." claims inside the section were repointed at the historical
  rehearsal ("the release workflow had its first exercise on GitHub during the prerelease
  rehearsal"); the preamble states the prerelease of 2026-11-09 rehearsed the tagged
  release path (release run 42648216366).
- The Unreleased distribution bullet no longer names the rc.1 version.
- `tests/release/test_changelog.py` drop-guard updated: the real-changelog
  extractable-history check now covers `v0.6.0`, `v0.5.4`, `v0.5.3`, `v0.1.0` (the rc.1
  section no longer exists to extract, and its guard entry is removed).
- Historical evidence outside the changelog is unchanged on purpose: `docs/RELEASING.md`
  rehearsal evidence, the delivery records, and `PLAN.md` history state what actually
  happened (tag `v2.0.0-rc.1`, release run 42648216366), and `tests/release/test_docs.py`
  pins that evidence. The published GitHub release body for the prerelease is immutable on
  GitHub and was not edited here.

Battery re-run green after the repair.
