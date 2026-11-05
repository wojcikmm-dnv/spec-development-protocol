---
status: approved
approved_by: user (chat instruction to continue the roadmap in order)
approved_at: 2026-11-05T17:00:00+01:00
---

# Step 06: Host Adapters and Qualification

## Outcome and Boundary

Map the workflow's capabilities onto hosts without claiming more than was observed:
host capability profiles, capability negotiation in the validator, preview entry points
for the coordinator, and an evidence-based compatibility matrix.

- Size: L; risk: Moderate; uncertainty: Bounded by host availability. Profile:
  Balanced with independent review. Security: capability assertion and approval
  boundaries were reviewed. QA: bounded real-host trials where a host is available.
- Hosts: GitHub Copilot CLI 1.0.85 is installed and tested. Claude Code is not
  installed, so it is recorded as blocked, not assumed to work. VS Code Copilot and
  other hosts are not tested.

## Acceptance Criteria

1. Host profiles record each capability as verified with cited evidence, false, or
   unverified; the validator refuses a verified capability without evidence.
2. Isolated stages need an `independent-context` capability; a host lacking verified
   capabilities blocks delivery instead of allowing self-review.
3. The source of asserted capabilities is recorded in the run record and visible.
4. A compatibility matrix distinguishes generated, installed, skill followed,
   delivery executed, and qualified, and lists nothing above its evidence.
5. Thin preview entry points exist; existing `/deliver` behavior is unchanged.
6. Any real-host trial is read-only or tool-restricted, uses scratch locations, and
   leaves the user's configuration and repository unchanged.

## Allowed Paths

`.apm/skills/sdp-core/**`, `.apm/skills/sdp-workflows/**`, `.apm/agents/` (new
coordinator; a compatibility note on the orchestrator), `.apm/prompts/` (new),
`tests/contracts/**`, `docs/**`, `CHANGELOG.md`, this package's records. No changes to
global Copilot or Claude configuration.
