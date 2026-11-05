# Spec Development Protocol {version} - Release ZIP

This archive is the plugin bundle produced by `apm pack`: agents, prompts (as `commands/`),
instructions, and skills. Use it when you cannot install through APM or a marketplace.

## Use

1. Verify the download. The release publishes `SHA256SUMS`; compare it with the archive
   (`sha256sum -c SHA256SUMS`, or `Get-FileHash <file> -Algorithm SHA256` on Windows). This
   confirms the file arrived intact; it does not prove who published it.
2. Extract the archive to a folder you control. It contains nothing outside its top-level
   folder.
3. Point your agent host at the extracted folder as a plugin. Only GitHub Copilot CLI has been
   tested (`copilot --plugin-dir <folder>`). Nothing else was run; see `docs/COMPATIBILITY.md`
   in the repository for what was and was not observed.
4. Initialize a project with the `sdp-init` skill (`skills/sdp-init/scripts/init.py`). It
   previews first and never overwrites existing files.

The skill scripts use only the Python standard library and are written for Python 3.9 or
newer; they were run on 3.11 through 3.13.

## Upgrading an earlier project

Projects set up with SDP 0.5.3 or 0.5.4 can be moved to the current layout with the
`sdp-migrate` skill. It previews, keeps a backup, and never invents an approval. Commit or
back up your work first.

## License

MIT; see `LICENSE`.
