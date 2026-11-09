# Delivery History - GitHub Prerelease Rehearsal (Step 11)

## 2026-11-09 - Delivered (in progress)

Owner authorization: "go ahead" (2026-11-09 chat), authorizing the version, the target
repository, and the tag push the roadmap listed as needing separate owner
authorization, under the standing exception that records acceptance immediately after
delivery.

Prepared:

- Version `2.0.0-rc.1` set in `apm.yml`, `plugin.json`, `.github/plugin/plugin.json`,
  and `.claude-plugin/plugin.json` per the `docs/RELEASING.md` version-authority steps;
  marketplace files were regenerated with the rehearsal venv's `apm` after the tag
  existed locally, because `apm pack` derives the marketplace version from the latest
  `v*` tag (it left `^0.5.4` in place until the tag existed).
- `CHANGELOG.md` gained the `2.0.0-rc.1` section; the unreleased notes keep only the
  remaining host and distribution qualification limits; the moved release-notes
  statements that said "the release workflow has never run" and "Nothing is published
  by this change" were reworded so they stay true inside the published section.

Pending: local test battery, clean-Linux `check-all.sh`, push of `main` with the tag,
workflow verification, release-asset verification, hosted install with a double
initialization, documentation and test updates for the recorded evidence, independent
review, and the acceptance record.
