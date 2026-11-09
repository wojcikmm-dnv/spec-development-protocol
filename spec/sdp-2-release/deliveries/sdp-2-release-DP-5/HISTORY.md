# Delivery History - GitHub Prerelease Rehearsal (Step 11)

## 2026-11-09 - Delivered and accepted

Owner authorization: "go ahead" (2026-11-09 chat), authorizing the version, the target
repository, and the tag push the roadmap listed as needing separate owner
authorization, under the standing exception that records acceptance immediately after
delivery.

Prepared:

- Version `2.0.0-rc.1` set in `apm.yml`, `plugin.json`, `.github/plugin/plugin.json`,
  and `.claude-plugin/plugin.json` per the `docs/RELEASING.md` version-authority steps;
  marketplace files were regenerated with the rehearsal venv's `apm`; until the
  `packages:` entry in `apm.yml` moved, `apm pack` left `^0.5.4` in place (see the
  Executed section for the mechanism).
- `CHANGELOG.md` gained the `2.0.0-rc.1` section; the unreleased notes keep only the
  remaining host and distribution qualification limits; the moved release-notes
  statements that said "the release workflow has never run" and "Nothing is published
  by this change" were reworded so they stay true inside the published section.

Executed:

- Full battery: all six suites green (contracts, skills, init with 1 environment skip,
  migrate, packaging with 14 APM-skips locally, release), `check-baseline.py`,
  `check-skills.py`, and `sync-templates.sh --check` passed at the prepared commit.
- `scripts/changelog.py --tag v2.0.0-rc.1` extracted the rc.1 section;
  `build-release.py --check` passed after the marketplace range moved to `^2.0.0-rc.1`
  (`apm pack` derives the marketplace version from the `packages:` entry in `apm.yml`,
  not from the manifest version, so that entry had to move too); `apm pack
  --check-versions --check-clean --dry-run` passed.
- `bash scripts/check-all.sh` passed in a clean WSL checkout of `d5f28ba` (the builder's
  dirty-tree refusal makes /mnt/c unusable for the build; the CRLF worktree is a known
  artifact of Windows git there).
- A local build of `v2.0.0-rc.1` on that checkout produced ZIP SHA-256
  `5f9f52042c8c7179da58b0807aad95c74779e3173f99c6f41a42659b2e4a0a9e`.
- Committed `b1cc383` (versions, changelog, package records) and `d5f28ba` (marketplace
  range); both pushed together with tag `v2.0.0-rc.1` in one `git push` so CI's checkout
  sees the tag.
- [Release run 42648216366](https://github.com/wojcikmm-dnv/spec-development-protocol/actions/runs/42648216366)
  succeeded on its first run: build and publish jobs green; release 439327949 published
  with `prerelease: true`, `draft: false`, not latest, target `d5f28ba`, authored by
  `github-actions[bot]`; assets = ZIP (digest matching the local build byte for byte),
  `SHA256SUMS`, `release-metadata.json`; notes = the extracted changelog section plus the
  publisher's checksum disclaimer.
- The published ZIP downloaded and verified against `SHA256SUMS` (`sha256sum -c`: OK).
- Hosted APM channel in a disposable location: `apm install --target claude
  wojcikmm-dnv/spec-development-protocol#v2.0.0-rc.1` installed `2.0.0-rc.1`; the lockfile
  records `repo_url: wojcikmm-dnv/spec-development-protocol`, `resolved_ref:
  v2.0.0-rc.1`, `resolved_commit: d5f28ba44...`; files deployed to `.claude/`.
  `sdp-init` from the installed location previewed (`ok: true`), applied (creating
  `.github/TECH.md` and `spec/`), and applied again with `ok: true` and one `TECH.md`.
  Two APM quirks recorded in RELEASING.md and COMPATIBILITY-adjacent docs: an untargeted
  install in a bare directory stops with host-detection guidance, and APM drops the
  `agent:` frontmatter key from Claude command files with a warning.
- `docs/RELEASING.md` gained the Verified release rehearsal section and an updated
  not-verified list; `docs/INSTALLATION.md` and `README.md` state the observed evidence;
  `tests/release/test_docs.py` moved its assertions from "the release workflow has never
  run" to the recorded evidence; `CHANGELOG.md` and `PLAN.md` updated (Step 10 partial
  closure, Step 11 accepted).

## Independent review

An independent read-only review subagent inspected the delivery after publication,
verifying the recorded IDs, flags, and digests directly against the GitHub API release
and run objects. Findings and dispositions:

- Must-fix: `README.md` still claimed "hosted install not re-run for the current
  candidate", "None published for 2.0 yet", and "will ship in the first 2.0 release,
  which has not been published" — the sync-rule miss behind the delivery's allowed-changes
  list. Fixed by mirroring the `docs/INSTALLATION.md` corrections.
- Must-fix: this record pre-registered a reviewer `pass` with an empty findings section.
  Fixed by recording the actual findings here and reconciling the verdict in
  `DELIVERY-RUN.json` after the fixes.
- Should-fix, all fixed: `docs/INSTALLATION.md` requirements row still said "a GitHub run
  of the 3.9 job has not yet confirmed it" (the 3.9 job passed in run 42222480747);
  `PLAN.md` Step 12 said the 2.0 changelog entry stays open "until a release exists" and
  Step 10 referenced Step 11 as pending; a conflicted marketplace-version mechanism
  statement in this file; the `stages` record shape diverged from the DP-2..DP-4
  `stage_results` family under the same `schema_version: 3`; the developer evidence line
  over-stated the first `sdp-init` apply as `ok: true`.
- Accepted as-is: the `[2.0.0-rc.1]` changelog section is frozen — the published GitHub
  release body contains its text verbatim, so editing it now would desync the repo from
  the published notes; the Unreleased bullet supersedes the scoping.
- Guard added: `tests/release/test_changelog.py` now binds the extractable-history
  guard to `v2.0.0-rc.1`.

Review verdict: the recorded evidence is factually accurate end to end; after the fixes
above the delivery is consistent and the candidate is acceptable.
