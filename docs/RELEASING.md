# Building and Verifying a Release

This is the maintainer reference for producing and publishing the release ZIP. It covers
what is built and checked, and how the CI and release workflows use it. Creating the tag
that starts a release is always a manual, owner-authorized act.

## One version authority

`apm.yml` declares the version. `plugin.json`, `.github/plugin/plugin.json`,
`.claude-plugin/plugin.json`, and the version listed in `.claude-plugin/marketplace.json`
must agree with it, and the manifest `name` must match. `python scripts/build-release.py
--check` verifies this. Versions must be strict semantic versions (`1.2.3`,
`2.0.0-rc.1`); a leading `v` belongs only to the Git tag.

Release tags use `v<semver>` (`apm.yml` sets `marketplace.build.tagPattern` to
`v{version}`). Older tags such as `0.5.4` and `spec-development-protocol-v0.4.0` remain as
history and are not used going forward.

## Building the ZIP

```bash
python scripts/build-release.py --output dist
```

The builder requires the exact APM version pinned in `scripts/release-tools.json`. It runs
`apm pack --archive --marketplace none`, then:

- drops bytecode caches (`__pycache__`, `*.pyc`), which `apm pack` would otherwise ship from
  a developer machine;
- converts text files to LF, so the bytes do not depend on the checkout's line endings;
- adds `LICENSE` and `SETUP.md` (from `scripts/release-assets/`);
- sorts entries and fixes timestamps and permissions, so the same commit and tool version
  produce the same bytes;
- verifies the result and only then writes `<name>-<version>.zip`, `SHA256SUMS`, and
  `release-metadata.json` into the output folder, refusing a folder that already holds a
  different archive.

## What the verification checks

Every file under `.apm/agents`, `.apm/instructions`, `.apm/skills`, and every prompt (as
`commands/`) is present and byte-identical (after LF normalization); nothing else is in
the archive except `plugin.json`, `LICENSE`, and `SETUP.md`; hidden files are kept;
bytecode caches, `.git`, and other excluded artifacts are absent; no entry is absolute, uses
`..` or `.` segments, backslashes, drive letters, alternate-data-stream or otherwise hostile
names, is a symbolic link, or collides by case; and `plugin.json` carries the release
version. Hostile entries from `apm pack` itself are refused before anything is flattened.

`tests/packaging/` exercises each rule, builds twice and compares bytes, builds from CRLF
and LF copies and compares, extracts a built ZIP into an empty location and runs the init,
migration, and validator scripts from it, and runs `apm pack --check-versions
--check-clean --dry-run` against the committed marketplace files. Set `SDP_REQUIRE_APM=1`
to fail, rather than skip, the tests that need APM.

## Automation

`scripts/check-all.sh` runs every repository check (shell syntax, template and generated-
content drift, baseline and skill checks, manifest versions, all test suites) and fails if
the checks changed the working tree. Run it in a Linux checkout: from WSL on a Windows
working tree, Git reports every CRLF file as modified and the tree check fails.
CI and the release build both call it, so they cannot drift apart.

**CI** (`.github/workflows/ci.yml`, pull requests and pushes to `main`): the shared check
script on Linux, the test suites on Windows, and the suites for the shipped scripts on
Python 3.9 with no third-party packages. Tools are pinned: actions by commit, `apm-cli` from
`scripts/release-tools.json`, `PyYAML` and `jsonschema` by version.

**Release** (`.github/workflows/release.yml`, a pushed `v*` tag): two jobs.

1. `build` (read-only token): refuses a tag whose commit is not on `main`; extracts the
   `CHANGELOG.md` section for exactly that version (`scripts/changelog.py`; never
   `Unreleased`, and a missing, duplicated, or empty section stops the release); runs every
   check; builds the ZIP for that tag and commit (`build-release.py --tag --revision`, which
   also refuses a dirty or different tree); uploads the assets as a run artifact.
