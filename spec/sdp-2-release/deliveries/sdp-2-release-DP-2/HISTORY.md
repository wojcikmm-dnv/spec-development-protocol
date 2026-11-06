# Local Rehearsal Preparation History

## 2026-11-06 - Awaiting Acceptance

Updated the release guide's stale CI claims, separated verified CI from pending
release and host qualification, and added a local prerelease-preparation checklist.
Added two focused regression tests in the existing documentation test module.

### Evidence

- Read-only `gh run view 42222480747` returned success for commit
  `bf43597f66e1f2a8a108a61c2e90cf5cb94b0a91`. All three jobs succeeded:
  Linux Python 3.12 shared checks; Windows Python 3.12 all suites; Python 3.9
  shipped-script suites. The guide links to that run.
- `python -m unittest discover -s tests/release -p test_docs.py`: 21 tests passed.
- `bash -n install.sh` and `git diff --check` completed successfully.
- Editor diagnostics reported no errors in the changed guide or test module.
- Independent read-only technical review returned pass with no material findings.
  The reviewer cross-checked job scopes and authorization boundaries against CI
  and release configuration and inspected the two regression tests. The reviewer
  did not independently execute a release, host trial, or CI run.

### Scope and Limits

No `.apm/` files changed. README was not updated because installation behavior,
commands, and setup expectations did not change. Neither installer changed;
the retained shell installer passed its mandatory syntax check.

No versions, tags, releases, repository settings, commits, pushes, or paid trials
were created. Release publication, hosted catalog revision selection, and full
host delivery remain unverified. The prior suspicion that generated `notes.md`
would fail the clean-tree check was disproved by the existing `/notes.md` ignore
rule; no workflow change was made for that hypothesis.

This documentation package does not close the external rehearsal or host
qualification obligations. Acceptance is pending an explicit human decision.