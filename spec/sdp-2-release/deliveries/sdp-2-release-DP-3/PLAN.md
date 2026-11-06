---
status: approved
approved_by: user (chat: ok continue with next missing stuff)
approved_at: 2026-11-06
---

# Local Cross-OS Archive Verification

## Outcome and Boundary

Exercise the existing release builder on Windows and WSL Linux using the same
committed candidate and pinned APM. Record observed reproducibility without
claiming release-runner or host qualification.

The user's continuation authorizes local verification within the existing release
design. No public contract, package version, or distribution behavior changes.
This follows local preparation committed at `e7908dee`; it does not change the
prior package's acceptance metadata.

- Size: S; risk: Low; uncertainty: Resolved; profile: Lean.
- Allowed changes: `docs/RELEASING.md`, `tests/release/test_docs.py`, this package.
- Execution: disposable Windows/Linux checkouts and a temporary Linux environment
  containing the already-pinned APM `0.29.0`.
- Excluded: system package installation, repository dependency changes, versions,
  commits, pushes, tags, publication, component removal, and paid AI host trials.

## Acceptance Criteria

1. Both checkouts build the same full commit using the pinned packager and the
   existing builder's clean-revision checks.
2. Archive digests match and the source revision and tool version are retained.
3. Documentation distinguishes one observed local comparison from future
   candidates, actual GitHub release-runner output, and host qualification.
4. Focused documentation tests, independent review, shell syntax, and whitespace
   checks pass. Acceptance remains a human decision.

## Verification

Run the existing `scripts/build-release.py` with the exact `--revision` on both
platforms, independently hash each ZIP, and compare the digests. Run
`python -m unittest discover -s tests/release -p test_docs.py`,
`bash -n install.sh`, `git diff --check`, and editor diagnostics.

README and installers remain unchanged because no installation commands, layout,
copying behavior, or setup requirements changed. No `.apm/` source changes are needed.