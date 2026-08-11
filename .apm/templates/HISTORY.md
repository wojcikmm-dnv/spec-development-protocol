# History: <Feature Title>

Append-only log of completed work and hardening outcomes for `spec/<slug>/`. Do not edit or delete prior entries — append new ones.

## Entry Format

Copy this block per completed story or hardening event:

```md
### <ISO date> — STORY-<N>: <title>
- Gate: <5 Implementation | 6 Hardening>
- Actor: <sdp.developer | sdp.reviewer | sdp.security | sdp.qa>
- Summary: <what was done / what was found>
- Severity (if finding): <Critical | High | Medium | Low>
- Security review: <per-story audit result | epic-level deferred | waived: "<reason>">
- Hardening cycle count for this story: <n>
- Outcome: <Approved | Request Changes | Pass | Fail | Escalated to user>
```

## Escalation Log

If a story fails the same hardening step twice, log the escalation here per the Loop Breaker rule in `sdlc-process.instructions.md`:

```md
### <ISO date> — ESCALATION: STORY-<N>
- Failed step: <reviewer | security | qa>
- Cycles: 2
- Decision requested from user: <descope | split story | accept documented risk>
- Resolution: <pending | resolved: description>
```
