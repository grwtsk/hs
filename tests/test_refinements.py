"""Synthetic archive checks; passing tests do not decide any disagreement."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/book/check_refinements.py"
sys.path.insert(0, str(SCRIPT.parent))
import check_refinements as archive
sys.path.pop(0)

FILES = (archive.SOURCE, archive.MANIFEST, archive.INDEX, archive.PRECEDENCE,
         archive.PROPOSALS, archive.founding.SOURCE, archive.founding.MANIFEST,
         archive.founding.INDEX)


class RefinementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in FILES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)

    def edit(self, path: str, mutate) -> None:
        value = json.loads((self.root / path).read_bytes())
        mutate(value)
        (self.root / path).write_text(json.dumps(value) + "\n", encoding="utf-8")

    def reject(self, pattern: str) -> None:
        with self.assertRaisesRegex(archive.ArchiveError, pattern):
            archive.check(self.root)

    def cli(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run([sys.executable, "-B", str(SCRIPT), *args,
                               "--root", str(self.root)], capture_output=True,
                              check=False, timeout=10)

    def test_capture_counts_and_original_integrity(self) -> None:
        data, rows, turns = archive.check(self.root)
        self.assertEqual(len(data), 5529)
        self.assertEqual(len(rows), 25)
        self.assertEqual([t["id"] for t in turns], [f"HS-U{i:02d}" for i in range(2, 12)])
        self.assertEqual(sum(r["kind"] == "author_paragraph" for r in rows), 15)
        old, _ = archive.founding.check(self.root)
        self.assertEqual(archive.sha256(old), archive.founding.EXPECTED_SHA256)

    def test_wrappers_not_author_paragraphs(self) -> None:
        data, rows, turns = archive.check(self.root)
        self.assertEqual(sum(r["kind"] == "editorial_heading" for r in rows), 10)
        for turn in turns:
            self.assertFalse(data[turn["byte_start"]:turn["byte_end"]].startswith(b"##"))
        manifest = json.loads((self.root / archive.MANIFEST).read_bytes())
        self.assertIn("editorial", manifest["source_role"])
        self.assertEqual(manifest["authority_effect"], "none")

    def test_every_nonblank_line_addressed_once(self) -> None:
        data, rows, _ = archive.check(self.root)
        lines = data.split(b"\n")
        coverage = []
        for row in rows:
            coverage.extend(range(row["line_start"], row["line_end"] + 1))
            chunk = data[row["byte_start"]:row["byte_end"]]
            self.assertEqual(chunk, b"\n".join(lines[row["line_start"]-1:row["line_end"]]))
            self.assertEqual(archive.sha256(chunk), row["sha256"])
        self.assertEqual(coverage, [i for i, line in enumerate(lines, 1) if line.strip()])

    def test_exact_spelling_spaces_and_capture_limit(self) -> None:
        data, _, turns = archive.check(self.root)
        self.assertIn(b"possbile  LLM", data)
        self.assertIn(b"classification and  routing", data)
        self.assertIn(b"witing and mark them explicityly", data)
        self.assertFalse(data.endswith(b"\n"))
        self.assertEqual(turns[-1]["byte_end"], len(data))
        manifest = json.loads((self.root / archive.MANIFEST).read_bytes())
        self.assertTrue(any("two periods" in item for item in manifest["limits"]))

    def test_source_edit_rejected(self) -> None:
        path = self.root / archive.SOURCE
        path.write_bytes(path.read_bytes().replace(b"not presented by a scalar", b"presented by a scalar"))
        self.reject("REFINEMENTS_BYTES_CHANGED")

    def test_newline_and_space_normalization_rejected(self) -> None:
        path = self.root / archive.SOURCE
        old = path.read_bytes()
        for new in (old + b"\n", old.replace(b"\n", b"\r\n"), old.replace(b"possbile  LLM", b"possbile LLM")):
            with self.subTest(length=len(new)):
                path.write_bytes(new)
                self.reject("REFINEMENTS_BYTES_CHANGED")
        path.write_bytes(old)

    def test_missing_research_turn_rejected(self) -> None:
        path = self.root / archive.SOURCE
        path.write_bytes(path.read_bytes().split(b"\n\n## U10", 1)[0])
        self.reject("REFINEMENTS_BYTES_CHANGED")

    def test_coedited_source_manifest_rejected(self) -> None:
        path = self.root / archive.SOURCE
        path.write_bytes(path.read_bytes() + b"accepted")
        self.edit(archive.MANIFEST, lambda v: v.update(sha256=archive.sha256(path.read_bytes())))
        self.reject("REFINEMENTS_BYTES_CHANGED")

    def test_manifest_role_cannot_become_acceptance(self) -> None:
        self.edit(archive.MANIFEST, lambda v: v.update(authority_effect="human_approved"))
        self.reject("REFINEMENTS_MANIFEST_CHANGED")

    def test_changed_index_range_rejected(self) -> None:
        path = self.root / archive.INDEX
        path.write_bytes(path.read_bytes().replace(b"\t1\t1\t0\t", b"\t1\t1\t1\t", 1))
        self.reject("REFINEMENTS_INDEX_CHANGED")

    def test_heading_cannot_be_reclassified_as_author(self) -> None:
        path = self.root / archive.INDEX
        path.write_bytes(path.read_bytes().replace(b"editorial_heading", b"author_paragraph", 1))
        self.reject("REFINEMENTS_INDEX_CHANGED")

    def test_earlier_archive_cannot_be_rewritten(self) -> None:
        path = self.root / archive.founding.SOURCE
        path.write_bytes(path.read_bytes().replace(b"144", b"145", 1))
        self.reject("SOURCE_BYTES_CHANGED")

    def test_all_disagreements_are_mapped_without_adoption(self) -> None:
        archive.check(self.root)
        value = json.loads((self.root / archive.PROPOSALS).read_bytes())
        self.assertEqual(len(value["entries"]), 12)
        self.assertEqual({e["status"] for e in value["entries"]}, {"PROPOSED_NOT_ADOPTED"})
        self.assertEqual(set().union(*(set(e["disagreements"]) for e in value["entries"])), set(archive.DG_OWNERS))

    def test_proposal_cannot_be_marked_adopted(self) -> None:
        self.edit(archive.PROPOSALS, lambda v: v["entries"][0].update(status="HUMAN_ADOPTED"))
        self.reject("UNAUTHORIZED_STATUS_PROMOTION")

    def test_agent_role_cannot_become_author(self) -> None:
        self.edit(archive.PROPOSALS, lambda v: v.update(annotation_author="human"))
        self.reject("LEDGER_ROLE_CHANGED")

    def test_unknown_source_ref_rejected(self) -> None:
        self.edit(archive.PROPOSALS, lambda v: v["entries"][0].update(source_refs=["HS-U01-B999"]))
        self.reject("UNKNOWN_SOURCE_REFERENCE")

    def test_missing_owner_rejected(self) -> None:
        self.edit(archive.PROPOSALS, lambda v: v["entries"][0].update(human_issues=[]))
        self.reject("MISSING_HUMAN_OWNER")

    def test_boolean_owner_rejected(self) -> None:
        self.edit(archive.PROPOSALS, lambda v: v["entries"][0].update(human_issues=[True]))
        self.reject("INVALID_HUMAN_OWNER")

    def test_duplicate_and_missing_proposals_rejected(self) -> None:
        path = self.root / archive.PROPOSALS
        original = path.read_bytes()
        self.edit(archive.PROPOSALS, lambda v: v["entries"].pop())
        self.reject("LEDGER_ENTRY_COVERAGE_CHANGED")
        path.write_bytes(original)
        self.edit(archive.PROPOSALS, lambda v: v["entries"].append(copy.deepcopy(v["entries"][0])))
        self.reject("LEDGER_ENTRY_COVERAGE_CHANGED")

    def test_unknown_disagreement_rejected(self) -> None:
        self.edit(archive.PROPOSALS, lambda v: v["entries"][0].update(disagreements=["DG-99"]))
        self.reject("UNKNOWN_DISAGREEMENT")

    def test_reverse_precedence_rejected(self) -> None:
        self.edit(archive.PRECEDENCE, lambda v: v["entries"][0].update(earlier_refs=["HS-U11-P001"]))
        self.reject("REVERSED_SOURCE_ORDER")

    def test_non_scalar_not_blanket_supersession(self) -> None:
        p = json.loads((self.root / archive.PRECEDENCE).read_bytes())["entries"][5]
        self.assertEqual(p["source_refs"], ["HS-U07-P001"])
        self.assertEqual(p["relation"], "explicit_non_scalar_constraint")
        self.assertIn("U04 did not explicitly command a scalar", p["summary"])
        self.edit(archive.PRECEDENCE, lambda v: v["entries"][5].update(relation="supersedes_all"))
        self.reject("INVALID_RELATION")

    def test_duplicate_nonfinite_and_bool_json_rejected(self) -> None:
        path = self.root / archive.PROPOSALS
        original = path.read_bytes()
        path.write_bytes(original.replace(b'"schema_version": 1,', b'"schema_version": 1, "schema_version": 1,', 1))
        self.reject("DUPLICATE_MANIFEST_KEY")
        path.write_bytes(b'{"x": NaN}')
        self.reject("NONFINITE_MANIFEST_VALUE")
        path.write_bytes(original)
        self.edit(archive.PROPOSALS, lambda v: v.update(schema_version=True))
        self.reject("INVALID_LEDGER_VERSION")

    def test_symlink_path_escape_and_resource_bound(self) -> None:
        path = self.root / archive.SOURCE
        path.unlink()
        path.symlink_to(ROOT / archive.SOURCE)
        self.reject("ARCHIVE_SYMLINK")
        path.unlink()
        path.write_bytes(b"x" * 100001)
        self.reject("ARCHIVE_FILE_TOO_LARGE")
        with self.assertRaisesRegex(archive.ArchiveError, "ARCHIVE_PATH_ESCAPE"):
            archive.founding.read_file(self.root, "../outside", 100)

    def test_cli_is_read_only_and_exact_byte_show(self) -> None:
        before = {p: (self.root / p).read_bytes() for p in FILES}
        checked = self.cli("check")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertIn(b"authority=none", checked.stdout)
        shown = self.cli("show", "HS-U07-P001")
        data, rows, _ = archive.check(self.root)
        row = next(r for r in rows if r["id"] == "HS-U07-P001")
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertEqual(shown.stdout, data[row["byte_start"]:row["byte_end"]])
        whole = self.cli("show", "HS-U08")
        self.assertEqual(whole.returncode, 0, whole.stderr)
        self.assertIn(b"\n\nThe LLM", whole.stdout)
        index = self.cli("index")
        self.assertEqual(index.returncode, 0, index.stderr)
        self.assertEqual(index.stdout, before[archive.INDEX])
        self.assertEqual(before, {p: (self.root / p).read_bytes() for p in FILES})

    def test_unknown_ref_missing_file_and_usage_fail(self) -> None:
        result = self.cli("show", "HS-U99")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"UNKNOWN_REFERENCE", result.stderr)
        (self.root / archive.PROPOSALS).unlink()
        self.assertEqual(self.cli("check").returncode, 1)
        self.assertEqual(self.cli("show").returncode, 2)
        self.assertEqual(self.cli("check", "HS-U02").returncode, 2)


if __name__ == "__main__":
    unittest.main()
