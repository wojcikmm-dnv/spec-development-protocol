# Retire the Legacy Installers History

## 2026-11-09 - Awaiting Acceptance

Removed the legacy 0.5.x install channel on the owner's explicit chat approval
("go ahead, also fix other not finished changes regards plan", given after being told
the removal was gated). Cleaned every active reference, documented the historical
tag availability honestly, and updated the maintainer instructions.

### Changes

- Deleted `install.sh` and `install.ps1` (`git rm`).
- `docs/INSTALLATION.md`: removed the channel row, the curl/iwr examples, the
  "Install script options" section, and the shell-requirement row; updated the
  pinning, setup, update, and mixed-install wording.
- `docs/UPGRADING.md`: the manual 0.5.2 upgrade path no longer uses the installer;
  noted the retirement and pointed at `sdp-init`/`sdp-migrate`.
- `docs/RELEASING.md`: replaced the removal-gating paragraph with the recorded
  gate deviation (removal happened on explicit owner approval while the hosted
  rehearsal and release are pending).
- `scripts/check-all.sh`: dropped the `bash -n install.sh` line.
- `.github/copilot-instructions.md`: rewrote the repository model, change flow,
  mandatory sync rules, safety bullets, output expectations, and validation
  checklist for the retired installers.
- `README.md`: removed the GitHub release badge and the "installer output"
  contributing sentence.
- `CHANGELOG.md`: added the Unreleased Removed section, reworded the Planned and
  Documentation bullets, and fixed the `sdp-init` bullet that still said the
  installers were unchanged.
- `PLAN.md`: change-boundary row, CI evidence (run 42610731073 on `deee456`), the
  awaiting-acceptance package list, Step 11 status, and the Step 13 status with
  approved checkboxes.
- `tests/release/test_docs.py`: replaced the installer-variables test with a
  regression guard asserting README and the installation guide contain no
  `install.sh`/`install.ps1`/`SDP_BRANCH` substrings, and pruned the dead
  `SDP_BRANCH='` alternative from the pinned-tag scan.

### Deliberately Kept

- `.github/sdp-version` marker detection in `.apm/skills/sdp-init/scripts/init.py`
  and `.apm/skills/sdp-migrate/scripts/migrate.py` with their tests
  (`tests/init/test_init.py`, `tests/migrate/test_migrate.py`): legacy projects
  still carry the marker and its tests pass.
- `scripts/build-legacy-manifests.py`: records files the released tags' installers
  copied; it reads released tags, not local files.
- Historical `CHANGELOG.md` entries, historical packages under `spec/`,
  `REFACTOR_PORPOSAL.md`, `build/` archives, and the template mirror.

### Validation and Review

- Full battery (WSL, 2026-11-09): `check-baseline.py`, `check-skills.py`,
  `sync-templates.sh --check`, and all six suites pass: contracts 151, skills 43,
  init 32, migrate 46, packaging 47, release 114 (433 tests, 0 failures, 15
  environment skips). Windows `git diff --check` clean.
- The installers are absent from the working tree; deleted files are staged.
- Independent read-only review returned FAIL with 2 must-fix, 2 should-fix, and 3
  nit findings; every finding was fixed in the same pass and the full battery was
  re-run green afterward:
  1. (must-fix) `PLAN.md` cited `sdp-2-release-DP-4` before the record existed -
     this package was created.
  2. (must-fix) The CHANGELOG `sdp-init` bullet still said the installers were
     unchanged - reworded to point at Removed.
  3. (should-fix) The CHANGELOG Documentation bullet described a test that no
     longer exists - reworded for the new guard.
  4. (should-fix) `.github/copilot-instructions.md` still asked whether
     `install.sh` was updated - dropped.
  5. (nit) Dangling colon in `docs/UPGRADING.md` item 2 - removed.
  6. (nit) Active `bash -n install.sh` instruction in `PLAN.md`'s planning-doc
     verification - removed; Step 01's historical bullet stands as history.
  7. (nit) Dead regex alternatives in the pinned-tag scan - pruned.
- The review confirmed: no active surface presents the installers or installer
  environment variables as present tooling; no dangling anchors; `check-all.sh`
  references only existing scripts; every Step 13 checkbox matches reality.

### Limits and Gate Deviation

The removal happened on explicit owner authorization while the replacement-channel
gates are not fully met: no 2.0 release is published, the hosted-channel rehearsal
(`step-10-hosted-catalog-rehearsal`, `step-11-github-rehearsal`) is pending, and
Claude Code qualification (`step-06-claude-code-qualification`) is blocked. The
released 0.5.x tags keep the scripts. This gap is recorded in `PLAN.md` Step 13 and
`docs/RELEASING.md` rather than presented as passed gates.

The Windows-vs-WSL `git diff --check` CRLF artifact (`core.autocrlf=true`,
index-normalized LF) was observed and disregarded; the Windows git check is
authoritative for this checkout.

No commits, pushes, tags, releases, publications, or paid host trials were made
in the delivery itself. Superseded agents/prompts stay with later packages.

## 2026-11-09 - Accepted

The owner accepted this package in chat immediately after delivery, explicitly
excepting the standard wait: "go, not wait for my acceptance - I want to have
results NOW. Exception to the standard flow". CI passed on all three matrices on
this package's own commit (run 42639411557,
`7ea3dbfdc09f3ac793659e93c8f7155f01d0eb97`, 2026-11-09). Acceptance is recorded in
`DELIVERY-RUN.json`. The gate deviation stays recorded: the removal happened on
explicit approval while the hosted rehearsal and the 2.0 release are pending;
those obligations remain open.
