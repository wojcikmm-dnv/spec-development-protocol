---
status: approved
approved_by: user (chat: go; Start implementation)
approved_at: 2026-11-06
---

# Local Release Rehearsal Preparation

## Outcome and Boundary

Correct stale release-guide CI claims and document local prerelease preparation
without authorizing publication. The user approved the presented local-only plan
with "go" and "Start implementation". The approval date is known; no precise
chat-message time is asserted.

- Size: S; risk: Low; uncertainty: Resolved; profile: Lean.
- Allowed paths: `docs/RELEASING.md`, `tests/release/test_docs.py`, and this package.
- No version changes, commits, pushes, tags, publication, repository settings,
  installer/component removal, or paid AI host trials.
- No claim of full host or replacement-channel qualification.

## Acceptance Criteria

1. The guide cites confirmed fork CI evidence and its three runtime/job scopes.
2. Confirmed CI results are distinguished from release publication, hosted
   installation, and full agent execution, which remain unverified.
3. Local rehearsal preparation explains that pushing a version tag starts
   publication and requires separate authorization; paid trials and removals
   retain their own approval boundaries.
4. Focused documentation tests and independent review pass; shell syntax and
   whitespace checks pass. Human acceptance remains explicit.

## Steps and Verification

1. Verify CI run 42222480747 using read-only `gh run view`.
2. Update the existing release guide and adjacent documentation regression tests.
3. Run `python -m unittest discover -s tests/release -p test_docs.py`,
   `bash -n install.sh`, `git diff --check`, and editor diagnostics.
4. Obtain independent read-only technical review and record actual evidence.
5. Present the package for human acceptance; do not publish or commit it.

README and installer updates are unnecessary: installation commands, source
layout, user setup expectations, and copying behavior are unchanged.