# Step 11 Delivery History

## 2026-11-05 - Accepted (authored and locally tested; not run on GitHub)

Delivered CI and release workflows, `scripts/changelog.py`, `scripts/publish-release.py`,
`scripts/check-all.sh`, `--tag`/`--revision` for the builder, and `tests/release/` (92
tests). Windows Python 3.11: release 92 pass, packaging 47 pass.

### Defects found by independent review (each reproduced) and fixed

- Medium: the builder did not check that the tree it packed was the tagged commit, so a
  check that edited a file could ship bytes not in the tag while the metadata claimed the
  commit. It now refuses a different HEAD or any changed or untracked file, and
  `check-all.sh` fails if the checks change the tree. `git diff --check` in that script was a
  no-op on a clean checkout and was removed.
- Medium: the publisher never confirmed the tag still pointed at the built commit and sent no
  `target_commitish`. It now creates the draft for the commit and refuses before creating
  and again before publishing if the tag is missing or points elsewhere (annotated tags are
  peeled).
- Low-Medium: a resumed draft was trusted wholesale (foreign body, extra assets). It now
  resets the notes and refuses foreign assets. Two releases for one tag stop the run.
- Low: download and socket errors escaped as tracebacks; an unreadable asset in a draft
  wedged every rerun. Errors map to the documented exit codes; an unreadable draft asset is
  replaced.
- Low: changelog parser: indented headings (1-3 spaces) were swallowed, an unterminated
  fence or comment ran to the end of the file, a backtick in a fence info string was treated
  as a fence, a top-level `#` heading did not end a section, `splitlines` split on Unicode
  separators and created hidden headings, and non-ASCII digits matched `\d`. All fixed
  and covered by tests; unterminated fences and comments are now errors.
- My own test found a real bug before review: `$` in the version pattern accepted a trailing
  newline (`v1.2.3\n`); the pattern now uses `\Z`, and a test keeps the changelog and
  builder patterns identical.
- Nit: stable releases use `make_latest: legacy` so an old backport does not become latest.
- CI concurrency no longer cancels runs on `main`; re-running all release jobs can replace
  the same run's artifact.

### Evidence

Mutation checks: in the first pass all but three mutations were caught (an unverified final
draft state, and two builder checks that only slow tests cover); each got a targeted test and
is now caught. After the review fixes, 26 of 27 new mutations were caught at once; the
survivor (a fence closed by the wrong marker kind) got its own test and is now caught. The reviewer confirmed there is no workflow injection, token leak, or path
by which the publish job uploads different bytes than the build job made, and that a pip-
installed `apm-cli` 0.29.0 and the standalone binary gave the same archive on Windows.

### Limits

No workflow ran on GitHub. The publisher's REST calls were tested against a local fake
server and the reviewer's knowledge of the API, not the real service. Cross-OS byte identity
(Windows versus the Linux release runner), the Node runtime of pinned actions, and hash-
pinning of `apm-cli`'s dependencies are unverified. Obligation `step-11-github-rehearsal`
stays open: a separately authorized prerelease rehearsal and a native catalog install.

The user's instruction "11" is recorded as approval and acceptance of the authored files.

## 2026-11-06 - CI verified on the owner's fork

The validation CI ran on github.com/wojcikmm-dnv/spec-development-protocol:
run 42212949027 on commit f8ba5ee passed all three matrices. The earlier failing
run (42061860730 on 3ab0483) was the `migrate.py` Python-3.9 newline bug and a
writer-lock failure under the runner's short temp path; fixes `c4ad2a7`,
`7ec1e65`, and `f8ba5ee` are now verified on GitHub. Public check-run failure
annotations from `scripts/run-suites.py` work. Still open: the release workflow
(changelog extraction, build, publish REST) and the prerelease rehearsal, tracked
as `step-11-github-rehearsal`.
