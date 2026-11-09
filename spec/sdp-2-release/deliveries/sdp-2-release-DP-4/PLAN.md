---
status: approved
approved_by: user (chat: "go ahead, also fix other not finished changes regards plan")
approved_at: 2026-11-09
---

# Retire the Legacy Installers

## Outcome and Boundary

Remove the legacy 0.5.x install channel (`install.sh`, `install.ps1`) and every
maintainer-facing reference that presents them as present tooling, on the owner's
explicit approval. Document historical tag availability and the retirement of the
moving-`main` installer URLs without adding a replacement wrapper. Superseded
agents/prompts are out of scope and stay with later packages.

The owner approved the removal knowing the replacement-channel gates are not fully
met: no 2.0 release is published and the hosted-channel rehearsal and Claude Code
qualification are pending. The deviation is recorded here and in the roadmap. The
released 0.5.x tags keep the scripts; existing projects keep the `.github/sdp-version`
marker detection in `sdp-init`/`sdp-migrate`.

- Size: M; risk: Low; uncertainty: Resolved; profile: Lean.
- Allowed changes: `README.md`, `CHANGELOG.md`, `PLAN.md`, `docs/INSTALLATION.md`,
  `docs/UPGRADING.md`, `docs/RELEASING.md`, `scripts/check-all.sh`,
  `.github/copilot-instructions.md`, `tests/release/test_docs.py`, this package,
  and the deleted installers.
- Excluded: superseded agents/prompts, the template mirror, historical build
  archives, shipped marker-detection behavior, releases, tags, publication,
  and any replacement download-and-execute wrapper.

## Acceptance Criteria

1. `install.sh` and `install.ps1` are deleted; no active document, automation, or
   maintainer instruction presents them as present tools; historical changelog
   statements are preserved.
2. README, the installation guide, and the upgrading guide keep working channel,
   update, and migration guidance, and agree with each other.
3. Focused documentation tests, an independent review with findings resolved, and the
   full check battery pass. Acceptance remains a human decision.

## Verification

Delete with `git rm`, run the six suites via `scripts/run-suites.py`,
`scripts/check-baseline.py`, `scripts/check-skills.py`, `bash scripts/sync-templates.sh
--check`, `git diff --check` (Windows git, the authoritative checker for this
checkout), and an independent read-only review of the diff. Confirm no active
reference to the retired files outside history.
