# Local Cross-OS Archive Verification History

## 2026-11-06 - Awaiting Acceptance

Built the same committed candidate on Windows and WSL Linux using the existing
release builder and pinned APM, then updated the release guide with the bounded
evidence. Added one regression test to the existing documentation test module.

### Build Evidence

- Commit: `e7908dee783ea8a18275c826d6c413f6e25f6e29`.
- Package version: `0.5.4`; APM version: `0.29.0` on both platforms.
- Both builds used `scripts/build-release.py --revision` with that full commit
  and succeeded, including clean-revision and bundle verification.
- Both ZIPs produced SHA-256
  `88757e6cfbc291fb6179e8764939ec4878f505721ffe804fc435181b305eb215`.
- Independent checksum commands: Windows `Get-FileHash -Algorithm SHA256` and
  WSL `sha256sum` agreed with the builder results.
- Windows scratch output: `%TEMP%/sdp-cross-os-20261106-1430/output`.
- Linux scratch output: `/var/tmp/sdp-cross-os-20261106-1430/output`.

The Linux environment was isolated under the same `/var/tmp` scratch folder.
`python3 -m venv --without-pip` plus system pip's `--python` option installed
`apm-cli==0.29.0` there; no system packages or repository dependencies were changed.

### Validation and Review

- Focused documentation suite: 22 tests passed.
- Shell installer syntax and whitespace checks passed.
- Independent read-only technical review returned pass with no material findings.
  It inspected evidence wording, test coverage, and builder verification behavior;
  it did not independently run the builds, GitHub release workflow, or agent hosts.

### Environment and Candidate Checks

The initial WSL environment lacked `ensurepip`; the isolated setup above resolved
that without administrator installation. A scratch directory under `/tmp` became
unavailable between commands; the successful build used `/var/tmp` instead.

The first Windows build correctly refused an outdated requested revision:
the repository had advanced to `e7908dee`. Both successful builds used the new
verified commit; the existing repository commit was preserved. These setup and
revision-check failures did not reject an implementation candidate.

### Limits and Ownership

This is one observed comparison, not a guarantee for future candidates, tooling,
or the actual GitHub release runner. Hosted publication, immutable catalog revision
selection, and full agent delivery remain unverified.

No `.apm/`, README, or installer changes were needed: installation behavior is
unchanged. No commits, pushes, tags, releases, removals, or paid AI trials were made.
Temporary build artifacts are retained at the scratch locations above.

Acceptance is pending an explicit human decision. External rehearsal obligations
remain with their owning packages; this package does not close them.