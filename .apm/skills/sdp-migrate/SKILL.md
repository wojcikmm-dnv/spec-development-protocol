---
name: sdp-migrate
description: Migrates a project from SDP 0.5.3 or 0.5.4 to the schema 4 layout without losing approvals, history, or audit obligations. Use when upgrading an existing SDP project, when init reports earlier-installer files or legacy state, or when asked to restore or roll back a migration; previews first, backs up everything, and never fabricates an approval.
---

# Migrate an Existing Project

## Purpose

Move an existing project to the current record layout safely. The tool previews by default,
keeps a backup and a journal, validates its result, and restores everything if a step fails.

## Prerequisites

- The SDP package is installed (`sdp-core` is next to this skill). Python 3.9 or newer.
- A clean Git state, or a backup you trust. Commit or stash your work first.
- Supported sources are SDP 0.5.3 and 0.5.4. Older layouts stop with an upgrade message.

## Procedure

1. Run `python <this skill>/scripts/migrate.py --repo <repo> preview`. Show the human the
   packages, what each becomes, warnings, and any `ambiguities` or `blockers`.
2. Resolve every ambiguity with the human. A status that cannot be determined is mapped
   explicitly: `--status-map <package id or slug>=<status>`. Never guess a status. A
   package that is carried over as `accepted` or `rejected` must already record that
   decision with a named human; otherwise the migration stops and asks. Pending audit
   obligations and notes in the old `spec/ACTIVE.md` must have a migrated package to live in;
   if they do not, the migration stops so they are not lost. Text that is not valid UTF-8 is
   refused rather than rewritten lossily.
3. With the human's go-ahead, run the same command with `apply`. It writes
   `.sdp-backup/<timestamp>/` first (the originals and a journal), makes the changes,
   validates every migrated record, and restores everything if validation fails.
4. Tell the human what was voided: any plan that was approved or delivering is restarted as
   `planned` and its approval must be given again, because the approved plan cannot be
   verified.
5. Optional cleanup of copied files: add `--remove-legacy-files
   --confirm-replacement-installed` only after the human confirms the SDP package is
   installed and loads. Only files whose content matches a released file exactly, in a
   project with the old installer's `.github/sdp-version` marker, are moved into the backup.
   Customized copies and APM-managed files are kept.

## Rollback and recovery

- `migrate.py --repo <repo> restore --backup .sdp-backup/<timestamp>` returns every changed
  file to its original content and removes what the migration created. It leaves alone any
  file you changed after migrating and tells you which; move or revert those files and run
  `restore` again to finish.
- `migrate.py --repo <repo> status` reports an interrupted migration. Apply refuses to run
  until it is restored. Roll back the package version together with the project state; do
  not resume schema 4 records with an older version.

## What it never does

- Fabricate or carry over an approval or acceptance it cannot verify. Accepted and rejected
  packages keep their recorded human decision; everything else restarts as `planned`.
- Delete anything: removed files move into the backup.
- Edit product code, `TECH.md`, or shared specs (`PRD.md`, `BACKLOG.md`, `EPIC-*.md`,
  `DESIGN.md`).
- Follow links or junctions out of the repository, or contact the network.

## Quality Bar

- A preview and an apply agree, and a second run reports nothing to do.
- The original run record of each migrated package is preserved as `DELIVERY-RUN.legacy.json`.
- Pending audit obligations survive.
