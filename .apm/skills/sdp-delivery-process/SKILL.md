---
name: sdp-delivery-process
description: Detailed reference for the stable SDP delivery process covering delivery profiles, assurance triggers, the plan contract, supervised and manual delivery, delivery state and active-package resolution, parallel delivery, worker verdicts, acceptance, and feedback routing. Use when planning, delivering, reviewing, resuming, or auditing an SDP package and the short always-on rules are not enough.
---

# Delivery Process Reference

## Purpose

The always-on instructions keep only the rules that must never be forgotten. This skill holds
the full text, loaded when you need it, so a conversation does not carry 400 lines of process
it is not using.

## When to read which section

Read [references/process-detail.md](references/process-detail.md) and go straight to the
section for what you are doing:

| You are | Section |
| --- | --- |
| Deciding how much process a change needs | Right-Sizing Earlier Gates, Capability Sizing, Delivery Profiles |
| Choosing security or QA stages | Assurance Triggers (including the epic security policies) |
| Writing or approving a plan | Delivery Contract, Artifact Approval, Implementation Autonomy |
| Running `/deliver`, resuming, or handling a correction | Supervised Delivery (normal path, advanced actions, correction routing) |
| Judging whether earlier review still applies | Candidate Identity |
| Finding the active package or writing state | Delivery State |
| Delivering packages in parallel | Parallel Delivery (safety verdicts, merge-friendly edits, worktree flow, merge readiness) |
| Recording or reading evidence | Run State and Evidence, Worker Verdicts |
| Presenting or deciding acceptance | Human Acceptance |
| A review or QA finding came back | Feedback Routing |

## Which workflow this describes

This is the stable process that the `/deliver` orchestrator follows and that writes schema 3
run records. The preview schema 4 path (`sdp-core`, `sdp-workflows`, `/run-workflow`) enforces
the same gates and human decisions through the validator; its contract is in `docs/PROTOCOL.md`
of the source repository. Do not mix the two on one package.

## Rules that stay in force regardless

These are repeated in the always-on instructions, so you do not need to load this skill to
obey them:

- No product code before an approved delivery plan.
- Developer validation and independent technical review always run; only optional security or
  QA stages may be `not_applicable`, with a policy reason.
- A named human accepts or rejects; acceptance never commits, merges, or deploys.
- `spec/ACTIVE.md` is a pointer with no body; shared specs are read-only during delivery.
- Never invent evidence, verdicts, or checks.
