---
name: write-tests
description: Guidance for writing meaningful unit and integration tests. Use when adding or changing behavior, fixing a bug, or reviewing test quality; covers choosing cases from acceptance criteria, isolating unit tests, testing boundaries, and handling failing tests honestly.
---

# Skill: Write Tests

## Purpose

Produce maintainable tests that validate behavior, not implementation, so the team
can ship and refactor with confidence.

## Prerequisites

- Acceptance criteria are clear, or the bug's expected behavior is stated.
- The testing stack and commands are in `TECH.md`.

## Procedure

1. **Enumerate cases** from the acceptance criteria: happy path, error paths, and
   edge cases. For a bug, start with a test that reproduces it and fails.
2. **Structure** each test as Arrange, Act, Assert.
3. **Name** tests by behavior, such as `rejects_expired_token` or
   `should reject an expired token`, following the project convention.
4. **Focus** on one behavior per test. Several assertions are fine when they jointly
   verify that outcome.
5. **Test behavior, not implementation:** assert observable results, not private
   calls, internal state, or incidental ordering.
6. **Choose the right level.** Unit tests are isolated and deterministic: no real
   network, clock, randomness, or shared state unless controlled. Integration tests
   exercise contracts at real boundaries (HTTP, storage) with real or in-memory
   implementations, cover auth paths, and reset state between tests.
7. **Never hide a failure.** Do not skip, delete, or weaken a failing test to get a
   pass. If a test must change, record the root cause and confirm the required
   behavior is still verified elsewhere.
8. **Follow the project's test-location and naming convention.**

## Failure Routing

- The test exposes a real defect: fix the code, not the test.
- The test is flaky: find the nondeterminism (time, order, shared state) and remove
  it; do not retry until green.
- The requirement is wrong or ambiguous: stop and ask; do not encode a guess.

## Quality Bar

- Every acceptance criterion is tested.
- Happy, error, and edge scenarios are covered where they exist.
- A test would fail if the behavior it protects broke.
- Unit tests are deterministic; boundary tests are explicit about their real I/O.
