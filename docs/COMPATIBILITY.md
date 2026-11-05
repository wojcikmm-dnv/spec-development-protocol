# Host Compatibility

SDP is portable by design, but packaging for a host does not prove it behaves the same
there. This matrix separates what was generated, what was installed and discovered, and
what was actually executed. Nothing is listed above the evidence behind it.

## Levels

| Level | Meaning |
| --- | --- |
| Generated | The package for this host layout is produced. Says nothing about behavior. |
| Installed | The generated package was installed in an isolated location and the host listed its skills. |
| Skill followed | A real model run loaded an SDP skill and acted on it, under tool restrictions. |
| Delivery executed | A full bug-workflow delivery ran on the host, including independent review, repair, and resume. |
| Qualified | Delivery executed and every capability the workflow needs is verified with evidence in the host profile. |

A host is **qualified** only at the last level. Until then, `next --host <name>` blocks
supervised delivery, because the host profile does not list the isolation and review
capabilities as verified. Self-review is never substituted.

## Matrix

| Host | Tested version | Generated | Installed | Skill followed | Delivery executed | Qualified |
| --- | --- | --- | --- | --- | --- | --- |
| GitHub Copilot CLI | 1.0.85 | yes | yes | yes (read-only steps) | no | no |
| GitHub Copilot in VS Code | none | yes (shared layout) | not tested | not tested | no | no |
| Claude Code | none | yes (APM layout) | not tested | not tested | no | no |
| Codex, Gemini CLI, Cursor | none | via APM targets | not tested | not tested | no | no |

Claude Code is not installed in the maintainer environment, so nothing was executed
there. Its profile is blocked, not assumed to work. Other hosts are listed only because
APM can generate files for them.

## Host profiles

Each host has a profile in `.apm/skills/sdp-workflows/hosts/<host>.json`. A capability
(`implement`, `technical-review`, `security-review`, `acceptance-validation`,
`independent-context`) is `true` only when the profile cites evidence, otherwise
`"unverified"` or `false`. The validator refuses a verified capability without
evidence. `sdp.py next --host <name>` counts only verified capabilities.

## What was observed on Copilot CLI 1.0.85

Install and discovery were checked in a scratch `COPILOT_HOME` so no personal
configuration changed. Two bounded model runs were also made, each in a scratch
repository:

- Coordinator step: the model loaded `sdp-workflows`, ran the validator's `next`, and
  reported the returned action correctly without changing anything.
- Independent review: in a separate process with `write` and `shell` denied, the model
  loaded `sdp-technical-review` and found a seeded off-by-one and the test that encoded
  it. The shipped grader accepted the result for case `off-by-one-drops-last-item`, and
  the model's attempt to create a file was refused.

These show that the skills load and can be followed under tool restrictions. They do not
show that a coordinator can dispatch an isolated reviewer inside one delivery, so
`independent-context` remains unverified. The delivery history has the details:
`spec/sdp-2-hosts/deliveries/sdp-2-hosts-DP-1/HISTORY.md`.

## Reproducing a check

1. `apm pack -o <temp-dir>` builds the bundle.
2. `COPILOT_HOME=<scratch> copilot plugin install <bundle>` then `copilot skill list`
   shows what the host discovered.
3. `copilot -p "<prompt>" --plugin-dir <bundle> --deny-tool=write --deny-tool=shell
   --max-ai-credits 30` runs a bounded read-only trial. Model runs use your quota and
   can vary; treat one run as an observation, not a guarantee.

## Limits

One observation on one model does not show that other models follow a skill. The
`independent-context` capability needs a separate session or subagent with different
permissions; until a delivery is run with one, it stays unverified. Direct plugin
installs are marked deprecated by Copilot CLI; the supported route is a marketplace
install. A local marketplace was checked (it loads live from the checkout); a hosted one has
not been (see [RELEASING.md](RELEASING.md)).
