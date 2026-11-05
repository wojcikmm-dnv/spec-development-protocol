---
description: Preview. Run the bug workflow for the active package by following the validator's next action.
argument-hint: "[delivery-id | inspect | resume]"
agent: sdp.coordinator
---

Preview of the schema 4 workflow. For normal delivery keep using `/deliver`.

1. Resolve the package folder under `spec/<slug>/deliveries/<id>/`: an explicit ID,
   the `sdp/<id>` branch, `spec/ACTIVE.md`, or the only open package.
2. Follow the `sdp-workflows` skill: run `next`, do exactly that action, record the
   result, and run `next` again.
3. Stop for human decisions and report any capability block. Never approve a plan or
   accept a delivery yourself.

`inspect` reports status without changing anything. `resume` continues from `next`.
