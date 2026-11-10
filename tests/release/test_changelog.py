import importlib.util
import io
import contextlib
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("changelog", ROOT / "scripts" / "changelog.py")
changelog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(changelog)

SAMPLE = """# Changelog

## [Unreleased]

### Added

- Work in progress.

## [3.0.0] - 2027-03-01

- Newer than the tag under test.

## [2.0.0] - 2027-01-15

### Added

- Two point zero.

---

## [2.0.0-rc.1] - 2027-01-01

- Release candidate.

## [v1.0.0]

- Old style heading.

## [0.1.0] \u2014 Initial release

- First.

[2.0.0]: https://example.invalid/2.0.0
"""


class TagTests(unittest.TestCase):
    def test_valid_tags(self):
        for tag, version in (("v1.2.3", "1.2.3"), ("v0.0.1", "0.0.1"), ("v2.0.0-rc.1", "2.0.0-rc.1"), ("v1.0.0+build.5", "1.0.0+build.5")):
            self.assertEqual(version, changelog.tag_version(tag))

    def test_invalid_tags_are_refused(self):
        for tag in ("1.2.3", "V1.2.3", "v1.2", "v01.2.3", "v1.2.3.4", "vlatest", "v", "", "v1.2.3 ", "v1.2.3\n", None, "refs/tags/v1.2.3"):
            with self.subTest(tag=tag), self.assertRaises(changelog.ChangelogError):
                changelog.tag_version(tag)

    def test_prerelease_detection_ignores_build_metadata(self):
        self.assertTrue(changelog.is_prerelease("2.0.0-rc.1"))
        self.assertTrue(changelog.is_prerelease("2.0.0-rc.1+build"))
        self.assertFalse(changelog.is_prerelease("2.0.0"))
        self.assertFalse(changelog.is_prerelease("2.0.0+meta-data"))

    def test_the_version_pattern_matches_the_release_builder(self):
        builder = importlib.util.spec_from_file_location("build_release", ROOT / "scripts" / "build-release.py")
        module = importlib.util.module_from_spec(builder)
        builder.loader.exec_module(module)
        self.assertEqual(changelog.SEMVER.pattern, module.SEMVER.pattern)


