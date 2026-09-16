---
description: Execute an approved implementation plan for a single story.
argument-hint: "Provide the approved plan reference and story ID."
agent: sdp.developer
---

The `sdp.developer` agent will:

1. Verify `spec/<slug>/PLAN.md` has `status: approved` — it refuses to run otherwise.
2. Execute the steps in the approved plan, staying within its declared Scope Budget.
3. Add or update tests as required.
4. Hand off once to `sdp.reviewer` when done — it will not loop back into implementation on its own.

This command requires an approved plan from `/plan-task`. It will not run without one.
