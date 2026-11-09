# Changelog CI Status History

## 2026-11-06 - Awaiting Acceptance

Replaced the Added-section CI sentence's stale first-run description with the verified
result: CI passed on all three fork jobs (Linux `check-all.sh`, Windows suites, Python 3.9
shipped scripts) as of 2026-11-06, and the release workflow has never run.

### Evidence

- The verified run and commit are recorded in
  `spec/sdp-2-release/deliveries/sdp-2-release-DP-2/HISTORY.md` (run 42222480747,
  commit `bf43597f66e1f2a8a108a61c2e90cf5cb94b0a91`) and linked in `docs/RELEASING.md`.
- `python scripts/run-suites.py release`: 114 tests passed; the changelog module alone:
  32 tests passed.
- `bash -n install.sh` and `git diff --check` succeeded.
- Independent read-only technical review: pass. The reviewer confirmed the corrected
  sentence matches the recorded evidence, retains the never-run fact, and claims no
  release-workflow or host activity.

### Scope and Limits

Only `CHANGELOG.md` changed in this package. README and the installers were not updated
because no behavior, command, or structure changed.

The changelog cites a verified run and commit; later pushes on the fork were not
verified and are not claimed. Release publication and host rehearsal remain unverified.

## 2026-11-09 - Accepted

The owner accepted this package in chat, explicitly excepting the standard wait:
"go, not wait for my acceptance - I want to have results NOW. Exception to the
standard flow". CI has since passed on all three matrices for later commits, most
recently run 42639411557 on `7ea3dbfdc09f3ac793659e93c8f7155f01d0eb97` (2026-11-09),
which re-verified this package's content. Acceptance is recorded in
`DELIVERY-RUN.json`; parenthetical evidence in `PLAN.md` Step 11 was also updated
with the newer run.
