# Upgrading and Migration

Choose by what your project has today.

| Your project | Do this |
| --- | --- |
| SDP 0.5.3 or 0.5.4 (with or without `spec/` state) | Migrate with `sdp-migrate` (below). |
| An earlier layout (0.5.2 or older) | Not supported by the tool; upgrade by hand to 0.5.3 using the steps at the end of this page, then migrate. |
| No `spec/` state yet | Nothing to migrate; initialize the project (see [Installation](INSTALLATION.md)). |

## Migrating to the schema 4 layout

`sdp-migrate` moves delivery records to schema 4 without inventing approvals. Commit or back
up your work first. It previews by default.

```bash
python <installed skills>/sdp-migrate/scripts/migrate.py --repo . preview
python <installed skills>/sdp-migrate/scripts/migrate.py --repo . apply
```

What it does:

- Open packages (planned, delivering, blocked, awaiting acceptance, changes requested) restart
  as `planned`. An approved plan's approval is voided in `PLAN.md` (the body is untouched) and
  recorded in `HISTORY.md`, because the approved plan cannot be verified. A named human must
  approve it again.
- Accepted and rejected packages keep their decision only when it names a human; otherwise the
  tool stops and asks. It never fabricates an approval or acceptance.
- The original record is kept as `DELIVERY-RUN.legacy.json` and its hash is recorded in
  `migrated_from`. Pending audit obligations are preserved; notes and audits in the old
  `ACTIVE.md` that no migrated package can hold stop the migration instead of being dropped.
- A 0.5.3 feature-level package moves to `spec/<slug>/deliveries/<id>/`.
- Ambiguous statuses need a human mapping: `--status-map <package id or slug>=<status>`.
- Text that is not valid UTF-8, links, junctions, and paths outside the repository are
  refused.

`apply` first writes `.sdp-backup/<timestamp>/` (the originals and a journal), makes the
changes with atomic replaces, validates every migrated record, and restores everything if
anything fails. Re-running a plain `apply` on a migrated project reports nothing to do. Keep
`.sdp-backup/` until you have accepted the result; it shows up as untracked in Git, so decide
whether to commit it or ignore it.

### Removing copied install-script files

Only after the new package is installed and loads:

```bash
python <installed skills>/sdp-migrate/scripts/migrate.py --repo . apply \
  --remove-legacy-files --confirm-replacement-installed
```

Files are moved into the backup (nothing is deleted) and only when the old installer marker
exists, the file is not APM-managed, and its content equals a released 0.5.3 or 0.5.4 file.
Customized copies stay and are listed.

### Rolling back

- `migrate.py --repo . status` reports an interrupted migration; `apply` refuses to run until
  it is restored.
- `migrate.py --repo . restore --backup .sdp-backup/<timestamp>` returns every changed file to
  its original content and removes what the migration created. A file you edited after the
  migration is left alone and listed; move or revert it and run `restore` again.
- Roll the package version back together with the project state. Do not resume schema 4
  records with an older package.

## What changes for users

Existing commands keep working in this release line. The schema 4 path adds preview entry
points (`/run-workflow`, the `sdp.coordinator` agent) and a validator; the mapping from each
existing command to its schema 4 equivalent is in [PROTOCOL.md](PROTOCOL.md#command-mapping).
Removing the install scripts and superseded agents is a later, separately approved step.

## Manual steps for earlier layouts

### From the strict identity workflow (0.5.2 and older)

1. Back up project customizations.
2. Upgrade SDP-managed files together with the install script, pinned to the version you are
   moving to (this step is for 0.5.2 and older, so use `SDP_BRANCH=v0.5.3`):

   ```bash
   curl -fsSL https://raw.githubusercontent.com/WojcikMM/spec-development-protocol/main/install.sh \
     | SDP_BRANCH=v0.5.3 SDP_FORCE=true SDP_TECH_MODE=skip bash
   ```
3. Update `TECH.md` with the SDP Delivery Policy.
4. Migrate active state: `current_story` becomes `current_delivery`, `status` becomes
   `feature_status`, `final_status` becomes the closest `delivery_status`.
5. Regenerate the active `PLAN.md` with the current template.
6. Start new run checkpoints with the current `DELIVERY-RUN.json` schema and keep unresolved
   security obligations in `pending_audit`.

Do not mix old plan or run semantics with new agents; a default non-overwriting install can
leave mixed versions, so upgrade deliberately. Projects that still need strict digests,
manifests, and retained stage evidence should set Compliance as their mandatory profile.

### To package-scoped state (0.5.3 to 0.5.4)

1. Move `spec/<slug>/PLAN.md` to `spec/<slug>/deliveries/<delivery-id>/PLAN.md`, with the run
   record and that delivery's history entries.
2. Move `delivery_status` and `pending_audit` from `ACTIVE.md` into the package
   `DELIVERY-RUN.json` and drop `feature_status`.
3. Optionally add `spec/ACTIVE.md` to `.gitignore` and fill the integration-branch and
   merge-hotspot lines in `TECH.md`.

`sdp-migrate` performs these moves for you and is the supported way to do them.