class ExtractTests(unittest.TestCase):
    def test_extracts_exactly_the_requested_section(self):
        notes = changelog.extract(SAMPLE, "v2.0.0")
        self.assertIn("Two point zero.", notes)
        self.assertNotIn("Release candidate", notes)
        self.assertNotIn("Newer than the tag", notes)
        self.assertNotIn("Work in progress", notes)

    def test_trailing_rule_and_reference_links_are_trimmed(self):
        notes = changelog.extract(SAMPLE, "v2.0.0")
        self.assertFalse(notes.rstrip().endswith("---"))
        last = changelog.extract(SAMPLE, "v0.1.0")
        self.assertNotIn("example.invalid", last)
        self.assertTrue(last.endswith("- First.\n"))

    def test_prerelease_is_separate_from_its_stable_version(self):
        self.assertIn("Release candidate", changelog.extract(SAMPLE, "v2.0.0-rc.1"))
        self.assertNotIn("Two point zero", changelog.extract(SAMPLE, "v2.0.0-rc.1"))

    def test_optional_date_v_prefix_and_trailing_text_are_accepted(self):
        self.assertIn("Old style heading", changelog.extract(SAMPLE, "v1.0.0"))
        self.assertIn("First.", changelog.extract(SAMPLE, "v0.1.0"))
        self.assertIn("Newer", changelog.extract(SAMPLE, "v3.0.0"))

    def test_unreleased_is_never_used(self):
        text = "## [Unreleased]\n\n- Not shipped.\n"
        for tag in ("v1.0.0", "v0.0.0"):
            with self.subTest(tag=tag), self.assertRaises(changelog.ChangelogError):
                changelog.extract(text, tag)

    def test_missing_section_is_an_error_not_a_neighbour(self):
        with self.assertRaises(changelog.ChangelogError) as raised:
            changelog.extract(SAMPLE, "v2.0.1")
        self.assertIn("no section for 2.0.1", str(raised.exception))

    def test_duplicate_sections_are_an_error(self):
        text = "## [1.0.0]\n\n- a\n\n## [v1.0.0] - 2027-01-01\n\n- b\n"
        with self.assertRaises(changelog.ChangelogError) as raised:
            changelog.extract(text, "v1.0.0")
        self.assertIn("2 sections", str(raised.exception))

    def test_empty_sections_are_an_error(self):
        for body in ("", "\n\n", "### Added\n\n### Fixed\n", "---\n", "[1.0.0]: https://example.invalid\n"):
            with self.subTest(body=body), self.assertRaises(changelog.ChangelogError):
                changelog.extract(f"## [1.0.0] - 2027-01-01\n{body}\n## [0.9.0]\n\n- real\n", "v1.0.0")

    def test_headings_inside_code_fences_do_not_split_a_section(self):
        text = "## [1.0.0]\n\nExample:\n\n```markdown\n## [9.9.9]\n\n- fake\n```\n\nAfter the fence.\n\n## [0.9.0]\n\n- old\n"
        notes = changelog.extract(text, "v1.0.0")
        self.assertIn("## [9.9.9]", notes)
        self.assertIn("After the fence.", notes)
        self.assertNotIn("old", notes)
        with self.assertRaises(changelog.ChangelogError):
            changelog.extract(text, "v9.9.9")

    def test_tilde_fences_and_longer_closers_work(self):
        text = "## [1.0.0]\n\n~~~\n## [9.9.9]\n~~~\n\n````\n```\n## [8.8.8]\n````\n\n- done\n\n## [0.9.0]\n\n- old\n"
        notes = changelog.extract(text, "v1.0.0")
        self.assertIn("- done", notes)
        self.assertIn("## [8.8.8]", notes)
        self.assertNotIn("old", notes)

    def test_a_fence_is_only_closed_by_its_own_kind(self):
        text = "## [1.0.0]\n\n```\n~~~\n## [0.9.0]\n\n- inside\n```\n\n- tail\n\n## [0.8.0]\n\n- old\n"
        notes = changelog.extract(text, "v1.0.0")
        self.assertIn("- inside", notes)
        self.assertIn("- tail", notes)
        self.assertNotIn("old", notes)

    def test_other_second_level_headings_end_a_section(self):
        notes = changelog.extract("## [1.0.0]\n\n- keep\n\n## Notes\n\n- not part\n", "v1.0.0")
        self.assertIn("keep", notes)
        self.assertNotIn("not part", notes)

    def test_headings_with_extra_words_and_no_dash_do_not_match(self):
        with self.assertRaises(changelog.ChangelogError):
            changelog.extract("## [1.0.0] final\n\n- x\n", "v1.0.0")

    def test_subsections_stay_inside_their_version(self):
        notes = changelog.extract(SAMPLE, "v2.0.0")
        self.assertIn("### Added", notes)

    def test_windows_line_endings(self):
        notes = changelog.extract(SAMPLE.replace("\n", "\r\n"), "v2.0.0")
        self.assertIn("Two point zero.", notes)
        self.assertNotIn("\r", notes)

    def test_headings_indented_up_to_three_spaces_still_end_a_section_and_four_do_not(self):
        for indent, ends in ((" ", True), ("   ", True), ("    ", False)):
            with self.subTest(indent=len(indent)):
                notes = changelog.extract(f"## [1.0.0]\n\n- keep\n\n{indent}## [0.9.0]\n\n- other\n", "v1.0.0")
                self.assertEqual(ends, "other" not in notes)

    def test_a_top_level_heading_after_the_last_section_ends_it(self):
        notes = changelog.extract("## [1.0.0]\n\n- keep\n\n# Appendix\n\n- not release notes\n", "v1.0.0")
        self.assertNotIn("Appendix", notes)

    def test_unterminated_fences_and_comments_are_errors_not_guesses(self):
        for text in ("## [1.0.0]\n\n```\n- code\n\n## [0.9.0]\n\n- old\n", "## [1.0.0]\n\n<!--\n- hidden\n\n## [0.9.0]\n\n- old\n"):
            with self.subTest(text=text[:30]), self.assertRaises(changelog.ChangelogError):
                changelog.extract(text, "v1.0.0")

    def test_a_backtick_in_the_info_string_means_it_is_not_a_fence(self):
        notes = changelog.extract("## [1.0.0]\n\n``` a`b\n\n- keep\n\n## [0.9.0]\n\n- old\n", "v1.0.0")
        self.assertIn("keep", notes)
        self.assertNotIn("old", notes)

    def test_headings_inside_html_comments_are_ignored(self):
        notes = changelog.extract("## [1.0.0]\n\n<!--\n## [9.9.9]\n-->\n\n- keep\n\n## [0.9.0]\n\n- old\n", "v1.0.0")
        self.assertIn("## [9.9.9]", notes)
        self.assertIn("keep", notes)

    def test_unicode_line_separators_never_create_headings_and_are_preserved(self):
        for separator in ("\u2028", "\x85", "\x0c", "\u2029"):
            with self.subTest(separator=repr(separator)):
                notes = changelog.extract(f"## [1.0.0]\n\n- two{separator}## [0.9.0]\n\n- more\n", "v1.0.0")
                self.assertIn(separator, notes)
                self.assertIn("more", notes)

    def test_non_ascii_digits_are_not_versions(self):
        with self.assertRaises(changelog.ChangelogError):
            changelog.tag_version("v1\u0660.0.0")

    def test_a_byte_order_mark_does_not_hide_the_first_heading(self):
        self.assertIn("- a", changelog.extract("\ufeff## [1.0.0]\n\n- a\n", "v1.0.0"))

    def test_the_real_changelog_has_extractable_history(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        for tag in ("v0.6.0", "v0.5.4", "v0.5.3", "v0.1.0"):
            with self.subTest(tag=tag):
                self.assertTrue(changelog.extract(text, tag).strip())
        with self.assertRaises(changelog.ChangelogError):
            changelog.extract(text, "v9.9.9")


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = Path(self.tmp.name) / "CHANGELOG.md"
        self.log.write_text(SAMPLE, encoding="utf-8")

    def run_main(self, *arguments):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = changelog.main(["--changelog", str(self.log), *arguments])
        return code, out.getvalue(), err.getvalue()

    def test_prints_notes(self):
        code, out, _ = self.run_main("--tag", "v2.0.0")
        self.assertEqual(0, code)
        self.assertIn("Two point zero.", out)

    def test_writes_a_file(self):
        target = Path(self.tmp.name) / "notes.md"
        code, out, _ = self.run_main("--tag", "v2.0.0", "--output", str(target))
        self.assertEqual((0, ""), (code, out))
        self.assertIn("Two point zero.", target.read_text(encoding="utf-8"))

    def test_failures_exit_nonzero_and_write_nothing(self):
        target = Path(self.tmp.name) / "notes.md"
        for tag in ("v7.7.7", "7.7.7", "[Unreleased]"):
            with self.subTest(tag=tag):
                code, out, err = self.run_main("--tag", tag, "--output", str(target))
                self.assertEqual(1, code)
                self.assertIn("FAIL", err)
                self.assertFalse(target.exists())

    def test_missing_changelog_is_reported(self):
        self.log.unlink()
        code, _, err = self.run_main("--tag", "v2.0.0")
        self.assertEqual(1, code)
        self.assertIn("FAIL", err)


if __name__ == "__main__":
    unittest.main()
