# Step 07 Delivery History

## 2026-11-05 - Accepted

Delivered `sdp-init` (`scripts/init.py`, SKILL.md) and 32 tests in `tests/init`.

### Evidence

- WSL (Python 3.12): 32 tests pass, 1 skipped (Windows-only junction test). Windows
  (Python 3.11): 32 pass, 5 skipped (symlink and POSIX-permission cases). Together every
  case ran on at least one platform.
- Real layouts: the packed plugin bundle and an `apm install --target copilot`
  project both ran the initializer from their installed location, found the packaged
  template, previewed, applied, and made a no-op second run in scratch repositories.
  This repository was unchanged.
- Mutation checks caught: symlink or path-escape removal (as a pair, since two layers
  guard the same thing), treating a present file as missing, rollback removal, ignoring
  conflicts, removing the package-template preference, legacy detection removal,
  allowing an overwrite race, the pre-write recheck, and silent rollback failures.

### Defects found and fixed during the work

- My own junction test found that on Windows a junction is not reported as a symlink,
  so the initializer would have written through it to an outside folder. Fixed with
  junction detection plus a check that the nearest existing ancestor resolves inside
  the repository, verified on native Windows.
- Rollback did not remove parent directories it created, and hard links are not
  available on every file system. Fixed, with an exclusive-create fallback.
- The first legacy detection warned on APM installs, because APM deploys the same
  files the old installer copied. Detection now treats `.github/sdp-version` as the
  definite installer marker and gives only a softer note for unmarked copies without
  an APM lockfile.

### Independent security review

Triage of eight findings:

- Fixed: no re-validation between preview and write (each action is re-inspected
  immediately before writing and refused with `changed_since_preview`); template
  fallback to repository-controlled folders (removed entirely, since `TECH.md` is
  later read as agent instructions); silent rollback failures (now reported).
- Rejected: a dangling-symlink-at-destination claim; the destination is checked with
  link detection already, and a test now proves it. A redundant second symlink check
  was removed because mutation testing showed it added nothing.
- Accepted and documented: a tiny race window remains for a person with write access to
  the repository; relative `--repo` paths are reported as resolved real paths.

### Limits

The initializer is not a sandbox. It creates two items and does not install packages.
Native plugin marketplace installs are not yet testable (Step 10 builds the catalogs),
and Claude Code was not available. The user-facing entry is the `sdp-init` skill; hosts
that expose skills as slash commands show it as `/sdp-init`, which was not separately
verified.

The user's continue instruction is recorded as approval and acceptance.
