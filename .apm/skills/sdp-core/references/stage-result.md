# Stage Result and Trigger Contract

Every assurance stage (`reviewer`, `security`, `qa`) and the implementer report the
same shape so the validator can record it. Map each field to the matching
`sdp.py result` flag.

Investigation and planning (`sdp-investigate`, `sdp-plan-delivery`) use the same
shape to report to the user, with `stage` set to `developer` by convention. They
are not recorded with `sdp.py result`, which records implementation and assurance
results for a candidate; keep their output in the plan or the package history.

## Result

| Field | Meaning |
| --- | --- |
| `stage` | `developer`, `reviewer`, `security`, or `qa` |
| `verdict` | `pass`, `fail`, `blocked`, or `not_applicable` |
| `findings` | One string each, formatted `Severity: problem (path:line) - fix` |
| `checks` | What was run or inspected |
| `evidence` | Log paths, test names, or command output references |
| `detected_triggers` | Specialist stages this work needs, such as `security:input` |
| `next_action` | One concrete recommendation |

## Verdicts

- `pass`: nothing at Critical or High severity, and every required criterion met.
- `fail`: any Critical or High finding, or an unmet required acceptance criterion.
  A `fail` needs at least one finding.
- `blocked`: the stage could not run, such as a missing tool or environment. State
  what is missing. A block is never a pass and is not counted as a rejection.
- `not_applicable`: allowed only for optional security or QA stages, with a reason.
  Developer and reviewer results can never be `not_applicable`.

## Severity

- Critical: exploitable now, data loss, or the change cannot work.
- High: wrong behavior in a normal path, broken acceptance, or a real security gap.
- Medium: edge-case defect, weak test, or maintainability risk worth fixing.
- Low: minor clarity or consistency issue.

Medium and Low findings are recorded debt unless project policy says otherwise.

## Trigger Vocabulary

Format `stage:area`. Report a trigger when the change touches the area, even if you
cannot judge it yourself.

| Trigger | Report when the change touches |
| --- | --- |
| `security:auth` | authentication or session handling |
| `security:authz` | permissions, roles, or resource ownership |
| `security:secrets` | credentials, keys, tokens, or configuration secrets |
| `security:input` | untrusted input, parsing, queries, or file or URL handling |
| `security:data` | personal, financial, or otherwise sensitive data |
| `security:crypto` | hashing, encryption, signing, or randomness |
| `security:network` | trust boundaries, CORS, redirects, or outbound calls |
| `security:dependency` | new or changed dependencies, build, or infrastructure |
| `qa:journey` | a critical user workflow |
| `qa:integration` | behavior across a service or storage boundary |
| `qa:accessibility` | UI that must be keyboard or screen-reader usable |
| `qa:compatibility` | supported platforms, versions, or data formats |
| `qa:migration` | schema or data migrations |
| `qa:performance` | latency, throughput, or resource limits |

A reviewer reports triggers; it does not dismiss them. Only the specialist stage that
ran, or a human accepting the risk with a reason, disposes of a trigger.
