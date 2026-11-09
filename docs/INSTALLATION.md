# Installation

SDP reaches a project in one of several ways. This page says what each way is, how to pin a
version, what was and was not verified, and how to set up the project afterwards.

## Channels

| Channel | Command | Verification in this repository |
| --- | --- | --- |
| APM | `apm install WojcikMM/spec-development-protocol` | `apm pack` output is built and tested on every change. The hosted install of the `2.0.0-rc.1` prerelease from the fork was exercised (2026-11-09); in a bare project an untargeted install stops with host-detection guidance, so pass `--target` (for example `--target claude`) or install into a project with detected hosts. |
| GitHub Copilot CLI plugin marketplace | `copilot plugin marketplace add WojcikMM/spec-development-protocol`, then `copilot plugin install spec-development-protocol@spec-development-protocol` | Verified only with a local directory registered as the marketplace, which Copilot CLI loads live without copying. A hosted install is not verified. |
| Claude Code marketplace | uses the generated `.claude-plugin/` files | Files are generated and version-checked. Claude Code was not available, so nothing was run. |
| Release ZIP | download from a GitHub release, verify `SHA256SUMS`, extract | The build and its contents are tested. The `2.0.0-rc.1` prerelease was published by the release workflow (2026-11-09) and its ZIP matched a locally built archive byte for byte; the first stable 2.0 release is still pending. |

Nothing here claims that a given host follows the skills during a full delivery; see
[COMPATIBILITY.md](COMPATIBILITY.md) for what was observed.

## APM and native plugins

APM is a package manager for agent files. It resolves a version from a Git tag, records it in a
lockfile in your project, and deploys the files to each host it detects. A native plugin
channel is the host's own mechanism: you register a marketplace (a catalog file in a
repository) and the host installs from it. The package contents are the same; the difference is
who pins the version and where the files land. Prefer one channel per project and do not mix
them.

SDP is not a Visual Studio Code extension and ships no VSIX. A VSIX adds editor features; SDP
adds agents, prompts, instructions, and skills that a host such as GitHub Copilot loads. The
`.apm/templates/` folder cannot be packaged by APM directly, so the templates ship as assets of
the `sdp-templates` skill.

SDP has not been submitted to any curated catalog.

## Stable and prerelease versions

Releases use tags of the form `v<major>.<minor>.<patch>`; a suffix such as `-rc.1` marks a
prerelease. A published prerelease is flagged as such on GitHub and never becomes the latest
release. Pin the version you tested. The released 0.5.x tags contain the stable agents,
prompts, instructions, and six skills only (API, UI, migration, errors, tests, and the template
assets); the `2.0.0-rc.1` prerelease (published 2026-11-09) already ships `sdp-init`,
`sdp-migrate`, the validator, and the workflow skills, and the first stable 2.0 release is
still pending after host qualification.

```bash
apm install WojcikMM/spec-development-protocol#v0.5.4
```

Without a pin you get whatever the channel resolves at that moment, which may be a moving
branch.

## Initialize the project

Installing a package gives you skills and agents; initializing creates the files that belong
to your project. With a version that includes `sdp-init`, use it. (A legacy 0.5.x
script-based copy creates `.github/TECH.md` during installation; the install scripts are
retired and remain only inside the released 0.5.x tags.) `<installed skills>` is the
`skills` folder of the installed package, wherever your channel placed it (in this repository
it is `.apm/skills`, in the ZIP it is `skills/`); find it by looking for the folder that
contains `sdp-init`. Use `python3` where `python` is not available. The skill previews first
and never overwrites:

```bash
python <installed skills>/sdp-init/scripts/init.py --repo .          # preview
python <installed skills>/sdp-init/scripts/init.py --repo . --apply  # create what is missing
```

It creates `.github/TECH.md` from the installed template and an empty `spec/` folder; Git does
not track an empty folder, so commit your first spec file before relying on `spec/` being in
the repository. Then fill in `TECH.md` (stack, commands, conventions, default delivery
profile, security and QA triggers). Add scoped `AGENTS.md` files where they reduce scanning,
starting from the `AGENTS.md` template.

## Updating

- APM: use APM's own update command (see its documentation) and review the lockfile change.
- Native plugin: update through the host.
- ZIP: replace the extracted folder with the newer one.

Update the package version and the project state together. If a release changes the record
format, run [`sdp-migrate`](UPGRADING.md) and keep its backup until you have accepted the
result; do not resume newer records with an older package.

## Manual fallback

Clone or download the repository, create `.github/` in your project, and copy the contents of
`.apm/` into it without overwriting your customizations. Prefer a pinned tag over `main`.

## Requirements

| Requirement | Notes |
| --- | --- |
| Visual Studio Code with the GitHub Copilot extension and Agent Mode | Needed for the stable `/deliver` prompts. A Copilot subscription is required. VS Code was not tested; only GitHub Copilot CLI has any recorded observation. |
| Python 3.9 or newer and Git | For the shipped scripts (validator, init, migration), which use only the standard library. Observed on Python 3.9 (locally), 3.11, 3.12, and 3.13; the GitHub 3.9 CI job passed on run 42222480747. |
| APM | To install through APM: APM's own requirements (its standalone installer, or `pip` with Python 3.10 or newer). To build or pack this package: APM 0.29.0, the version pinned in `scripts/release-tools.json`. |

Without Python the validator-backed schema 4 workflow is blocked with an explicit message;
the stable prompts keep working. The validator checks records and enforces transitions; it is
not a sandbox, approver names are asserted strings, and it cannot prove who reviewed what (see
[PROTOCOL.md](PROTOCOL.md)).

## Ownership and mixed installs

Package files (agents, prompts, instructions, skills) belong to the channel that installed
them. Project files (`TECH.md`, `AGENTS.md`, `spec/`) belong to you and are never overwritten
by SDP tooling. Do not install APM and a native plugin into the same project, and do not mix
a package with leftover 0.5.x script copies: the host then sees two copies. `sdp-init`
reports leftover copies: a `.github/sdp-version` marker means the retired 0.5.x install
scripts ran, and SDP agent files under `.github` with no APM lockfile are reported as
possible plain copies. It deletes nothing. To remove verified legacy copies, use
`sdp-migrate --remove-legacy-files --confirm-replacement-installed` after the new package is
installed and loads; it moves only files that exactly match a released file into a backup.
