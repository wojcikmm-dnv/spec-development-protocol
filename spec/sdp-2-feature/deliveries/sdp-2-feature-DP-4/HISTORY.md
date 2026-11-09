# Handoff Chain and Command Mapping History

## 2026-11-09 - Accepted

The owner accepted this package under the standing exception recorded on
2026-11-09 (results now, no wait for acceptance after delivery),
continuing the session's exception mode. Acceptance is recorded in
`DELIVERY-RUN.json`.

## 2026-11-09 - Awaiting Acceptance

Completed the remaining Step 08b-agent-procedures and Step 13 superseded-component
work without removing any working command, on the owner's standing continuation
authorization and "continue" chat direction.

### Changes

- `docs/PROTOCOL.md`: the command-mapping intro no longer says commands are
  retired at Step 13 (inserters retired, commands keep working); the
  skill-coverage map intro states the completed consolidation, the manual-flow
  handoff chains, and the schema 4 workflow path.
- `docs/WORKFLOW.md`: the supervised/manual section adds the schema 4 preview
  reference (`/run-workflow`) and points at the command mapping.
- `.apm/prompts/deliver.prompt.md`: ends with the preview-path note (the
  `sdp.coordinator` agent must not run on the same package) and the mapping
  pointer. No command names changed.
- `PLAN.md`: 08b-agent-procedures and Step 13 superseded-component checkboxes
  updated; the progress paragraph and Step 08/13 narratives updated to the
  completed state.

### Coverage Finding (superseded agents/prompts)

The command mapping in `docs/PROTOCOL.md` covers all 11 prompts
(`audit-security`, `create-prd`, `deliver`, `design-system`, `discover-tech`,
`implement`, `plan-task`, `qa-validate`, `refine-backlog`, `run-review`,
`run-workflow`), and every extracted stage skill
(`sdp-implement`, `sdp-investigate`, `sdp-plan-delivery`, `sdp-technical-review`,
`sdp-security-review`, `sdp-acceptance-validation`, `write-tests`) carries
`sdp.skill.json` and `evals/cases.json` (verified on the working tree,
2026-11-09). Finding: no current agent or prompt is superseded while the schema 4
path is preview-only; each maps to a distinct role, skill, or preview entry
point, so removing any would break the working stable path. Nothing was deleted;
removal applies only if the schema 4 path qualifies and replaces a command, with
its breaking name documented then.

### Validation and Review

- `python scripts/run-suites.py skills` (43), `scripts/run-suites.py release`
  (114), `check-baseline.py`, `check-skills.py`, and
  `bash scripts/sync-templates.sh --check` pass; Windows `git diff --check`
  clean (2026-11-09).
- Independent read-only review returned FAIL with one must-fix finding: PLAN.md's
  own Step 08/progress narratives still said the work "waits for Step 13" while
  the boxes were checked; fixed together with a should-fix (package ledger) and
  two nits (Step 13 status wording; an approval-metadata typo). The reviewer
  verified: the 11-prompt count and `sdp.coordinator`/`run-workflow` naming, that
  the "must not run on the same package" claim matches the orchestrator and
  coordinator agent sources, no contradictions across README/docs/agents, the
  docs-test section-split and host-claim regexes still pass, the DP-4 boundary
  matches the actual diff, and both new link anchors resolve.
- Worker agent content is untouched (the accepted `sdp-2-feature-DP-3` state is
  preserved); no agent or prompt was deleted.

### Limits and Ownership

No host executed a delivery; the schema 4 preview path is unchanged and
unqualified. Host skill-loading behavior is not observed. No commits, pushes,
tags, releases, publications, deletions, or host trials were made by this
package. Acceptance is pending an explicit human decision.
