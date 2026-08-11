---
description: Create an implementation plan for one approved story. Does not write code.
argument-hint: "Provide one approved story/task ID."
agent: sdp.planner
---

The `sdp.planner` agent will:

1. Create a detailed implementation plan for a single story, including a mandatory Scope Budget (max files, estimated changed lines, complexity tier).
2. If the story doesn't fit the budget, it will stop and recommend splitting it instead of producing an oversized plan.
3. Save the plan to `spec/<slug>/PLAN.md` with `status: draft`, for your approval.

This command **does not write code** and does not auto-chain to implementation. After you set `status: approved` in `PLAN.md`, run `/implement` explicitly.
