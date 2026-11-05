# Step 04 Delivery History

## 2026-11-05 - Accepted

Delivered six extracted skills (`sdp-investigate`, `sdp-plan-delivery`,
`sdp-implement`, `sdp-technical-review`, `sdp-security-review`,
`sdp-acceptance-validation`), a rewritten `write-tests`, a shared
`stage-result.md` contract, a skill descriptor schema, `grade_eval.py`, 28
evaluation cases with reference answers, `scripts/check-skills.py`, and 28 tests.

### Evidence

- `python scripts/check-skills.py`: pass. `python -m unittest discover -s
  tests/skills`: 28 tests pass, including rejection of name/folder mismatch,
  missing description or "Use when", broken links, missing or invalid descriptor,
  missing evaluation file, a reference answer failing its own case, verdict-only
  failing cases, too few cases, and an oversized skill.
- Adversarial grader tests: an empty-findings answer and a wrong-verdict answer
  fail for every case that expects findings. Keyword stuffing can still pass; this is
  documented as a limit, not hidden.
- The checker caught two of the author's own reference answers that did not match
  their patterns; both were corrected. A "clean" fixture that omitted an import was
  also found and fixed by the author during review of the fixtures.

### Independent review

Verdict fail with ten findings; triage:

- Fixed: Compliance behavior per stage skill, the one-repair ceiling in
  `sdp-implement`, migration identifier rules, the plan frontmatter example and
  approval flow, the lightweight-path wording (no new limits), epic-level audits
  grounded in existing fields, the scope of the stage-result contract for
  pre-delivery skills, and the meaning of case kinds.
- Rejected: the suggested `is_epic_final` plan field and a 30-day limit on
  lightweight paths; neither exists in SDP and inventing them would add unapproved
  contracts. Epic audits now use the derived story status and the earliest
  `candidate.base_revision` instead, and block when the baseline is unknown.

The fixes were verified by the checker and tests; a second independent review of the
delta was not run.

### Limits

Evaluation cases are deterministic graders for a produced result. They do not run
a model and do not show that any model follows a skill. Legacy skills
(`create-api-endpoint`, `create-ui-component`, `database-migration`,
`error-handling`) have no descriptor or cases yet. Skills are not wired into agents
or workflows until Steps 05 and 08.

The user's continue instruction is recorded as approval and acceptance.
