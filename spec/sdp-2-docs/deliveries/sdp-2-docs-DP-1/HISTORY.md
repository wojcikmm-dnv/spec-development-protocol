# Step 12 Delivery History

## 2026-11-06 - Accepted for the current state

Delivered the rewritten README and `docs/INSTALLATION.md`, `WORKFLOW.md`, `REFERENCE.md`,
`UPGRADING.md`, plus `tests/release/test_docs.py` (19 tests). The old README's process
sections moved into `docs/WORKFLOW.md` and `docs/REFERENCE.md`; its upgrade sections moved
into `docs/UPGRADING.md`.

### Defects found by an independent reviewer who followed the documents (each verified)

- High: the pin example (`v0.5.4`) and the Initialize step contradicted each other. The 0.5.x
  tags contain only six skills, with no `sdp-init`, `sdp-migrate`, validator, or workflows.
  The documents now say which version has what and that no 2.0 release exists.
- Medium: `<installed skills>` was never defined and `python` may be `python3`; now explained.
- Medium: the install-script commands were dropped, and the 0.5.2 upgrade path would have
  installed `main`. Commands restored, pinned to the tag (`v0.5.3` for that path).
- Medium: APM was listed only as a build tool, though it is also an install channel, and APM
  needs Python 3.10 or newer to install through pip. Requirements corrected.
- Low: a re-run claim that held only for plain `apply`; the empty `spec/` folder Git does not
  track; the untracked `.sdp-backup/`; "everything CI runs" (the Linux job only); plan jargon
  ("Step 10") in `COMPATIBILITY.md`; Copilot CLI missing from the requirements. All corrected.
- Restored content that mattered: the templates path, the model-telemetry note, model
  routing, and a short statement of why SDP exists.
- The reviewer also showed the first version of `test_docs.py` could pass on wrong docs
  (37 of 40 mutations survived). It now checks documented flags against the scripts'
  argument parsers, install-script variables and defaults against `install.sh`, the state
  list against the validator, exact inventory sets, pinned tags against Git tags, broader
  benefit-claim patterns, and that host claims do not exceed the compatibility matrix.

### Evidence

After strengthening the tests, I re-ran the reviewer's surviving mutations (wrong flags,
wrong defaults, collapsed or invented states, fake inventory rows, speed claims, host claims,
unreal pins). Every one whose anchor matched was caught. Two of my first mutations did not
apply (an anchor that did not match, and a PowerShell grouping mistake that built the wrong
text), so I rewrote and re-ran them and they were caught. My own run of the first test set
found a real error in `PROTOCOL.md` (a script path that did not exist).

### Limits

Prose accuracy beyond the checked items is not tested. Hosted channel installs, the 2.0
changelog entry as a real section, and documentation for a removed installer remain for the
release and for Steps 13 and 14. The stable `/deliver` path has no recorded host evidence on
either VS Code or Copilot CLI beyond the observations in `COMPATIBILITY.md`; the README says so.

The user's instruction to continue is recorded as approval and acceptance.
