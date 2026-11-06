#!/usr/bin/env python3
"""Run test suites and, on GitHub Actions, turn every failure into a public annotation.

    python scripts/run-suites.py contracts init migrate

Job logs need a sign-in to read; annotations do not, so a failing run stays diagnosable.
Standard library only; works on Python 3.9.
"""

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAIL_LINES = 14


def escape(text):
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def annotate(suite, test, trace):
    tail = "\n".join(trace.strip().splitlines()[-TAIL_LINES:])
    print(f"::error title={escape(suite)}%3A {escape(str(test))[:150]}::{escape(tail)[:3000]}")


def run(suite):
    directory = str(ROOT / "tests" / suite)
    sys.path.insert(0, directory)
    try:
        tests = unittest.defaultTestLoader.discover(directory, top_level_dir=directory)
        result = unittest.TextTestRunner(verbosity=1).run(tests)
    finally:
        sys.path.remove(directory)
    if os.environ.get("GITHUB_ACTIONS"):
        for test, trace in result.failures + result.errors:
            annotate(suite, test, trace)
    return result.wasSuccessful()


def main(argv):
    if not argv:
        print("usage: run-suites.py <suite> [<suite> ...]", file=sys.stderr)
        return 2
    ok = True
    for suite in argv:
        print(f"== tests/{suite}", flush=True)
        ok = run(suite) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
