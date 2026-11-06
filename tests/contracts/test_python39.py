import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHIPPED = sorted((ROOT / ".apm" / "skills").glob("*/scripts/*.py"))
# Calls whose keyword arguments exist only from Python 3.10.
NEEDS_310 = {("write_text", "newline"), ("read_text", "newline"), ("zip", "strict"), ("open_text", "newline")}


class Python39Tests(unittest.TestCase):
    def test_there_are_shipped_scripts_to_check(self):
        self.assertGreaterEqual(len(SHIPPED), 4)

    def test_shipped_scripts_parse_as_python_39(self):
        for script in SHIPPED:
            with self.subTest(script=script.name):
                ast.parse(script.read_text(encoding="utf-8"), filename=str(script), feature_version=(3, 9))

    def test_shipped_scripts_do_not_use_keyword_arguments_that_need_python_310(self):
        for script in SHIPPED:
            tree = ast.parse(script.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
                for keyword in node.keywords:
                    with self.subTest(script=script.name, line=node.lineno):
                        self.assertNotIn((name, keyword.arg), NEEDS_310, f"{script.name}:{node.lineno} {name}({keyword.arg}=...) needs Python 3.10")


if __name__ == "__main__":
    unittest.main()
