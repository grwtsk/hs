"""Synthetic range/format regressions plus read-only binding to the public archive.

No private manuscript, participant particulars, or medical source is a fixture.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("nav_check", ROOT / "tools/book/check_edit_navigation.py")
assert spec is not None and spec.loader is not None
nav = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nav)


def fixture():
    data = "Synthetic question?\nSynthetic café.\n\nSynthetic ending.".encode()
    offset, rows = 0, []
    for line_number, line in enumerate(data.split(b"\n"), 1):
        if line:
            rows.append(dict(id=f"SYNTHETIC-P{len(rows)+1:02d}", line=line_number,
                             byte_start=offset, byte_end=offset+len(line),
                             sha256=hashlib.sha256(line).hexdigest()))
        offset += len(line) + 1
    return data, rows


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.data, self.rows = fixture()

    def rejects(self, rows, data=None):
        with self.assertRaises((nav.NavigationError, UnicodeError)):
            nav.validate_ranges(self.data if data is None else data, rows, "SYNTHETIC")

    def test_actual_frozen_binding(self):
        nav.check(ROOT)

    def test_actual_cli(self):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "tools/book/check_edit_navigation.py"), "check"], capture_output=True, text=True, timeout=10, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("authority=none", result.stdout)

    def test_synthetic_complete_utf8(self):
        nav.validate_ranges(self.data, self.rows, "SYNTHETIC")

    def test_missing_intro(self):
        self.rejects(self.rows[1:])

    def test_duplicate_id(self):
        self.rows[1]["id"] = self.rows[0]["id"]
        self.rejects(self.rows)

    def test_reordered_spans(self):
        self.rejects(self.rows[::-1])

    def test_wrong_line(self):
        self.rows[-1]["line"] -= 1
        self.rejects(self.rows)

    def test_boolean_is_not_integer(self):
        self.rows[0]["line"] = True
        self.rejects(self.rows)

    def test_character_offset_is_not_utf8_offset(self):
        self.rows[1]["byte_end"] -= 1
        self.rejects(self.rows)

    def test_overlap(self):
        self.rows[1]["byte_start"] = self.rows[0]["byte_end"] - 1
        self.rejects(self.rows)

    def test_payload_gap(self):
        self.rows[1]["byte_start"] += 1
        self.rejects(self.rows)

    def test_lf_is_not_payload(self):
        self.rows[0]["byte_end"] += 1
        self.rejects(self.rows)

    def test_wrong_digest(self):
        self.rows[0]["sha256"] = "0" * 64
        self.rejects(self.rows)

    def test_extra_approval_field(self):
        self.rows[0]["human_approved"] = True
        self.rejects(self.rows)

    def test_malformed_row(self):
        self.rows[0] = None
        self.rejects(self.rows)

    def test_empty_rows(self):
        self.rejects([])

    def test_invalid_utf8(self):
        self.rejects(self.rows, b"\xff")

    def test_crlf(self):
        self.rejects(self.rows, self.data.replace(b"\n", b"\r\n"))

    def test_duplicate_json_keys(self):
        with self.assertRaises(nav.NavigationError):
            json.loads('{"synthetic":1,"synthetic":2}', object_pairs_hook=nav.unique)

    def test_nonfinite_json(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token), self.assertRaises(nav.NavigationError):
                json.loads('{"synthetic":'+token+'}', parse_constant=nav.nonfinite)

    def test_oversize_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "synthetic.txt").write_bytes(b"x" * (nav.LIMIT + 1))
            with self.assertRaises(nav.NavigationError):
                nav.read(root, "synthetic.txt")

    def test_symlink_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "synthetic.txt").write_text("Synthetic only.")
            (root / "alias.txt").symlink_to(root / "synthetic.txt")
            with self.assertRaises(nav.NavigationError):
                nav.read(root, "alias.txt")

    def test_path_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "inside"
            root.mkdir()
            (root.parent / "synthetic.txt").write_text("Synthetic only.")
            with self.assertRaises(nav.NavigationError):
                nav.read(root, "../synthetic.txt")


if __name__ == "__main__":
    unittest.main()
