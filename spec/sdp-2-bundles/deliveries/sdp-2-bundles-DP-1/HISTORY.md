# Step 10 (local part) Delivery History

## 2026-11-05 - Accepted

Delivered `scripts/build-release.py`, the APM pin, `SETUP.md`, `docs/RELEASING.md`, and
`tests/packaging/` (39 tests, Windows Python 3.11). Two builds of one commit are
byte-identical, and an LF checkout and a CRLF checkout produce the same bytes.

### Facts learned about the tools

- `apm pack` ships `__pycache__` and `*.pyc` from the developer machine and preserves
  hidden files; its ZIP has no `LICENSE`. The builder strips caches and adds the license.
- Running the test suites creates bytecode caches under `.apm/skills/*/scripts/`
  (they are gitignored), so a naive local pack would have shipped them.
- `apm pack` regenerates tracked marketplace files; the builder passes `--marketplace none`
  so a build never edits the working tree. `apm pack --check-versions --check-clean
  --dry-run` passes and is part of the tests.
- Copilot CLI registers a local directory as a marketplace and then loads the plugin live
  from it without copying, so a local marketplace install proves discovery only. A `file://`
  URL was refused. Clean-copy native installs need a hosted repository.

### Defects found by independent review (each reproduced) and fixed

- Medium: bytes depended on the checkout's line endings (78 of 82 entries had CRLF on a
  normal Windows checkout, and `LICENSE` and `SETUP.md` disagreed). Text is now normalized
  to LF in the bundle and in the comparison.
- Medium to low: `.` path segments, extra and hostile entries (`.env`, `*.sh`, alternate
  data streams, case collisions, trailing dots), and symbolic links that the build path
  flattened were accepted. The bundle must now equal the expected file set; raw entries
  from `apm` are checked before flattening.
- Low: a failed build left an empty folder or a published ZIP without its checksum; a
  stale ZIP of another version stayed beside the new one. Output is written only after
  verification, atomically, and a folder with another archive is refused.
- Low: `--check` and `build` printed tracebacks for malformed manifests; a manifest `name`
  mismatch passed `--check`; the APM pin was a substring match (`10.29.0`, `0.29.0-evil`
  were accepted). All fixed.
- Low: `SETUP.md` claimed more than was verified ("same as `apm install`", other hosts,
  Python 3.9 runtime). Reworded to what was observed.
- Test gaps filled (builder behavior, hostile `apm` output, failure cleanup, version-key
  parsing, pin matching) and the silent skip made switchable with `SDP_REQUIRE_APM=1`.
- Equivalent mutant: allowing `.` segments is also caught by the trailing-dot rule, so
  removing the explicit `.` rule changes nothing.

### Evidence

Mutation checks caught 19 of 20 changes; the survivor is the equivalent mutant above.

### Limits

Python 3.9 and hosted native installs are unverified. The ZIP was not loaded by an agent
host; only its scripts were run after extraction. Obligation
`step-10-hosted-catalog-rehearsal` stays open.

The user's continue instruction is recorded as approval and acceptance.
