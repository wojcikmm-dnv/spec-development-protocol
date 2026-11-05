#!/usr/bin/env python3
"""Grade a stage result against an SDP skill evaluation case (standard library only).

This checks a submitted result against expected verdict, finding patterns, and
triggers. It does not run a model; run the skill in your host first, then grade
what it returned.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITIES = ("Critical", "High", "Medium", "Low")


def _texts(result):
    parts = [*result.get("findings", []), result.get("reason") or "", result.get("next_action") or ""]
    return [part for part in parts if part]


def _severity_rank(finding):
    match = re.match(r"\s*(Critical|High|Medium|Low)\b", finding)
    return SEVERITIES.index(match.group(1)) if match else len(SEVERITIES)


def grade(case, result):
    """Return a list of failure strings; empty means the result satisfies the case."""
    expect = case["expect"]
    failures = []
    if result.get("verdict") != expect["verdict"]:
        failures.append(f"verdict is {result.get('verdict')!r}, expected {expect['verdict']!r}")
    texts = _texts(result)
    for pattern in expect.get("finding_patterns", []):
        if not any(re.search(pattern, text, re.IGNORECASE) for text in texts):
            failures.append(f"no finding matches /{pattern}/")
    for pattern in expect.get("forbidden_patterns", []):
        if any(re.search(pattern, text, re.IGNORECASE) for text in texts):
            failures.append(f"a finding matches forbidden /{pattern}/")
    missing = set(expect.get("triggers", [])) - set(result.get("detected_triggers", []))
    if missing:
        failures.append(f"missing triggers: {', '.join(sorted(missing))}")
    minimum = expect.get("min_severity")
    if minimum and not any(_severity_rank(f) <= SEVERITIES.index(minimum) for f in result.get("findings", [])):
        failures.append(f"no finding at {minimum} severity or higher")
    if result.get("verdict") == "fail" and not result.get("findings"):
        failures.append("a fail needs at least one finding")
    if result.get("verdict") == "not_applicable" and not result.get("reason"):
        failures.append("not_applicable needs a reason")
    return failures


def load_cases(path):
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    return document, {case["id"]: case for case in document["cases"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True, help="path to a skill's evals/cases.json")
    parser.add_argument("--case", required=True, help="case id")
    parser.add_argument("--result", required=True, help="path to a JSON stage result")
    arguments = parser.parse_args(argv)
    try:
        _, cases = load_cases(arguments.cases)
        case = cases[arguments.case]
        result = json.loads(Path(arguments.result).read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError) as error:
        print(f"FAIL: cannot load input: {error}", file=sys.stderr)
        return 2
    failures = grade(case, result)
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    if not failures:
        print(f"PASS: {arguments.case}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
