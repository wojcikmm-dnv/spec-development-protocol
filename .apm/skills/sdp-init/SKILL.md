---
name: sdp-init
description: Initializes a repository for SDP without overwriting anything. Use when setting up SDP in a new or existing project, after installing the SDP package, or when asked to create the project policy file and spec folder; previews first, creates only what is missing, and reports leftover files from earlier installers.
---

# Initialize a Project

## Purpose

Installing the SDP package gives you skills and agents. Initializing a project creates
the few files that belong to the project itself. This is separate from installation and
never overwrites your work.

## Prerequisites

- The SDP package is installed, so the `sdp-templates` skill exists next to this one.
- Python 3.9 or newer. Git is needed later by the validator.

## Procedure

1. Run `python <this skill>/scripts/init.py --repo <repo>`. It previews and writes
   nothing. Show the human the plan.
2. If it lists `conflicts` (a symbolic link, a path that is a file where a folder is
   needed, or a location outside the repository), stop and report them. Nothing was
   changed.
3. If it lists `warnings`, read them to the human. A `legacy_files` warning means copied
   files from an earlier installer exist; do not delete them and do not run both setups.
4. With the human's go-ahead, run the same command with `--apply`. It creates
   `.github/TECH.md` from the template and an empty `spec/` folder, only where missing,
   and removes anything it created if a step fails.
5. Tell the human to fill in `.github/TECH.md`: stack, commands, conventions, and the
   delivery policy. Running the script again is safe and changes nothing.

## What it never does

- Overwrite or edit an existing `TECH.md`, `spec/`, specs, run records, or history.
- Delete files, including leftovers from earlier installers.
- Follow symbolic links or junctions out of the repository or write outside it.
- Take templates from the repository being initialized. A cloned repository is not
  trusted, and `TECH.md` is later read by agents as instructions, so the template
  always comes from the installed package (or a directory you pass explicitly).
- Install packages or contact the network.

## Limits

It re-checks each destination immediately before writing and refuses if anything
changed since the preview, but a person with write access to the repository can still
race those checks within a very small window; it is not a sandbox. Review
`.github/TECH.md` like any instruction file before relying on it.

## Quality Bar

- A preview and an `--apply` run agree.
- A second run reports nothing to do.
- Existing project files are byte-for-byte unchanged.
