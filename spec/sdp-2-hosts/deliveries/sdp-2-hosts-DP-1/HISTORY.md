# Step 06 Delivery History

## 2026-11-05 - Accepted with Claude Code blocked

Delivered host capability profiles, capability negotiation (`next --host`,
`transition --host`, an `independent-context` requirement, and a recorded
`capability_source`), the preview `sdp.coordinator` agent and `/run-workflow` prompt,
and `docs/COMPATIBILITY.md`. 96 contract tests pass (WSL, Python 3.12).

### Host evidence (GitHub Copilot CLI 1.0.85)

All steps used scratch locations (`COPILOT_HOME` and `--plugin-dir`) and a throwaway
repository, so personal configuration and this repository were unchanged.

- `apm pack` output installed with `copilot plugin install`: 14 skills discovered,
  including every SDP skill; the host warned that direct plugin installs are deprecated.
- The installed `sdp-core` validator resolved its sibling workflow definitions from the
  plugin directory and ran `next`, `approve`, and `next` against a scratch repository.
  `SDP_WORKFLOW_DIR` behaved as documented.
- Coordinator step (one model run, 28 of 30 AI credits): the model loaded
  `sdp-workflows`, searched for the validator, ran `sdp.py next`, and reported the
  returned action (`start-delivery`, owned by the coordinator) correctly. The record was
  unchanged. The search for the script cost credits, so the skill now says where the
  validator lives.
- Independent review (one model run in a separate process, 11 of 30 AI credits, `write`
  and `shell` denied): the model loaded `sdp-technical-review`, found the seeded
  off-by-one in `src/paging.py` and noted the test encoded the bug, returned a result the
  shipped grader accepted for `off-by-one-drops-last-item`, and was refused when it tried
  to create a file. The file did not exist afterwards.
- These are single observations on one model. They show the skills load and can be
  followed under tool restrictions, not that a coordinator can dispatch an isolated
  reviewer inside one delivery. No delivery was executed on any host.

### Claude Code: blocked

Claude Code is not installed in the maintainer environment. Nothing was run, so its
profile lists every capability as unverified with a `blocked_reason`, and the matrix says
not tested. Marketplace behavior there is also unverified.

### Independent review

Verdict fail with seven findings; triage:

- Fixed: `transition` accepted caller-asserted capabilities that bypassed host
  profiles. `transition --host` now enforces the profile, and every transition to
  `delivering` records `capability_source` (`host:<name>` or `explicit`), which
  `inspect` shows and the coordinator must state in the acceptance brief. The residual
  limit (an explicit list is an assertion) is documented in PROTOCOL.md.
- Fixed: the old orchestrator now carries a note that it writes schema 3 and must not be
  mixed with the schema 4 workflow on a package.
- Rejected: marking `implement` verified from a run in which editing was denied; that
  would be exactly the over-claim the matrix exists to prevent. Capabilities stay
  unverified until a delivery exercises them.
- Rejected: excluding the Claude profile from the package. It documents a blocked
  status; unverified entries carry no authority because `next` counts only verified ones.
- Noted: no coordinator agent has run a full delivery, so the end-to-end block-handling
  path is only covered by contract tests.

### Cost and limits

The two model trials used about 39 AI credits in total from the signed-in Copilot
account. Model runs vary, so these are observations rather than guarantees. VS Code
Copilot, Codex, Gemini, and Cursor were not tested. Mixed use of `/deliver` and
`/run-workflow` on one package is unsupported.

The user's continue instruction is recorded as approval and acceptance. The roadmap's
exit criterion, "both initial hosts pass", is NOT met: Claude Code is blocked.
