# Step 09 Delivery History

## 2026-11-05 - Accepted

Delivered `sdp-migrate` (preview, apply, restore, status), the legacy file manifest built
from the released 0.5.3 and 0.5.4 tags, and the `migrated_from` record field. Tests: 46
migration tests pass on WSL (Python 3.12) and on Windows (Python 3.11, one symlink test
skipped); contracts 144, skills 28, init 32 still pass. `apm pack` output runs the tool
from the bundle and finds the manifest and sdp-core.

### Defects found and fixed

By my own tests:

- A failed atomic replace left a `.sdp-tmp` file behind; the write is now cleaned up and
  restore also removes strays.
- `fsync` on a read-only handle fails on Windows (`Bad file descriptor`); and Windows can
  briefly deny a rename (`WinError 5`), so replaces now retry a few times.
- A restore ordering bug I introduced while fixing the first item (caught immediately).

By independent review, each reproduced before fixing:

- Medium-High: a nested package was identified by the record's `delivery_id`, so a
  mismatch migrated to the wrong folder and colliding ids overwrote preserved evidence.
  Nested packages now use the folder name.
- Medium: tracebacks on a non-list `pending_audit` or non-string plan status; a string
  `pending_audit` was split into characters (fabricated obligations). Now refused with a
  message.
- Medium: audits and notes in the old `ACTIVE.md` were dropped when its slug had no
  package. The migration now stops instead.
- Medium: `rejected` carried over with no human decision, and `--status-map` could invent
  one. Both terminal statuses now need a recorded decision that names a human.
- Low-Medium: non-UTF-8 text was rewritten with replacement characters (now refused);
  `apply` after a crash did not refuse before analysis (now checked first); a backup area
  that was a link was followed (now checked); restore did not check journal paths (now
  checked up front); preview and apply disagreed for a linked `.github` (preview now runs
  the same path check); restore accepted only exact relative paths (now normalized);
  an unknown `--status-map` target was ignored (now a blocker); empty `.github`
  subfolders were left by removal ordering (now deepest first).
- Rejected or kept as documented: a restore conflict leaves the journal open. That is
  intended (the tool must not overwrite a later edit); the message and docs now say how to
  finish. The reviewer's tampered-journal concern is covered by the path checks above and
  needs write access to the repository anyway.

### Evidence

Mutation checks caught all nine: accepting a decision-less acceptance, not voiding an
approval, keeping an open status, ignoring restore conflicts, skipping post-apply
validation, overwriting preserved evidence, removing without the marker, removing
customized files, and dropping pending audits. Crash-injection by the reviewer (48 crash
points across both layouts) always restored the original tree.

### Limits

Preview does not run the validator on the final tree; apply does. Ownership by hash
covers files from the released 0.5.3 and 0.5.4 tags only. Approver names in legacy records
are asserted strings. No host has run a migrated project through a full delivery.

The user's continue instruction is recorded as approval and acceptance.
