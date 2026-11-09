# Copilot Maintainer Instructions - SDP Library

You are maintaining the Spec Development Protocol (SDP) template repository.

## Repository Model

- Source files for distribution are stored in `.apm/`.
- Client projects receive these files by installing the package through APM or a native
  plugin channel; the legacy `install.sh`/`install.ps1` installers were retired in Step 13.
- This repository's own `.github/` folder is for maintainer workflow and automation only.

## Primary Goal

Keep the library consistent, versionable, and safe to reuse across projects.
Every change must preserve the contract:

- `.apm/*` is the canonical template source.
- Distribution reaches clients through APM and native plugin channels only.

## Change Flow (Required)

1. Identify the requested change and map it to one or more areas:
	 - Template content (`.apm/agents`, `.apm/prompts`, `.apm/instructions`, `.apm/skills`, `.apm/templates`)
	 - User documentation (`README.md`, `docs/`)
2. Implement content changes in `.apm/` first (never in repository `.github/` as template source).
3. Update `README.md` whenever behavior, structure, commands, or setup expectations change.
4. Validate and summarize what changed and why.

## Mandatory Sync Rules

When any of the following happens, updates are required:

- New file/folder added in `.apm/`:
	- Update `README.md` structure or usage sections if users should know about it.
	- Verify packaging still includes it in the distribution bundles.
- File/folder renamed/moved in `.apm/`:
	- Update all affected paths in `README.md` and `docs/`.
- Install or update behavior changed:
	- Update the channel and setup sections in `README.md` and `docs/INSTALLATION.md`.
- Runtime expectations changed (for example, TECH initialization, migration behavior):
	- Update `README.md`, `docs/INSTALLATION.md`, and affected docs.

Do not leave behavior and docs out of sync.

## Standards for New Files

- Use clear, explicit naming aligned with SDP terms.
- Keep templates generic and reusable across greenfield and legacy projects.
- Prefer practical instructions over vague principles.
- Preserve gate discipline and traceability across PRD -> backlog -> design -> plan -> implementation -> hardening.
- Use ASCII by default.

## Safety and Compatibility

- Do not delete or overwrite unrelated user files in client repositories.
- Initialization and migration behavior must remain non-destructive by default.
- Destructive operations must stay explicit and consent-gated.

## Validation Checklist (Run Before Finishing)

1. `bash scripts/check-all.sh` passes (the CI entry point).
2. New/changed paths in `.apm/` are correctly reflected in documentation and packaging.
3. `README.md` and `docs/` examples match actual behavior.
4. If install or update guidance changed, the corresponding messages remain accurate.

## Output Expectations for Maintainer Tasks

When completing a change, always report:

- What changed in `.apm/`
- Whether `README.md` and `docs/` were updated
- Why each update was or was not required
