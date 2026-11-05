---
name: sdp-security-review
description: Audits a change that touches a security boundary for exploitable weaknesses. Use when authentication, authorization, secrets, untrusted input, sensitive data, cryptography, network trust, or dependencies change, when a security trigger was reported, or when a plan or epic requires a security audit; read-only and independent.
---

# Security Review

## Purpose

Find realistic, exploitable weaknesses in the changed attack surface. Do not run a
ceremonial audit on code that does not touch a security boundary.

## Run Conditions

Run when a trigger such as `security:input` was reported, the epic policy is
`per-story`, an `epic-level` audit is due, Compliance requires it, or the change
touches authentication, authorization, secrets, untrusted input, sensitive data,
cryptography, network trust, or dependencies.

Return `not_applicable` with a reason only when none of these hold and no
undisposed trigger exists. A `waived` epic policy does not hide an undisposed
trigger. Run independently of the implementer, read-only, with no product edits.

## Procedure

1. **Map the changed attack surface:** entry points, data that crosses a trust
   boundary, and what an attacker controls.
2. **Model realistic abuse:** for each entry point ask who can call it, with what
   input, and what the worst outcome is.
3. **Check, as applicable:** authorization on every path and at resource level;
   input validation and injection (SQL, command, path, template, deserialization);
   output encoding; session and token handling; secrets in code, logs, or
   responses; cryptographic choices; error and logging leakage; dependency and
   configuration risk; secure defaults.
4. **Confirm with evidence.** Run or read a test that demonstrates the weakness or
   its absence. Mark anything you could not verify as unverified, not as safe.
5. **Verdict** per `sdp-core/references/stage-result.md`. A Critical or High finding
   fails. Medium and Low findings are documented debt.

## Epic-Level Audits

An `epic-level` audit is due when the epic's policy is `epic-level` and the package
under review contains the epic's last story that has no accepted package; story
status is derived from accepted packages and the backlog, not stored. The baseline
is the earliest `candidate.base_revision` among the epic's package run records.
Audit everything that changed since that revision, not just the latest package, and
return the evidence for final acceptance. If you cannot determine the baseline,
return `blocked` and say what is missing instead of auditing a guess.

## Compliance Profile

In Compliance this stage is required and may not be `not_applicable`. Return the
extra evidence `TECH.md` configures (for example manifests or environment identity)
as produced by project tooling; never invent or approximate it.

## Output

A `stage-result` with each finding stating the attack, the affected location, the
impact, and a minimal fix. Never edit code and never claim a boundary is safe
without naming what you checked.

## Quality Bar

- Every finding includes a concrete abuse path, not a category name.
- Tooling limits and unverified areas are stated.
- No finding is dropped because a fix looks inconvenient.
