---
status: approved
approved_by: user (chat: continue; standing continuation and self-commit authorization 2026-11-05)
approved_at: 2026-11-09
---

# Complete the Handoff Chain and Command Mapping Work

## Outcome and Boundary

Finish the remaining Step 08b-agent-procedures and Step 13 superseded-component
work without removing any working command: document the handoff chains as the
manual flow with schema 4 workflow references, point `/deliver` at the preview
path, update the stale "until Step" documentation lines to the completed state,
and record the coverage finding for superseded agents/prompts.

- Size: S; risk: Low; uncertainty: Resolved; profile: Lean.
- Allowed changes: `docs/PROTOCOL.md`, `docs/WORKFLOW.md`,
  `.apm/prompts/deliver.prompt.md`, `PLAN.md`, this package.
- Excluded: agent file content (the accepted `sdp-2-feature-DP-3` state is
  preserved), deleting agents or prompts, validator behavior, workflow JSON,
  releases, tags, publication, and host trials.

## Acceptance Criteria

1. The command mapping in `docs/PROTOCOL.md` is accurate for all 11 prompts and
   no longer says commands are retired at Step 13.
2. The skill-coverage map states the completed consolidation and the manual-flow
   handoff chains; `docs/WORKFLOW.md` references the schema 4 workflow and its
   mapping; `/deliver` points at the preview `/run-workflow` without claiming
   behavioral equivalence.
3. Coverage check documented: every stage skill carries a descriptor and
   evaluation fixtures, and no current agent or prompt is superseded while the
   schema 4 path is preview. No command is removed and no breaking name created.
4. Focused suites, an independent review, and the full check battery pass.

## Verification

Run `scripts/run-suites.py` for skills and release, `check-baseline.py`,
`check-skills.py`, `sync-templates.sh --check`, `git diff --check` (Windows git),
and an independent read-only review of the diff.