2. `publish` (the only job with `contents: write`): `scripts/publish-release.py` verifies
   the artifact against the tag, creates or resumes a draft release for the built commit,
   uploads only missing or differing assets, re-downloads and compares every asset, confirms
   the tag still points at the built commit, then publishes. A tag with a prerelease suffix
   is published as a prerelease and never as the latest release. A published release is
   never modified.

A changelog section uses `## [1.2.3] - 2027-01-31` (the date and a leading `v` are optional).
Release notes end with a note that checksums show integrity, not who published.

### Failures and recovery

| Where | Meaning | What to do |
| --- | --- | --- |
| `build` job fails | A check, the changelog section, the version, or the tree is wrong. Nothing was published. | Fix on `main`, delete and recreate the tag on the corrected commit (the tag has no release yet), or use a new version. |
| `publish` exit 10 | The build output is not what the tag expects. | Rerun the workflow after fixing the cause; nothing was contacted. |
| `publish` exit 20 | Refused: a published release differs from the build, the tag moved, or a draft holds foreign assets. | Do not force it. Publish a new version; remove foreign assets from the draft by hand if it is a draft. |
| `publish` exit 30 | Upload or verification failed. The draft is kept. | Re-run failed jobs; the run resumes. |
| `publish` exit 31 | Assets are verified but the final publish step failed. | Re-run failed jobs; only the publish step repeats. |

After a release is published, a catalog update should reference the tag and the commit shown
in the run summary. Re-running all jobs of one run replaces that run's artifact.

### Cutting a release

These steps are manual: move the `Unreleased` notes into a `## [x.y.z] - date` section; set
the version in `apm.yml`, `plugin.json`, `.github/plugin/plugin.json`, and
`.claude-plugin/plugin.json` and regenerate the marketplace files with `apm pack`; run
`bash scripts/check-all.sh`; merge to `main`; then tag that commit `vx.y.z` and push the
tag. Protecting `v*` tags and requiring approval for a `release` environment are repository
settings that this repository does not configure.

## Catalog decision

The marketplace manifests (`.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`) are generated by `apm pack` and committed to the main
branch next to the code they describe, with `source` pointing at the repository itself. This
avoids a second repository to keep in sync, and `apm pack --check-clean` fails when a
committed file drifts from what the tool would generate. A protected generated-catalog
branch or a separate catalog repository remains an option if the project later needs to
publish catalog updates independently of the code; that is a publishing decision for the
owner.

## What is not verified

- The release workflow has never run, and the publisher's GitHub REST usage was tested only
  against a local fake server, so real API behavior (draft listing, redirects, `make_latest`,
  rate limits) is unconfirmed until a separately authorized prerelease rehearsal.
- CI ran once, on a fork, for commit `3ab0483`: the Linux job (every check, including the
  packaging tests with a pip-installed `apm-cli` 0.29.0) passed. The Python 3.9 job failed and
  exposed a real bug in the shipped `migrate.py` (`Path.write_text(newline=)` needs Python 3.10),
  now fixed and guarded by a static test. The Windows job failed for a reason that is not yet
  known (job logs need a sign-in); CI now turns each failing test into an annotation so the
  next run names it. Neither fix has been confirmed by a new GitHub run.
- GitHub reported that the pinned actions target Node 20 and are forced onto Node 24 (a
  warning only); newer action versions are not yet adopted.
- `apm-cli` is pinned by version, but its dependencies are not hash-pinned.
- A byte-identical build across operating systems was observed on Windows only; the release
  builds on Linux, so the published bytes may differ from a local Windows build.

- Installing from a hosted marketplace. GitHub Copilot CLI registers a local directory as a
  marketplace and then loads the plugin live from that directory without copying it, so a
  local install does not exercise a clean copy. The check needs a published repository and
  a tagged release.
- How each native channel pins a revision. Nothing here claims an exact behavior; verify it
  against a real tag before relying on it.
- The release ZIP in any agent host. Only the extracted layout's scripts were run; Copilot
  CLI was tested earlier against the directory bundle from `apm pack`.
- Python 3.9. The scripts parse as 3.9 but were run on 3.11 to 3.13.
