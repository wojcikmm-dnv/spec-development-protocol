# Delivery Plan - 0.6.0 Release Preparation

- **Status:** approved
- **Approved by:** user (chat: "Prepare the release of new version - but that should not be version 2.0.0-rc.1 but 0.6.0. Please keep check the CHANGELOG.md and all stuff if we cover all latest changes.", 2026-11-10)
- **Size:** S
- **Risk:** Low
- **Uncertainty:** Resolved
- **Supersedes the 2.0.0-rc.1 line as the release version; on the same release path verified by `sdp-2-release-DP-5`.**

## Outcome

The release version of the library is `0.6.0`: the stable release of the content rehearsed
by the published `2.0.0-rc.1` prerelease, continuing the 0.x numbering the released tags
use. All manifests agree on `0.6.0`, the changelog carries an extractable `0.6.0` section
that also covers everything landed since the prerelease, and the user-facing docs state the
observed release state without overclaiming.

## Change boundary

Allowed:

- `apm.yml` (manifest version and the active `packages:` range), `plugin.json`,
  `.github/plugin/plugin.json`, `.claude-plugin/plugin.json`, and the regenerated
  `.claude-plugin/marketplace.json` / `.agents/plugins/marketplace.json`.
- `CHANGELOG.md` (new `0.6.0` section, `Unreleased` refresh; the published `2.0.0-rc.1`
  section is frozen and is not edited).
- Version phrasing in `README.md`, `docs/INSTALLATION.md`, `docs/RELEASING.md`, and
  `PLAN.md` (forward-looking references only; rehearsal evidence stays historical).
- `tests/release/test_changelog.py` (bind the extractable-history check to `v0.6.0`).
- This package's folder `spec/sdp-2-release/deliveries/sdp-2-release-DP-6/`.

Not in this package:

- Creating or pushing the `v0.6.0` tag or publishing (STOP gate in `docs/RELEASING.md` —
  a pushed `v*` tag starts both release jobs and is not a dry run).
- Host qualification (Step 14), Copilot CLI marketplace and Claude-hosted channel installs,
  Step 15 extensions.
- Any `.apm/` template, agent, prompt, or skill content change.

## Acceptance criteria

1. `apm.yml`, all three `plugin.json` files, and `apm pack`'s regenerated marketplace
   output agree on `0.6.0` / `^0.6.0`, and `scripts/build-release.py --check` passes.
2. `CHANGELOG.md` has exactly one nonempty `0.6.0` section that the extractor resolves for
   tag `v0.6.0`, and the section covers the changes landed since `2.0.0-rc.1` (rehearsal
   evidence, guard tests, this release).
3. User-facing docs name `0.6.0` as the release version and keep honest limits (no claims
   that host qualification happened).
4. The full check battery passes (six suites, check-baseline, check-skills,
   sync-templates), and `Windows git diff --check` is clean.

## Verification

- `bash scripts/check-all.sh` (CI entry point) in a clean checkout after the push.
- Locally: `python3 scripts/run-suites.py` per suite, `scripts/check-baseline.py`,
  `scripts/check-skills.py`, `bash scripts/sync-templates.sh --check`.
- `scripts/changelog.py --tag v0.6.0`; `scripts/build-release.py --check`;
  `apm pack --check-versions --check-clean --dry-run`.
