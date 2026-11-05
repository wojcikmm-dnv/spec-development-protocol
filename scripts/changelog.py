#!/usr/bin/env python3
"""Release tag validation and changelog section extraction (standard library only).

    python scripts/changelog.py --tag v1.2.3 [--changelog CHANGELOG.md] [--output notes.md]

Prints the section for exactly that version. It never falls back to `Unreleased`, never
picks a neighbouring version, and fails on a missing, duplicated, or empty section.
Headings look like `## [1.2.3]`, `## [v1.2.3]`, or `## [1.2.3] - 2026-01-31`; text after a
dash is ignored. Any other `#` or `##` heading ends a section. Headings inside fenced code
blocks or HTML comments are not headings, and an unterminated fence or comment is an error
rather than a guess. Only ATX headings (`## ...`) are recognized.
"""

import argparse
import re
import sys
from pathlib import Path

SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?\Z")
TOP_HEADING = re.compile(r"^ {0,3}#{1,2}(?!#)(?:[ \t]|$)")
HEADING = re.compile(r"^ {0,3}##[ \t]+\[(?P<name>[^\]]+)\](?:[ \t]*[-\u2013\u2014][ \t]*(?P<rest>.*))?[ \t]*$")
OPEN_FENCE = re.compile(r"^ {0,3}(?:(`{3,})[^`]*|(~{3,}).*)$")
CLOSE_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})[ \t]*$")
REFERENCE_DEFINITION = re.compile(r"^\[[^\]]+\]:[ \t]*\S")


class ChangelogError(Exception):
    pass


def tag_version(tag):
    """The semantic version of a `v<semver>` tag; anything else is refused."""
    if not isinstance(tag, str) or not tag.startswith("v") or not SEMVER.match(tag[1:]):
        raise ChangelogError(f"{tag!r} is not a release tag of the form v<major>.<minor>.<patch>[-prerelease]")
    return tag[1:]


def is_prerelease(version):
    return "-" in version.split("+", 1)[0]


def section_name(line):
    heading = HEADING.match(line)
    if not heading:
        return None
    name = heading.group("name").strip()
    return name[1:] if name.startswith("v") and SEMVER.match(name[1:]) else name


def sections(text):
    """Return [(version or None, body_lines)] in document order; None marks a section that cannot be a release."""
    found, current, fence, in_comment = [], None, None, False
    for line in text.lstrip("\ufeff").split("\n"):
        line = line.rstrip("\r")
        if fence is not None:
            closer = CLOSE_FENCE.match(line)
            if closer and closer.group(1)[0] == fence[0] and len(closer.group(1)) >= len(fence):
                fence = None
        elif in_comment:
            in_comment = "-->" not in line
        elif OPEN_FENCE.match(line):
            fence = (OPEN_FENCE.match(line).group(1) or OPEN_FENCE.match(line).group(2))
        elif line.lstrip().startswith("<!--") and "-->" not in line:
            in_comment = True
        elif TOP_HEADING.match(line):
            current = [section_name(line), []]
            found.append(current)
            continue
        if current is not None:
            current[1].append(line)
    if fence is not None or in_comment:
        raise ChangelogError("CHANGELOG.md has an unterminated code fence or HTML comment")
    return [(version, body) for version, body in found]


def clean(body):
    lines = list(body)
    while lines and (not lines[-1].strip() or lines[-1].strip() == "---" or REFERENCE_DEFINITION.match(lines[-1])):
        lines.pop()
    while lines and not lines[0].strip():
        lines.pop(0)
    return lines


def has_content(lines):
    return any(line.strip() and not line.lstrip().startswith("#") for line in lines)


def extract(text, tag):
    version = tag_version(tag)
    matches = [body for name, body in sections(text) if name == version]
    if not matches:
        raise ChangelogError(f"CHANGELOG.md has no section for {version}")
    if len(matches) > 1:
        raise ChangelogError(f"CHANGELOG.md has {len(matches)} sections for {version}")
    lines = clean(matches[0])
    if not has_content(lines):
        raise ChangelogError(f"the CHANGELOG.md section for {version} is empty")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--changelog", default=str(Path(__file__).resolve().parent.parent / "CHANGELOG.md"))
    parser.add_argument("--output")
    arguments = parser.parse_args(argv)
    try:
        notes = extract(Path(arguments.changelog).read_text(encoding="utf-8"), arguments.tag)
    except (ChangelogError, OSError, UnicodeDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    if arguments.output:
        Path(arguments.output).write_text(notes, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
