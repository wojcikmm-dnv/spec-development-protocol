#!/usr/bin/env bash
# Every repository check that CI and the release workflow rely on, in one place.
# Needs python (3.10+), git, the apm version pinned in scripts/release-tools.json, PyYAML and jsonschema.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export PYTHONDONTWRITEBYTECODE=1

bash -n install.sh
bash scripts/sync-templates.sh --check
python scripts/check-baseline.py --self-test
python scripts/check-baseline.py
python scripts/check-skills.py
python scripts/build-release.py --check
for suite in contracts skills init migrate packaging release; do
  echo "== tests/${suite}"
  python -m unittest discover -s "tests/${suite}"
done
# The checks must leave the checkout exactly as they found it, or a release could pack files that are not in the tag.
if [ -n "$(git status --porcelain --untracked-files=all)" ]; then
  echo "The checks changed the working tree:" >&2
  git status --short --untracked-files=all >&2
  exit 1
fi
