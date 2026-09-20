"""Synthetic regressions for source identity; no philosophical approval tests."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/book/check_founding_source.py"
spec = importlib.util.spec_from_file_location("founding_source", SCRIPT)
assert spec is not None and spec.loader is not None
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


class ArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in (archive.SOURCE, archive.MANIFEST, archive.INDEX):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def change_manifest(self, **changes: object) -> None:
        path = self.root / archive.MANIFEST
        value = json.loads(path.read_bytes())
        value.update(changes)
        path.write_text(json.dumps(value) + "\n", encoding="utf-8")

    def reject(self, expected: str) -> None:
        with self.assertRaisesRegex(archive.ArchiveError, expected):
            archive.check(self.root)

    def cli(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), *args, "--root", str(self.root)],
            capture_output=True, timeout=10, check=False,
        )

    def test_frozen_identity_and_coverage(self) -> None:
        data, rows = archive.check(self.root)
        self.assertEqual(archive.sha256(data), archive.EXPECTED_SHA256)
        self.assertEqual(len(data), 17779)
        self.assertEqual(len(rows), 115)
        self.assertEqual(sum(r["kind"] == "paragraph" for r in rows), 104)
        self.assertEqual(sum(r["kind"] == "heading" for r in rows), 10)
        self.assertEqual([r["id"] for r in rows],
                         [f"HS-U01-B{i:03d}" for i in range(1, 116)])
        self.assertEqual([r["section"] for r in rows[-2:]], ["ADDENDUM"] * 2)

    def test_every_nonblank_line_is_addressed_exactly_once(self) -> None:
        data, rows = archive.check(self.root)
        lines = data.split(b"\n")
        coverage: list[int] = []
        for row in rows:
            coverage.extend(range(row["line_start"], row["line_end"] + 1))
            block = data[row["byte_start"]:row["byte_end"]]
            expected = b"\n".join(lines[row["line_start"] - 1:row["line_end"]])
            self.assertEqual(block, expected)
            self.assertEqual(archive.sha256(block), row["sha256"])
        nonblank = [i for i, line in enumerate(lines, 1) if line.strip(b" \t")]
        self.assertEqual(coverage, nonblank)
        self.assertEqual(rows[0]["byte_start"], 0)
        self.assertEqual(rows[-1]["byte_end"], len(data))

    def test_original_whitespace_and_spelling_retained(self) -> None:
        data, _ = archive.check(self.root)
        self.assertTrue(data.startswith(b"# Noeaaeue Hs\n \n"))
        self.assertFalse(data.endswith(b"\n"))
        self.assertIn(b"Every boundary in Noeoueeue", data)
        self.assertIn(b"computative bit torrants striped of tensors", data)
        self.assertIn(b"1/(2\\pi)", data)

    def test_unicode_offsets_are_bytes_not_character_offsets(self) -> None:
        data, rows = archive.check(self.root)
        line = next(r for r in rows if "144" in
                    data[r["byte_start"]:r["byte_end"]].decode("utf-8"))
        block = data[line["byte_start"]:line["byte_end"]]
        self.assertIn("144 × 144".encode(), block)
        self.assertGreater(line["byte_end"], len(data[:line["byte_end"]].decode()))

    def test_source_edit_rejected(self) -> None:
        path = self.root / archive.SOURCE
        path.write_bytes(path.read_bytes().replace(b"144", b"145", 1))
        self.reject("SOURCE_BYTES_CHANGED")

    def test_final_newline_added_rejected(self) -> None:
        path = self.root / archive.SOURCE
        path.write_bytes(path.read_bytes() + b"\n")
        self.reject("SOURCE_BYTES_CHANGED")

    def test_whitespace_normalization_rejected(self) -> None:
        path = self.root / archive.SOURCE
        path.write_bytes(path.read_bytes().replace(b"\n \n", b"\n\n", 1))
        self.reject("SOURCE_BYTES_CHANGED")

    def test_crlf_rewrite_rejected(self) -> None:
        path = self.root / archive.SOURCE
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.reject("SOURCE_BYTES_CHANGED")

    def test_missing_addendum_rejected(self) -> None:
        path = self.root / archive.SOURCE
        path.write_bytes(path.read_bytes().split(b"\n\nWhen content manifests", 1)[0])
        self.reject("SOURCE_BYTES_CHANGED")

    def test_coedited_source_and_manifest_not_rebased(self) -> None:
        path = self.root / archive.SOURCE
        data = path.read_bytes().replace(b"144", b"145", 1)
        path.write_bytes(data)
        self.change_manifest(sha256=archive.sha256(data), byte_length=len(data))
        self.reject("MANIFEST_IDENTITY_OR_ROLE_CHANGED")

    def test_wrong_source_identity_rejected(self) -> None:
        self.change_manifest(source_id="HS-U02")
        self.reject("MANIFEST_IDENTITY_OR_ROLE_CHANGED")

    def test_manifest_path_cannot_redirect_reader(self) -> None:
        self.change_manifest(path="../../outside")
        self.reject("MANIFEST_IDENTITY_OR_ROLE_CHANGED")

    def test_preservation_does_not_become_approval(self) -> None:
        self.change_manifest(authority_effect="philosophy_accepted")
        self.reject("MANIFEST_IDENTITY_OR_ROLE_CHANGED")

    def test_bool_schema_version_rejected(self) -> None:
        self.change_manifest(schema_version=True)
        self.reject("UNSUPPORTED_MANIFEST")

    def test_duplicate_manifest_key_rejected(self) -> None:
        path = self.root / archive.MANIFEST
        raw = path.read_text(encoding="utf-8")
        path.write_text(raw.replace('"schema_version": 1,',
                                   '"schema_version": 1, "schema_version": 1,', 1),
                        encoding="utf-8")
        self.reject("DUPLICATE_MANIFEST_KEY")

    def test_nonfinite_manifest_value_rejected(self) -> None:
        path = self.root / archive.MANIFEST
        path.write_text('{"schema_version": NaN}', encoding="utf-8")
        self.reject("NONFINITE_MANIFEST_VALUE")

    def test_changed_passage_count_rejected(self) -> None:
        self.change_manifest(passage_count=114)
        self.reject("PASSAGE_COUNT_CHANGED")

    def test_renumbered_index_rejected(self) -> None:
        path = self.root / archive.INDEX
        path.write_bytes(path.read_bytes().replace(b"HS-U01-B001", b"HS-U01-B002", 1))
        self.reject("PASSAGE_INDEX_CHANGED")

    def test_missing_index_row_rejected(self) -> None:
        path = self.root / archive.INDEX
        path.write_bytes(b"\n".join(path.read_bytes().split(b"\n")[:-2]) + b"\n")
        self.reject("PASSAGE_INDEX_CHANGED")

    def test_changed_index_range_rejected(self) -> None:
        path = self.root / archive.INDEX
        path.write_bytes(path.read_bytes().replace(b"\t1\t1\t0\t", b"\t1\t1\t1\t", 1))
        self.reject("PASSAGE_INDEX_CHANGED")

    def test_file_size_bound(self) -> None:
        (self.root / archive.MANIFEST).write_bytes(b" " * 16385)
        self.reject("ARCHIVE_FILE_TOO_LARGE")

    def test_symlink_rejected(self) -> None:
        path = self.root / archive.SOURCE
        path.unlink()
        path.symlink_to(ROOT / archive.SOURCE)
        self.reject("ARCHIVE_SYMLINK")

    def test_commands_are_read_only_and_show_exact_bytes(self) -> None:
        names = (archive.SOURCE, archive.MANIFEST, archive.INDEX)
        before = {name: (self.root / name).read_bytes() for name in names}
        checked = self.cli("check")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertIn(b"authority=none", checked.stdout)
        index = self.cli("index")
        self.assertEqual(index.returncode, 0, index.stderr)
        self.assertEqual(index.stdout, before[archive.INDEX])
        shown = self.cli("show", "HS-U01-B002")
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertEqual(shown.stdout, b"**The interface belongs to the person using it.**")
        after = {name: (self.root / name).read_bytes() for name in names}
        self.assertEqual(before, after)

    def test_unknown_id_and_missing_file_fail(self) -> None:
        result = self.cli("show", "HS-U01-B999")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"UNKNOWN_PASSAGE_ID", result.stderr)
        (self.root / archive.INDEX).unlink()
        result = self.cli("check")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"ARCHIVE_READ_OR_FORMAT_ERROR", result.stderr)

    def test_malformed_manifest_and_cli_usage_fail(self) -> None:
        (self.root / archive.MANIFEST).write_bytes(b"{broken")
        self.assertEqual(self.cli("check").returncode, 1)
        self.assertEqual(self.cli("show").returncode, 2)
        self.assertEqual(self.cli("check", "HS-U01-B002").returncode, 2)


if __name__ == "__main__":
    unittest.main()
