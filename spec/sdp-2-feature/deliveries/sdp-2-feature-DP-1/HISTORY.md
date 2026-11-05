# Step 08a Delivery History

## 2026-11-05 - Accepted

Delivered the `feature` workflow, `feature-next`, `approve-artifact`, gate enforcement at
plan approval, the lightweight path, frontmatter-covering plan fingerprints, and the
command mapping. 144 contract tests pass (WSL, Python 3.12).

### Defects found and fixed

- A real approval bypass, found by independent review and widened by reproducing it: a
  quoted space, `PENDING`, whitespace, `TBD`, `none`, or `n/a` were accepted as an
  approved identity or timestamp. All human-identity checks now use one `not_a_human`
  helper that rejects placeholders and agent-like names. This also hardens plan approval
  and acceptance, which share the check.
- A gate-file naming bug in my first implementation (it looked for `PRD`, not `PRD.md`)
  made every gate read as missing; found by the tests.
- Raw `KeyError` tracebacks when a package record is malformed, in `feature-next` and
  in prerequisite lookup. Records are now structure-checked and failures are clean
  errors. The independent review had called this correct; a test showed it was not.
- Symlinked epics were reported as missing instead of invalid; unknown story
  dependencies stalled silently; plan stories absent from the backlog were accepted; a
  junk lightweight basis such as `x` was accepted. All now give clear errors.
- The frozen-spec check ran outside the artifact lock; it now runs inside it.

### Evidence

Mutation checks caught: frontmatter left out of the fingerprint, gate check removal,
optional lightweight basis, agent artifact approval, the delivery freeze, ignored
artifact fingerprints, ignored story dependencies, ignored audit obligations, rejected
packages still holding stories, single-epic gating, placeholder handling, unknown plan
stories, symlink reporting, unknown dependencies, and junk bases.

### Limits

The `basis` is a stated reference; the approving human, not the validator, judges whether
it is real. Upstream gate artifacts are not hashed into an approved plan; the freeze rule
protects them during delivery, and a small race remains between starting a delivery and
approving an artifact at the same moment. Gate authoring is still done by the existing
agents through their entry points. 08b is deferred to Step 13 with the reason recorded in
PLAN.md. Approver identities are asserted strings, as documented.

The user's continue instruction is recorded as approval and acceptance.
