---
name: sdp-investigate
description: Reproduces and diagnoses a reported bug before any fix is planned. Use when handling a bug report, regression, failing test, or unexpected behavior and the root cause is not yet established; produces a reproduction, evidence, root cause, and a bounded fix proposal.
---

# Investigate a Defect

## Purpose

Establish what is actually wrong before changing code, so the fix plan targets the
cause and its boundary rather than a symptom.

## Prerequisites

- A report with expected versus actual behavior, or a failing check.
- Read access to the code and a way to run it. Product code is not edited here.

## Procedure

1. **Restate** the expected and actual behavior in one sentence each. If either is
   unclear, ask one focused question before continuing.
2. **Reproduce** with the smallest deterministic steps or a failing test. Record the
   exact command and output. If you cannot reproduce it, stop with `blocked` and
   list what you tried and what is missing.
3. **Isolate** by narrowing inputs, versions, or code paths until one change in
   condition flips the behavior. Prefer evidence from running code over reading it.
4. **Find the cause**, not the first suspect. State the mechanism: which line or
   assumption produces the wrong result and why. Check whether the same cause
   affects other callers.
5. **Bound the fix.** Name the paths a fix would change and what must not change.
   Note the regression test that would have caught it.
6. **Classify risk.** Report triggers (`security:*`, `qa:*`) when the cause touches
   those areas. Say whether the cause is a code defect or a flaw in an approved
   requirement or design.

## Output

Reproduction steps with evidence, root cause with the mechanism, affected callers,
proposed fix boundary and test, risks, and triggers. Return a `stage-result` using
the contract in `sdp-core/references/stage-result.md`.

## Escalation

Stop and route to refinement or design when the "bug" is behavior the approved
requirements actually specify, when the fix needs a new public contract, dependency,
or data change, or when the cause is a design flaw. Do not widen scope to make a
fix feasible.

## Quality Bar

- The reproduction fails before and would pass after the fix.
- The root cause explains every observed symptom.
- No product code or test was edited.
- Claims cite output you saw, not output you expect.
