# Step 08b (instructions half) Delivery History

## 2026-11-06 - Accepted

Commit `b7cb90c` moved the schema-3 delivery process detail out of
`.apm/instructions/sdlc-process.instructions.md` (457 to 133 lines) into the new
on-demand `sdp-delivery-process` skill (`references/process-detail.md`, 400
lines, verbatim). The orchestrator and planner point at the skill; prompts stay
thin entry points; root `AGENTS.md` was regenerated. Follow-up edits after review
strengthened the instructions tests.

### Evidence

- `python scripts/run-suites.py skills`: 37 tests pass, including the new
  frontmatter test and per-section content assertions for all 16 moved sections.
- `python scripts/run-suites.py contracts`: 151 tests pass, including the new
  validator atomic-retry test; `check-baseline` (`--self-test`), `check-skills`,
  the sync-templates mirror check, and `build-release.py --check` all pass.
- Verbatim transfer: `git diff b7cb90c^ b7cb90c -- .apm/instructions/sdlc-process.instructions.md`
  shows 59 summary lines added and 383 lines moved; the deleted bulk is
  word-identical to `process-detail.md` (independently verified against the 0.5.4
  bundle mirror, which reproduces the pre-change 457-line file).

### Independent review

An independent read-only reviewer subagent inspected commit `b7cb90c` against the
0.5.4 mirror and on-disk files and returned pass with no must-fix findings:
all 16 moved sections word-identical; the always-on invariants (approval gate,
mandatory review, repair ceiling, state ownership, acceptance) stay loaded; the
skill, agent pointers, `AGENTS.md`, CHANGELOG, and PLAN agree. Structured
findings triage:

- Fixed: the moved-section test asserted headings only, so a silently altered
  section under an unchanged heading would pass; it now asserts a distinctive
  sentence from every moved section, and the always-on line cap tightened from
  150 to 140.
- Fixed: the reviewer's verbatim caveat (static verification against the mirror)
  was closed by `git diff b7cb90c^ b7cb90c` as recorded above.
- Applied nits: a discovery-frontmatter test for the skill; the 08b checkbox was
  split into instructions and agent-procedure halves in `PLAN.md`.

### Blocks and limits

The reviewer could not execute commands and substituted the on-disk AFTER state
and the 0.5.4 bundle mirror as the BEFORE state; the verbatim caveat was closed
by the git diff recorded in evidence. Whether a host reliably executes the skill
when a conversation needs it is not observed; this remains part of
`step-06-claude-code-qualification` / host qualification, not a claim of this
package. Replacing duplicated agent procedures and handoff chains is deferred to
Step 13. The reviewer's environment note is preserved as the reviewer's own
verification method, not substituted evidence.

### Pending-audit note

This delivery completes the instructions half of the
`step-08b-instruction-reduction` obligation. The agent-procedure half is tracked
with Step 13; this package records no pending audit of its own.

The user's chat instruction "I accept and approve" (2026-11-06T14:02:53+01:00) is
recorded as acceptance of this package in `DELIVERY-RUN.json`. The same
instruction recorded the owner's approval of the direction in
`REFACTOR_PORPOSAL.md`.
