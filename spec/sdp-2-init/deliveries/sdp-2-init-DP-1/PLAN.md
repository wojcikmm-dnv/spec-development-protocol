---
status: approved
approved_by: user (chat instruction to continue the roadmap in order)
approved_at: 2026-11-05T19:00:00+01:00
---

# Step 07: Non-Destructive Initialization

## Outcome and Boundary

Provide project setup without the legacy installers: a standard-library initializer
skill, `sdp-init`, that previews, then creates only the project-owned files that are
missing. Installation of the package stays separate. The installers are unchanged.

- Size: M; risk: High (writes user files, path safety, trust of templates); uncertainty:
  Resolved. Profile: Balanced with independent review. Security: required and run.
  QA: fresh, customized, legacy, read-only, link, race, and failure fixtures plus real
  packed and APM-installed layouts.

## Acceptance Criteria

1. Preview is the default and writes nothing; `--apply` creates only missing
   `.github/TECH.md` and `spec/`; a second run changes nothing.
2. Existing TECH, specs, run records, history, and unrelated `.github` content are
   preserved byte for byte.
3. Symbolic links, Windows junctions, path conflicts, and locations outside the
   repository are refused with nothing written; anything created is rolled back on
   failure.
4. Copied files from the old installer are reported, never removed, without false
   alarms for APM-managed files.
5. Templates never come from the repository being initialized.
6. It works from the APM-installed and plugin-installed layouts.

## Allowed Paths

`.apm/skills/sdp-init/**`, `tests/init/**`, `README.md`, `CHANGELOG.md`, this
package's records. No change to the installers.
