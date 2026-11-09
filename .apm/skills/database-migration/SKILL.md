---
name: database-migration
description: Guidance for writing safe, reversible database schema migrations. Use when adding or changing a schema, data migration, index, or constraint.
---

# Skill: Write Database Migration

## Purpose

Produce a safe, reviewable, and reversible database schema change that can be deployed without downtime or data loss.

## Prerequisites

- Data model change is defined in the technical design.
- ORM/migration tool is specified in `TECH.md`.
- Existing migrations have been read for naming, ordering, and style conventions.

## Checklist

1.  **One change per migration**: Don't bundle unrelated schema changes. Name it clearly. Never edit a migration that has already been applied or merged; add a new one.
2.  **Plan recovery**: Provide a rollback when the migration technology and
    data semantics make rollback safe. For an approved irreversible operation,
    define backup, forward-fix, and failure recovery instead of a misleading
    down migration.
3.  **Non-nullable columns**: Must have a `DEFAULT` value or a backfill step. Add constraints (foreign keys, uniqueness, checks) in a way that does not rewrite or lock large tables for long.
4.  **Renaming and dropping**: Use a multi-step expand-migrate-contract pattern. Do not rename or drop and deploy in a single step; the previous application version must keep working while the new schema is live.
5.  **Index creation**: Use `CONCURRENTLY` (PostgreSQL) or equivalent to avoid table locks. Index columns that new queries filter or join on.
6.  **Backfills**: Run in batches. Separate data migrations from schema migrations. Make them resumable and safe to run twice.
7.  **Testing**: Run the migration and safe recovery path in a representative
    environment, including against existing data, not only an empty database.
    Verify the schema diff, compatibility window, and data-loss risk. Run the
    application's tests against the migrated schema.

## Quality Bar

- Migration and the approved recovery strategy are verified.
- No data loss occurs and existing rows still satisfy the new constraints.
- The previous application version is compatible with the new schema during rollout.
- CI runs the migration during the test pipeline.
