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

### Preparing a prerelease rehearsal locally

Local preparation does not authorize publication. `2.0.0-rc.1` is a proposed
rehearsal version, not the current package version or an approved release.

1. Agree the version and target repository with the owner before changing versions.
  A rehearsal on `wojcikmm-dnv/spec-development-protocol` exercises the fork's
  workflow, not publication or catalog configuration on the upstream repository.
2. Follow the version and marketplace synchronization steps above. Add a nonempty
  changelog section for exactly the proposed version; retain unfinished work under
  `Unreleased` and state the remaining host and distribution qualification limits.
3. Run the focused release tests, then `bash scripts/check-all.sh` in a clean Linux
  checkout of the prepared commit. Record the revision, tool versions, and results.
  Keep generated notes and assets outside tracked source; the builder and shared
  checks must continue refusing changes to the candidate.
4. Stop for separate owner authorization before committing or pushing preparation
  changes, creating or pushing the version tag, or publishing. A pushed `v*` tag
  automatically starts both the build and publish jobs; it is not a dry run.
5. After authorized publication, verify prerelease status, assets, checksums, and
  source revision. Test hosted installation in disposable project and host locations,
  record the revision each channel actually resolves, and run initialization twice.
  Installation checks do not qualify full delivery execution; paid AI host trials
  require a separately agreed spending limit.

The legacy install scripts were retired on the owner's explicit approval (2026-11-09)
while hosted-channel rehearsal and the 2.0 release are still pending; that gap is recorded
in the roadmap, and released 0.5.x tags keep the scripts. Superseded-agent and prompt
removal remains gated by compatibility mappings, coverage checks, and
explicit removal approval. No rehearsal checklist waives those gates or human acceptance.

## Catalog decision

The marketplace manifests (`.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`) are generated by `apm pack` and committed to the main
branch next to the code they describe, with `source` pointing at the repository itself. This
avoids a second repository to keep in sync, and `apm pack --check-clean` fails when a
committed file drifts from what the tool would generate. A protected generated-catalog
branch or a separate catalog repository remains an option if the project later needs to
publish catalog updates independently of the code; that is a publishing decision for the
owner.

## Verified CI evidence

On 2026-11-06, [CI run 42222480747](https://github.com/wojcikmm-dnv/spec-development-protocol/actions/runs/42222480747)
passed on fork commit `bf43597f66e1f2a8a108a61c2e90cf5cb94b0a91`:

- Linux, Python 3.12: the shared checks, including packaging with pinned APM.
- Windows, Python 3.12: every test suite.
- Python 3.9: the shipped-script contract, initialization, and migration suites
  without third-party packages.

This confirms that the earlier Python-3.9 migration and Windows writer-lock failures
no longer fail those CI suites. It does not prove the cause of every earlier failure,
host qualification, hosted installation, or successful release publication.

## Verified archive reproducibility

On 2026-11-06, disposable Windows and WSL Linux checkouts of commit
`e7908dee783ea8a18275c826d6c413f6e25f6e29` built the same `0.5.4` release ZIP using
APM `0.29.0`. Both builds passed the builder's clean-revision and bundle checks and
produced SHA-256 `88757e6cfbc291fb6179e8764939ec4878f505721ffe804fc435181b305eb215`.
The Linux packager was installed in an isolated temporary virtual environment;
neither build changed the author checkout or published a release.

This is an observed cross-OS comparison for one commit and tool version, not a
guarantee for later candidates or other environments. The actual GitHub release
runner's archive still needs comparison during the authorized rehearsal.

## What is not verified

- The release workflow has never run, and the publisher's GitHub REST usage was tested only
  against a local fake server, so real API behavior (draft listing, redirects, `make_latest`,
  rate limits) is unconfirmed until a separately authorized prerelease rehearsal.
- GitHub reported that the pinned actions target Node 20 and are forced onto Node 24 (a
  warning only); newer action versions are not yet adopted.
- `apm-cli` is pinned by version, but its dependencies are not hash-pinned.
- The actual GitHub release runner's archive bytes. The local Windows/WSL comparison
  above does not establish what a future release job produces.

- Installing from a hosted marketplace. GitHub Copilot CLI registers a local directory as a
  marketplace and then loads the plugin live from that directory without copying it, so a
  local install does not exercise a clean copy. The check needs a published repository and
  a tagged release.
- How each native channel pins a revision. Nothing here claims an exact behavior; verify it
  against a real tag before relying on it.
- The release ZIP in any agent host. Only the extracted layout's scripts were run; Copilot
  CLI was tested earlier against the directory bundle from `apm pack`.
- Python 3.9 host execution. The shipped-script suites passed on that runtime in CI,
  but no full agent delivery has been observed on it.
